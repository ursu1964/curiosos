"""M0 work and execution repositories backed by Curios persistence primitives."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import NoReturn

from curios_contracts import (
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    UtcTimestamp,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
    canonical_to_record,
    record_to_canonical,
)

WORK_ITEM_TRANSITIONS: dict[WorkItemState, frozenset[WorkItemState]] = {
    WorkItemState.CREATED: frozenset({WorkItemState.READY, WorkItemState.CANCELLED}),
    WorkItemState.READY: frozenset({WorkItemState.RUNNING, WorkItemState.CANCELLED}),
    WorkItemState.RUNNING: frozenset(
        {
            WorkItemState.WAITING,
            WorkItemState.COMPLETED,
            WorkItemState.FAILED,
            WorkItemState.CANCELLED,
        }
    ),
    WorkItemState.WAITING: frozenset(
        {
            WorkItemState.RUNNING,
            WorkItemState.FAILED,
            WorkItemState.CANCELLED,
        }
    ),
    WorkItemState.COMPLETED: frozenset(),
    WorkItemState.FAILED: frozenset(),
    WorkItemState.CANCELLED: frozenset(),
}

EXECUTION_TRANSITIONS: dict[ExecutionState, frozenset[ExecutionState]] = {
    ExecutionState.CREATED: frozenset({ExecutionState.RUNNING, ExecutionState.CANCELLED}),
    ExecutionState.RUNNING: frozenset(
        {
            ExecutionState.WAITING,
            ExecutionState.SUCCEEDED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        }
    ),
    ExecutionState.WAITING: frozenset(
        {
            ExecutionState.RUNNING,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        }
    ),
    ExecutionState.SUCCEEDED: frozenset(),
    ExecutionState.FAILED: frozenset(),
    ExecutionState.CANCELLED: frozenset(),
}


class RepositoryErrorCode(StrEnum):
    """Stable repository failure categories for M0 work persistence."""

    CONFLICT = "CONFLICT"
    ILLEGAL_TRANSITION = "ILLEGAL_TRANSITION"
    NOT_FOUND = "NOT_FOUND"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"


class RepositoryError(RuntimeError):
    """Bounded M0 repository error that does not leak database-native details."""

    def __init__(
        self,
        code: RepositoryErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
    ) -> None:
        super().__init__(message)
        self.code = RepositoryErrorCode(code)
        self.retryable = retryable
        self.operation = operation

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": str(self),
            "retryable": self.retryable,
            "operation": self.operation,
        }


@dataclass(frozen=True, slots=True)
class StoredWorkItem:
    """A persisted work item plus its optimistic concurrency version."""

    item: WorkItem
    version: str


@dataclass(frozen=True, slots=True)
class StoredExecutionRecord:
    """A persisted execution record plus its optimistic concurrency version."""

    record: ExecutionRecord
    version: str


class M0WorkRepository:
    """Repository boundary for M0 WorkItem and ExecutionRecord records."""

    def __init__(self, store: PersistenceStore) -> None:
        if not isinstance(store, PersistenceStore):
            msg = "store must be a PersistenceStore"
            raise TypeError(msg)
        self._store = store

    def create_work(self, item: WorkItem) -> StoredWorkItem:
        """Persist a new work item without scheduling or executing it."""
        if not isinstance(item, WorkItem):
            msg = "item must be a WorkItem"
            raise TypeError(msg)
        record = canonical_to_record(item)
        try:
            with self._store.transaction() as transaction:
                transaction.insert_record(record)
        except PersistenceError as exc:
            _raise_repository_error(_translate_persistence_error(exc, operation="create_work"))
        return StoredWorkItem(item=item, version=_record_version(record))

    def read_work(self, work_id: WorkId) -> StoredWorkItem | None:
        """Read a persisted work item by canonical work ID."""
        return self._read_work(work_id, operation="read_work")

    def _read_work(self, work_id: WorkId, *, operation: str) -> StoredWorkItem | None:
        if not isinstance(work_id, WorkId):
            msg = "work_id must be a WorkId"
            raise TypeError(msg)
        error: RepositoryError | None = None
        try:
            with self._store.transaction() as transaction:
                record = transaction.read_record(PersistenceRecordKind.WORK, str(work_id))
        except PersistenceError as exc:
            error = _translate_persistence_error(exc, operation=operation)
        if error is not None:
            _raise_repository_error(error)
        if record is None:
            return None
        item = _decode_work_record(record, operation=operation)
        return StoredWorkItem(item=item, version=_record_version(record))

    def transition_work(
        self,
        work_id: WorkId,
        target_state: WorkItemState,
        *,
        occurred_at: UtcTimestamp,
        expected_version: str | None = None,
    ) -> StoredWorkItem:
        """Move a work item through an allowed M0 state transition."""
        target_state = WorkItemState(target_state)
        current = self._read_work(work_id, operation="transition_work")
        if current is None:
            _raise_repository_error(_not_found("transition_work", f"work {work_id} was not found"))
        if expected_version is not None and expected_version != current.version:
            _raise_repository_error(_conflict("transition_work"))
        transitioned = transition_work_item(
            current.item,
            target_state,
            occurred_at=occurred_at,
        )
        if transitioned == current.item:
            return current
        return self._replace_work(current, transitioned)

    def create_execution(self, record: ExecutionRecord) -> StoredExecutionRecord:
        """Persist a new execution-attempt record without invoking an executor."""
        if not isinstance(record, ExecutionRecord):
            msg = "record must be an ExecutionRecord"
            raise TypeError(msg)
        stored = canonical_to_record(record)
        try:
            with self._store.transaction() as transaction:
                transaction.insert_record(stored)
        except PersistenceError as exc:
            _raise_repository_error(_translate_persistence_error(exc, operation="create_execution"))
        return StoredExecutionRecord(record=record, version=_record_version(stored))

    def read_execution(self, execution_id: ExecutionId) -> StoredExecutionRecord | None:
        """Read a persisted execution-attempt record by canonical execution ID."""
        return self._read_execution(execution_id, operation="read_execution")

    def _read_execution(
        self,
        execution_id: ExecutionId,
        *,
        operation: str,
    ) -> StoredExecutionRecord | None:
        if not isinstance(execution_id, ExecutionId):
            msg = "execution_id must be an ExecutionId"
            raise TypeError(msg)
        error: RepositoryError | None = None
        try:
            with self._store.transaction() as transaction:
                record = transaction.read_record(
                    PersistenceRecordKind.EXECUTION,
                    str(execution_id),
                )
        except PersistenceError as exc:
            error = _translate_persistence_error(exc, operation=operation)
        if error is not None:
            _raise_repository_error(error)
        if record is None:
            return None
        execution = _decode_execution_record(record, operation=operation)
        return StoredExecutionRecord(record=execution, version=_record_version(record))

    def transition_execution(
        self,
        execution_id: ExecutionId,
        target_state: ExecutionState,
        *,
        occurred_at: UtcTimestamp,
        expected_version: str | None = None,
    ) -> StoredExecutionRecord:
        """Move an execution attempt through an allowed M0 state transition."""
        target_state = ExecutionState(target_state)
        current = self._read_execution(execution_id, operation="transition_execution")
        if current is None:
            _raise_repository_error(
                _not_found("transition_execution", f"execution {execution_id} was not found")
            )
        if expected_version is not None and expected_version != current.version:
            _raise_repository_error(_conflict("transition_execution"))
        transitioned = transition_execution_record(
            current.record,
            target_state,
            occurred_at=occurred_at,
        )
        if transitioned == current.record:
            return current
        return self._replace_execution(current, transitioned)

    def _replace_work(self, current: StoredWorkItem, item: WorkItem) -> StoredWorkItem:
        record = canonical_to_record(item)
        try:
            with self._store.transaction() as transaction:
                transaction.replace_record(record, expected_payload_sha256=current.version)
        except PersistenceError as exc:
            _raise_repository_error(_translate_persistence_error(exc, operation="transition_work"))
        return StoredWorkItem(item=item, version=_record_version(record))

    def _replace_execution(
        self,
        current: StoredExecutionRecord,
        record: ExecutionRecord,
    ) -> StoredExecutionRecord:
        stored = canonical_to_record(record)
        try:
            with self._store.transaction() as transaction:
                transaction.replace_record(stored, expected_payload_sha256=current.version)
        except PersistenceError as exc:
            _raise_repository_error(
                _translate_persistence_error(exc, operation="transition_execution")
            )
        return StoredExecutionRecord(record=record, version=_record_version(stored))


def transition_work_item(
    item: WorkItem,
    target_state: WorkItemState,
    *,
    occurred_at: UtcTimestamp,
) -> WorkItem:
    """Return a work item moved to an allowed M0 state, or unchanged if repeated."""
    if not isinstance(item, WorkItem):
        msg = "item must be a WorkItem"
        raise TypeError(msg)
    target_state = WorkItemState(target_state)
    occurred_at = UtcTimestamp(occurred_at)
    if target_state is item.state:
        return item
    if target_state not in WORK_ITEM_TRANSITIONS[item.state]:
        _raise_repository_error(
            RepositoryError(
                RepositoryErrorCode.ILLEGAL_TRANSITION,
                f"Illegal work transition {item.state.value} -> {target_state.value}.",
                retryable=False,
                operation="transition_work",
            )
        )
    return WorkItem(
        work_id=item.work_id,
        work_type=item.work_type,
        title=item.title,
        objective=item.objective,
        dependencies=item.dependencies,
        required_capabilities=item.required_capabilities,
        inputs=item.inputs,
        expected_outputs=item.expected_outputs,
        policy_constraint_refs=item.policy_constraint_refs,
        authority_ref=item.authority_ref,
        principal_ref=item.principal_ref,
        evidence_requirement_refs=item.evidence_requirement_refs,
        created_at=item.created_at,
        updated_at=occurred_at,
        state=target_state,
    )


def transition_execution_record(
    record: ExecutionRecord,
    target_state: ExecutionState,
    *,
    occurred_at: UtcTimestamp,
) -> ExecutionRecord:
    """Return an execution record moved to an allowed M0 state, or unchanged if repeated."""
    if not isinstance(record, ExecutionRecord):
        msg = "record must be an ExecutionRecord"
        raise TypeError(msg)
    target_state = ExecutionState(target_state)
    occurred_at = UtcTimestamp(occurred_at)
    if target_state is record.state:
        return record
    if target_state not in EXECUTION_TRANSITIONS[record.state]:
        _raise_repository_error(
            RepositoryError(
                RepositoryErrorCode.ILLEGAL_TRANSITION,
                f"Illegal execution transition {record.state.value} -> {target_state.value}.",
                retryable=False,
                operation="transition_execution",
            )
        )
    return ExecutionRecord(
        execution_id=record.execution_id,
        work_id=record.work_id,
        executor_ref=record.executor_ref,
        agent_instance_id=record.agent_instance_id,
        provider_refs=record.provider_refs,
        started_at=record.started_at,
        ended_at=occurred_at if target_state in _TERMINAL_EXECUTION_STATES else record.ended_at,
        state=target_state,
        result=record.result,
        evidence_refs=record.evidence_refs,
        error_refs=record.error_refs,
        errors=record.errors,
        observability_context=record.observability_context,
    )


_TERMINAL_EXECUTION_STATES = frozenset(
    {ExecutionState.SUCCEEDED, ExecutionState.FAILED, ExecutionState.CANCELLED}
)


def _record_version(record: PersistenceRecord) -> str:
    encoded = json.dumps(
        record.payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _decode_work_record(record: PersistenceRecord, *, operation: str) -> WorkItem:
    error: RepositoryError | None = None
    try:
        item = record_to_canonical(record)
    except Exception:
        error = _corrupt_record(operation, "work", "WorkItem")
    else:
        if isinstance(item, WorkItem):
            return item
        error = _corrupt_record(operation, "work", "WorkItem")
    _raise_repository_error(error)


def _decode_execution_record(record: PersistenceRecord, *, operation: str) -> ExecutionRecord:
    error: RepositoryError | None = None
    try:
        execution = record_to_canonical(record)
    except Exception:
        error = _corrupt_record(operation, "execution", "ExecutionRecord")
    else:
        if isinstance(execution, ExecutionRecord):
            return execution
        error = _corrupt_record(operation, "execution", "ExecutionRecord")
    _raise_repository_error(error)


def _translate_persistence_error(exc: PersistenceError, *, operation: str) -> RepositoryError:
    if exc.code is PersistenceErrorCode.CONFLICT:
        return _conflict(operation)
    return RepositoryError(
        RepositoryErrorCode.PERSISTENCE_FAILURE,
        "Work repository persistence operation failed.",
        retryable=exc.retryable,
        operation=operation,
    )


def _corrupt_record(operation: str, record_name: str, canonical_name: str) -> RepositoryError:
    return RepositoryError(
        RepositoryErrorCode.PERSISTENCE_FAILURE,
        f"Persisted {record_name} record did not decode as {canonical_name}.",
        retryable=False,
        operation=operation,
    )


def _conflict(operation: str) -> RepositoryError:
    return RepositoryError(
        RepositoryErrorCode.CONFLICT,
        "Repository record version conflicts with existing state.",
        retryable=False,
        operation=operation,
    )


def _not_found(operation: str, message: str) -> RepositoryError:
    return RepositoryError(
        RepositoryErrorCode.NOT_FOUND,
        message,
        retryable=False,
        operation=operation,
    )


def _raise_repository_error(error: RepositoryError) -> NoReturn:
    raise error from None
