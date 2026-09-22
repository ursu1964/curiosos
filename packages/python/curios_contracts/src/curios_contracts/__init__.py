"""Curios-owned canonical contract package boundary."""

from curios_contracts.agents import (
    AGENT_INSTANCE_STATE_VALUES,
    AgentDefinition,
    AgentInstance,
    AgentInstanceState,
)
from curios_contracts.artifacts import (
    ARTIFACT_KIND_VALUES,
    INTEGRITY_ALGORITHM_VALUES,
    ArtifactKind,
    ArtifactReference,
    IntegrityAlgorithm,
    IntegrityDescriptor,
)
from curios_contracts.capabilities import (
    CAPABILITY_CATEGORY_VALUES,
    CAPABILITY_QUALITY_VALUES,
    Capability,
    CapabilityCategory,
    CapabilityQuality,
    CapabilityRequirement,
)
from curios_contracts.errors import (
    ERROR_CATEGORY_VALUES,
    ERROR_SEVERITY_VALUES,
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    ResultWarning,
)
from curios_contracts.events import RUNTIME_EVENT_TYPES, EventEnvelope, EventType, RuntimeEventType
from curios_contracts.evidence import EVIDENCE_KIND_VALUES, EvidenceKind, EvidenceReference
from curios_contracts.executions import EXECUTION_STATE_VALUES, ExecutionRecord, ExecutionState
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
from curios_contracts.providers import (
    PROVIDER_STATUS_VALUES,
    PROVIDER_TYPE_VALUES,
    ProviderDescriptor,
    ProviderStatus,
    ProviderType,
)
from curios_contracts.references import (
    REFERENCE_KIND_VALUES,
    ObjectReference,
    ReferenceKind,
)
from curios_contracts.results import RESULT_STATUS_VALUES, Result, ResultStatus
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import DurationMilliseconds, UtcTimestamp
from curios_contracts.verification import (
    VERIFICATION_OUTCOME_VALUES,
    VerificationOutcome,
    VerificationReference,
)
from curios_contracts.work import WORK_ITEM_STATE_VALUES, WorkItem, WorkItemState

__version__ = "0.0.0"

__all__ = (
    "AGENT_INSTANCE_STATE_VALUES",
    "ARTIFACT_KIND_VALUES",
    "CAPABILITY_CATEGORY_VALUES",
    "CAPABILITY_QUALITY_VALUES",
    "ENGINEERING_LIFECYCLE_VALUES",
    "ERROR_CATEGORY_VALUES",
    "ERROR_SEVERITY_VALUES",
    "EVIDENCE_KIND_VALUES",
    "EXECUTION_STATE_VALUES",
    "ID_PREFIXES",
    "ID_TYPES",
    "INTEGRITY_ALGORITHM_VALUES",
    "PROVIDER_STATUS_VALUES",
    "PROVIDER_TYPE_VALUES",
    "REFERENCE_KIND_VALUES",
    "RESULT_STATUS_VALUES",
    "RUNTIME_EVENT_TYPES",
    "VERIFICATION_OUTCOME_VALUES",
    "WORK_ITEM_STATE_VALUES",
    "AgentDefinition",
    "AgentDefinitionId",
    "AgentInstance",
    "AgentInstanceId",
    "AgentInstanceState",
    "ApplicationId",
    "ArtifactId",
    "ArtifactKind",
    "ArtifactReference",
    "Capability",
    "CapabilityCategory",
    "CapabilityId",
    "CapabilityQuality",
    "CapabilityRequirement",
    "ContractError",
    "CorrelationId",
    "CuriosId",
    "DurationMilliseconds",
    "EngineeringLifecycle",
    "ErrorCategory",
    "ErrorCode",
    "ErrorSeverity",
    "EventEnvelope",
    "EventId",
    "EventType",
    "ExecutionRecord",
    "EvidenceKind",
    "EvidenceId",
    "EvidenceReference",
    "ExecutionState",
    "ExecutionId",
    "IntegrityAlgorithm",
    "IntegrityDescriptor",
    "MilestoneId",
    "ObjectReference",
    "ObservabilityContext",
    "ProjectId",
    "ProviderDescriptor",
    "ProviderId",
    "ProviderStatus",
    "ProviderType",
    "ReferenceKind",
    "Result",
    "ResultStatus",
    "ResultWarning",
    "RuntimeEventType",
    "SchemaVersion",
    "TraceId",
    "UtcTimestamp",
    "VerificationOutcome",
    "VerificationId",
    "VerificationReference",
    "WorkItem",
    "WorkItemState",
    "WorkId",
    "WorkstreamId",
    "__version__",
    "ensure_id_type",
    "to_json_compatible",
)
