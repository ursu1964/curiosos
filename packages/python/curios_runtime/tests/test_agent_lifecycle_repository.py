from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256

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
    EventId,
    ExecutionId,
    ObjectReference,
    ProjectId,
    SchemaVersion,
    UtcTimestamp,
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
from curios_runtime import (
    AGENT_INSTANCE_TRANSITIONS,
    AgentLifecycleError,
    AgentLifecycleErrorCode,
    M1AgentLifecycleRepository,
    M1AgentRepository,
    agent_lifecycle_event,
    transition_agent_instance,
)


def test_transition_state_machine_persists_instance_and_canonical_event() -> None:
    store = _TransactionalMemoryStore()
    _seed_agent(store)
    repository = M1AgentLifecycleRepository(store)
    current = _instance(state=AgentInstanceState.CREATED, execution=True)

    ready = repository.transition_instance(
        current.agent_instance_id,
        AgentInstanceState.READY,
        event_id=fixed_id(EventId),
        occurred_at=UTC_NOW,
        expected_state=AgentInstanceState.CREATED,
    )

    assert ready.changed is True
    assert ready.instance.state is AgentInstanceState.READY
    assert ready.instance.started_at is None
    assert ready.instance.ended_at is None
    assert ready.event is not None
    assert ready.event.event_type == "agent.lifecycle.transitioned"
    assert ready.event.subject_ref == ObjectReference.from_id(current.agent_instance_id)
    assert ready.event.producer == ObjectReference.from_id(current.agent_instance_id)
    assert ready.event.observability_context.agent_instance_id == current.agent_instance_id
    assert ready.event.observability_context.work_id == current.work_id
    assert ready.event.observability_context.execution_id == current.execution_id
    assert ready.event.observability_context.principal_ref == current.principal_ref
    assert ready.event.payload == {
        "agent_instance_id": str(current.agent_instance_id),
        "agent_definition_id": str(current.agent_definition_id),
        "work_id": str(current.work_id),
        "execution_id": str(current.execution_id),
        "source_state": "CREATED",
        "target_state": "READY",
        "started_at": None,
        "ended_at": None,
    }
    assert ready.event.metadata == {"task_id": "TASK-M1-007"}

    persisted = _read_instance_record(store, current.agent_instance_id)
    assert persisted.state is AgentInstanceState.READY
    assert store.records_of_kind(PersistenceRecordKind.EVENT) == (canonical_to_record(ready.event),)
    assert {
        "work_type",
        "dependencies",
        "executor_ref",
        "provider_refs",
        "result",
        "evidence_refs",
        "errors",
    }.isdisjoint(canonical_to_record(persisted).payload)


def test_active_and_terminal_transitions_update_lifecycle_timestamps_only() -> None:
    store = _TransactionalMemoryStore()
    _seed_agent(store)
    repository = M1AgentLifecycleRepository(store)

    repository.transition_instance(
        fixed_id(AgentInstanceId),
        AgentInstanceState.READY,
        event_id=fixed_id(EventId),
        occurred_at=UTC_NOW,
    )
    active = repository.transition_instance(
        fixed_id(AgentInstanceId),
        AgentInstanceState.ACTIVE,
        event_id=fixed_id(EventId, ordinal=1),
        occurred_at=UTC_NOW,
    )
    completed = repository.transition_instance(
        fixed_id(AgentInstanceId),
        AgentInstanceState.COMPLETED,
        event_id=fixed_id(EventId, ordinal=2),
        occurred_at=UTC_LATER,
    )

    assert active.instance.state is AgentInstanceState.ACTIVE
    assert active.instance.started_at == UTC_NOW
    assert active.instance.ended_at is None
    assert completed.instance.state is AgentInstanceState.COMPLETED
    assert completed.instance.started_at == UTC_NOW
    assert completed.instance.ended_at == UTC_LATER
    assert completed.instance.work_id == fixed_id(WorkId)
    assert completed.instance.execution_id == fixed_id(ExecutionId)
    assert len(store.records_of_kind(PersistenceRecordKind.EVENT)) == 3


