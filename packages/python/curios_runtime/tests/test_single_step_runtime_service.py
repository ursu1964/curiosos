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
    ExecutionState,
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
    assert len(service.executor.requests) == 1  # type: ignore[attr-defined]


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
    assert tuple(event.event_type for event in result.events) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
        RuntimeEventType.EXECUTION_FAILED.value,
    )


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


def test_policy_evaluator_failure_is_pre_executor_and_bounded() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    executor = _Executor()
    service = SingleStepRuntimeService(
        work_repository=repository,
        event_store=event_store,
        policy_evaluator=_RaisingPolicyEvaluator(RuntimeError("policy native detail")),  # type: ignore[arg-type]
        executor=executor,
    )

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.POLICY_FAILURE
    assert error.value.__cause__ is None
    assert "policy native detail" not in str(error.value)
    assert _work_state(repository) is WorkItemState.CREATED
    assert _execution_state(repository) is None
    assert _event_types(event_store) == ()
    assert _evidence_ids(event_store) == ()
    assert executor.requests == ()


def test_policy_event_failure_is_pre_executor_and_preserves_work_state() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_insert_event(RuntimeEventType.POLICY_EVALUATED)
    executor = _Executor()
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.RUNTIME_STORE_FAILURE
    assert error.value.__cause__ is None
    assert _work_state(repository) is WorkItemState.CREATED
    assert _execution_state(repository) is None
    assert _event_types(event_store) == ()
    assert _evidence_ids(event_store) == ()
    assert executor.requests == ()


def test_pre_executor_work_transition_failure_does_not_create_execution() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_replace_work(WorkItemState.READY)
    executor = _Executor()
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.REPOSITORY_FAILURE
    assert _work_state(repository) is WorkItemState.CREATED
    assert _execution_state(repository) is None
    assert _event_types(event_store) == (RuntimeEventType.POLICY_EVALUATED.value,)
    assert _evidence_ids(event_store) == ()
    assert executor.requests == ()


def test_pre_executor_execution_creation_failure_leaves_work_running_without_executor() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_insert_execution()
    executor = _Executor()
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.REPOSITORY_FAILURE
    assert _work_state(repository) is WorkItemState.RUNNING
    assert _execution_state(repository) is None
    assert _event_types(event_store) == (RuntimeEventType.POLICY_EVALUATED.value,)
    assert _evidence_ids(event_store) == ()
    assert executor.requests == ()


def test_pre_executor_execution_start_failure_leaves_created_execution_without_executor() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_replace_execution(ExecutionState.RUNNING)
    executor = _Executor()
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.REPOSITORY_FAILURE
    assert _work_state(repository) is WorkItemState.RUNNING
    assert _execution_state(repository) is ExecutionState.CREATED
    assert _event_types(event_store) == (RuntimeEventType.POLICY_EVALUATED.value,)
    assert _evidence_ids(event_store) == ()
    assert executor.requests == ()


def test_pre_executor_execution_started_event_failure_prevents_executor() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_insert_event(RuntimeEventType.EXECUTION_STARTED)
    executor = _Executor()
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.RUNTIME_STORE_FAILURE
    assert _work_state(repository) is WorkItemState.RUNNING
    assert _execution_state(repository) is ExecutionState.RUNNING
    assert _event_types(event_store) == (RuntimeEventType.POLICY_EVALUATED.value,)
    assert _evidence_ids(event_store) == ()
    assert executor.requests == ()


def test_post_executor_success_evidence_append_failure_fails_work_after_effect_success() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    evidence = _evidence()
    store.fail_insert_evidence()
    executor = _Executor(SingleStepExecutionOutcome(Result.success(), (evidence,)))
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.RUNTIME_STORE_FAILURE
    assert error.value.detail["executor_effect"] == "succeeded"
    assert _work_state(repository) is WorkItemState.FAILED
    assert _execution_state(repository) is ExecutionState.SUCCEEDED
    assert _event_types(event_store) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
        RuntimeEventType.EXECUTION_FAILED.value,
    )
    assert _evidence_ids(event_store) == ()
    assert len(executor.requests) == 1


