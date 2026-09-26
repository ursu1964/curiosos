from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    ApplicationId,
    CapabilityId,
    ExecutionId,
    ProjectId,
    SchemaVersion,
    WorkId,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
    canonical_to_record,
)
from curios_runtime import AgentRepositoryError, AgentRepositoryErrorCode, M1AgentRepository


def test_full_agent_definition_and_instance_round_trip_without_shadow_state() -> None:
    store = _InspectableStore()
    repository = M1AgentRepository(store)
    definition = _full_definition()
    instance = _full_instance()

    stored_definition = repository.create_definition(definition)
    stored_instance = repository.create_instance(instance)

    assert repository.read_definition(definition.agent_definition_id) == stored_definition
    assert repository.read_instance(instance.agent_instance_id) == stored_instance
    assert stored_definition.definition == definition
    assert stored_instance.instance == instance

    definition_payload = store.require_record(
        PersistenceRecordKind.AGENT_DEFINITION,
        str(definition.agent_definition_id),
    ).payload
    instance_payload = store.require_record(
        PersistenceRecordKind.AGENT_INSTANCE,
        str(instance.agent_instance_id),
    ).payload
    assert definition_payload == definition.to_json_compatible()
    assert instance_payload == instance.to_json_compatible()
    assert {
        "work_type",
        "dependencies",
        "required_capabilities",
        "executor_ref",
        "provider_refs",
        "result",
        "evidence_refs",
        "errors",
    }.isdisjoint(instance_payload)


def test_cross_typed_repository_ids_fail_before_persistence_lookup() -> None:
    repository = M1AgentRepository(_InspectableStore())

    with pytest.raises(TypeError, match="AgentDefinitionId"):
        repository.read_definition(fixed_id(AgentInstanceId))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="AgentInstanceId"):
        repository.read_instance(fixed_id(AgentDefinitionId))  # type: ignore[arg-type]


def test_missing_definition_failure_does_not_partially_persist_instance() -> None:
    store = _InspectableStore()
    repository = M1AgentRepository(store)

    with pytest.raises(AgentRepositoryError) as exc:
        repository.create_instance(_full_instance())

    assert exc.value.code is AgentRepositoryErrorCode.NOT_FOUND
    assert repository.list_instances(limit=10) == ()
    assert store.records_of_kind(PersistenceRecordKind.AGENT_INSTANCE) == ()


def test_instance_insert_failure_after_definition_read_is_bounded_and_atomic() -> None:
    store = _InspectableStore(fail_inserts_for={PersistenceRecordKind.AGENT_INSTANCE})
    repository = M1AgentRepository(store)
    repository.create_definition(_full_definition())

    with pytest.raises(AgentRepositoryError) as exc:
        repository.create_instance(_full_instance())

    assert exc.value.to_json_compatible() == {
        "code": "PERSISTENCE_FAILURE",
        "message": "Agent repository persistence operation failed.",
        "retryable": True,
        "operation": "create_instance",
    }
    assert "provider_native" not in str(exc.value)
    assert repository.read_instance(fixed_id(AgentInstanceId)) is None
    assert store.records_of_kind(PersistenceRecordKind.AGENT_INSTANCE) == ()


def test_wrong_persistence_record_kind_is_corrupt_not_reinterpreted() -> None:
    agent_definition_id = fixed_id(AgentDefinitionId)
    wrong_kind_record = PersistenceRecord(
        PersistenceRecordKind.AGENT_INSTANCE,
        str(agent_definition_id),
        _full_instance().to_json_compatible(),
    )
    repository = M1AgentRepository(_WrongKindReadStore(wrong_kind_record))

    with pytest.raises(AgentRepositoryError) as exc:
        repository.read_definition(agent_definition_id)

    assert exc.value.code is AgentRepositoryErrorCode.CORRUPT_RECORD
    assert exc.value.operation == "read_definition"
    assert exc.value.retryable is False


def _full_definition() -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId),
        name="local_agent",
        version=SchemaVersion(1, 0, 0),
        purpose="Persist full canonical agent-definition fields.",
        allowed_capability_ids=(fixed_id(CapabilityId), fixed_id(CapabilityId, ordinal=1)),
        constraints={
            "max_parallel_work": 1,
            "provider_neutral": True,
            "tags": ("m1", "validation"),
        },
        model_requirement_refs=(ref_for(CapabilityId),),
        input_contract_refs=(ref_for(ProjectId),),
        output_contract_refs=(ref_for(ApplicationId),),
    )


def _full_instance() -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=fixed_id(WorkId),
        execution_id=fixed_id(ExecutionId),
        state=AgentInstanceState.ACTIVE,
        created_at=UTC_NOW,
        authority_ref=ref_for(ProjectId),
        principal_ref=ref_for(ApplicationId),
        started_at=UTC_NOW,
        ended_at=UTC_LATER,
        observability_context=None,
    )


class _InspectableStore(PersistenceStore):
    def __init__(
        self,
        *,
        fail_inserts_for: set[PersistenceRecordKind] | None = None,
    ) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {}
        self._order: list[tuple[PersistenceRecordKind, str]] = []
        self._fail_inserts_for = set(fail_inserts_for or set())

    @contextmanager
    def transaction(self) -> Iterator[_InspectableTransaction]:  # type: ignore[override]
        yield _InspectableTransaction(self)

    def require_record(self, kind: PersistenceRecordKind, record_id: str) -> PersistenceRecord:
        return self._records[(kind, record_id)]

    def records_of_kind(self, kind: PersistenceRecordKind) -> tuple[PersistenceRecord, ...]:
        return tuple(
            record for (record_kind, _), record in self._records.items() if record_kind is kind
        )


class _InspectableTransaction:
    def __init__(self, store: _InspectableStore) -> None:
        self._store = store

    def insert_record(self, record: PersistenceRecord) -> None:
        if record.kind in self._store._fail_inserts_for:
            raise PersistenceError(
                PersistenceErrorCode.CONNECTIVITY,
                "provider_native insert failed",
                retryable=True,
                operation=f"insert_{record.kind.value}",
                cause_type="OperationalError",
            )
        key = (record.kind, record.record_id)
        if key in self._store._records:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "duplicate",
                retryable=False,
                operation=f"insert_{record.kind.value}",
                cause_type="IntegrityError",
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
        return tuple(
            self._store._records[key] for key in self._store._order if key[0] is normalized_kind
        )[:limit]


class _WrongKindReadStore(PersistenceStore):
    def __init__(self, record: PersistenceRecord) -> None:
        self._record = record

    @contextmanager
    def transaction(self) -> Iterator[_WrongKindReadTransaction]:  # type: ignore[override]
        yield _WrongKindReadTransaction(self._record)


class _WrongKindReadTransaction:
    def __init__(self, record: PersistenceRecord) -> None:
        self._record = record

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        if self._record.record_id == record_id:
            return self._record
        return None


def test_persistence_boundary_preserves_agent_records_as_canonical_payloads() -> None:
    definition = _full_definition()
    instance = _full_instance()

    definition_record = canonical_to_record(definition)
    instance_record = canonical_to_record(instance)

    assert definition_record.kind is PersistenceRecordKind.AGENT_DEFINITION
    assert definition_record.record_id == str(definition.agent_definition_id)
    assert definition_record.payload == definition.to_json_compatible()
    assert instance_record.kind is PersistenceRecordKind.AGENT_INSTANCE
    assert instance_record.record_id == str(instance.agent_instance_id)
    assert instance_record.payload == instance.to_json_compatible()
