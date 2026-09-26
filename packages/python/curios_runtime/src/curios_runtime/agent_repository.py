"""M1 agent definition and disposable instance persistence boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import NoReturn

from curios_contracts import AgentDefinition, AgentDefinitionId, AgentInstance, AgentInstanceId
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
    canonical_to_record,
    record_to_canonical,
)


class AgentRepositoryErrorCode(StrEnum):
    """Stable failure categories for M1 agent persistence."""

    CONFLICT = "CONFLICT"
    CORRUPT_RECORD = "CORRUPT_RECORD"
    NOT_FOUND = "NOT_FOUND"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"


class AgentRepositoryError(RuntimeError):
    """Bounded M1 agent repository error without persistence-native leakage."""

    def __init__(
        self,
        code: AgentRepositoryErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
    ) -> None:
        super().__init__(message)
        self.code = AgentRepositoryErrorCode(code)
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
class StoredAgentDefinition:
    """A persisted agent definition plus its optimistic concurrency version."""

    definition: AgentDefinition
    version: str


@dataclass(frozen=True, slots=True)
class StoredAgentInstance:
    """A persisted disposable agent instance plus its optimistic concurrency version."""

    instance: AgentInstance
    version: str


class M1AgentRepository:
    """Repository boundary for canonical M1 agent definitions and instances."""

    def __init__(self, store: PersistenceStore) -> None:
        if not isinstance(store, PersistenceStore):
            msg = "store must be a PersistenceStore"
            raise TypeError(msg)
        self._store = store

    def create_definition(self, definition: AgentDefinition) -> StoredAgentDefinition:
        """Persist a canonical agent definition without granting runtime authority."""
        if not isinstance(definition, AgentDefinition):
            msg = "definition must be an AgentDefinition"
            raise TypeError(msg)
        record = canonical_to_record(definition)
        try:
            with self._store.transaction() as transaction:
                transaction.insert_record(record)
        except PersistenceError as exc:
            _raise_agent_error(_translate_persistence_error(exc, operation="create_definition"))
        return StoredAgentDefinition(definition=definition, version=_record_version(record))

    def read_definition(
        self,
        agent_definition_id: AgentDefinitionId,
    ) -> StoredAgentDefinition | None:
        """Read a persisted canonical agent definition by ID."""
        if not isinstance(agent_definition_id, AgentDefinitionId):
            msg = "agent_definition_id must be an AgentDefinitionId"
            raise TypeError(msg)
        error: AgentRepositoryError | None = None
        try:
            with self._store.transaction() as transaction:
                record = transaction.read_record(
                    PersistenceRecordKind.AGENT_DEFINITION,
                    str(agent_definition_id),
                )
        except PersistenceError as exc:
            error = _translate_persistence_error(exc, operation="read_definition")
        if error is not None:
            _raise_agent_error(error)
        if record is None:
            return None
        definition = _record_to_definition(record, operation="read_definition")
        return StoredAgentDefinition(definition=definition, version=_record_version(record))

    def list_definitions(self, *, limit: int) -> tuple[StoredAgentDefinition, ...]:
        """List persisted agent definitions in deterministic append order."""
        try:
            with self._store.transaction() as transaction:
                records = transaction.list_records(
                    PersistenceRecordKind.AGENT_DEFINITION,
                    limit=limit,
                )
        except PersistenceError as exc:
            _raise_agent_error(_translate_persistence_error(exc, operation="list_definitions"))
        return tuple(
            StoredAgentDefinition(
                definition=_record_to_definition(record, operation="list_definitions"),
                version=_record_version(record),
            )
            for record in records
        )

    def create_instance(self, instance: AgentInstance) -> StoredAgentInstance:
        """Persist a canonical disposable agent instance without lifecycle execution."""
        if not isinstance(instance, AgentInstance):
            msg = "instance must be an AgentInstance"
            raise TypeError(msg)
        definition = self.read_definition(instance.agent_definition_id)
        if definition is None:
            _raise_agent_error(
                AgentRepositoryError(
                    AgentRepositoryErrorCode.NOT_FOUND,
                    f"Agent definition {instance.agent_definition_id} was not found.",
                    retryable=False,
                    operation="create_instance",
                )
            )
        record = canonical_to_record(instance)
        try:
            with self._store.transaction() as transaction:
                transaction.insert_record(record)
        except PersistenceError as exc:
            _raise_agent_error(_translate_persistence_error(exc, operation="create_instance"))
        return StoredAgentInstance(instance=instance, version=_record_version(record))

    def read_instance(self, agent_instance_id: AgentInstanceId) -> StoredAgentInstance | None:
        """Read a persisted canonical agent instance by ID."""
        if not isinstance(agent_instance_id, AgentInstanceId):
            msg = "agent_instance_id must be an AgentInstanceId"
            raise TypeError(msg)
        error: AgentRepositoryError | None = None
        try:
            with self._store.transaction() as transaction:
                record = transaction.read_record(
                    PersistenceRecordKind.AGENT_INSTANCE,
                    str(agent_instance_id),
                )
        except PersistenceError as exc:
            error = _translate_persistence_error(exc, operation="read_instance")
        if error is not None:
            _raise_agent_error(error)
        if record is None:
            return None
        instance = _record_to_instance(record, operation="read_instance")
        return StoredAgentInstance(instance=instance, version=_record_version(record))

    def list_instances(self, *, limit: int) -> tuple[StoredAgentInstance, ...]:
        """List persisted disposable agent instances in deterministic append order."""
        try:
            with self._store.transaction() as transaction:
                records = transaction.list_records(
                    PersistenceRecordKind.AGENT_INSTANCE,
                    limit=limit,
                )
        except PersistenceError as exc:
            _raise_agent_error(_translate_persistence_error(exc, operation="list_instances"))
        return tuple(
            StoredAgentInstance(
                instance=_record_to_instance(record, operation="list_instances"),
                version=_record_version(record),
            )
            for record in records
        )


def _record_to_definition(record: PersistenceRecord, *, operation: str) -> AgentDefinition:
    if record.kind is not PersistenceRecordKind.AGENT_DEFINITION:
        _raise_agent_error(_corrupt_record(operation, "agent definition", "AgentDefinition"))
    try:
        value = record_to_canonical(record)
    except Exception:
        _raise_agent_error(_corrupt_record(operation, "agent definition", "AgentDefinition"))
    if isinstance(value, AgentDefinition):
        return value
    _raise_agent_error(_corrupt_record(operation, "agent definition", "AgentDefinition"))


def _record_to_instance(record: PersistenceRecord, *, operation: str) -> AgentInstance:
    if record.kind is not PersistenceRecordKind.AGENT_INSTANCE:
        _raise_agent_error(_corrupt_record(operation, "agent instance", "AgentInstance"))
    try:
        value = record_to_canonical(record)
    except Exception:
        _raise_agent_error(_corrupt_record(operation, "agent instance", "AgentInstance"))
    if isinstance(value, AgentInstance):
        return value
    _raise_agent_error(_corrupt_record(operation, "agent instance", "AgentInstance"))


def _record_version(record: PersistenceRecord) -> str:
    encoded = json.dumps(
        record.payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _translate_persistence_error(
    exc: PersistenceError,
    *,
    operation: str,
) -> AgentRepositoryError:
    if exc.code is PersistenceErrorCode.CONFLICT:
        return AgentRepositoryError(
            AgentRepositoryErrorCode.CONFLICT,
            "Agent repository record conflicts with existing state.",
            retryable=False,
            operation=operation,
        )
    return AgentRepositoryError(
        AgentRepositoryErrorCode.PERSISTENCE_FAILURE,
        "Agent repository persistence operation failed.",
        retryable=exc.retryable,
        operation=operation,
    )


def _corrupt_record(
    operation: str,
    record_name: str,
    canonical_name: str,
) -> AgentRepositoryError:
    return AgentRepositoryError(
        AgentRepositoryErrorCode.CORRUPT_RECORD,
        f"Persisted {record_name} record did not decode as {canonical_name}.",
        retryable=False,
        operation=operation,
    )


def _raise_agent_error(error: AgentRepositoryError) -> NoReturn:
    raise error from None