def test_post_executor_success_terminal_work_transition_failure_marks_work_failed() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_replace_work(WorkItemState.COMPLETED)
    executor = _Executor(SingleStepExecutionOutcome(Result.success()))
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.REPOSITORY_FAILURE
    assert error.value.detail["executor_effect"] == "succeeded"
    assert _work_state(repository) is WorkItemState.FAILED
    assert _execution_state(repository) is ExecutionState.SUCCEEDED
    assert _event_types(event_store) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
        RuntimeEventType.EXECUTION_FAILED.value,
    )
    assert _evidence_ids(event_store) == ()
    assert len(executor.requests) == 1


def test_post_executor_success_terminal_execution_transition_failure_marks_failure_truth() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_replace_execution(ExecutionState.SUCCEEDED)
    executor = _Executor(SingleStepExecutionOutcome(Result.success()))
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.REPOSITORY_FAILURE
    assert error.value.detail["executor_effect"] == "succeeded"
    assert _work_state(repository) is WorkItemState.FAILED
    assert _execution_state(repository) is ExecutionState.FAILED
    assert _event_types(event_store) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
        RuntimeEventType.EXECUTION_FAILED.value,
    )
    assert _evidence_ids(event_store) == ()
    assert len(executor.requests) == 1


def test_success_completion_event_failure_returns_terminal_result_with_warning() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_insert_event(RuntimeEventType.EXECUTION_COMPLETED)
    executor = _Executor(SingleStepExecutionOutcome(Result.success()))
    service = _service(repository, event_store, executor)

    result = service.run_once(_request())

    assert result.status is SingleStepRuntimeStatus.COMPLETED
    assert result.recording_errors[0].code is SingleStepRuntimeErrorCode.RUNTIME_STORE_FAILURE
    assert _work_state(repository) is WorkItemState.COMPLETED
    assert _execution_state(repository) is ExecutionState.SUCCEEDED
    assert _event_types(event_store) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
    )
    assert _evidence_ids(event_store) == ()
    assert len(executor.requests) == 1


def test_post_executor_failure_work_transition_failure_is_bounded_cleanup_failure() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_replace_work(WorkItemState.FAILED)
    failure: Result[object] = Result.failure((contract_error(),))
    executor = _Executor(SingleStepExecutionOutcome(failure))
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.EXECUTOR_FAILURE
    assert error.value.__cause__ is None
    assert _work_state(repository) is WorkItemState.RUNNING
    assert _execution_state(repository) is ExecutionState.FAILED
    assert _event_types(event_store) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
    )
    assert _evidence_ids(event_store) == ()
    assert len(executor.requests) == 1


def test_post_executor_failure_execution_transition_failure_is_bounded_cleanup_failure() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_replace_execution(ExecutionState.FAILED)
    failure: Result[object] = Result.failure((contract_error(),))
    executor = _Executor(SingleStepExecutionOutcome(failure))
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.EXECUTOR_FAILURE
    assert error.value.__cause__ is None
    assert _work_state(repository) is WorkItemState.FAILED
    assert _execution_state(repository) is ExecutionState.RUNNING
    assert _event_types(event_store) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
    )
    assert _evidence_ids(event_store) == ()
    assert len(executor.requests) == 1


def test_post_executor_failure_event_failure_returns_failed_result_with_warning() -> None:
    store = _AdversarialPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    store.fail_insert_event(RuntimeEventType.EXECUTION_FAILED)
    failure: Result[object] = Result.failure((contract_error(),))
    executor = _Executor(SingleStepExecutionOutcome(failure))
    service = _service(repository, event_store, executor)

    result = service.run_once(_request())

    assert result.status is SingleStepRuntimeStatus.FAILED
    assert result.recording_errors[0].code is SingleStepRuntimeErrorCode.RUNTIME_STORE_FAILURE
    assert _work_state(repository) is WorkItemState.FAILED
    assert _execution_state(repository) is ExecutionState.FAILED
    assert _event_types(event_store) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
    )
    assert _evidence_ids(event_store) == ()
    assert len(executor.requests) == 1


