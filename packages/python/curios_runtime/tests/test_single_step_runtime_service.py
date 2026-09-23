from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, contract_error, fixed_id, ref_for
from curios_contracts import (
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ExecutionId,
    Principal,
    ProviderId,
    Result,
    RuntimeEventType,
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
)
from curios_policy import MinimalM0PolicyEvaluator
from curios_runtime import (
    EventEvidenceRuntimeStore,
    M0WorkRepository,
    SingleStepExecutionOutcome,
    SingleStepExecutionRequest,
    SingleStepRuntimeError,
    SingleStepRuntimeErrorCode,
    SingleStepRuntimeRequest,
    SingleStepRuntimeService,
    SingleStepRuntimeStatus,
)


def test_single_step_completes_authorized_work_and_records_runtime_facts() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    evidence = _evidence()
    executor = _Executor(SingleStepExecutionOutcome(Result.success({"inventory": []}), (evidence,)))
    service = _service(repository, event_store, executor)

    result = service.run_once(_request())

    assert result.status is SingleStepRuntimeStatus.COMPLETED
    assert result.work.item.state is WorkItemState.COMPLETED
    assert result.execution is not None
    assert result.execution.record.state.value == "SUCCEEDED"
    assert result.executor_result == Result.success({"inventory": []})
    assert result.evidence_refs == (evidence,)
    assert tuple(event.event_type for event in result.events) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
        RuntimeEventType.EVIDENCE_PRODUCED.value,
        RuntimeEventType.EXECUTION_COMPLETED.value,
    )
    assert event_store.require_evidence(evidence.evidence_id) == evidence
    assert repository.read_work(fixed_id(WorkId)).item.state is WorkItemState.COMPLETED  # type: ignore[union-attr]
    assert (
        repository.read_execution(fixed_id(ExecutionId)).record.state.value == "SUCCEEDED"  # type: ignore[union-attr]
    )
    assert executor.requests[0].work.state is WorkItemState.RUNNING
    assert executor.requests[0].policy_decision.is_authorizing


def test_policy_unknown_blocks_effects_without_invoking_executor_or_changing_work() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    executor = _Executor()
    service = _service(repository, event_store, executor)

    result = service.run_once(_request(policy_state_known=False))

    assert result.status is SingleStepRuntimeStatus.BLOCKED
    assert result.policy_decision.outcome.value == "UNKNOWN"
    assert result.work.item.state is WorkItemState.CREATED
    assert result.execution is None
    assert executor.requests == ()
    assert tuple(event.event_type for event in event_store.list_events()) == (
        RuntimeEventType.POLICY_EVALUATED.value,
    )
    assert repository.read_work(fixed_id(WorkId)).item.state is WorkItemState.CREATED  # type: ignore[union-attr]


def test_policy_denial_blocks_unsupported_work_type_without_executor_invocation() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work(work_type="model_generation"))
    executor = _Executor()
    service = _service(repository, event_store, executor)

    result = service.run_once(_request())

    assert result.status is SingleStepRuntimeStatus.BLOCKED
    assert result.policy_decision.outcome.value == "DENY"
    assert result.policy_decision.is_authorizing is False
    assert executor.requests == ()
    assert repository.read_work(fixed_id(WorkId)).item.state is WorkItemState.CREATED  # type: ignore[union-attr]


def test_executor_failure_marks_failed_without_native_exception_leakage() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    service = _service(repository, event_store, _RaisingExecutor(RuntimeError("native detail")))

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.EXECUTOR_FAILURE
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert error.value.__suppress_context__ is True
    assert "native detail" not in str(error.value)
    assert error.value.detail == {"cause_type": "RuntimeError"}
    assert repository.read_work(fixed_id(WorkId)).item.state is WorkItemState.FAILED  # type: ignore[union-attr]
    assert repository.read_execution(fixed_id(ExecutionId)).record.state.value == "FAILED"  # type: ignore[union-attr]
    assert tuple(event.event_type for event in event_store.list_events()) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
        RuntimeEventType.EXECUTION_FAILED.value,
    )


def test_executor_failure_result_marks_work_failed_and_returns_bounded_result() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    failure: Result[object] = Result.failure((contract_error(),))
    service = _service(repository, event_store, _Executor(SingleStepExecutionOutcome(failure)))

    result = service.run_once(_request())

    assert result.status is SingleStepRuntimeStatus.FAILED
    assert result.executor_result == failure
    assert result.work.item.state is WorkItemState.FAILED
    assert result.execution is not None
    assert result.execution.record.state.value == "FAILED"


def test_missing_work_translates_repository_absence_without_lower_error_leakage() -> None:
    service = _service(
        M0WorkRepository(_MemoryPersistenceStore()),
        EventEvidenceRuntimeStore(_MemoryPersistenceStore()),
        _Executor(),
    )

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.NOT_FOUND
    assert error.value.operation == "read_work"
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert error.value.__suppress_context__ is True


