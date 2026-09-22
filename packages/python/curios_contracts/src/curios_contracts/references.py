"""Provider-neutral object reference primitives for canonical Curios contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Self

from curios_contracts.identifiers import (
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
)


class ReferenceKind(StrEnum):
    """Stable object-reference namespaces derived from frozen Curios ID prefixes."""

    PROJECT = "project"
    APPLICATION = "application"
    MILESTONE = "milestone"
    WORKSTREAM = "workstream"
    WORK = "work"
    EXECUTION = "execution"
    AGENT_DEFINITION = "agent_definition"
    AGENT_INSTANCE = "agent_instance"
    CAPABILITY = "capability"
    PROVIDER = "provider"
    ARTIFACT = "artifact"
    EVIDENCE = "evidence"
    VERIFICATION = "verification"
    EVENT = "event"
    TRACE = "trace"


_REFERENCE_ID_TYPES: dict[ReferenceKind, type[CuriosId]] = {
    ReferenceKind.PROJECT: ProjectId,
    ReferenceKind.APPLICATION: ApplicationId,
    ReferenceKind.MILESTONE: MilestoneId,
    ReferenceKind.WORKSTREAM: WorkstreamId,
    ReferenceKind.WORK: WorkId,
    ReferenceKind.EXECUTION: ExecutionId,
    ReferenceKind.AGENT_DEFINITION: AgentDefinitionId,
    ReferenceKind.AGENT_INSTANCE: AgentInstanceId,
    ReferenceKind.CAPABILITY: CapabilityId,
    ReferenceKind.PROVIDER: ProviderId,
    ReferenceKind.ARTIFACT: ArtifactId,
    ReferenceKind.EVIDENCE: EvidenceId,
    ReferenceKind.VERIFICATION: VerificationId,
    ReferenceKind.EVENT: EventId,
    ReferenceKind.TRACE: TraceId,
}
_REFERENCE_KIND_BY_ID_TYPE: dict[type[CuriosId], ReferenceKind] = {
    id_type: kind for kind, id_type in _REFERENCE_ID_TYPES.items()
}


@dataclass(frozen=True, slots=True)
class ObjectReference:
    """Small canonical reference to another Curios runtime object.

    The pair of ``kind`` and typed ``ref_id`` preserves namespace meaning without
    introducing the full object model for that referenced entity.
    """

    kind: ReferenceKind
    ref_id: CuriosId

    _id_types: ClassVar[dict[ReferenceKind, type[CuriosId]]] = _REFERENCE_ID_TYPES

    def __post_init__(self) -> None:
        kind = ReferenceKind(self.kind)
        if not isinstance(self.ref_id, CuriosId):
            msg = "ref_id must be a CuriosId"
            raise TypeError(msg)

        expected_id_type = self._id_types[kind]
        if type(self.ref_id) is not expected_id_type:
            msg = f"{kind.value} references require {expected_id_type.__name__}"
            raise TypeError(msg)

        object.__setattr__(self, "kind", kind)

    @classmethod
    def from_id(cls, ref_id: CuriosId) -> Self:
        """Create a reference using the namespace implied by a concrete ID type."""
        kind = _REFERENCE_KIND_BY_ID_TYPE.get(type(ref_id))
        if kind is None:
            msg = f"unsupported reference ID type {type(ref_id).__name__}"
            raise TypeError(msg)
        return cls(kind=kind, ref_id=ref_id)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "object reference JSON must be an object"
            raise TypeError(msg)
        kind = ReferenceKind(value["kind"])
        ref_id_value = value["ref_id"]
        if not isinstance(ref_id_value, str):
            msg = "object reference ref_id must be a string"
            raise TypeError(msg)
        return cls(kind=kind, ref_id=cls._id_types[kind](ref_id_value))

    def to_json_compatible(self) -> dict[str, str]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "kind": self.kind.value,
            "ref_id": str(self.ref_id),
        }


REFERENCE_KIND_VALUES: tuple[str, ...] = tuple(member.value for member in ReferenceKind)