@pytest.mark.parametrize(
    "state",
    (
        WorkItemState.RUNNING,
        WorkItemState.WAITING,
        WorkItemState.COMPLETED,
        WorkItemState.FAILED,
        WorkItemState.CANCELLED,
    ),
)
def test_non_startable_work_fails_before_executor_invocation(state: WorkItemState) -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work(state=state))
    executor = _Executor()
    service = _service(repository, event_store, executor)

    with pytest.raises(SingleStepRuntimeError) as error:
        service.run_once(_request())

    assert error.value.code is SingleStepRuntimeErrorCode.ILLEGAL_STATE
    assert error.value.detail == {"work_state": state.value}
    assert executor.requests == ()
    assert repository.read_work(fixed_id(WorkId)).item.state is state  # type: ignore[union-attr]


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
        self._requests: list[SingleStepExecutionRequest] = []

    @property
    def requests(self) -> tuple[SingleStepExecutionRequest, ...]:
        return tuple(self._requests)

    def execute(self, request: SingleStepExecutionRequest) -> SingleStepExecutionOutcome:
        self._requests.append(request)
        raise self._error


class _RaisingPolicyEvaluator:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def evaluate(self, request: object) -> object:
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


class _AdversarialPersistenceStore(_MemoryPersistenceStore):
    def __init__(self) -> None:
        super().__init__()
        self._failures: list[_FailureRule] = []

    @contextmanager
    def transaction(self) -> Iterator[_AdversarialTransaction]:  # type: ignore[override]
        yield _AdversarialTransaction(self)

    def fail_insert_event(self, event_type: RuntimeEventType) -> None:
        self._failures.append(
            _FailureRule(
                action="insert",
                kind=PersistenceRecordKind.EVENT,
                payload_key="event_type",
                payload_value=event_type.value,
            )
        )

    def fail_insert_evidence(self) -> None:
        self._failures.append(_FailureRule(action="insert", kind=PersistenceRecordKind.EVIDENCE))

    def fail_insert_execution(self) -> None:
        self._failures.append(_FailureRule(action="insert", kind=PersistenceRecordKind.EXECUTION))

    def fail_replace_work(self, state: WorkItemState) -> None:
        self._failures.append(
            _FailureRule(
                action="replace",
                kind=PersistenceRecordKind.WORK,
                payload_key="state",
                payload_value=state.value,
            )
        )

    def fail_replace_execution(self, state: ExecutionState) -> None:
        self._failures.append(
            _FailureRule(
                action="replace",
                kind=PersistenceRecordKind.EXECUTION,
                payload_key="state",
                payload_value=state.value,
            )
        )

    def _maybe_fail(self, action: str, record: PersistenceRecord) -> None:
        for index, failure in enumerate(self._failures):
            if failure.matches(action, record):
                del self._failures[index]
                raise PersistenceError(
                    PersistenceErrorCode.CONNECTIVITY,
                    "injected persistence failure",
                    retryable=True,
                    operation=f"{action}_{record.kind.value}",
                    cause_type="OperationalError",
                )


class _FailureRule:
    def __init__(
        self,
        *,
        action: str,
        kind: PersistenceRecordKind,
        payload_key: str | None = None,
        payload_value: object | None = None,
    ) -> None:
        self.action = action
        self.kind = kind
        self.payload_key = payload_key
        self.payload_value = payload_value

    def matches(self, action: str, record: PersistenceRecord) -> bool:
        if action != self.action or record.kind is not self.kind:
            return False
        if self.payload_key is None:
            return True
        return record.payload.get(self.payload_key) == self.payload_value


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


class _AdversarialTransaction(_MemoryTransaction):
    def __init__(self, store: _AdversarialPersistenceStore) -> None:
        super().__init__(store)
        self._adversarial_store = store

    def insert_record(self, record: PersistenceRecord) -> None:
        self._adversarial_store._maybe_fail("insert", record)
        super().insert_record(record)

    def replace_record(self, record: PersistenceRecord, *, expected_payload_sha256: str) -> None:
        self._adversarial_store._maybe_fail("replace", record)
        super().replace_record(record, expected_payload_sha256=expected_payload_sha256)


def _work_state(repository: M0WorkRepository) -> WorkItemState:
    stored = repository.read_work(fixed_id(WorkId))
    assert stored is not None
    return stored.item.state


def _execution_state(repository: M0WorkRepository) -> ExecutionState | None:
    stored = repository.read_execution(fixed_id(ExecutionId))
    if stored is None:
        return None
    return stored.record.state


def _event_types(event_store: EventEvidenceRuntimeStore) -> tuple[str, ...]:
    return tuple(event.event_type for event in event_store.list_events())


def _evidence_ids(event_store: EventEvidenceRuntimeStore) -> tuple[EvidenceId, ...]:
    return tuple(evidence.evidence_id for evidence in event_store.list_evidence())


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
