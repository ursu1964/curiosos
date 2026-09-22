from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from contract_fixtures import SCHEMA_V1, UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    CorrelationId,
    EventEnvelope,
    EventId,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    ProjectId,
    RuntimeEventType,
    TraceId,
    VerificationId,
    VerificationOutcome,
    VerificationReference,
    WorkId,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
)
from curios_runtime import EventEvidenceRuntimeStore, RuntimeStoreError, RuntimeStoreErrorCode

PACKAGE_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src" / "curios_runtime"
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"


def _observability() -> ObservabilityContext:
    return ObservabilityContext(
        project_id=fixed_id(ProjectId),
        work_id=fixed_id(WorkId),
        execution_id=fixed_id(ExecutionId),
        trace_id=fixed_id(TraceId),
        correlation_id=fixed_id(CorrelationId),
        causation_ref=ObjectReference.from_id(fixed_id(EventId, ordinal=3)),
    )


def _event(ordinal: int = 0) -> EventEnvelope:
    return EventEnvelope(
        event_id=fixed_id(EventId, ordinal=ordinal),
        event_type=RuntimeEventType.EVIDENCE_PRODUCED.value,
        schema_version=SCHEMA_V1,
        occurred_at=UTC_NOW if ordinal == 0 else UTC_LATER,
        producer=ref_for(ProjectId),
        subject_ref=ref_for(WorkId),
        observability_context=_observability(),
        payload={
            "evidence_id": str(fixed_id(EvidenceId)),
            "execution_id": str(fixed_id(ExecutionId)),
            "nested": {"stable": True, "ordinal": ordinal},
        },
        metadata={"source": "runtime-store-test"},
    )


def _evidence(ordinal: int = 0) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=fixed_id(EvidenceId, ordinal=ordinal),
        kind=EvidenceKind.INSPECTION,
        subject_ref=ref_for(WorkId),
        collected_at=UTC_NOW if ordinal == 0 else UTC_LATER,
        summary=f"Evidence fixture {ordinal}",
        trace_id=fixed_id(TraceId),
    )


def _verification() -> VerificationReference:
    return VerificationReference(
        verification_id=fixed_id(VerificationId),
        subject_ref=ref_for(EvidenceId),
        outcome=VerificationOutcome.PASSED,
        evidence_refs=(_evidence(), fixed_id(EvidenceId, ordinal=1)),
        verified_at=UTC_LATER,
        verifier_ref=ref_for(ProjectId),
    )


def test_event_round_trip_preserves_identity_correlation_references_and_payload() -> None:
    store = EventEvidenceRuntimeStore(_MemoryPersistenceStore())
    event = _event()

    assert store.append_event(event) == event
    recovered = store.require_event(event.event_id)

    assert recovered == event
    assert recovered.event_id == event.event_id
    assert recovered.producer == event.producer
    assert recovered.subject_ref == event.subject_ref
    assert recovered.observability_context == event.observability_context
    assert recovered.payload == event.payload
    assert recovered.to_json() == event.to_json()


def test_evidence_and_verification_round_trip_preserves_references() -> None:
    store = EventEvidenceRuntimeStore(_MemoryPersistenceStore())
    evidence = _evidence()
    verification = _verification()

    assert store.append_evidence(evidence) == evidence
    assert store.append_verification(verification) == verification

    assert store.require_evidence(evidence.evidence_id) == evidence
    assert store.require_verification(verification.verification_id) == verification
    assert store.require_verification(verification.verification_id).evidence_refs == (
        evidence,
        fixed_id(EvidenceId, ordinal=1),
    )


def test_duplicate_event_identity_translates_to_runtime_conflict() -> None:
    store = EventEvidenceRuntimeStore(_MemoryPersistenceStore())
    event = _event()

    store.append_event(event)

    with pytest.raises(RuntimeStoreError) as duplicate:
        store.append_event(event)

    assert duplicate.value.code is RuntimeStoreErrorCode.CONFLICT
    assert duplicate.value.__cause__ is None
    assert duplicate.value.__context__ is None
    assert duplicate.value.to_json_compatible()["detail"] == {
        "persistence_code": "CONFLICT",
    }


def test_missing_records_are_safe_and_require_methods_raise_not_found() -> None:
    store = EventEvidenceRuntimeStore(_MemoryPersistenceStore())

    assert store.get_event(fixed_id(EventId)) is None
    assert store.get_evidence(fixed_id(EvidenceId)) is None
    assert store.get_verification(fixed_id(VerificationId)) is None

    with pytest.raises(RuntimeStoreError) as missing:
        store.require_event(fixed_id(EventId))

    assert missing.value.code is RuntimeStoreErrorCode.NOT_FOUND
    assert missing.value.to_json_compatible()["detail"] == {
        "record_id": str(fixed_id(EventId)),
        "record_kind": "event",
    }


