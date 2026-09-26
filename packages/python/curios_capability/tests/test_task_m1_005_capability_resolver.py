from __future__ import annotations

import json

import pytest
from contract_fixtures import fixed_id
from curios_capability import (
    CapabilityResolution,
    CapabilityResolutionReason,
    CapabilityResolutionStatus,
    resolve_capability_requirement,
    resolve_capability_requirements,
)
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    Capability,
    CapabilityCategory,
    CapabilityId,
    CapabilityRequirement,
    ObjectReference,
    ProviderId,
    SchemaVersion,
    WorkId,
    to_json_compatible,
)


def test_known_requirement_matches_exactly_one_capability_and_agent_definition() -> None:
    requirement = _requirement()

    resolution = resolve_capability_requirement(
        requirement,
        capabilities=(_capability(),),
        agent_definitions=(_agent_definition(),),
    )

    assert resolution.status is CapabilityResolutionStatus.MATCHED
    assert resolution.reason is CapabilityResolutionReason.EXACT_MATCH
    assert resolution.capability_ref == ObjectReference.from_id(_capability_id())
    assert resolution.agent_definition_ref == ObjectReference.from_id(_agent_definition_id())
    assert resolution.ambiguous_capability_refs == ()
    assert resolution.ambiguous_agent_definition_refs == ()


def test_resolution_is_deterministic_and_round_trips_json() -> None:
    requirement = _requirement()
    first = resolve_capability_requirement(
        requirement,
        capabilities=(_capability(),),
        agent_definitions=(_agent_definition(),),
    )
    second = resolve_capability_requirement(
        requirement,
        capabilities=(_capability(),),
        agent_definitions=(_agent_definition(),),
    )
    decoded = json.loads(json.dumps(first.to_json_compatible(), sort_keys=True))

    assert first == second
    assert first.to_json_compatible() == second.to_json_compatible()
    assert CapabilityResolution.from_json_compatible(decoded) == first


def test_missing_capability_is_bounded_and_does_not_emit_partial_selection() -> None:
    resolution = resolve_capability_requirement(
        _requirement(),
        capabilities=(),
        agent_definitions=(_agent_definition(),),
    )

    assert resolution.status is CapabilityResolutionStatus.MISSING
    assert resolution.reason is CapabilityResolutionReason.CAPABILITY_NOT_OFFERED
    assert resolution.capability_ref is None
    assert resolution.agent_definition_ref is None
    assert resolution.ambiguous_capability_refs == ()
    assert resolution.ambiguous_agent_definition_refs == ()


def test_missing_agent_definition_keeps_capability_fact_without_granting_authority() -> None:
    resolution = resolve_capability_requirement(
        _requirement(),
        capabilities=(_capability(),),
        agent_definitions=(),
    )

    assert resolution.status is CapabilityResolutionStatus.MISSING
    assert resolution.reason is CapabilityResolutionReason.AGENT_NOT_ELIGIBLE
    assert resolution.capability_ref == ObjectReference.from_id(_capability_id())
    assert resolution.agent_definition_ref is None


def test_duplicate_offered_capabilities_fail_as_ambiguous() -> None:
    resolution = resolve_capability_requirement(
        _requirement(),
        capabilities=(_capability(description="First"), _capability(description="Second")),
        agent_definitions=(_agent_definition(),),
    )

    assert resolution.status is CapabilityResolutionStatus.AMBIGUOUS
    assert resolution.reason is CapabilityResolutionReason.DUPLICATE_CAPABILITY
    assert resolution.capability_ref is None
    assert resolution.agent_definition_ref is None
    assert resolution.ambiguous_capability_refs == (
        ObjectReference.from_id(_capability_id()),
        ObjectReference.from_id(_capability_id()),
    )
    assert resolution.ambiguous_agent_definition_refs == ()


def test_multiple_eligible_agent_definitions_fail_as_ambiguous_in_stable_order() -> None:
    first = _agent_definition(ordinal=0)
    second = _agent_definition(ordinal=1)

    resolution = resolve_capability_requirement(
        _requirement(),
        capabilities=(_capability(),),
        agent_definitions=(second, first),
    )

    assert resolution.status is CapabilityResolutionStatus.AMBIGUOUS
    assert resolution.reason is CapabilityResolutionReason.MULTIPLE_ELIGIBLE_AGENTS
    assert resolution.capability_ref == ObjectReference.from_id(_capability_id())
    assert resolution.agent_definition_ref is None
    assert resolution.ambiguous_agent_definition_refs == (
        ObjectReference.from_id(first.agent_definition_id),
        ObjectReference.from_id(second.agent_definition_id),
    )