def test_repeated_same_state_transition_is_idempotent_and_does_not_emit_event() -> None:
    store = _TransactionalMemoryStore()
    _seed_agent(store)
    repository = M1AgentLifecycleRepository(store)

    first = repository.transition_instance(
        fixed_id(AgentInstanceId),
        AgentInstanceState.READY,
        event_id=fixed_id(EventId),
        occurred_at=UTC_NOW,
    )
    second = repository.transition_instance(
        fixed_id(AgentInstanceId),
        AgentInstanceState.READY,
        event_id=fixed_id(EventId, ordinal=1),
        occurred_at=UTC_LATER,
    )

    assert first.changed is True
    assert second.changed is False
    assert second.event is None
    assert second.instance == first.instance
    assert second.version == first.version
    assert len(store.records_of_kind(PersistenceRecordKind.EVENT)) == 1


@pytest.mark.parametrize(
    ("source", "target"),
    (
        (AgentInstanceState.CREATED, AgentInstanceState.ACTIVE),
        (AgentInstanceState.READY, AgentInstanceState.WAITING),
        (AgentInstanceState.COMPLETED, AgentInstanceState.ACTIVE),
        (AgentInstanceState.FAILED, AgentInstanceState.READY),
        (AgentInstanceState.CANCELLED, AgentInstanceState.READY),
    ),
)
def test_invalid_transitions_fail_boundedly_without_state_or_event_write(
    source: AgentInstanceState,
    target: AgentInstanceState,
) -> None:
    store = _TransactionalMemoryStore()
    _seed_agent(store, instance=_instance(state=source))
    repository = M1AgentLifecycleRepository(store)

    with pytest.raises(AgentLifecycleError) as exc:
        repository.transition_instance(
            fixed_id(AgentInstanceId),
            target,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
        )

    assert exc.value.code is AgentLifecycleErrorCode.ILLEGAL_TRANSITION
    assert _read_instance_record(store, fixed_id(AgentInstanceId)).state is source
    assert store.records_of_kind(PersistenceRecordKind.EVENT) == ()


def test_missing_instance_and_wrong_typed_ids_fail_before_mutation() -> None:
    repository = M1AgentLifecycleRepository(_TransactionalMemoryStore())

    with pytest.raises(AgentLifecycleError) as missing:
        repository.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
        )
    with pytest.raises(TypeError, match="AgentInstanceId"):
        repository.transition_instance(  # type: ignore[arg-type]
            fixed_id(AgentDefinitionId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
        )
    with pytest.raises(TypeError, match="EventId"):
        repository.transition_instance(  # type: ignore[arg-type]
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(AgentInstanceId),
            occurred_at=UTC_NOW,
        )

    assert missing.value.code is AgentLifecycleErrorCode.NOT_FOUND


def test_stale_expected_state_or_version_conflicts_without_event_write() -> None:
    store = _TransactionalMemoryStore()
    _seed_agent(store)
    repository = M1AgentLifecycleRepository(store)
    current = M1AgentRepository(store).read_instance(fixed_id(AgentInstanceId))
    assert current is not None

    with pytest.raises(AgentLifecycleError) as stale_state:
        repository.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
            expected_state=AgentInstanceState.ACTIVE,
        )
    with pytest.raises(AgentLifecycleError) as stale_version:
        repository.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
            expected_version="0" * 64,
        )

    assert stale_state.value.code is AgentLifecycleErrorCode.CONFLICT
    assert stale_version.value.code is AgentLifecycleErrorCode.CONFLICT
    assert (
        _read_instance_record(store, fixed_id(AgentInstanceId)).state is AgentInstanceState.CREATED
    )
    assert store.records_of_kind(PersistenceRecordKind.EVENT) == ()