def test_corrupt_payload_fails_safely_without_persistence_native_leakage() -> None:
    store = EventEvidenceRuntimeStore(
        _MemoryPersistenceStore(
            seeded=(
                PersistenceRecord(
                    kind=PersistenceRecordKind.EVENT,
                    record_id=str(fixed_id(EventId)),
                    payload={"event_id": str(fixed_id(EventId))},
                ),
            )
        )
    )

    with pytest.raises(RuntimeStoreError) as corrupt:
        store.require_event(fixed_id(EventId))

    assert corrupt.value.code is RuntimeStoreErrorCode.CORRUPT_RECORD
    assert corrupt.value.__cause__ is None
    assert corrupt.value.to_json_compatible() == {
        "code": "CORRUPT_RECORD",
        "message": "persistence record payload is not canonical",
        "operation": "get_event",
        "retryable": False,
    }


def test_integrity_failures_from_persistence_become_corrupt_runtime_records() -> None:
    store = EventEvidenceRuntimeStore(
        _FailingPersistenceStore(
            PersistenceError(
                PersistenceErrorCode.INTEGRITY,
                "hash mismatch with database detail",
                retryable=False,
                operation="read_event",
                cause_type="NativeDatabaseError",
            )
        )
    )

    with pytest.raises(RuntimeStoreError) as corrupt:
        store.require_event(fixed_id(EventId))

    assert corrupt.value.code is RuntimeStoreErrorCode.CORRUPT_RECORD
    assert corrupt.value.__cause__ is None
    assert corrupt.value.__context__ is None
    assert "NativeDatabaseError" not in str(corrupt.value.to_json_compatible())


def test_list_operations_are_bounded_and_deterministic() -> None:
    store = EventEvidenceRuntimeStore(_MemoryPersistenceStore())
    first = _event(0)
    second = _event(1)
    first_evidence = _evidence(0)
    second_evidence = _evidence(1)

    store.append_event(first)
    store.append_event(second)
    store.append_evidence(first_evidence)
    store.append_evidence(second_evidence)

    assert store.list_events(limit=1) == (first,)
    assert store.list_events(limit=2) == (first, second)
    assert store.list_evidence(limit=2) == (first_evidence, second_evidence)
    with pytest.raises(ValueError, match="limit must be between 1 and 1000"):
        store.list_events(limit=0)
    with pytest.raises(ValueError, match="limit must be between 1 and 1000"):
        store.list_evidence(limit=1001)


def test_runtime_store_public_boundary_exports_no_persistence_objects() -> None:
    import curios_runtime

    assert not set(curios_runtime.__all__).intersection(
        {
            "PersistenceRecord",
            "PersistenceRecordKind",
            "PersistenceStore",
            "Connection",
            "Engine",
            "Session",
            "Table",
        }
    )


def test_runtime_store_source_does_not_introduce_blocked_runtime_scope() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_ROOT.rglob("*.py"))
    pyproject = PYPROJECT.read_text(encoding="utf-8")

    for forbidden in (
        "asyncio",
        "broker",
        "queue",
        "scheduler",
        "curios_policy",
        "WorkRepository",
        "ExecutionRepository",
        "StateTransition",
        "FastAPI",
    ):
        assert forbidden not in source
    assert "curios-policy" not in pyproject


class _MemoryPersistenceStore:
    def __init__(self, seeded: tuple[PersistenceRecord, ...] = ()) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {
            (record.kind, record.record_id): record for record in seeded
        }
        self._order: list[tuple[PersistenceRecordKind, str]] = [
            (record.kind, record.record_id) for record in seeded
        ]

    @contextmanager
    def transaction(self) -> Iterator[_MemoryTransaction]:
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


class _FailingPersistenceStore:
    def __init__(self, error: PersistenceError) -> None:
        self._error = error

    @contextmanager
    def transaction(self) -> Iterator[_FailingTransaction]:
        yield _FailingTransaction(self._error)


class _FailingTransaction:
    def __init__(self, error: PersistenceError) -> None:
        self._error = error

    def insert_record(self, record: PersistenceRecord) -> None:
        raise self._error

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        raise self._error

    def list_records(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
    ) -> tuple[PersistenceRecord, ...]:
        raise self._error


def _take(values: Iterator[PersistenceRecord], *, limit: int) -> list[PersistenceRecord]:
    output: list[PersistenceRecord] = []
    for value in values:
        if len(output) == limit:
            break
        output.append(value)
    return output
