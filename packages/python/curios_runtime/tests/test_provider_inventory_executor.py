from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256

from contract_fixtures import UTC_LATER, UTC_NOW, contract_error, fixed_id, human_principal, ref_for
from curios_contracts import (
    CapabilityId,
    EventId,
    EvidenceKind,
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    ObjectReference,
    ObservabilityContext,
    PolicyDecision,
    PolicyDecisionOutcome,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    Result,
    RuntimeEventType,
    SchemaVersion,
    TraceId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_core import CoreContext
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
    ProviderInventoryExecutor,
    SingleStepExecutionRequest,
    SingleStepRuntimeRequest,
    SingleStepRuntimeService,
    SingleStepRuntimeStatus,
)


def test_provider_inventory_executor_returns_canonical_descriptors_in_stable_order() -> None:
    later = _descriptor(ordinal=2, provider_type=ProviderType.DATABASE)
    earlier = _descriptor(ordinal=1, provider_type=ProviderType.MODEL)
    executor = ProviderInventoryExecutor(
        (
            _Catalog(Result.success((later,))),
            _Catalog(Result.success((earlier,))),
        )
    )

    outcome = executor.execute(_execution_request())

    assert outcome.result == Result.success(
        {
            "work_type": "provider_inventory",
            "provider_count": 2,
            "providers": [earlier.to_json_compatible(), later.to_json_compatible()],
        },
        evidence_refs=outcome.evidence_refs,
    )
    assert len(outcome.evidence_refs) == 1
    evidence = outcome.evidence_refs[0]
    assert evidence.kind is EvidenceKind.PROVIDER_REPORT
    assert evidence.subject_ref == ref_for(WorkId)
    assert evidence.collected_at == UTC_LATER
    assert evidence.trace_id == fixed_id(TraceId)


def test_empty_inventory_is_successful_and_evidenced() -> None:
    outcome = ProviderInventoryExecutor((_Catalog(Result.success(())),)).execute(
        _execution_request()
    )

    assert outcome.result.value == {
        "work_type": "provider_inventory",
        "provider_count": 0,
        "providers": [],
    }
    assert len(outcome.evidence_refs) == 1


def test_unsupported_work_type_and_effect_fail_before_catalog_invocation() -> None:
    catalog = _Catalog(Result.success((_descriptor(),)))
    executor = ProviderInventoryExecutor((catalog,))

    unsupported_work = executor.execute(_execution_request(work_type="model_generation"))
    unsupported_effect = executor.execute(_execution_request(requested_effects=("EXTERNAL_READ",)))
    non_authorizing = executor.execute(_execution_request(outcome=PolicyDecisionOutcome.UNKNOWN))

    assert unsupported_work.result.errors[0].error_code == "PROVIDER_INVENTORY_UNSUPPORTED_WORK"
    assert unsupported_effect.result.errors[0].error_code == "PROVIDER_INVENTORY_UNSUPPORTED_EFFECT"
    assert non_authorizing.result.errors[0].error_code == "PROVIDER_INVENTORY_NOT_AUTHORIZED"
    assert catalog.calls == ()


def test_catalog_result_failure_fails_whole_inventory_without_partial_value() -> None:
    failing_catalog = _Catalog(Result.failure((contract_error(),)))
    executor = ProviderInventoryExecutor(
        (
            _Catalog(Result.success((_descriptor(ordinal=1),))),
            failing_catalog,
            _Catalog(Result.success((_descriptor(ordinal=2),))),
        )
    )

    outcome = executor.execute(_execution_request())

    assert outcome.result.status.value == "failure"
    assert outcome.result.value is None
    assert outcome.evidence_refs == ()
    assert outcome.result.errors[0].error_code == "PROVIDER_INVENTORY_CATALOG_FAILURE"
    assert outcome.result.errors[0].details == {
        "catalog_index": 1,
        "catalog_error_codes": ("CONTRACT_FAILURE",),
    }


def test_catalog_exception_translates_without_native_exception_leakage() -> None:
    executor = ProviderInventoryExecutor((_RaisingCatalog(RuntimeError("provider native detail")),))

    outcome = executor.execute(_execution_request())

    error = outcome.result.errors[0]
    assert error.error_code == "PROVIDER_INVENTORY_CATALOG_EXCEPTION"
    assert error.details == {"catalog_index": 0, "cause_type": "RuntimeError"}
    assert "provider native detail" not in error.message
    assert outcome.evidence_refs == ()


def test_duplicate_provider_descriptors_are_rejected() -> None:
    descriptor = _descriptor(ordinal=3)
    executor = ProviderInventoryExecutor(
        (
            _Catalog(Result.success((descriptor,))),
            _Catalog(Result.success((descriptor,))),
        )
    )

    outcome = executor.execute(_execution_request())

    assert outcome.result.errors[0].error_code == "PROVIDER_INVENTORY_DUPLICATE_PROVIDER"
    assert outcome.result.errors[0].details == {"provider_id": str(descriptor.provider_id)}
    assert outcome.evidence_refs == ()


