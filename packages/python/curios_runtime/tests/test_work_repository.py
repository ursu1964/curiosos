from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    ProviderId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_persistence import PersistenceError, PersistenceErrorCode, PersistenceStore
from curios_runtime import (
    EXECUTION_TRANSITIONS,
    WORK_ITEM_TRANSITIONS,
    M0WorkRepository,
    RepositoryError,
    RepositoryErrorCode,
    transition_execution_record,
    transition_work_item,
)


def _work(state: WorkItemState = WorkItemState.CREATED) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId),
        work_type="provider_inventory",
        title="Provider inventory",
        objective="Collect provider descriptors.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=state,
    )


def _execution(state: ExecutionState = ExecutionState.CREATED) -> ExecutionRecord:
    return ExecutionRecord(
        execution_id=fixed_id(ExecutionId),
        work_id=fixed_id(WorkId),
        executor_ref=ref_for(ProviderId),
        started_at=UTC_NOW,
        state=state,
    )


@pytest.mark.parametrize(
    ("source", "target"),
    tuple(
        (source, target)
        for source, targets in WORK_ITEM_TRANSITIONS.items()
        for target in sorted(targets, key=lambda state: state.value)
    ),
)
def test_work_item_legal_transitions_preserve_identity_and_update_state(
    source: WorkItemState,
    target: WorkItemState,
) -> None:
    transitioned = transition_work_item(_work(source), target, occurred_at=UTC_LATER)

    assert transitioned.work_id == fixed_id(WorkId)
    assert transitioned.state is target
    assert transitioned.updated_at == UTC_LATER


@pytest.mark.parametrize(
    ("source", "target"),
    (
        (WorkItemState.CREATED, WorkItemState.RUNNING),
        (WorkItemState.CREATED, WorkItemState.COMPLETED),
        (WorkItemState.READY, WorkItemState.COMPLETED),
        (WorkItemState.COMPLETED, WorkItemState.RUNNING),
        (WorkItemState.FAILED, WorkItemState.READY),
        (WorkItemState.CANCELLED, WorkItemState.READY),
    ),
)
def test_work_item_illegal_transitions_are_rejected(
    source: WorkItemState,
    target: WorkItemState,
) -> None:
    with pytest.raises(RepositoryError) as exc:
        transition_work_item(_work(source), target, occurred_at=UTC_LATER)

    assert exc.value.code is RepositoryErrorCode.ILLEGAL_TRANSITION
    assert "Illegal work transition" in str(exc.value)


def test_repeated_work_item_transition_is_idempotent() -> None:
    item = _work(WorkItemState.READY)

    assert transition_work_item(item, WorkItemState.READY, occurred_at=UTC_LATER) is item


@pytest.mark.parametrize(
    ("source", "target"),
    tuple(
        (source, target)
        for source, targets in EXECUTION_TRANSITIONS.items()
        for target in sorted(targets, key=lambda state: state.value)
    ),
)
def test_execution_legal_transitions_preserve_identity_and_set_terminal_end_time(
    source: ExecutionState,
    target: ExecutionState,
) -> None:
    transitioned = transition_execution_record(_execution(source), target, occurred_at=UTC_LATER)

    assert transitioned.execution_id == fixed_id(ExecutionId)
    assert transitioned.work_id == fixed_id(WorkId)
    assert transitioned.state is target
    if target in {ExecutionState.SUCCEEDED, ExecutionState.FAILED, ExecutionState.CANCELLED}:
        assert transitioned.ended_at == UTC_LATER
    else:
        assert transitioned.ended_at is None


@pytest.mark.parametrize(
    ("source", "target"),
    (
        (ExecutionState.CREATED, ExecutionState.SUCCEEDED),
        (ExecutionState.CREATED, ExecutionState.FAILED),
        (ExecutionState.SUCCEEDED, ExecutionState.RUNNING),
        (ExecutionState.FAILED, ExecutionState.RUNNING),
        (ExecutionState.CANCELLED, ExecutionState.RUNNING),
    ),
)
def test_execution_illegal_transitions_are_rejected(
    source: ExecutionState,
    target: ExecutionState,
) -> None:
    with pytest.raises(RepositoryError) as exc:
        transition_execution_record(_execution(source), target, occurred_at=UTC_LATER)

    assert exc.value.code is RepositoryErrorCode.ILLEGAL_TRANSITION
    assert "Illegal execution transition" in str(exc.value)


def test_repeated_execution_transition_is_idempotent() -> None:
    record = _execution(ExecutionState.RUNNING)

    assert (
        transition_execution_record(record, ExecutionState.RUNNING, occurred_at=UTC_LATER) is record
    )


def test_missing_work_and_execution_are_bounded_repository_errors() -> None:
    repository = M0WorkRepository(_MissingStore())

    with pytest.raises(RepositoryError) as missing_work:
        repository.transition_work(fixed_id(WorkId), WorkItemState.READY, occurred_at=UTC_LATER)
    with pytest.raises(RepositoryError) as missing_execution:
        repository.transition_execution(
            fixed_id(ExecutionId),
            ExecutionState.RUNNING,
            occurred_at=UTC_LATER,
        )

    assert missing_work.value.code is RepositoryErrorCode.NOT_FOUND
    assert missing_execution.value.code is RepositoryErrorCode.NOT_FOUND


def test_repository_translates_persistence_failures_without_native_leakage() -> None:
    repository = M0WorkRepository(_FailingStore())

    with pytest.raises(RepositoryError) as exc:
        repository.create_work(_work())

    serialized = exc.value.to_json_compatible()
    assert serialized == {
        "code": "PERSISTENCE_FAILURE",
        "message": "Work repository persistence operation failed.",
        "retryable": True,
        "operation": "create_work",
    }
    assert "SELECT provider_native_detail" not in str(exc.value)


class _MissingStore(PersistenceStore):
    def __init__(self) -> None:
        pass

    @contextmanager
    def transaction(self) -> Iterator[_MissingTransaction]:  # type: ignore[override]
        yield _MissingTransaction()


class _MissingTransaction:
    def read_record(self, kind: object, record_id: str) -> None:
        return None


class _FailingStore(PersistenceStore):
    def __init__(self) -> None:
        pass

    @contextmanager
    def transaction(self) -> Iterator[object]:  # type: ignore[override]
        raise PersistenceError(
            PersistenceErrorCode.CONNECTIVITY,
            "native SELECT provider_native_detail failed",
            retryable=True,
            operation="transaction",
            cause_type="OperationalError",
        )
        yield object()