def test_event_store_failure_prevents_executor_and_preserves_work_state() -> None:
    store = _FailingInsertStore()
    repository = M0WorkRepository(store)
    repository.create_work(_work())
    executor = _Executor()
    service = _service(repository, EventEvidenceRuntimeStore(store), executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.RUNTIME_STORE_FAILURE
    assert error.value.__cause__ is None
    assert executor.requests == ()
    assert repository.read_work(fixed_id(WorkId)).item.state is WorkItemState.CREATED  # type: ignore[union-attr]


def test_non_startable_work_fails_before_executor_invocation() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work(state=WorkItemState.COMPLETED))
    executor = _Executor()
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.ILLEGAL_STATE
    assert error.value.detail == {"work_state": "COMPLETED"}
    assert executor.requests == ()
    assert repository.read_work(fixed_id(WorkId)).item.state is WorkItemState.COMPLETED  # type: ignore[union-attr]


def _service(
    repository: M0WorkRepository,
    event_store: EventEvidenceRuntimeStore,
    executor: object,
) -> SingleStepRuntimeService:
    return SingleStepRuntimeService(
        work_repository=repository,
        event_store=event_store,
        policy_evaluator=MinimalM0PolicyEvaluator(),
        executor=executor,  # type: ignore[arg-type]
    )


def _request(*, policy_state_known: bool = True) -> SingleStepRuntimeRequest:
    return SingleStepRuntimeRequest(
        work_id=fixed_id(WorkId),
        principal=Principal.from_json_compatible(
            {
                "principal_type": "HUMAN",
                "identity": "operator@example.test",
                "principal_ref": ref_for(ProviderId).to_json_compatible(),
            }
        ),
        producer_ref=ref_for(ProviderId),
        executor_ref=ref_for(ProviderId),
        scope="project sandbox",
        resource_refs=(ref_for(ProviderId),),
        policy_state_known=policy_state_known,
        occurred_at=UTC_LATER,
        execution_id=fixed_id(ExecutionId),
    )


def _work(
    *,
    work_type: str = "provider_inventory",
    state: WorkItemState = WorkItemState.CREATED,
) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId),
        work_type=work_type,
        title="Provider inventory",
        objective="Collect provider descriptors.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=state,
    )


def _evidence() -> EvidenceReference:
    return EvidenceReference(
        evidence_id=fixed_id(EvidenceId),
        kind=EvidenceKind.PROVIDER_REPORT,
        subject_ref=ref_for(WorkId),
        collected_at=UTC_LATER,
        summary="Provider inventory executor evidence.",
    )


class _Executor:
    def __init__(self, outcome: SingleStepExecutionOutcome | None = None) -> None:
        self._outcome = outcome or SingleStepExecutionOutcome(Result.success())
        self._requests: list[SingleStepExecutionRequest] = []

    @property
    def requests(self) -> tuple[SingleStepExecutionRequest, ...]:
        return tuple(self._requests)

    def execute(self, request: SingleStepExecutionRequest) -> SingleStepExecutionOutcome:
        self._requests.append(request)
        return self._outcome


class _RaisingExecutor:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def execute(self, request: SingleStepExecutionRequest) -> SingleStepExecutionOutcome:
        raise self._error


class _MemoryPersistenceStore(PersistenceStore):
    def __init__(self) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {}
        self._order: list[tuple[PersistenceRecordKind, str]] = []

    @contextmanager
    def transaction(self) -> Iterator[_MemoryTransaction]:  # type: ignore[override]
        yield _MemoryTransaction(self)


class _FailingInsertStore(_MemoryPersistenceStore):
    @contextmanager
    def transaction(self) -> Iterator[_FailingInsertTransaction]:  # type: ignore[override]
        yield _FailingInsertTransaction(self)


class _MemoryTransaction:
    def __init__(self, store: _MemoryPersistenceStore) -> None:
        self._store = store

    def insert_record(self, record: PersistenceRecord) -> None:
        key = (record.kind, record.record_id)
        if key in self._store._records:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "duplicate",
                retryable=False,
                operation=f"insert_{record.kind.value}",
            )
        self._store._records[key] = record
        self._store._order.append(key)

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        return self._store._records.get((PersistenceRecordKind(kind), record_id))

    def list_records(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
    ) -> tuple[PersistenceRecord, ...]:
        normalized_kind = PersistenceRecordKind(kind)
        records = (
            self._store._records[key] for key in self._store._order if key[0] is normalized_kind
        )
        return tuple(_take(records, limit=limit))

    def replace_record(self, record: PersistenceRecord, *, expected_payload_sha256: str) -> None:
        key = (record.kind, record.record_id)
        current = self._store._records.get(key)
        if current is None or _record_version(current) != expected_payload_sha256:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "version conflict",
                retryable=False,
                operation=f"replace_{record.kind.value}",
            )
        self._store._records[key] = record


class _FailingInsertTransaction(_MemoryTransaction):
    def insert_record(self, record: PersistenceRecord) -> None:
        if record.kind is PersistenceRecordKind.EVENT:
            raise PersistenceError(
                PersistenceErrorCode.CONNECTIVITY,
                "database native detail",
                retryable=True,
                operation="insert_event",
                cause_type="OperationalError",
            )
        super().insert_record(record)


def _take(values: Iterator[PersistenceRecord], *, limit: int) -> list[PersistenceRecord]:
    output: list[PersistenceRecord] = []
    for value in values:
        if len(output) == limit:
            break
        output.append(value)
    return output


def _record_version(record: PersistenceRecord) -> str:
    encoded = json.dumps(
        record.payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
