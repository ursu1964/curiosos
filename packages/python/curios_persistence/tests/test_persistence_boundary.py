from __future__ import annotations

import traceback
from collections.abc import Callable

import curios_persistence.boundary as persistence_boundary
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
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
    apply_schema_migrations,
    canonical_to_record,
    record_to_canonical,
)
from curios_persistence.boundary import _translate_error
from curios_persistence.schema import M0_PERSISTENCE_TABLE_NAMES
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError, SQLAlchemyError

_NATIVE_STATEMENT = "SELECT provider_native_detail"
_NATIVE_DETAIL = "provider-native-credential-fragment"
_TEST_POSTGRES_URL = "postgresql+psycopg://curios@127.0.0.1:5432/curios_dev"


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


@pytest.mark.parametrize(
    ("operation", "exercise"),
    (
        pytest.param("readiness", lambda store: store.check_readiness(), id="readiness"),
        pytest.param("transaction", lambda store: _open_transaction(store), id="transaction"),
    ),
)
def test_store_public_boundaries_do_not_chain_native_connectivity_errors(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    exercise: Callable[[PersistenceStore], object],
) -> None:
    native_error = OperationalError(
        _NATIVE_STATEMENT,
        {"parameter": _NATIVE_DETAIL},
        Exception(_NATIVE_DETAIL),
    )
    monkeypatch.setattr(
        persistence_boundary,
        "_create_engine",
        lambda config: _FailingEngine(native_error),
    )
    store = PersistenceStore(PersistenceConfig(sqlalchemy_url=_TEST_POSTGRES_URL))

    with pytest.raises(PersistenceError) as translated:
        exercise(store)

    _assert_public_error_is_bounded(
        translated.value,
        code=PersistenceErrorCode.CONNECTIVITY,
        retryable=True,
        operation=operation,
        cause_type="OperationalError",
    )


def test_record_conflict_failures_do_not_chain_native_integrity_errors() -> None:
    native_error = IntegrityError(
        _NATIVE_STATEMENT,
        {"parameter": _NATIVE_DETAIL},
        Exception(_NATIVE_DETAIL),
    )
    transaction = persistence_boundary.PersistenceTransaction(_FailingConnection(native_error))

    with pytest.raises(PersistenceError) as translated:
        transaction.insert_record(
            PersistenceRecord(PersistenceRecordKind.WORK, "work_conflict", {"kind": "work"})
        )

    _assert_public_error_is_bounded(
        translated.value,
        code=PersistenceErrorCode.CONFLICT,
        retryable=False,
        operation="insert_work",
        cause_type="IntegrityError",
    )


def test_record_operation_failures_do_not_chain_native_schema_errors() -> None:
    native_error = ProgrammingError(
        _NATIVE_STATEMENT,
        {"parameter": _NATIVE_DETAIL},
        Exception(_NATIVE_DETAIL),
    )
    transaction = persistence_boundary.PersistenceTransaction(_FailingConnection(native_error))

    with pytest.raises(PersistenceError) as translated:
        transaction.read_record(PersistenceRecordKind.WORK, "work_missing")

    _assert_public_error_is_bounded(
        translated.value,
        code=PersistenceErrorCode.SCHEMA,
        retryable=False,
        operation="read_work",
        cause_type="ProgrammingError",
    )


def test_generic_record_operation_failures_do_not_chain_native_database_errors() -> None:
    native_error = SQLAlchemyError(_NATIVE_DETAIL)
    transaction = persistence_boundary.PersistenceTransaction(_FailingConnection(native_error))

    with pytest.raises(PersistenceError) as translated:
        transaction.count_records(PersistenceRecordKind.WORK)

    _assert_public_error_is_bounded(
        translated.value,
        code=PersistenceErrorCode.UNKNOWN,
        retryable=False,
        operation="count_work",
        cause_type="SQLAlchemyError",
    )


def test_schema_migration_failures_do_not_chain_native_schema_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native_error = ProgrammingError(
        _NATIVE_STATEMENT,
        {"parameter": _NATIVE_DETAIL},
        Exception(_NATIVE_DETAIL),
    )
    engine = _FailingEngine(native_error)
    monkeypatch.setattr(persistence_boundary, "_create_engine", lambda config: engine)

    with pytest.raises(PersistenceError) as translated:
        apply_schema_migrations(PersistenceConfig(sqlalchemy_url=_TEST_POSTGRES_URL))

    _assert_public_error_is_bounded(
        translated.value,
        code=PersistenceErrorCode.SCHEMA,
        retryable=False,
        operation="schema_migration",
        cause_type="ProgrammingError",
    )
    assert engine.disposed is True


def test_contract_translation_rejects_unsupported_event_type() -> None:
    with pytest.raises(ValueError, match="event type"):
        EventType("not_a_dotted_type")


def _open_transaction(store: PersistenceStore) -> None:
    with store.transaction():
        pass


def _assert_public_error_is_bounded(
    error: PersistenceError,
    *,
    code: PersistenceErrorCode,
    retryable: bool,
    operation: str,
    cause_type: str,
) -> None:
    assert error.__cause__ is None
    assert error.__context__ is None
    assert error.__suppress_context__ is False
    assert error.code is code
    assert error.retryable is retryable
    assert error.operation == operation
    assert error.to_json_compatible() == {
        "code": code.value,
        "message": str(error),
        "retryable": retryable,
        "operation": operation,
        "cause_type": cause_type,
    }

    public_error_surface = " ".join(
        (
            str(error),
            repr(error),
            repr(error.to_json_compatible()),
            "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        )
    )
    assert _NATIVE_STATEMENT not in public_error_surface
    assert _NATIVE_DETAIL not in public_error_surface


class _FailingEngine:
    def __init__(self, error: SQLAlchemyError) -> None:
        self._error = error
        self.disposed = False

    def connect(self) -> object:
        raise self._error

    def begin(self) -> object:
        raise self._error

    def dispose(self) -> None:
        self.disposed = True


class _FailingConnection:
    def __init__(self, error: SQLAlchemyError) -> None:
        self._error = error

    def execute(self, statement: object) -> object:
        raise self._error
