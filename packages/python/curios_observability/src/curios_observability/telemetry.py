"""Telemetry provider boundary for canonical Curios observability records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from curios_contracts import EventEnvelope, ObservabilityContext

type TelemetryAttributeValue = (
    bool
    | int
    | float
    | str
    | tuple[bool, ...]
    | tuple[int, ...]
    | tuple[float, ...]
    | tuple[str, ...]
)
type TelemetryAttributes = Mapping[str, TelemetryAttributeValue]


@runtime_checkable
class TelemetryProvider(Protocol):
    """Provider boundary that records canonical Curios events in telemetry systems."""

    def record_event(self, event: EventEnvelope) -> None:
        """Record a canonical Curios event without changing its semantics."""


@dataclass(frozen=True, slots=True)
class NoopTelemetryProvider:
    """Telemetry provider implementation that validates input and records nothing."""

    def record_event(self, event: EventEnvelope) -> None:
        """Accept a canonical Curios event without producing provider output."""
        _require_event(event)


def observability_context_attributes(
    context: ObservabilityContext,
) -> dict[str, TelemetryAttributeValue]:
    """Project Curios observability context into provider-safe scalar attributes."""
    if not isinstance(context, ObservabilityContext):
        msg = "context must be ObservabilityContext"
        raise TypeError(msg)

    attributes: dict[str, TelemetryAttributeValue] = {}
    for field_name, value in context.to_json_compatible().items():
        if isinstance(value, str):
            attributes[f"curios.{field_name}"] = value
            continue
        if isinstance(value, dict):
            _add_reference_attributes(attributes, f"curios.{field_name}", value)
    return attributes


def event_attributes(event: EventEnvelope) -> dict[str, TelemetryAttributeValue]:
    """Project a canonical Curios event envelope into telemetry attributes."""
    _require_event(event)

    attributes: dict[str, TelemetryAttributeValue] = {
        "curios.event_id": str(event.event_id),
        "curios.event_type": str(event.event_type),
        "curios.schema_version": str(event.schema_version),
        "curios.occurred_at": str(event.occurred_at),
    }
    _add_reference_attributes(attributes, "curios.producer", event.producer.to_json_compatible())
    _add_reference_attributes(
        attributes,
        "curios.subject_ref",
        event.subject_ref.to_json_compatible(),
    )
    attributes.update(observability_context_attributes(event.observability_context))
    return attributes


def _add_reference_attributes(
    attributes: dict[str, TelemetryAttributeValue],
    prefix: str,
    value: Mapping[str, object],
) -> None:
    kind = value.get("kind")
    ref_id = value.get("ref_id")
    if isinstance(kind, str):
        attributes[f"{prefix}.kind"] = kind
    if isinstance(ref_id, str):
        attributes[f"{prefix}.ref_id"] = ref_id


def _require_event(event: object) -> EventEnvelope:
    if not isinstance(event, EventEnvelope):
        msg = "event must be EventEnvelope"
        raise TypeError(msg)
    return event
