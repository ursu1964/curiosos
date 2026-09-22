"""Curios-owned canonical contract package boundary."""

from curios_contracts.artifacts import (
    ARTIFACT_KIND_VALUES,
    INTEGRITY_ALGORITHM_VALUES,
    ArtifactKind,
    ArtifactReference,
    IntegrityAlgorithm,
    IntegrityDescriptor,
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
from curios_contracts.evidence import EVIDENCE_KIND_VALUES, EvidenceKind, EvidenceReference
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

__version__ = "0.0.0"

__all__ = (
    "ARTIFACT_KIND_VALUES",
    "ENGINEERING_LIFECYCLE_VALUES",
    "ERROR_CATEGORY_VALUES",
    "ERROR_SEVERITY_VALUES",
    "EVIDENCE_KIND_VALUES",
    "ID_PREFIXES",
    "ID_TYPES",
    "INTEGRITY_ALGORITHM_VALUES",
    "REFERENCE_KIND_VALUES",
    "RESULT_STATUS_VALUES",
    "VERIFICATION_OUTCOME_VALUES",
    "AgentDefinitionId",
    "AgentInstanceId",
    "ApplicationId",
    "ArtifactId",
    "ArtifactKind",
    "ArtifactReference",
    "CapabilityId",
    "ContractError",
    "CuriosId",
    "DurationMilliseconds",
    "EngineeringLifecycle",
    "ErrorCategory",
    "ErrorCode",
    "ErrorSeverity",
    "EventId",
    "EvidenceKind",
    "EvidenceId",
    "EvidenceReference",
    "ExecutionId",
    "IntegrityAlgorithm",
    "IntegrityDescriptor",
    "MilestoneId",
    "ObjectReference",
    "ProjectId",
    "ProviderId",
    "ReferenceKind",
    "Result",
    "ResultStatus",
    "ResultWarning",
    "SchemaVersion",
    "TraceId",
    "UtcTimestamp",
    "VerificationOutcome",
    "VerificationId",
    "VerificationReference",
    "WorkId",
    "WorkstreamId",
    "__version__",
    "ensure_id_type",
    "to_json_compatible",
)
