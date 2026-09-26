from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager

import pytest
from contract_fixtures import UTC_NOW, fixed_id
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    CapabilityId,
    ExecutionId,
    SchemaVersion,
    WorkId,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
)
from curios_runtime import (
    AgentRepositoryError,
    AgentRepositoryErrorCode,
    M1AgentRepository,
)


def _definition(ordinal: int = 0) -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId, ordinal=ordinal),
        name=f"local_agent_{ordinal}",
        version=SchemaVersion(1, 0, 0),
        purpose="Handle deterministic local assignment.",
        allowed_capability_ids=(fixed_id(CapabilityId, ordinal=ordinal),),
    )


def _instance(
    ordinal: int = 0,
    *,
    definition_ordinal: int = 0,
    state: AgentInstanceState = AgentInstanceState.CREATED,
    execution: bool = True,
) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId, ordinal=ordinal),
        agent_definition_id=fixed_id(AgentDefinitionId, ordinal=definition_ordinal),
        work_id=fixed_id(WorkId, ordinal=ordinal),
        execution_id=fixed_id(ExecutionId, ordinal=ordinal) if execution else None,
        state=state,
        created_at=UTC_NOW,
    )


def test_repository_creates_reads_and_lists_agent_records_without_lifecycle_authority() -> None:
    repository = M1AgentRepository(_MemoryStore())
    first_definition = repository.create_definition(_definition(0))
    second_definition = repository.create_definition(_definition(1))
    first_instance = repository.create_instance(_instance(0, definition_ordinal=0))
    second_instance = repository.create_instance(
        _instance(1, definition_ordinal=1, execution=False)
    )

    assert (
        repository.read_definition(first_definition.definition.agent_definition_id)
        == first_definition
    )
    assert repository.read_instance(first_instance.instance.agent_instance_id) == first_instance
    assert repository.list_definitions(limit=10) == (first_definition, second_definition)
    assert repository.list_instances(limit=10) == (first_instance, second_instance)
    assert first_instance.instance.work_id == fixed_id(WorkId)
    assert first_instance.instance.execution_id == fixed_id(ExecutionId)
    assert first_instance.instance.state is AgentInstanceState.CREATED
    assert not hasattr(repository, "transition_instance")
    assert not hasattr(repository, "assign_work")
    assert not hasattr(repository, "execute")


def test_instance_creation_requires_persisted_definition_without_touching_work_or_execution() -> (
    None
):
    repository = M1AgentRepository(_MemoryStore())

    with pytest.raises(AgentRepositoryError) as missing:
        repository.create_instance(_instance())

    assert missing.value.code is AgentRepositoryErrorCode.NOT_FOUND
    assert missing.value.operation == "create_instance"
    assert "work" not in str(missing.value).lower()
    assert "execution" not in str(missing.value).lower()


def test_duplicate_definition_and_instance_id_conflicts_are_bounded() -> None:
    repository = M1AgentRepository(_MemoryStore())
    repository.create_definition(_definition())
    repository.create_instance(_instance())

    with pytest.raises(AgentRepositoryError) as duplicate_definition:
        repository.create_definition(_definition())
    with pytest.raises(AgentRepositoryError) as duplicate_instance:
        repository.create_instance(_instance())

    assert duplicate_definition.value.code is AgentRepositoryErrorCode.CONFLICT
    assert duplicate_instance.value.code is AgentRepositoryErrorCode.CONFLICT
    assert duplicate_definition.value.__cause__ is None
    assert duplicate_instance.value.__cause__ is None


def test_repository_translates_persistence_failures_without_native_leakage() -> None:
    repository = M1AgentRepository(_FailingStore())

    with pytest.raises(AgentRepositoryError) as exc:
        repository.create_definition(_definition())

    assert exc.value.to_json_compatible() == {
        "code": "PERSISTENCE_FAILURE",
        "message": "Agent repository persistence operation failed.",
        "retryable": True,
        "operation": "create_definition",
    }
    assert "provider_native" not in str(exc.value)


