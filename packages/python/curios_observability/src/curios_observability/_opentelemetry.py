"""OpenTelemetry adapter hidden behind the Curios telemetry provider boundary."""

from __future__ import annotations

from dataclasses import dataclass

from curios_contracts import EventEnvelope
from opentelemetry import trace as _trace
from opentelemetry.trace import Span

from curios_observability.telemetry import event_attributes


@dataclass(frozen=True, slots=True)
class OpenTelemetryProvider:
    """Record Curios events on the current OpenTelemetry span."""

    def record_event(self, event: EventEnvelope) -> None:
        """Project a Curios event outward without making OpenTelemetry canonical."""
        span = current_span()
        span.add_event(str(event.event_type), attributes=event_attributes(event))


def create_opentelemetry_provider() -> OpenTelemetryProvider:
    """Create the OpenTelemetry-backed telemetry provider."""
    return OpenTelemetryProvider()


def current_span() -> Span:
    """Return the current OpenTelemetry span for this private adapter."""
    return _trace.get_current_span()
