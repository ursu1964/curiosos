from __future__ import annotations

import json
from dataclasses import fields

import pytest
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    ApplicationId,
    ArtifactId,
    Capability,
    CapabilityCategory,
    CapabilityId,
    CapabilityQuality,
    CapabilityRequirement,
    ContractError,
    DurationMilliseconds,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    EvidenceId,
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    ObjectReference,
    ObservabilityContext,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    ReferenceKind,
    Result,
    SchemaVersion,
    TraceId,
    UtcTimestamp,
    VerificationId,
    WorkId,
    WorkItem,
    WorkItemState,
    to_json_compatible,
)
from curios_contracts.lifecycle import EngineeringLifecycle


def _timestamp() -> UtcTimestamp:
    return UtcTimestamp("2026-09-22T10:00:00Z")


def _capability_id() -> CapabilityId:
    return CapabilityId("cap_01K5V7EDNV6G7GVQ8F94N3EX01")


def _work_id() -> WorkId:
    return WorkId("wrk_01K5V7EDNV6G7GVQ8F94N3EX02")


def _capability_requirement() -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=_capability_id(),
        quality=CapabilityQuality.STANDARD,
        privacy_constraints={"data_boundary": "synthetic"},
    )


def _artifact_ref() -> ObjectReference:
    return ObjectReference.from_id(ArtifactId("art_01K5V7EDNV6G7GVQ8F94N3EX03"))


def test_capability_is_provider_independent_and_stably_serializable() -> None:
    capability = Capability(
        capability_id=_capability_id(),
        key="dataset_profiling",
        version=SchemaVersion(major=1, minor=0, patch=0),
        description="Profile a dataset and summarize structural properties.",
        category=CapabilityCategory.DATA,
        metadata={"input_shape": "tabular"},
    )

    compatible = capability.to_json_compatible()
    decoded = json.loads(json.dumps(to_json_compatible(capability), sort_keys=True))

    assert isinstance(capability.capability_id, CapabilityId)
    assert "provider_id" not in compatible
    assert "provider_type" not in compatible
    assert decoded == compatible
    assert Capability.from_json_compatible(decoded) == capability


def test_capability_requirement_supports_optional_provider_neutral_constraints() -> None:
    policy_ref = ObjectReference.from_id(ApplicationId("app_01K5V7EDNV6G7GVQ8F94N3EX04"))
    requirement = CapabilityRequirement(
        capability_id=_capability_id(),
        quality=CapabilityQuality.HIGH,
        privacy_constraints={"data_boundary": "workspace"},
        latency_budget_ms=DurationMilliseconds(2500),
        cost_budget={"units": 100},
        resource_constraints={"memory_tier": "small"},
        policy_constraint_refs=(policy_ref,),
    )

    field_names = {field.name for field in fields(CapabilityRequirement)}
    decoded = json.loads(json.dumps(to_json_compatible(requirement), sort_keys=True))

    assert requirement.capability_id == _capability_id()
    assert "provider_id" not in field_names
    assert "provider_type" not in field_names
    assert "model_name" not in field_names
    assert decoded["latency_budget_ms"] == 2500
    assert CapabilityRequirement.from_json_compatible(decoded) == requirement


def test_provider_descriptor_declares_capabilities_without_credentials() -> None:
    provider = ProviderDescriptor(
        provider_id=ProviderId("prv_01K5V7EDNV6G7GVQ8F94N3EX05"),
        provider_type=ProviderType.TOOL,
        version=SchemaVersion(major=0, minor=1, patch=0),
        declared_capability_ids=(_capability_id(),),
        configuration_requirement_refs=(_artifact_ref(),),
        status=ProviderStatus.AVAILABLE,
        implementation_metadata={"adapter_family": "synthetic"},
    )

    compatible = provider.to_json_compatible()
    decoded = json.loads(json.dumps(to_json_compatible(provider), sort_keys=True))

    assert provider.declared_capability_ids == (_capability_id(),)
    assert compatible["provider_id"] == str(provider.provider_id)
    assert compatible["version"] == "0.1.0"
    assert "credentials" not in compatible
    assert ProviderDescriptor.from_json_compatible(decoded) == provider
    with pytest.raises(ValueError, match="secret-shaped key"):
        ProviderDescriptor(
            provider_id=ProviderId.generate(),
            provider_type=ProviderType.TOOL,
            version=SchemaVersion(major=0, minor=1, patch=0),
            declared_capability_ids=(_capability_id(),),
            implementation_metadata={"api_key": "not_allowed"},
        )


def test_work_item_bounds_work_intent_and_runtime_state() -> None:
    dependency_id = WorkId("wrk_01K5V7EDNV6G7GVQ8F94N3EX06")
    output_ref = ObjectReference.from_id(VerificationId("ver_01K5V7EDNV6G7GVQ8F94N3EX07"))
    work = WorkItem(
        work_id=_work_id(),
        work_type="contract_test",
        title="Exercise contract shape",
        objective="Prove bounded work serialization.",
        dependencies=(dependency_id,),
        required_capabilities=(_capability_requirement(),),
        inputs=(_artifact_ref(),),
        expected_outputs=(output_ref,),
        policy_constraint_refs=(ObjectReference.from_id(ApplicationId.generate()),),
        authority_ref=ObjectReference.from_id(ApplicationId.generate()),
        principal_ref=ObjectReference.from_id(ApplicationId.generate()),
        evidence_requirement_refs=(ObjectReference.from_id(EvidenceId.generate()),),
        created_at=_timestamp(),
        updated_at=_timestamp(),
        state=WorkItemState.READY,
    )

    decoded = json.loads(json.dumps(to_json_compatible(work), sort_keys=True))

    assert work.dependencies == (dependency_id,)
    assert work.required_capabilities[0].capability_id == _capability_id()
    assert work.inputs[0].kind is ReferenceKind.ARTIFACT
    assert work.expected_outputs[0].kind is ReferenceKind.VERIFICATION
    assert work.state is WorkItemState.READY
    assert id(WorkItemState) != id(EngineeringLifecycle)
    assert WorkItem.from_json_compatible(decoded) == work


