"""Curios-owned observability and telemetry provider boundary."""

from curios_observability._opentelemetry import (
    OpenTelemetryProvider,
    create_opentelemetry_provider,
)
from curios_observability.telemetry import (
    NoopTelemetryProvider,
    TelemetryAttributes,
    TelemetryAttributeValue,
    TelemetryProvider,
    event_attributes,
    observability_context_attributes,
)

__version__ = "0.0.0"

__all__ = (
    "NoopTelemetryProvider",
    "OpenTelemetryProvider",
    "TelemetryAttributes",
    "TelemetryAttributeValue",
    "TelemetryProvider",
    "__version__",
    "create_opentelemetry_provider",
    "event_attributes",
    "observability_context_attributes",
)
