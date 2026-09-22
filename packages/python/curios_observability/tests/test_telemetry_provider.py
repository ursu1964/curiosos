from __future__ import annotations

import pytest
from curios_contracts import (
    CorrelationId,
    EventEnvelope,
    EventId,
    EventType,
    ObjectReference,
    ObservabilityContext,
    ProjectId,
    RuntimeEventType,
    SchemaVersion,
    TraceId,
    UtcTimestamp,
    WorkId,
)
from curios_observability import (
    NoopTelemetryProvider,
    TelemetryProvider,
    _opentelemetry,
    create_opentelemetry_provider,
    event_attributes,
    observability_context_attributes,
)

ULID = "00000000000000000000000000"


def _id(prefix: str) -> str:
    return f"{prefix}_{ULID}"


def _event() -> EventEnvelope:
    return EventEnvelope(
        event_id=EventId(_id("evt")),
        event_type=RuntimeEventType.EXECUTION_STARTED.value,
        schema_version=SchemaVersion(1, 0, 0),
        occurred_at=UtcTimestamp.parse("2026-09-22T08:00:00Z"),
        producer=ObjectReference.from_id(ProjectId(_id("prj"))),
        subject_ref=ObjectReference.from_id(WorkId(_id("wrk"))),
        observability_context=ObservabilityContext(
            trace_id=TraceId(_id("trc")),
            correlation_id=CorrelationId(_id("cor")),
        ),
        payload={"state": "started"},
    )


def test_observability_context_attributes_preserve_curios_identifiers() -> None:
    context = ObservabilityContext(
        trace_id=TraceId(_id("trc")),
        correlation_id=CorrelationId(_id("cor")),
    )

    attributes = observability_context_attributes(context)

    assert attributes == {
        "curios.trace_id": _id("trc"),
        "curios.correlation_id": _id("cor"),
    }
    assert "otel.trace_id" not in attributes


def test_event_attributes_project_canonical_event_without_payload_authority() -> None:
    attributes = event_attributes(_event())

    assert attributes["curios.event_id"] == _id("evt")
    assert attributes["curios.event_type"] == "execution.started"
    assert attributes["curios.schema_version"] == "1.0.0"
    assert attributes["curios.producer.kind"] == "project"
    assert attributes["curios.producer.ref_id"] == _id("prj")
    assert attributes["curios.subject_ref.kind"] == "work"
    assert attributes["curios.subject_ref.ref_id"] == _id("wrk")
    assert "curios.payload" not in attributes


def test_noop_provider_is_the_minimum_telemetry_provider_boundary() -> None:
    provider = NoopTelemetryProvider()

    assert isinstance(provider, TelemetryProvider)
    provider.record_event(_event())


def test_opentelemetry_provider_records_canonical_event_on_current_span(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[tuple[str, object]] = []

    class Span:
        def add_event(self, name: str, attributes: object) -> None:
            recorded.append((name, attributes))

    monkeypatch.setattr(_opentelemetry, "current_span", lambda: Span())

    create_opentelemetry_provider().record_event(_event())

    assert recorded == [
        (
            EventType("execution.started"),
            {
                "curios.event_id": _id("evt"),
                "curios.event_type": "execution.started",
                "curios.schema_version": "1.0.0",
                "curios.occurred_at": "2026-09-22T08:00:00Z",
                "curios.producer.kind": "project",
                "curios.producer.ref_id": _id("prj"),
                "curios.subject_ref.kind": "work",
                "curios.subject_ref.ref_id": _id("wrk"),
                "curios.trace_id": _id("trc"),
                "curios.correlation_id": _id("cor"),
            },
        )
    ]
