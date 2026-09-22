from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from curios_contracts import (
    RUNTIME_EVENT_TYPES,
    CorrelationId,
    EventEnvelope,
    EventId,
    EventType,
    ObjectReference,
    ObservabilityContext,
    ProviderId,
    RuntimeEventType,
    SchemaVersion,
    TraceId,
    UtcTimestamp,
    WorkId,
    to_json_compatible,
)


def _event_envelope() -> EventEnvelope:
    work_id = WorkId.generate()
    producer_ref = ObjectReference.from_id(ProviderId.generate())
    subject_ref = ObjectReference.from_id(work_id)
    return EventEnvelope(
        event_id=EventId.generate(),
        event_type=RuntimeEventType.EXECUTION_STARTED.value,
        schema_version=SchemaVersion.parse("1.0.0"),
        occurred_at=UtcTimestamp.from_datetime(datetime(2026, 9, 22, 8, 15, 30, tzinfo=UTC)),
        producer=producer_ref,
        subject_ref=subject_ref,
        observability_context=ObservabilityContext(
            work_id=work_id,
            trace_id=TraceId.generate(),
            correlation_id=CorrelationId.generate(),
        ),
        payload={"execution_mode": "dry_run", "attempt": 1},
        metadata={"source": "unit_test"},
    )


def test_event_envelope_required_fields_and_canonical_serialization() -> None:
    envelope = _event_envelope()

    serialized = envelope.to_json()

    assert serialized["event_id"] == str(envelope.event_id)
    assert serialized["event_type"] == "execution.started"
    assert serialized["schema_version"] == "1.0.0"
    assert serialized["occurred_at"] == "2026-09-22T08:15:30Z"
    assert serialized["producer"] == envelope.producer.to_json_compatible()
    assert isinstance(serialized["subject_ref"], dict)
    assert serialized["subject_ref"] == envelope.subject_ref.to_json_compatible()
    assert serialized["observability_context"] == envelope.observability_context.to_json()
    assert serialized["payload"] == {"execution_mode": "dry_run", "attempt": 1}


def test_event_envelope_round_trips_through_json() -> None:
    envelope = _event_envelope()

    decoded = json.loads(json.dumps(to_json_compatible(envelope), sort_keys=True))

    assert EventEnvelope.from_json(decoded) == envelope


def test_event_envelope_rejects_missing_and_wrong_required_fields() -> None:
    envelope = _event_envelope().to_json()
    del envelope["event_id"]

    with pytest.raises(ValueError, match="missing a required field"):
        EventEnvelope.from_json(envelope)
    with pytest.raises(TypeError, match="event_id must be EventId"):
        EventEnvelope(
            event_id="evt_not_typed",  # type: ignore[arg-type]
            event_type=RuntimeEventType.WORK_CREATED.value,
            schema_version=SchemaVersion.parse("1.0.0"),
            occurred_at=UtcTimestamp.now(),
            producer=ObjectReference.from_id(ProviderId.generate()),
            subject_ref=ObjectReference.from_id(WorkId.generate()),
            observability_context=ObservabilityContext(),
            payload={},
        )


def test_event_envelope_rejects_non_json_payload_values() -> None:
    with pytest.raises(TypeError, match="payload"):
        EventEnvelope(
            event_id=EventId.generate(),
            event_type=RuntimeEventType.WORK_CREATED.value,
            schema_version=SchemaVersion.parse("1.0.0"),
            occurred_at=UtcTimestamp.now(),
            producer=ObjectReference.from_id(ProviderId.generate()),
            subject_ref=ObjectReference.from_id(WorkId.generate()),
            observability_context=ObservabilityContext(),
            payload={"bad": {object()}},
        )


def test_event_envelope_rejects_non_finite_payload_numbers() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        EventEnvelope(
            event_id=EventId.generate(),
            event_type=RuntimeEventType.WORK_CREATED.value,
            schema_version=SchemaVersion.parse("1.0.0"),
            occurred_at=UtcTimestamp.now(),
            producer=ObjectReference.from_id(ProviderId.generate()),
            subject_ref=ObjectReference.from_id(WorkId.generate()),
            observability_context=ObservabilityContext(),
            payload={"bad": float("nan")},
        )


def test_event_type_is_stable_serializable_and_version_independent() -> None:
    event_type = EventType("execution.completed")

    assert str(event_type) == "execution.completed"
    assert event_type.to_json_primitive() == "execution.completed"
    assert RuntimeEventType.EXECUTION_COMPLETED.value == event_type
    assert (
        EventEnvelope(
            event_id=EventId.generate(),
            event_type=event_type,
            schema_version=SchemaVersion.parse("2.0.0"),
            occurred_at=UtcTimestamp.now(),
            producer=ObjectReference.from_id(ProviderId.generate()),
            subject_ref=ObjectReference.from_id(WorkId.generate()),
            observability_context=ObservabilityContext(),
            payload={},
        ).event_type
        == event_type
    )


@pytest.mark.parametrize("value", ["", "WorkCreated", "work", "work.created.v1", "work-created"])
def test_invalid_event_types_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="event type"):
        EventType(value)


def test_minimal_runtime_event_vocabulary_is_explicit_and_bounded() -> None:
    assert (
        EventType("work.created"),
        EventType("execution.started"),
        EventType("execution.completed"),
        EventType("execution.failed"),
        EventType("provider.invoked"),
        EventType("policy.evaluated"),
        EventType("approval.requested"),
        EventType("approval.resolved"),
        EventType("evidence.produced"),
        EventType("verification.completed"),
    ) == RUNTIME_EVENT_TYPES