def test_event_conflict_rolls_back_state_update() -> None:
    store = _TransactionalMemoryStore()
    _seed_agent(store)
    duplicate_event = agent_lifecycle_event(
        _instance(state=AgentInstanceState.CREATED),
        _instance(state=AgentInstanceState.READY),
        event_id=fixed_id(EventId),
        occurred_at=UTC_NOW,
    )
    _insert_record(store, canonical_to_record(duplicate_event))
    repository = M1AgentLifecycleRepository(store)

    with pytest.raises(AgentLifecycleError) as exc:
        repository.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
        )

    assert exc.value.code is AgentLifecycleErrorCode.CONFLICT
    assert (
        _read_instance_record(store, fixed_id(AgentInstanceId)).state is AgentInstanceState.CREATED
    )
    assert store.records_of_kind(PersistenceRecordKind.EVENT) == (
        canonical_to_record(duplicate_event),
    )


def test_replace_failure_and_insert_failure_are_bounded_and_atomic() -> None:
    for fail_operation in ("replace", "insert_event"):
        store = _TransactionalMemoryStore(fail_operation=fail_operation)
        _seed_agent(store)
        repository = M1AgentLifecycleRepository(store)

        with pytest.raises(AgentLifecycleError) as exc:
            repository.transition_instance(
                fixed_id(AgentInstanceId),
                AgentInstanceState.READY,
                event_id=fixed_id(EventId),
                occurred_at=UTC_NOW,
            )

        assert exc.value.code is AgentLifecycleErrorCode.PERSISTENCE_FAILURE
        assert "provider_native" not in str(exc.value)
        assert _read_instance_record(store, fixed_id(AgentInstanceId)).state is (
            AgentInstanceState.CREATED
        )
        assert store.records_of_kind(PersistenceRecordKind.EVENT) == ()


@pytest.mark.parametrize("corruption", ("wrong_kind", "missing_required", "malformed_shape"))
def test_corrupt_persisted_instance_fails_boundedly(corruption: str) -> None:
    store = _TransactionalMemoryStore()
    if corruption == "wrong_kind":
        record = canonical_to_record(_definition())
        store._records[(PersistenceRecordKind.AGENT_INSTANCE, str(fixed_id(AgentInstanceId)))] = (
            PersistenceRecord(
                PersistenceRecordKind.AGENT_DEFINITION,
                str(fixed_id(AgentInstanceId)),
                record.payload,
            )
        )
        store._order.append((PersistenceRecordKind.AGENT_INSTANCE, str(fixed_id(AgentInstanceId))))
    else:
        payload = dict(_instance().to_json_compatible())
        if corruption == "missing_required":
            del payload["state"]
        elif corruption == "malformed_shape":
            payload["work_id"] = 17
        _insert_record(
            store,
            PersistenceRecord(
                PersistenceRecordKind.AGENT_INSTANCE,
                str(fixed_id(AgentInstanceId)),
                payload,
            ),
        )
    repository = M1AgentLifecycleRepository(store)

    with pytest.raises(AgentLifecycleError) as exc:
        repository.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
        )

    assert exc.value.code is AgentLifecycleErrorCode.CORRUPT_RECORD
    assert exc.value.retryable is False
    assert store.records_of_kind(PersistenceRecordKind.EVENT) == ()


def test_transition_helper_reuses_frozen_agent_instance_state_vocabulary() -> None:
    assert AGENT_INSTANCE_TRANSITIONS[AgentInstanceState.CREATED] == {
        AgentInstanceState.READY,
        AgentInstanceState.CANCELLED,
    }
    assert transition_agent_instance(
        _instance(state=AgentInstanceState.READY, execution=False),
        AgentInstanceState.ACTIVE,
        occurred_at=UTC_NOW,
    ) == _instance(
        state=AgentInstanceState.ACTIVE,
        execution=False,
        started_at=UTC_NOW,
    )


def _definition() -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId),
        name="local_agent",
        version=SchemaVersion(1, 0, 0),
        purpose="Handle deterministic local assignment.",
        allowed_capability_ids=(fixed_id(CapabilityId),),
    )


def _instance(
    *,
    state: AgentInstanceState = AgentInstanceState.CREATED,
    execution: bool = True,
    started_at: UtcTimestamp | None = None,
    ended_at: UtcTimestamp | None = None,
) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=fixed_id(WorkId),
        execution_id=fixed_id(ExecutionId) if execution else None,
        state=state,
        created_at=UTC_NOW,
        started_at=started_at,
        ended_at=ended_at,
        authority_ref=ref_for(ProjectId),
        principal_ref=ref_for(ApplicationId),
    )