def test_capability_hints_do_not_create_ranking_or_provider_selection() -> None:
    requirement = CapabilityRequirement(
        capability_id=_capability_id(),
        privacy_constraints={"boundary": "workspace"},
        cost_budget={"units": 1},
    )
    resolution = resolve_capability_requirement(
        requirement,
        capabilities=(_capability(metadata={"tier": "different"}),),
        agent_definitions=(_agent_definition(constraints={"tier": "different"}),),
    )

    assert resolution.status is CapabilityResolutionStatus.MATCHED
    assert "provider" not in str(resolution.to_json_compatible()).lower()


def test_multiple_requirements_preserve_requirement_order_without_shared_state() -> None:
    second_capability_id = fixed_id(CapabilityId, 1)
    resolutions = resolve_capability_requirements(
        (_requirement(), CapabilityRequirement(capability_id=second_capability_id)),
        capabilities=(_capability(),),
        agent_definitions=(_agent_definition(),),
    )

    assert [resolution.requirement.capability_id for resolution in resolutions] == [
        _capability_id(),
        second_capability_id,
    ]
    assert [resolution.status for resolution in resolutions] == [
        CapabilityResolutionStatus.MATCHED,
        CapabilityResolutionStatus.MISSING,
    ]


def test_resolution_record_rejects_cross_kind_and_inconsistent_refs() -> None:
    with pytest.raises(ValueError, match="capability_ref must reference capability"):
        CapabilityResolution(
            requirement=_requirement(),
            status=CapabilityResolutionStatus.MATCHED,
            reason=CapabilityResolutionReason.EXACT_MATCH,
            capability_ref=ObjectReference.from_id(WorkId.generate()),
            agent_definition_ref=ObjectReference.from_id(_agent_definition_id()),
        )

    with pytest.raises(ValueError, match="agent_definition_ref must reference agent_definition"):
        CapabilityResolution(
            requirement=_requirement(),
            status=CapabilityResolutionStatus.MATCHED,
            reason=CapabilityResolutionReason.EXACT_MATCH,
            capability_ref=ObjectReference.from_id(_capability_id()),
            agent_definition_ref=ObjectReference.from_id(ProviderId.generate()),
        )

    with pytest.raises(ValueError, match="matched capability resolution requires"):
        CapabilityResolution(
            requirement=_requirement(),
            status=CapabilityResolutionStatus.MATCHED,
            reason=CapabilityResolutionReason.EXACT_MATCH,
            capability_ref=ObjectReference.from_id(_capability_id()),
        )


def test_resolver_rejects_malformed_inputs_without_partial_output() -> None:
    with pytest.raises(TypeError, match="requirement must be a CapabilityRequirement"):
        resolve_capability_requirement(  # type: ignore[arg-type]
            object(),
            capabilities=(_capability(),),
            agent_definitions=(_agent_definition(),),
        )

    with pytest.raises(TypeError, match="capabilities must contain Capability values"):
        resolve_capability_requirement(
            _requirement(),
            capabilities=(object(),),  # type: ignore[arg-type]
            agent_definitions=(_agent_definition(),),
        )

    with pytest.raises(TypeError, match="agent_definitions must contain AgentDefinition values"):
        resolve_capability_requirement(
            _requirement(),
            capabilities=(_capability(),),
            agent_definitions=(object(),),  # type: ignore[arg-type]
        )


def test_resolution_surface_has_no_runtime_authority_fields() -> None:
    serialized = resolve_capability_requirement(
        _requirement(),
        capabilities=(_capability(),),
        agent_definitions=(_agent_definition(),),
    ).to_json_compatible()

    forbidden = {
        "provider_id",
        "provider_refs",
        "execution_id",
        "work_id",
        "state",
        "authority_ref",
        "principal_ref",
        "policy_decision",
        "schedule",
        "retry",
        "route",
    }
    assert forbidden.isdisjoint(serialized)
    assert to_json_compatible(serialized) == serialized


def _capability_id() -> CapabilityId:
    return fixed_id(CapabilityId)


def _agent_definition_id(ordinal: int = 0) -> AgentDefinitionId:
    return fixed_id(AgentDefinitionId, ordinal)


def _requirement() -> CapabilityRequirement:
    return CapabilityRequirement(capability_id=_capability_id())


def _capability(
    *,
    description: str = "Summarize recorded project context.",
    metadata: dict[str, object] | None = None,
) -> Capability:
    return Capability(
        capability_id=_capability_id(),
        key="recorded_context_summary",
        version=SchemaVersion(major=1, minor=0, patch=0),
        description=description,
        category=CapabilityCategory.COGNITIVE,
        metadata=metadata,
    )


def _agent_definition(
    *,
    ordinal: int = 0,
    constraints: dict[str, object] | None = None,
) -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=_agent_definition_id(ordinal),
        name=f"summary_agent_{ordinal}",
        version=SchemaVersion(major=1, minor=0, patch=0),
        purpose="Resolve bounded capability requirements for tests.",
        allowed_capability_ids=(_capability_id(),),
        constraints=constraints,
    )
