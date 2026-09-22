from __future__ import annotations

from dataclasses import dataclass

from curios_contracts import (
    AgentDefinitionId,
    AgentInstanceId,
    ArtifactId,
    CapabilityId,
    ContractError,
    CorrelationId,
    CuriosId,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    EventId,
    EvidenceId,
    ExecutionId,
    ObjectReference,
    Principal,
    PrincipalType,
    ProjectId,
    ProviderId,
    SchemaVersion,
    TraceId,
    UtcTimestamp,
    VerificationId,
    WorkId,
)

UTC_NOW = UtcTimestamp.parse("2026-09-22T08:15:30Z")
UTC_LATER = UtcTimestamp.parse("2026-09-22T09:15:30Z")
SCHEMA_V1 = SchemaVersion.parse("1.0.0")

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def fixed_id[IdT: CuriosId](id_type: type[IdT], ordinal: int = 0) -> IdT:
    """Return a deterministic typed Curios ID for repository contract fixtures."""
    if ordinal < 0 or ordinal >= len(_ULID_ALPHABET):
        msg = "fixture ordinal must fit the ULID alphabet"
        raise ValueError(msg)
    return id_type(f"{id_type.prefix}_{'0' * 25}{_ULID_ALPHABET[ordinal]}")


def ref_for[IdT: CuriosId](id_type: type[IdT], ordinal: int = 0) -> ObjectReference:
    return ObjectReference.from_id(fixed_id(id_type, ordinal))


@dataclass(frozen=True, slots=True)
class ContractIds:
    project_id: ProjectId = fixed_id(ProjectId)
    work_id: WorkId = fixed_id(WorkId)
    execution_id: ExecutionId = fixed_id(ExecutionId)
    agent_definition_id: AgentDefinitionId = fixed_id(AgentDefinitionId)
    agent_instance_id: AgentInstanceId = fixed_id(AgentInstanceId)
    capability_id: CapabilityId = fixed_id(CapabilityId)
    provider_id: ProviderId = fixed_id(ProviderId)
    artifact_id: ArtifactId = fixed_id(ArtifactId)
    evidence_id: EvidenceId = fixed_id(EvidenceId)
    verification_id: VerificationId = fixed_id(VerificationId)
    event_id: EventId = fixed_id(EventId)
    trace_id: TraceId = fixed_id(TraceId)
    correlation_id: CorrelationId = fixed_id(CorrelationId)


def contract_ids() -> ContractIds:
    return ContractIds()


def human_principal() -> Principal:
    return Principal(
        principal_type=PrincipalType.HUMAN,
        identity="operator@example.test",
        principal_ref=ref_for(ProjectId),
    )


def contract_error() -> ContractError:
    return ContractError(
        error_code=ErrorCode("CONTRACT_FAILURE"),
        message="Contract invariant failed.",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        retryable=False,
        subject_ref=ref_for(WorkId),
        trace_id=fixed_id(TraceId),
    )