def test_execution_record_represents_one_attempt_not_work_item() -> None:
    execution_id = ExecutionId("exe_01K5V7EDNV6G7GVQ8F94N3EX08")
    agent_instance_id = AgentInstanceId("agi_01K5V7EDNV6G7GVQ8F94N3EX09")
    provider_ref = ObjectReference.from_id(ProviderId("prv_01K5V7EDNV6G7GVQ8F94N3EX0A"))
    error = ContractError(
        error_code=ErrorCode("ATTEMPT_WARNING"),
        message="Attempt completed with a warning.",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.WARNING,
        retryable=False,
    )
    record = ExecutionRecord(
        execution_id=execution_id,
        work_id=_work_id(),
        executor_ref=ObjectReference.from_id(agent_instance_id),
        agent_instance_id=agent_instance_id,
        provider_refs=(provider_ref,),
        started_at=_timestamp(),
        ended_at=UtcTimestamp("2026-09-22T10:01:00Z"),
        state=ExecutionState.SUCCEEDED,
        result=Result.success(value={"ok": True}),
        evidence_refs=(EvidenceId("evd_01K5V7EDNV6G7GVQ8F94N3EX0B"),),
        error_refs=(ObjectReference.from_id(ArtifactId("art_01K5V7EDNV6G7GVQ8F94N3EX0C")),),
        errors=(error,),
        observability_context=ObservabilityContext(
            work_id=_work_id(),
            execution_id=execution_id,
            agent_instance_id=agent_instance_id,
            trace_id=TraceId("trc_01K5V7EDNV6G7GVQ8F94N3EX0D"),
        ),
    )

    decoded = json.loads(json.dumps(to_json_compatible(record), sort_keys=True))

    assert record.execution_id == execution_id
    assert record.work_id == _work_id()
    assert record.provider_refs == (provider_ref,)
    assert record.evidence_refs[0] == EvidenceId("evd_01K5V7EDNV6G7GVQ8F94N3EX0B")
    assert record.errors == (error,)
    assert record.observability_context is not None
    assert record.observability_context.execution_id == execution_id
    assert ExecutionRecord.from_json_compatible(decoded) == record


def test_agent_definition_is_reusable_and_does_not_grant_runtime_authority() -> None:
    definition = AgentDefinition(
        agent_definition_id=AgentDefinitionId("agd_01K5V7EDNV6G7GVQ8F94N3EX0E"),
        name="contract_runner",
        version=SchemaVersion(major=1, minor=0, patch=0),
        purpose="Execute bounded contract validation work.",
        allowed_capability_ids=(_capability_id(),),
        constraints={"max_parallel_work": 1},
        input_contract_refs=(_artifact_ref(),),
        output_contract_refs=(
            ObjectReference.from_id(VerificationId("ver_01K5V7EDNV6G7GVQ8F94N3EX0F")),
        ),
    )

    field_names = {field.name for field in fields(AgentDefinition)}
    decoded = json.loads(json.dumps(to_json_compatible(definition), sort_keys=True))

    assert definition.allowed_capability_ids == (_capability_id(),)
    assert definition.version == SchemaVersion(major=1, minor=0, patch=0)
    assert "authority_ref" not in field_names
    assert "principal_ref" not in field_names
    assert AgentDefinition.from_json_compatible(decoded) == definition


def test_agent_instance_is_runtime_participant_with_observability() -> None:
    execution_id = ExecutionId("exe_01K5V7EDNV6G7GVQ8F94N3EX0G")
    instance = AgentInstance(
        agent_instance_id=AgentInstanceId("agi_01K5V7EDNV6G7GVQ8F94N3EX0H"),
        agent_definition_id=AgentDefinitionId("agd_01K5V7EDNV6G7GVQ8F94N3EX0J"),
        work_id=_work_id(),
        execution_id=execution_id,
        state=AgentInstanceState.ACTIVE,
        observability_context=ObservabilityContext(work_id=_work_id(), execution_id=execution_id),
        authority_ref=ObjectReference.from_id(ApplicationId.generate()),
        principal_ref=ObjectReference.from_id(ApplicationId.generate()),
        created_at=_timestamp(),
        started_at=_timestamp(),
    )

    decoded = json.loads(json.dumps(to_json_compatible(instance), sort_keys=True))

    assert instance.agent_definition_id == AgentDefinitionId("agd_01K5V7EDNV6G7GVQ8F94N3EX0J")
    assert instance.work_id == _work_id()
    assert instance.execution_id == execution_id
    assert instance.state is AgentInstanceState.ACTIVE
    assert instance.observability_context is not None
    assert AgentInstance.from_json_compatible(decoded) == instance


def test_runtime_states_are_not_engineering_lifecycle_aliases() -> None:
    assert id(WorkItemState) != id(EngineeringLifecycle)
    assert id(ExecutionState) != id(EngineeringLifecycle)
    assert id(AgentInstanceState) != id(EngineeringLifecycle)
    assert id(WorkItemState) != id(ExecutionState)
    assert id(WorkItemState) != id(AgentInstanceState)
    assert id(ExecutionState) != id(AgentInstanceState)
    assert ExecutionState.SUCCEEDED.value not in {state.value for state in WorkItemState}
    assert AgentInstanceState.ACTIVE.value not in {state.value for state in WorkItemState}