def _seed_agent(
    store: _TransactionalMemoryStore,
    *,
    instance: AgentInstance | None = None,
) -> None:
    M1AgentRepository(store).create_definition(_definition())
    M1AgentRepository(store).create_instance(
        instance or _instance(state=AgentInstanceState.CREATED)
    )


def _insert_record(store: _TransactionalMemoryStore, record: PersistenceRecord) -> None:
    key = (record.kind, record.record_id)
    store._records[key] = record
    store._order.append(key)


def _read_instance_record(
    store: _TransactionalMemoryStore,
    agent_instance_id: AgentInstanceId,
) -> AgentInstance:
    record = store._records[(PersistenceRecordKind.AGENT_INSTANCE, str(agent_instance_id))]
    value = record.payload
    return AgentInstance.from_json_compatible(value)


class _TransactionalMemoryStore(PersistenceStore):
    def __init__(self, *, fail_operation: str | None = None) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {}
        self._order: list[tuple[PersistenceRecordKind, str]] = []
        self._fail_operation = fail_operation

    @contextmanager
    def transaction(self) -> Iterator[_TransactionalMemoryTransaction]:  # type: ignore[override]
        staged_records = dict(self._records)
        staged_order = list(self._order)
        transaction = _TransactionalMemoryTransaction(self, staged_records, staged_order)
        yield transaction
        self._records = staged_records
        self._order = staged_order

    def records_of_kind(self, kind: PersistenceRecordKind) -> tuple[PersistenceRecord, ...]:
        return tuple(
            self._records[key] for key in self._order if key[0] is PersistenceRecordKind(kind)
        )


class _TransactionalMemoryTransaction:
    def __init__(
        self,
        store: _TransactionalMemoryStore,
        records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord],
        order: list[tuple[PersistenceRecordKind, str]],
    ) -> None:
        self._store = store
        self._records = records
        self._order = order

    def insert_record(self, record: PersistenceRecord) -> None:
        if self._store._fail_operation == "insert_event" and record.kind is (
            PersistenceRecordKind.EVENT
        ):
            raise PersistenceError(
                PersistenceErrorCode.CONNECTIVITY,
                "provider_native insert failed",
                retryable=True,
                operation="insert_event",
                cause_type="OperationalError",
            )
        key = (record.kind, record.record_id)
        if key in self._records:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "duplicate",
                retryable=False,
                operation=f"insert_{record.kind.value}",
                cause_type="IntegrityError",
            )
        self._records[key] = record
        self._order.append(key)

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        return self._records.get((PersistenceRecordKind(kind), record_id))

    def list_records(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
    ) -> tuple[PersistenceRecord, ...]:
        normalized_kind = PersistenceRecordKind(kind)
        return tuple(self._records[key] for key in self._order if key[0] is normalized_kind)[:limit]

    def replace_record(self, record: PersistenceRecord, *, expected_payload_sha256: str) -> None:
        if self._store._fail_operation == "replace":
            raise PersistenceError(
                PersistenceErrorCode.CONNECTIVITY,
                "provider_native replace failed",
                retryable=True,
                operation=f"replace_{record.kind.value}",
                cause_type="OperationalError",
            )
        key = (record.kind, record.record_id)
        if key not in self._records:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "missing",
                retryable=False,
                operation=f"replace_{record.kind.value}",
                cause_type=None,
            )
        current = self._records[key]
        if _payload_sha256(current.payload) != expected_payload_sha256:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "version conflict",
                retryable=False,
                operation=f"replace_{record.kind.value}",
                cause_type=None,
            )
        self._records[key] = record


def _payload_sha256(payload: Mapping[str, object]) -> str:
    encoded = json_dumps(payload).encode("utf-8")
    return sha256(encoded).hexdigest()


def json_dumps(payload: Mapping[str, object]) -> str:
    return json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