@pytest.mark.parametrize("corruption", ("missing_required", "invalid_state", "malformed_shape"))
def test_read_instance_bounds_corrupt_persisted_payloads(corruption: str) -> None:
    agent_instance_id = fixed_id(AgentInstanceId)
    repository = M1AgentRepository(
        _CorruptStore(
            PersistenceRecord(
                PersistenceRecordKind.AGENT_INSTANCE,
                str(agent_instance_id),
                _corrupt_instance_payload(corruption, agent_instance_id),
            )
        )
    )

    with pytest.raises(AgentRepositoryError) as exc:
        repository.read_instance(agent_instance_id)

    assert exc.value.code is AgentRepositoryErrorCode.CORRUPT_RECORD
    assert exc.value.operation == "read_instance"
    assert exc.value.retryable is False
    assert "NOT_AN_AGENT_STATE" not in str(exc.value)
    assert "work_id" not in str(exc.value)


@pytest.mark.parametrize("corruption", ("missing_required", "malformed_shape"))
def test_read_definition_bounds_corrupt_persisted_payloads(corruption: str) -> None:
    agent_definition_id = fixed_id(AgentDefinitionId)
    repository = M1AgentRepository(
        _CorruptStore(
            PersistenceRecord(
                PersistenceRecordKind.AGENT_DEFINITION,
                str(agent_definition_id),
                _corrupt_definition_payload(corruption, agent_definition_id),
            )
        )
    )

    with pytest.raises(AgentRepositoryError) as exc:
        repository.read_definition(agent_definition_id)

    assert exc.value.code is AgentRepositoryErrorCode.CORRUPT_RECORD
    assert exc.value.operation == "read_definition"
    assert exc.value.retryable is False
    assert "name" not in str(exc.value)


def _corrupt_definition_payload(
    corruption: str,
    agent_definition_id: AgentDefinitionId,
) -> Mapping[str, object]:
    payload = dict(
        AgentDefinition(
            agent_definition_id=agent_definition_id,
            name="local_agent",
            version=SchemaVersion(1, 0, 0),
            purpose="Handle deterministic local assignment.",
            allowed_capability_ids=(),
        ).to_json_compatible()
    )
    if corruption == "missing_required":
        del payload["name"]
    elif corruption == "malformed_shape":
        payload["agent_definition_id"] = 17
    else:
        raise AssertionError(f"unknown corruption case {corruption}")
    return payload


def _corrupt_instance_payload(
    corruption: str,
    agent_instance_id: AgentInstanceId,
) -> Mapping[str, object]:
    payload = dict(
        AgentInstance(
            agent_instance_id=agent_instance_id,
            agent_definition_id=fixed_id(AgentDefinitionId),
            work_id=fixed_id(WorkId),
            state=AgentInstanceState.CREATED,
            created_at=UTC_NOW,
        ).to_json_compatible()
    )
    if corruption == "missing_required":
        del payload["work_id"]
    elif corruption == "invalid_state":
        payload["state"] = "NOT_AN_AGENT_STATE"
    elif corruption == "malformed_shape":
        payload["work_id"] = 17
    else:
        raise AssertionError(f"unknown corruption case {corruption}")
    return payload


class _MemoryStore(PersistenceStore):
    def __init__(self) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {}
        self._order: list[tuple[PersistenceRecordKind, str]] = []

    @contextmanager
    def transaction(self) -> Iterator[_MemoryTransaction]:  # type: ignore[override]
        yield _MemoryTransaction(self)


class _MemoryTransaction:
    def __init__(self, store: _MemoryStore) -> None:
        self._store = store

    def insert_record(self, record: PersistenceRecord) -> None:
        key = (record.kind, record.record_id)
        if key in self._store._records:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "duplicate",
                retryable=False,
                operation="insert",
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


class _CorruptStore(PersistenceStore):
    def __init__(self, record: PersistenceRecord) -> None:
        self._record = record

    @contextmanager
    def transaction(self) -> Iterator[_CorruptTransaction]:  # type: ignore[override]
        yield _CorruptTransaction(self._record)


class _CorruptTransaction:
    def __init__(self, record: PersistenceRecord) -> None:
        self._record = record

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        if self._record.kind is kind and self._record.record_id == record_id:
            return self._record
        return None
