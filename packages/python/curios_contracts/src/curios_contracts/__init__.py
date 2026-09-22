"""Curios-owned canonical contract package boundary."""

from curios_contracts.events import RUNTIME_EVENT_TYPES, EventEnvelope, EventType, RuntimeEventType
from curios_contracts.identifiers import (
    ID_PREFIXES,
    ID_TYPES,
    AgentDefinitionId,
    AgentInstanceId,
    ApplicationId,
    ArtifactId,
    CapabilityId,
    CorrelationId,
    CuriosId,
    EventId,
    EvidenceId,
    ExecutionId,
    MilestoneId,
    ProjectId,
    ProviderId,
    TraceId,
    VerificationId,
    WorkId,
    WorkstreamId,
    ensure_id_type,
)
from curios_contracts.lifecycle import ENGINEERING_LIFECYCLE_VALUES, EngineeringLifecycle
from curios_contracts.observability import ObservabilityContext
from curios_contracts.references import Reference
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import DurationMilliseconds, UtcTimestamp

__version__ = "0.0.0"

__all__ = (
    "ENGINEERING_LIFECYCLE_VALUES",
    "ID_PREFIXES",
    "ID_TYPES",
    "AgentDefinitionId",
    "AgentInstanceId",
    "ApplicationId",
    "ArtifactId",
    "CapabilityId",
    "CorrelationId",
    "CuriosId",
    "DurationMilliseconds",
    "EngineeringLifecycle",
    "EventEnvelope",
    "EventId",
    "EventType",
    "EvidenceId",
    "ExecutionId",
    "MilestoneId",
    "ObservabilityContext",
    "ProjectId",
    "ProviderId",
    "RUNTIME_EVENT_TYPES",
    "Reference",
    "RuntimeEventType",
    "SchemaVersion",
    "TraceId",
    "UtcTimestamp",
    "VerificationId",
    "WorkId",
    "WorkstreamId",
    "__version__",
    "ensure_id_type",
    "to_json_compatible",
)
