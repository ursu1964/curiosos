from __future__ import annotations

import json
import re
from collections.abc import Iterable

from contract_fixtures import SCHEMA_V1, UTC_NOW, fixed_id, human_principal, ref_for
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    Capability,
    CapabilityCategory,
    CapabilityId,
    ConfigurationProfile,
    ConfigurationProfileName,
    CorrelationId,
    EffectClassification,
    EventEnvelope,
    EventId,
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    PolicyDecision,
    PolicyDecisionOutcome,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    Result,
    RuntimeEventType,
    SecretReference,
    TraceId,
    WorkId,
    WorkItem,
    WorkItemState,
    to_json_compatible,
)

_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_ID_RE = re.compile(r"^[a-z]{3}_[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}$")
_UTC_RE = re.compile(r"^2026-09-22T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def _walk(value: object) -> Iterable[object]:
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, list | tuple):
        for item in value:
            yield from _walk(item)


def _assert_json_compatible(value: object) -> object:
    encoded = json.dumps(value, allow_nan=False, sort_keys=True)
    return json.loads(encoded)


def test_repository_contract_serialization_is_json_compatible_and_snake_case() -> None:
    payloads = [to_json_compatible(contract) for contract in _representative_contracts()]

    decoded = _assert_json_compatible(payloads)

    assert decoded == payloads
    for node in _walk(decoded):
        if isinstance(node, dict):
            assert all(_SNAKE_CASE_RE.fullmatch(key) for key in node)


def test_serialized_enums_ids_timestamps_and_schema_versions_are_stable() -> None:
    payload = to_json_compatible(_representative_contracts())
    scalar_values = [node for node in _walk(payload) if isinstance(node, str)]

    assert "READY" in scalar_values
    assert "ACTIVE" in scalar_values
    assert "model" in scalar_values
    assert "available" in scalar_values
    assert "cognitive" in scalar_values
    assert "ALLOW" in scalar_values
    assert "LOCAL_DOCKER" in scalar_values
    assert "1.0.0" in scalar_values
    assert "2026-09-22T08:15:30Z" in scalar_values
    assert any(_ID_RE.fullmatch(value) for value in scalar_values)
    assert all(not value.endswith("+00:00") for value in scalar_values)
    assert all(_UTC_RE.fullmatch(value) for value in scalar_values if value.startswith("2026-"))


def test_optional_null_and_contextual_omission_semantics_are_preserved() -> None:
    work = WorkItem(
        work_id=fixed_id(WorkId),
        work_type="contract_check",
        title="Verify null fields",
        objective="Preserve optional semantics.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
    )
    work_json = work.to_json_compatible()

    assert work_json["authority_ref"] is None
    assert work_json["principal_ref"] is None
    assert work_json["required_capabilities"] == []
    assert ObservabilityContext().to_json() == {}
    assert ObservabilityContext.from_json({}).to_json() == {}


def test_supported_contracts_round_trip_from_canonical_json() -> None:
    for contract in _representative_contracts():
        serialized = _assert_json_compatible(to_json_compatible(contract))
        from_json = getattr(type(contract), "from_json_compatible", None)
        if from_json is None:
            from_json = type(contract).from_json
        assert from_json(serialized) == contract


def test_formal_generated_json_schema_is_not_claimed_by_the_current_contracts() -> None:
    for contract in _representative_contracts():
        assert not hasattr(contract, "model_json_schema")
        assert not hasattr(type(contract), "model_json_schema")
        assert not hasattr(contract, "json_schema")
        assert not hasattr(type(contract), "json_schema")


def _representative_contracts() -> tuple[object, ...]:
    capability = Capability(
        capability_id=fixed_id(CapabilityId),
        key="summarize",
        version=SCHEMA_V1,
        description="Summarize bounded work inputs.",
        category=CapabilityCategory.COGNITIVE,
    )
    provider = ProviderDescriptor(
        provider_id=fixed_id(ProviderId),
        provider_type=ProviderType.MODEL,
        version=SCHEMA_V1,
        declared_capability_ids=(fixed_id(CapabilityId),),
        status=ProviderStatus.AVAILABLE,
    )
    work = WorkItem(
        work_id=fixed_id(WorkId),
        work_type="contract_check",
        title="Verify frozen contracts",
        objective="Prove repository-level serialization coherence.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
        inputs=(ref_for(ArtifactId),),
    )
    artifact = ArtifactReference(
        artifact_id=fixed_id(ArtifactId),
        kind=ArtifactKind.LOG,
        locator="curios://artifact/contract-log",
        created_at=UTC_NOW,
        storage_provider_ref=ObjectReference.from_id(fixed_id(ProviderId)),
    )
    agent_definition = AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId),
        name="contract_checker",
        version=SCHEMA_V1,
        purpose="Check repository-level contract coherence.",
        allowed_capability_ids=(fixed_id(CapabilityId),),
    )
    agent = AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=fixed_id(WorkId),
        execution_id=fixed_id(ExecutionId),
        state=AgentInstanceState.ACTIVE,
        created_at=UTC_NOW,
    )
    policy_decision = PolicyDecision(
        subject_ref=ref_for(WorkId),
        principal=human_principal(),
        requested_effects=(EffectClassification.READ_ONLY,),
        resource_refs=(ref_for(ArtifactId),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.ALLOW,
        reason="Synthetic fixture only.",
        decided_at=UTC_NOW,
    )
    event = EventEnvelope(
        event_id=fixed_id(EventId),
        event_type=RuntimeEventType.WORK_CREATED.value,
        schema_version=SCHEMA_V1,
        occurred_at=UTC_NOW,
        producer=ref_for(AgentInstanceId),
        subject_ref=ref_for(WorkId),
        observability_context=ObservabilityContext(
            work_id=fixed_id(WorkId),
            trace_id=fixed_id(TraceId),
            correlation_id=fixed_id(CorrelationId),
        ),
        payload={"fixture": True},
    )
    configuration = ConfigurationProfile(
        profile=ConfigurationProfileName.LOCAL_DOCKER,
        description="Synthetic local profile fixture.",
    )
    secret = SecretReference(
        secret_provider_ref=ref_for(ProviderId),
        name="openai_api_key",
        key="current",
        scope="local docker project",
        purpose="provider credential lookup",
    )
    result = Result.success(value={"status": "ok"})

    return (
        capability,
        provider,
        work,
        artifact,
        agent_definition,
        agent,
        policy_decision,
        event,
        configuration,
        secret,
        result,
    )
