"""Deterministic capability matching over frozen Curios contracts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts import (
    AgentDefinition,
    Capability,
    CapabilityRequirement,
    ObjectReference,
    ReferenceKind,
    to_json_compatible,
)


class CapabilityResolutionStatus(StrEnum):
    """Bounded capability-resolution outcomes."""

    MATCHED = "MATCHED"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"


class CapabilityResolutionReason(StrEnum):
    """Stable explanation vocabulary for deterministic resolution."""

    EXACT_MATCH = "EXACT_MATCH"
    CAPABILITY_NOT_OFFERED = "CAPABILITY_NOT_OFFERED"
    AGENT_NOT_ELIGIBLE = "AGENT_NOT_ELIGIBLE"
    DUPLICATE_CAPABILITY = "DUPLICATE_CAPABILITY"
    MULTIPLE_ELIGIBLE_AGENTS = "MULTIPLE_ELIGIBLE_AGENTS"


@dataclass(frozen=True, slots=True)
class CapabilityResolution:
    """Inert record of one deterministic capability-resolution decision."""

    requirement: CapabilityRequirement
    status: CapabilityResolutionStatus
    reason: CapabilityResolutionReason
    capability_ref: ObjectReference | None = None
    agent_definition_ref: ObjectReference | None = None
    ambiguous_capability_refs: tuple[ObjectReference, ...] = ()
    ambiguous_agent_definition_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.requirement, CapabilityRequirement):
            msg = "requirement must be a CapabilityRequirement"
            raise TypeError(msg)
        object.__setattr__(self, "status", CapabilityResolutionStatus(self.status))
        object.__setattr__(self, "reason", CapabilityResolutionReason(self.reason))
        object.__setattr__(
            self,
            "capability_ref",
            _optional_ref(self.capability_ref, ReferenceKind.CAPABILITY, "capability_ref"),
        )
        object.__setattr__(
            self,
            "agent_definition_ref",
            _optional_ref(
                self.agent_definition_ref,
                ReferenceKind.AGENT_DEFINITION,
                "agent_definition_ref",
            ),
        )
        object.__setattr__(
            self,
            "ambiguous_capability_refs",
            _sorted_refs(
                self.ambiguous_capability_refs,
                ReferenceKind.CAPABILITY,
                "ambiguous_capability_refs",
            ),
        )
        object.__setattr__(
            self,
            "ambiguous_agent_definition_refs",
            _sorted_refs(
                self.ambiguous_agent_definition_refs,
                ReferenceKind.AGENT_DEFINITION,
                "ambiguous_agent_definition_refs",
            ),
        )
        _validate_resolution_shape(self)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        if not isinstance(value, dict):
            msg = "capability resolution JSON must be an object"
            raise TypeError(msg)
        return cls(
            requirement=CapabilityRequirement.from_json_compatible(value["requirement"]),
            status=CapabilityResolutionStatus(_require_str(value["status"], "status")),
            reason=CapabilityResolutionReason(_require_str(value["reason"], "reason")),
            capability_ref=_optional_reference(value.get("capability_ref")),
            agent_definition_ref=_optional_reference(value.get("agent_definition_ref")),
            ambiguous_capability_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("ambiguous_capability_refs"),
                    "ambiguous_capability_refs",
                )
            ),
            ambiguous_agent_definition_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("ambiguous_agent_definition_refs"),
                    "ambiguous_agent_definition_refs",
                )
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "requirement": to_json_compatible(self.requirement),
            "status": self.status.value,
            "reason": self.reason.value,
            "capability_ref": to_json_compatible(self.capability_ref),
            "agent_definition_ref": to_json_compatible(self.agent_definition_ref),
            "ambiguous_capability_refs": to_json_compatible(self.ambiguous_capability_refs),
            "ambiguous_agent_definition_refs": to_json_compatible(
                self.ambiguous_agent_definition_refs
            ),
        }


def resolve_capability_requirement(
    requirement: CapabilityRequirement,
    *,
    capabilities: Iterable[Capability],
    agent_definitions: Iterable[AgentDefinition],
) -> CapabilityResolution:
    """Resolve one requirement by exact capability ID and eligible agent definition."""

    if not isinstance(requirement, CapabilityRequirement):
        msg = "requirement must be a CapabilityRequirement"
        raise TypeError(msg)

    offered = _capabilities_by_required_id(_require_capabilities(capabilities), requirement)
    if not offered:
        return CapabilityResolution(
            requirement=requirement,
            status=CapabilityResolutionStatus.MISSING,
            reason=CapabilityResolutionReason.CAPABILITY_NOT_OFFERED,
        )
    if len(offered) > 1:
        return CapabilityResolution(
            requirement=requirement,
            status=CapabilityResolutionStatus.AMBIGUOUS,
            reason=CapabilityResolutionReason.DUPLICATE_CAPABILITY,
            ambiguous_capability_refs=tuple(
                ObjectReference.from_id(capability.capability_id) for capability in offered
            ),
        )

    capability = offered[0]
    capability_ref = ObjectReference.from_id(capability.capability_id)
    eligible_agents = _agent_definitions_by_allowed_capability(
        _require_agent_definitions(agent_definitions),
        requirement,
    )
    if not eligible_agents:
        return CapabilityResolution(
            requirement=requirement,
            status=CapabilityResolutionStatus.MISSING,
            reason=CapabilityResolutionReason.AGENT_NOT_ELIGIBLE,
            capability_ref=capability_ref,
        )
    if len(eligible_agents) > 1:
        return CapabilityResolution(
            requirement=requirement,
            status=CapabilityResolutionStatus.AMBIGUOUS,
            reason=CapabilityResolutionReason.MULTIPLE_ELIGIBLE_AGENTS,
            capability_ref=capability_ref,
            ambiguous_agent_definition_refs=tuple(
                ObjectReference.from_id(agent.agent_definition_id) for agent in eligible_agents
            ),
        )

    return CapabilityResolution(
        requirement=requirement,
        status=CapabilityResolutionStatus.MATCHED,
        reason=CapabilityResolutionReason.EXACT_MATCH,
        capability_ref=capability_ref,
        agent_definition_ref=ObjectReference.from_id(eligible_agents[0].agent_definition_id),
    )


def resolve_capability_requirements(
    requirements: Iterable[CapabilityRequirement],
    *,
    capabilities: Iterable[Capability],
    agent_definitions: Iterable[AgentDefinition],
) -> tuple[CapabilityResolution, ...]:
    """Resolve a bounded sequence of requirements without changing their order."""

    normalized_requirements = _require_requirements(requirements)
    normalized_capabilities = _require_capabilities(capabilities)
    normalized_agent_definitions = _require_agent_definitions(agent_definitions)
    return tuple(
        resolve_capability_requirement(
            requirement,
            capabilities=normalized_capabilities,
            agent_definitions=normalized_agent_definitions,
        )
        for requirement in normalized_requirements
    )


def _capabilities_by_required_id(
    capabilities: tuple[Capability, ...],
    requirement: CapabilityRequirement,
) -> tuple[Capability, ...]:
    return tuple(
        sorted(
            (
                capability
                for capability in capabilities
                if capability.capability_id == requirement.capability_id
            ),
            key=lambda capability: (
                str(capability.capability_id),
                capability.key,
                str(capability.version),
                capability.description,
            ),
        )
    )


def _agent_definitions_by_allowed_capability(
    agent_definitions: tuple[AgentDefinition, ...],
    requirement: CapabilityRequirement,
) -> tuple[AgentDefinition, ...]:
    return tuple(
        sorted(
            (
                agent
                for agent in agent_definitions
                if requirement.capability_id in agent.allowed_capability_ids
            ),
            key=lambda agent: (str(agent.agent_definition_id), agent.name, str(agent.version)),
        )
    )


def _require_requirements(
    requirements: Iterable[CapabilityRequirement],
) -> tuple[CapabilityRequirement, ...]:
    normalized = tuple(requirements)
    for requirement in normalized:
        if not isinstance(requirement, CapabilityRequirement):
            msg = "requirements must contain CapabilityRequirement values"
            raise TypeError(msg)
    return normalized


def _require_capabilities(capabilities: Iterable[Capability]) -> tuple[Capability, ...]:
    normalized = tuple(capabilities)
    for capability in normalized:
        if not isinstance(capability, Capability):
            msg = "capabilities must contain Capability values"
            raise TypeError(msg)
    return normalized


def _require_agent_definitions(
    agent_definitions: Iterable[AgentDefinition],
) -> tuple[AgentDefinition, ...]:
    normalized = tuple(agent_definitions)
    for agent_definition in normalized:
        if not isinstance(agent_definition, AgentDefinition):
            msg = "agent_definitions must contain AgentDefinition values"
            raise TypeError(msg)
    return normalized


def _optional_ref(
    reference: ObjectReference | None,
    expected_kind: ReferenceKind,
    field_name: str,
) -> ObjectReference | None:
    if reference is None:
        return None
    if not isinstance(reference, ObjectReference):
        msg = f"{field_name} must be an ObjectReference when provided"
        raise TypeError(msg)
    if reference.kind is not expected_kind:
        msg = f"{field_name} must reference {expected_kind.value} objects"
        raise ValueError(msg)
    return reference


def _sorted_refs(
    references: tuple[ObjectReference, ...],
    expected_kind: ReferenceKind,
    field_name: str,
) -> tuple[ObjectReference, ...]:
    normalized = tuple(references)
    for reference in normalized:
        _optional_ref(reference, expected_kind, f"{field_name} item")
    return tuple(sorted(normalized, key=lambda reference: str(reference.ref_id)))


def _validate_resolution_shape(resolution: CapabilityResolution) -> None:
    if resolution.status is CapabilityResolutionStatus.MATCHED:
        if resolution.reason is not CapabilityResolutionReason.EXACT_MATCH:
            msg = "matched capability resolution requires EXACT_MATCH reason"
            raise ValueError(msg)
        if resolution.capability_ref is None or resolution.agent_definition_ref is None:
            msg = "matched capability resolution requires capability and agent definition refs"
            raise ValueError(msg)
        if resolution.ambiguous_capability_refs or resolution.ambiguous_agent_definition_refs:
            msg = "matched capability resolution must not include ambiguity refs"
            raise ValueError(msg)
        return

    if resolution.status is CapabilityResolutionStatus.MISSING:
        if resolution.agent_definition_ref is not None:
            msg = "missing capability resolution must not include an agent definition ref"
            raise ValueError(msg)
        if resolution.ambiguous_capability_refs or resolution.ambiguous_agent_definition_refs:
            msg = "missing capability resolution must not include ambiguity refs"
            raise ValueError(msg)
        if resolution.reason is CapabilityResolutionReason.CAPABILITY_NOT_OFFERED:
            if resolution.capability_ref is not None:
                msg = "missing offered capability must not include a capability ref"
                raise ValueError(msg)
            return
        if resolution.reason is CapabilityResolutionReason.AGENT_NOT_ELIGIBLE:
            if resolution.capability_ref is None:
                msg = "missing eligible agent requires the matched capability ref"
                raise ValueError(msg)
            return

    if resolution.status is CapabilityResolutionStatus.AMBIGUOUS:
        if resolution.agent_definition_ref is not None:
            msg = "ambiguous capability resolution must not include selected agent ref"
            raise ValueError(msg)
        if resolution.reason is CapabilityResolutionReason.DUPLICATE_CAPABILITY:
            if resolution.capability_ref is not None:
                msg = "duplicate capability ambiguity must not include selected capability ref"
                raise ValueError(msg)
            if len(resolution.ambiguous_capability_refs) < 2:
                msg = "duplicate capability ambiguity requires at least two capability refs"
                raise ValueError(msg)
            if resolution.ambiguous_agent_definition_refs:
                msg = "duplicate capability ambiguity must not include agent ambiguity refs"
                raise ValueError(msg)
            return
        if resolution.reason is CapabilityResolutionReason.MULTIPLE_ELIGIBLE_AGENTS:
            if resolution.capability_ref is None:
                msg = "agent ambiguity requires the matched capability ref"
                raise ValueError(msg)
            if len(resolution.ambiguous_agent_definition_refs) < 2:
                msg = "agent ambiguity requires at least two agent definition refs"
                raise ValueError(msg)
            if resolution.ambiguous_capability_refs:
                msg = "agent ambiguity must not include capability ambiguity refs"
                raise ValueError(msg)
            return

    msg = "capability resolution status and reason are inconsistent"
    raise ValueError(msg)


def _optional_reference(value: object) -> ObjectReference | None:
    if value is None:
        return None
    return ObjectReference.from_json_compatible(value)


def _optional_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    return tuple(value)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value
