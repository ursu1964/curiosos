"""Curios-owned canonical contract package boundary."""

from curios_contracts.identifiers import (
    ID_PREFIXES,
    ID_TYPES,
    AgentDefinitionId,
    AgentInstanceId,
    ApplicationId,
    ArtifactId,
    CapabilityId,
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
    "CuriosId",
    "DurationMilliseconds",
    "EngineeringLifecycle",
    "EventId",
    "EvidenceId",
    "ExecutionId",
    "MilestoneId",
    "ProjectId",
    "ProviderId",
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