def test_malformed_catalog_output_is_rejected_without_provider_native_leakage() -> None:
    executor = ProviderInventoryExecutor((_MalformedCatalog(),))

    outcome = executor.execute(_execution_request())

    assert outcome.result.errors[0].error_code == "PROVIDER_INVENTORY_MALFORMED_RESULT"
    assert outcome.result.errors[0].details == {
        "catalog_index": 0,
        "descriptor_type": "object",
    }
    assert outcome.evidence_refs == ()


def test_provider_inventory_executor_integrates_with_single_step_runtime_service() -> None:
    store = _MemoryPersistenceStore()
    repository = M0WorkRepository(store)
    event_store = EventEvidenceRuntimeStore(store)
    repository.create_work(_work())
    descriptor = _descriptor()
    executor = ProviderInventoryExecutor((_Catalog(Result.success((descriptor,))),))
    service = SingleStepRuntimeService(
        work_repository=repository,
        event_store=event_store,
        policy_evaluator=MinimalM0PolicyEvaluator(),
        executor=executor,
    )

    result = service.run_once(_runtime_request())

    assert result.status is SingleStepRuntimeStatus.COMPLETED
    assert result.executor_result is not None
    assert result.executor_result.value == {
        "work_type": "provider_inventory",
        "provider_count": 1,
        "providers": [descriptor.to_json_compatible()],
    }
    assert result.work.item.state is WorkItemState.COMPLETED
    assert result.execution is not None
    assert result.execution.record.state is ExecutionState.SUCCEEDED
    assert tuple(event.event_type for event in event_store.list_events()) == (
        RuntimeEventType.POLICY_EVALUATED.value,
        RuntimeEventType.EXECUTION_STARTED.value,
        RuntimeEventType.EVIDENCE_PRODUCED.value,
        RuntimeEventType.EXECUTION_COMPLETED.value,
    )
    assert len(event_store.list_evidence()) == 1


def _execution_request(
    *,
    work_type: str = "provider_inventory",
    requested_effects: tuple[str, ...] = ("READ_ONLY",),
    outcome: PolicyDecisionOutcome = PolicyDecisionOutcome.ALLOW,
) -> SingleStepExecutionRequest:
    return SingleStepExecutionRequest(
        work=_work(work_type=work_type),
        execution=ExecutionRecord(
            execution_id=fixed_id(ExecutionId),
            work_id=fixed_id(WorkId),
            executor_ref=ref_for(ProviderId),
            started_at=UTC_LATER,
            state=ExecutionState.RUNNING,
            observability_context=_observability(),
        ),
        policy_decision=PolicyDecision(
            subject_ref=ref_for(WorkId),
            principal=human_principal(),
            requested_effects=tuple(requested_effects),
            resource_refs=(ref_for(ProviderId),),
            scope="project sandbox",
            outcome=outcome,
            reason="test decision",
            decided_at=UTC_NOW,
            observability_context=_observability(),
        ),
        observability_context=_observability(),
    )


def _runtime_request() -> SingleStepRuntimeRequest:
    return SingleStepRuntimeRequest(
        work_id=fixed_id(WorkId),
        principal=human_principal(),
        producer_ref=ref_for(ProviderId),
        executor_ref=ref_for(ProviderId),
        scope="project sandbox",
        resource_refs=(ref_for(ProviderId),),
        observability_context=_observability(),
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


def _observability() -> ObservabilityContext:
    return ObservabilityContext(
        work_id=fixed_id(WorkId),
        execution_id=fixed_id(ExecutionId),
        trace_id=fixed_id(TraceId),
        causation_ref=ObjectReference.from_id(fixed_id(EventId)),
    )


def _descriptor(
    ordinal: int = 1,
    *,
    provider_type: ProviderType = ProviderType.MODEL,
) -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=fixed_id(ProviderId, ordinal=ordinal),
        provider_type=provider_type,
        version=SchemaVersion(1, 0, ordinal),
        declared_capability_ids=(fixed_id(CapabilityId, ordinal=ordinal),),
        status=ProviderStatus.AVAILABLE,
        implementation_metadata={"family": f"provider_{ordinal}"},
    )


class _Catalog:
    def __init__(self, result: Result[tuple[ProviderDescriptor, ...]]) -> None:
        self._result = result
        self._calls: list[CoreContext] = []

    @property
    def calls(self) -> tuple[CoreContext, ...]:
        return tuple(self._calls)

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        self._calls.append(context)
        return self._result


class _RaisingCatalog:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        raise self._error


class _MalformedCatalog:
    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        return Result.success((object(),))  # type: ignore[arg-type]


class _MemoryPersistenceStore(PersistenceStore):
    def __init__(self) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {}
        self._order: list[tuple[PersistenceRecordKind, str]] = []

    @contextmanager
    def transaction(self) -> Iterator[_MemoryTransaction]:  # type: ignore[override]
        yield _MemoryTransaction(self)


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
