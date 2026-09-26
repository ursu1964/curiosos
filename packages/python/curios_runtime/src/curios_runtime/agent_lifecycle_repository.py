"""M1 agent lifecycle transitions backed by canonical events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import NoReturn

from curios_contracts import (
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    EventEnvelope,
    EventId,
    EventType,
    ObjectReference,
    ObservabilityContext,
    SchemaVersion,
    UtcTimestamp,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
    canonical_to_record,
    record_to_canonical,
)

AGENT_INSTANCE_TRANSITIONS: dict[AgentInstanceState, frozenset[AgentInstanceState]] = {
    AgentInstanceState.CREATED: frozenset({AgentInstanceState.READY, AgentInstanceState.CANCELLED}),
    AgentInstanceState.READY: frozenset({AgentInstanceState.ACTIVE, AgentInstanceState.CANCELLED}),
    AgentInstanceState.ACTIVE: frozenset(
        {
            AgentInstanceState.WAITING,
            AgentInstanceState.COMPLETED,
            AgentInstanceState.FAILED,
            AgentInstanceState.CANCELLED,
        }
    ),
    AgentInstanceState.WAITING: frozenset(
        {
            AgentInstanceState.ACTIVE,
            AgentInstanceState.FAILED,
            AgentInstanceState.CANCELLED,
        }
    ),
    AgentInstanceState.COMPLETED: frozenset(),
    AgentInstanceState.FAILED: frozenset(),
    AgentInstanceState.CANCELLED: frozenset(),
}
AGENT_LIFECYCLE_EVENT_TYPE = EventType("agent.lifecycle.transitioned")
_TERMINAL_AGENT_STATES = frozenset(
    {
        AgentInstanceState.COMPLETED,
        AgentInstanceState.FAILED,
        AgentInstanceState.CANCELLED,
    }
)


class AgentLifecycleErrorCode(StrEnum):
    """Stable failure categories for M1 agent lifecycle persistence."""

    CONFLICT = "CONFLICT"
    CORRUPT_RECORD = "CORRUPT_RECORD"
    ILLEGAL_TRANSITION = "ILLEGAL_TRANSITION"
    NOT_FOUND = "NOT_FOUND"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"


class AgentLifecycleError(RuntimeError):
    """Bounded M1 agent lifecycle error without persistence-native leakage."""

    def __init__(
        self,
        code: AgentLifecycleErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
    ) -> None:
        super().__init__(message)
        self.code = AgentLifecycleErrorCode(code)
        self.retryable = retryable
        self.operation = operation

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": str(self),
            "retryable": self.retryable,
            "operation": self.operation,
        }


@dataclass(frozen=True, slots=True)
class StoredAgentLifecycleTransition:
    """A persisted lifecycle transition result and optional canonical event."""

    instance: AgentInstance
    version: str
    event: EventEnvelope | None
    changed: bool


class M1AgentLifecycleRepository:
    """Repository boundary for M1 agent lifecycle transitions and events."""

    def __init__(self, store: PersistenceStore) -> None:
        if not isinstance(store, PersistenceStore):
            msg = "store must be a PersistenceStore"
            raise TypeError(msg)
        self._store = store

    def transition_instance(
        self,
        agent_instance_id: AgentInstanceId,
        target_state: AgentInstanceState,
        *,
        event_id: EventId,
        occurred_at: UtcTimestamp,
        expected_version: str | None = None,
        expected_state: AgentInstanceState | None = None,
        causation_ref: ObjectReference | None = None,
    ) -> StoredAgentLifecycleTransition:
        """Persist one legal agent lifecycle transition and its canonical event."""
        if not isinstance(agent_instance_id, AgentInstanceId):
            msg = "agent_instance_id must be an AgentInstanceId"
            raise TypeError(msg)
        if not isinstance(event_id, EventId):
            msg = "event_id must be an EventId"
            raise TypeError(msg)
        target_state = AgentInstanceState(target_state)
        occurred_at = UtcTimestamp(occurred_at)
        if expected_state is not None:
            expected_state = AgentInstanceState(expected_state)
        if causation_ref is not None and not isinstance(causation_ref, ObjectReference):
            msg = "causation_ref must be an ObjectReference when provided"
            raise TypeError(msg)

        try:
            with self._store.transaction() as transaction:
                current_record = transaction.read_record(
                    PersistenceRecordKind.AGENT_INSTANCE,
                    str(agent_instance_id),
                )
                if current_record is None:
                    _raise_lifecycle_error(
                        AgentLifecycleError(
                            AgentLifecycleErrorCode.NOT_FOUND,
                            f"Agent instance {agent_instance_id} was not found.",
                            retryable=False,
                            operation="transition_instance",
                        )
                    )
                current = _record_to_instance(current_record, operation="transition_instance")
                current_version = _record_version(current_record)
                if expected_version is not None and expected_version != current_version:
                    _raise_lifecycle_error(_conflict("transition_instance"))
                if expected_state is not None and expected_state is not current.state:
                    _raise_lifecycle_error(_conflict("transition_instance"))

                transitioned = transition_agent_instance(
                    current,
                    target_state,
                    occurred_at=occurred_at,
                )
                if transitioned == current:
                    return StoredAgentLifecycleTransition(
                        instance=current,
                        version=current_version,
                        event=None,
                        changed=False,
                    )

                event = agent_lifecycle_event(
                    current,
                    transitioned,
                    event_id=event_id,
                    occurred_at=occurred_at,
                    causation_ref=causation_ref,
                )
                transitioned_record = canonical_to_record(transitioned)
                transaction.replace_record(
                    transitioned_record,
                    expected_payload_sha256=current_version,
                )
                transaction.insert_record(canonical_to_record(event))
                return StoredAgentLifecycleTransition(
                    instance=transitioned,
                    version=_record_version(transitioned_record),
                    event=event,
                    changed=True,
                )
        except PersistenceError as exc:
            _raise_lifecycle_error(
                _translate_persistence_error(exc, operation="transition_instance")
            )


def transition_agent_instance(
    instance: AgentInstance,
    target_state: AgentInstanceState,
    *,
    occurred_at: UtcTimestamp,
) -> AgentInstance:
    """Return an agent instance moved to an allowed state, or unchanged if repeated."""
    if not isinstance(instance, AgentInstance):
        msg = "instance must be an AgentInstance"
        raise TypeError(msg)
    target_state = AgentInstanceState(target_state)
    occurred_at = UtcTimestamp(occurred_at)
    if target_state is instance.state:
        return instance
    if target_state not in AGENT_INSTANCE_TRANSITIONS[instance.state]:
        _raise_lifecycle_error(
            AgentLifecycleError(
                AgentLifecycleErrorCode.ILLEGAL_TRANSITION,
                f"Illegal agent transition {instance.state.value} -> {target_state.value}.",
                retryable=False,
                operation="transition_instance",
            )
        )
    return AgentInstance(
        agent_instance_id=instance.agent_instance_id,
        agent_definition_id=instance.agent_definition_id,
        work_id=instance.work_id,
        execution_id=instance.execution_id,
        state=target_state,
        observability_context=instance.observability_context,
        authority_ref=instance.authority_ref,
        principal_ref=instance.principal_ref,
        created_at=instance.created_at,
        started_at=(
            occurred_at
            if target_state is AgentInstanceState.ACTIVE and instance.started_at is None
            else instance.started_at
        ),
        ended_at=(
            occurred_at
            if target_state in _TERMINAL_AGENT_STATES and instance.ended_at is None
            else instance.ended_at
        ),
    )


def agent_lifecycle_event(
    source: AgentInstance,
    target: AgentInstance,
    *,
    event_id: EventId,
    occurred_at: UtcTimestamp,
    causation_ref: ObjectReference | None = None,
) -> EventEnvelope:
    """Build the canonical event for one persisted agent lifecycle transition."""
    if not isinstance(source, AgentInstance):
        msg = "source must be an AgentInstance"
        raise TypeError(msg)
    if not isinstance(target, AgentInstance):
        msg = "target must be an AgentInstance"
        raise TypeError(msg)
    if source.agent_instance_id != target.agent_instance_id:
        msg = "source and target must refer to the same AgentInstance"
        raise ValueError(msg)
    if not isinstance(event_id, EventId):
        msg = "event_id must be an EventId"
        raise TypeError(msg)
    occurred_at = UtcTimestamp(occurred_at)
    if causation_ref is not None and not isinstance(causation_ref, ObjectReference):
        msg = "causation_ref must be an ObjectReference when provided"
        raise TypeError(msg)
    subject_ref = ObjectReference.from_id(target.agent_instance_id)
    return EventEnvelope(
        event_id=event_id,
        event_type=AGENT_LIFECYCLE_EVENT_TYPE,
        schema_version=SchemaVersion(1, 0, 0),
        occurred_at=occurred_at,
        producer=subject_ref,
        subject_ref=subject_ref,
        observability_context=ObservabilityContext(
            work_id=target.work_id,
            execution_id=target.execution_id,
            agent_instance_id=target.agent_instance_id,
            principal_ref=target.principal_ref,
            causation_ref=causation_ref,
        ),
        payload={
            "agent_instance_id": str(target.agent_instance_id),
            "agent_definition_id": str(target.agent_definition_id),
            "work_id": str(target.work_id),
            "execution_id": str(target.execution_id) if target.execution_id is not None else None,
            "source_state": source.state.value,
            "target_state": target.state.value,
            "started_at": str(target.started_at) if target.started_at is not None else None,
            "ended_at": str(target.ended_at) if target.ended_at is not None else None,
        },
        metadata={"task_id": "TASK-M1-007"},
    )


def _record_to_instance(record: PersistenceRecord, *, operation: str) -> AgentInstance:
    if record.kind is not PersistenceRecordKind.AGENT_INSTANCE:
        _raise_lifecycle_error(_corrupt_record(operation))
    try:
        value = record_to_canonical(record)
    except Exception:
        _raise_lifecycle_error(_corrupt_record(operation))
    if isinstance(value, AgentInstance):
        return value
    _raise_lifecycle_error(_corrupt_record(operation))


def _record_version(record: PersistenceRecord) -> str:
    encoded = json.dumps(
        record.payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _translate_persistence_error(
    exc: PersistenceError,
    *,
    operation: str,
) -> AgentLifecycleError:
    if exc.code is PersistenceErrorCode.CONFLICT:
        return _conflict(operation)
    return AgentLifecycleError(
        AgentLifecycleErrorCode.PERSISTENCE_FAILURE,
        "Agent lifecycle persistence operation failed.",
        retryable=exc.retryable,
        operation=operation,
    )


def _conflict(operation: str) -> AgentLifecycleError:
    return AgentLifecycleError(
        AgentLifecycleErrorCode.CONFLICT,
        "Agent lifecycle record version conflicts with existing state.",
        retryable=False,
        operation=operation,
    )


def _corrupt_record(operation: str) -> AgentLifecycleError:
    return AgentLifecycleError(
        AgentLifecycleErrorCode.CORRUPT_RECORD,
        "Persisted agent instance record did not decode as AgentInstance.",
        retryable=False,
        operation=operation,
    )


def _raise_lifecycle_error(error: AgentLifecycleError) -> NoReturn:
    raise error from None
