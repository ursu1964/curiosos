from __future__ import annotations

import pytest
from contract_fixtures import UTC_NOW, fixed_id, human_principal, ref_for
from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    EffectClassification,
    EventEnvelope,
    EventId,
    EventType,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    ObjectReference,
    ObservabilityContext,
    PolicyDecision,
    PolicyDecisionOutcome,
    ProjectId,
    ProviderId,
    ReferenceKind,
    RuntimeEventType,
    SchemaVersion,
    VerificationId,
    VerificationOutcome,
    VerificationReference,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_persistence import (
    PersistenceConfig,
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecordKind,
    canonical_to_record,
    record_to_canonical,
)
from curios_persistence.boundary import _translate_error
from curios_persistence.schema import M0_PERSISTENCE_TABLE_NAMES
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError


def test_persistence_config_accepts_only_postgresql_urls_and_hides_url_repr() -> None:
    config = PersistenceConfig(
        sqlalchemy_url="postgresql+psycopg://curios@127.0.0.1:5432/curios_dev",
        schema="m0_002_unit",
    )

    assert config.schema == "m0_002_unit"
    assert "postgresql" not in repr(config)
    with pytest.raises(ValueError, match="must target PostgreSQL"):
        PersistenceConfig(sqlalchemy_url="sqlite+pysqlite:///:memory:")
    with pytest.raises(ValueError, match="simple PostgreSQL identifier"):
        PersistenceConfig(
            sqlalchemy_url="postgresql+psycopg://curios@127.0.0.1:5432/curios_dev",
            schema="not-valid",
        )


def test_public_boundary_does_not_export_provider_native_objects() -> None:
    import curios_persistence

    assert not set(curios_persistence.__all__).intersection(
        {
            "Connection",
            "Engine",
            "MetaData",
            "Session",
            "Table",
            "create_engine",
        }
    )


def test_schema_owns_only_m0_runtime_record_tables() -> None:
    assert M0_PERSISTENCE_TABLE_NAMES == (
        "curios_m0_artifact_records",
        "curios_m0_event_records",
        "curios_m0_evidence_records",
        "curios_m0_execution_records",
        "curios_m0_policy_decision_records",
        "curios_m0_verification_records",
        "curios_m0_work_records",
    )


@pytest.mark.parametrize(
    ("canonical", "kind", "record_id"),
    (
        pytest.param(
            WorkItem(
                work_id=fixed_id(WorkId),
                work_type="provider_inventory",
                title="Provider inventory",
                objective="Collect provider descriptors.",
                created_at=UTC_NOW,
                updated_at=UTC_NOW,
                state=WorkItemState.CREATED,
            ),
            PersistenceRecordKind.WORK,
            str(fixed_id(WorkId)),
            id="work",
        ),
        pytest.param(
            ExecutionRecord(
                execution_id=fixed_id(ExecutionId),
                work_id=fixed_id(WorkId),
                executor_ref=ObjectReference(
                    kind=ReferenceKind.PROVIDER,
                    ref_id=fixed_id(ProviderId),
                ),
                started_at=UTC_NOW,
                state=ExecutionState.CREATED,
            ),
            PersistenceRecordKind.EXECUTION,
            str(fixed_id(ExecutionId)),
            id="execution",
        ),
        pytest.param(
            EventEnvelope(
                event_id=fixed_id(EventId),
                event_type=RuntimeEventType.WORK_CREATED.value,
                schema_version=SchemaVersion(1, 0, 0),
                occurred_at=UTC_NOW,
                producer=ref_for(ProjectId),
                subject_ref=ref_for(WorkId),
                observability_context=ObservabilityContext(trace_id=None),
                payload={"work_id": str(fixed_id(WorkId))},
            ),
            PersistenceRecordKind.EVENT,
            str(fixed_id(EventId)),
            id="event",
        ),
        pytest.param(
            EvidenceReference(
                evidence_id=fixed_id(EvidenceId),
                kind=EvidenceKind.INSPECTION,
                subject_ref=ref_for(WorkId),
                collected_at=UTC_NOW,
                summary="Provider descriptors inspected.",
            ),
            PersistenceRecordKind.EVIDENCE,
            str(fixed_id(EvidenceId)),
            id="evidence",
        ),
        pytest.param(
            ArtifactReference(
                artifact_id=fixed_id(ArtifactId),
                kind=ArtifactKind.DOCUMENT,
                locator="artifact://provider-inventory/result",
                created_at=UTC_NOW,
            ),
            PersistenceRecordKind.ARTIFACT,
            str(fixed_id(ArtifactId)),
            id="artifact",
        ),
        pytest.param(
            PolicyDecision(
                decision_id="pol_local_provider_inventory",
                subject_ref=ref_for(WorkId),
                principal=human_principal(),
                requested_effects=(EffectClassification.READ_ONLY,),
                resource_refs=(ref_for(ProviderId),),
                scope="local docker project",
                outcome=PolicyDecisionOutcome.ALLOW,
                reason="provider inventory is read only",
                decided_at=UTC_NOW,
            ),
            PersistenceRecordKind.POLICY_DECISION,
            "pol_local_provider_inventory",
            id="policy-decision",
        ),
        pytest.param(
            VerificationReference(
                verification_id=fixed_id(VerificationId),
                subject_ref=ref_for(EvidenceId),
                outcome=VerificationOutcome.PASSED,
                evidence_refs=(fixed_id(EvidenceId),),
                verified_at=UTC_NOW,
            ),
            PersistenceRecordKind.VERIFICATION,
            str(fixed_id(VerificationId)),
            id="verification",
        ),
    ),
)
def test_canonical_records_round_trip_through_persistence_payloads(
    canonical: object,
    kind: PersistenceRecordKind,
    record_id: str,
) -> None:
    record = canonical_to_record(canonical)

    assert record.kind is kind
    assert record.record_id == record_id
    assert record_to_canonical(record) == canonical


def test_policy_decision_requires_canonical_decision_id_for_persistence() -> None:
    decision = PolicyDecision(
        subject_ref=ref_for(WorkId),
        principal=human_principal(),
        requested_effects=(EffectClassification.READ_ONLY,),
        resource_refs=(ref_for(ProviderId),),
        scope="local docker project",
        outcome=PolicyDecisionOutcome.ALLOW,
        reason="provider inventory is read only",
        decided_at=UTC_NOW,
    )

    with pytest.raises(ValueError, match="requires decision_id"):
        canonical_to_record(decision)


def test_persistence_failures_translate_sqlalchemy_errors_deterministically() -> None:
    integrity = _translate_error(
        IntegrityError("insert", {}, Exception("duplicate")), operation="insert"
    )
    operational = _translate_error(
        OperationalError("connect", {}, Exception("unavailable")),
        operation="readiness",
    )
    programming = _translate_error(
        ProgrammingError("select", {}, Exception("missing table")),
        operation="read",
    )

    assert isinstance(integrity, PersistenceError)
    assert integrity.code is PersistenceErrorCode.CONFLICT
    assert integrity.retryable is False
    assert operational.code is PersistenceErrorCode.CONNECTIVITY
    assert operational.retryable is True
    assert programming.code is PersistenceErrorCode.SCHEMA
    assert programming.retryable is False


def test_contract_translation_rejects_unsupported_event_type() -> None:
    with pytest.raises(ValueError, match="event type"):
        EventType("not_a_dotted_type")
