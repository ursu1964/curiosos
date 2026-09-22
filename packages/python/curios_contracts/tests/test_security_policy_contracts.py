from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from curios_contracts import (
    APPROVAL_OUTCOME_VALUES,
    CONFIGURATION_PROFILE_VALUES,
    EFFECT_CLASSIFICATION_VALUES,
    GOVERNED_EFFECT_VALUES,
    POLICY_DECISION_OUTCOME_VALUES,
    PRINCIPAL_TYPE_VALUES,
    RISK_CLASSIFICATION_VALUES,
    AgentInstanceId,
    Approval,
    ApprovalOutcome,
    ArtifactId,
    Authority,
    ConfigurationProfile,
    ConfigurationProfileName,
    CorrelationId,
    EffectClassification,
    EventId,
    EvidenceId,
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    Permission,
    PolicyDecision,
    PolicyDecisionOutcome,
    Principal,
    PrincipalType,
    ProjectId,
    ProviderId,
    ReferenceKind,
    SecretReference,
    TraceId,
    UtcTimestamp,
    to_json_compatible,
)

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "curios_contracts"
JsonObject = dict[str, object]
JsonList = list[object]


def _as_json_object(value: object) -> JsonObject:
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _as_json_list(value: object) -> JsonList:
    assert isinstance(value, list)
    return value


def _provider_ref() -> ObjectReference:
    return ObjectReference.from_id(ProviderId.generate())


def _project_ref() -> ObjectReference:
    return ObjectReference.from_id(ProjectId.generate())


def _agent_ref() -> ObjectReference:
    return ObjectReference.from_id(AgentInstanceId.generate())


def _execution_ref() -> ObjectReference:
    return ObjectReference.from_id(ExecutionId.generate())


def _principal() -> Principal:
    return Principal(
        principal_type=PrincipalType.HUMAN,
        identity="operator@example.test",
        principal_ref=_project_ref(),
    )


def _permission() -> Permission:
    return Permission(
        action="read",
        resource_type="artifact",
        resource_ref=ObjectReference.from_id(ArtifactId.generate()),
        scope="project sandbox",
        permitted_effects=(EffectClassification.READ_ONLY,),
    )


def test_configuration_profile_local_docker_valid_and_serializes() -> None:
    profile = ConfigurationProfile(
        profile=ConfigurationProfileName.LOCAL_DOCKER,
        description="Local Docker development profile identity.",
    )

    serialized = to_json_compatible(profile)

    assert serialized == {
        "profile": "LOCAL_DOCKER",
        "schema_version": "1.0.0",
        "description": "Local Docker development profile identity.",
    }
    assert json.loads(json.dumps(serialized)) == serialized
    assert ConfigurationProfile.from_json_compatible(serialized) == profile


@pytest.mark.parametrize(
    "profile_name",
    ["base", "full", "observability", "docker_compose_base", "LOCAL_DOCKER_OBSERVABILITY"],
)
def test_tooling_profiles_are_not_canonical_environment_profiles(profile_name: str) -> None:
    with pytest.raises(ValueError):
        ConfigurationProfileName(profile_name)


def test_secret_reference_is_provider_neutral_and_never_contains_secret_value() -> None:
    secret = SecretReference(
        secret_provider_ref=_provider_ref(),
        name="openai_api_key",
        key="current",
        scope="local docker project",
        purpose="model provider credential lookup",
    )

    serialized = secret.to_json_compatible()
    provider_ref = _as_json_object(serialized["secret_provider_ref"])

    assert provider_ref["kind"] == ReferenceKind.PROVIDER.value
    assert "secret_value" not in serialized
    assert "value" not in serialized
    assert "sk-test-value" not in json.dumps(serialized)
    assert SecretReference.from_json_compatible(serialized) == secret


def test_secret_reference_rejects_values_and_unsafe_extras() -> None:
    with pytest.raises(TypeError):
        SecretReference(
            secret_provider_ref=_provider_ref(),
            name="db_password",
            scope="local",
            purpose="database",
            secret_value="supersecret",  # type: ignore[call-arg]
        )

    with pytest.raises(ValueError, match="unexpected field"):
        SecretReference.from_json_compatible(
            {
                "secret_provider_ref": _provider_ref().to_json_compatible(),
                "name": "db_password",
                "scope": "local",
                "purpose": "database",
                "secret_value": "supersecret",
            }
        )

    with pytest.raises(ValueError, match="secret-shaped"):
        SecretReference(
            secret_provider_ref=_provider_ref(),
            name="password=supersecret",
            scope="local",
            purpose="database",
        )


@pytest.mark.parametrize("principal_type", tuple(PrincipalType))
def test_principal_types_have_identity_without_credentials(principal_type: PrincipalType) -> None:
    principal_ref = _agent_ref() if principal_type is PrincipalType.AGENT_INSTANCE else None
    if principal_type is PrincipalType.PROVIDER:
        principal_ref = _provider_ref()
    principal = Principal(
        principal_type=principal_type,
        identity=f"{principal_type.value.lower()} principal",
        principal_ref=principal_ref,
        related_agent_ref=_agent_ref(),
        execution_ref=_execution_ref(),
    )

    serialized = principal.to_json_compatible()

    assert serialized["principal_type"] == principal_type.value
    assert "credential" not in serialized
    assert "password" not in serialized
    assert Principal.from_json_compatible(serialized) == principal


def test_principal_rejects_credential_fields() -> None:
    with pytest.raises(TypeError):
        Principal(
            principal_type=PrincipalType.HUMAN,
            identity="human",
            credentials={"token": "secret"},  # type: ignore[call-arg]
        )

    with pytest.raises(ValueError, match="unexpected field"):
        Principal.from_json_compatible(
            {
                "principal_type": "HUMAN",
                "identity": "human",
                "credential": "secret",
            }
        )


def test_permission_and_authority_are_separate_bounded_contracts() -> None:
    permission = _permission()
    authority = Authority(
        authority_id="authz-local-read",
        principal=_principal(),
        permissions=(permission,),
        scope="project sandbox",
        granted_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
        expires_at=UtcTimestamp.parse("2026-09-22T11:00:00Z"),
        approval_id="approval-local-read",
    )

    permission_json = permission.to_json_compatible()
    authority_json = authority.to_json_compatible()
    authority_principal = _as_json_object(authority_json["principal"])
    authority_permissions = _as_json_list(authority_json["permissions"])

    assert "principal" not in permission_json
    assert authority_principal["principal_type"] == "HUMAN"
    assert authority_permissions[0] == permission_json
    assert Authority.from_json_compatible(authority_json) == authority
    assert Permission.from_json_compatible(permission_json) == permission


def test_authority_expiration_must_bound_grant() -> None:
    with pytest.raises(ValueError, match="expires_at must be after granted_at"):
        Authority(
            authority_id="authz-expired",
            principal=_principal(),
            permissions=(_permission(),),
            scope="project sandbox",
            granted_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
            expires_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
        )


def test_effect_risk_and_policy_vocabularies_are_exact_and_separate() -> None:
    assert EFFECT_CLASSIFICATION_VALUES == (
        "READ_ONLY",
        "LOCAL_WRITE",
        "EXTERNAL_READ",
        "EXTERNAL_WRITE",
        "DESTRUCTIVE",
        "SECRET_ACCESS",
        "NETWORK_ACCESS",
        "EXECUTION",
    )
    assert "APPROVAL_REQUIRED" not in EFFECT_CLASSIFICATION_VALUES
    assert RISK_CLASSIFICATION_VALUES == ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert POLICY_DECISION_OUTCOME_VALUES == ("ALLOW", "DENY", "REQUIRES_APPROVAL", "UNKNOWN")
    assert APPROVAL_OUTCOME_VALUES == ("PENDING", "APPROVED", "REJECTED")
    assert CONFIGURATION_PROFILE_VALUES == ("LOCAL_DOCKER",)
    assert PRINCIPAL_TYPE_VALUES == (
        "HUMAN",
        "SERVICE",
        "AGENT_INSTANCE",
        "TOOL_EXECUTOR",
        "PROVIDER",
        "SYSTEM",
    )
    assert GOVERNED_EFFECT_VALUES == EFFECT_CLASSIFICATION_VALUES
    assert set(EFFECT_CLASSIFICATION_VALUES).isdisjoint(RISK_CLASSIFICATION_VALUES)


@pytest.mark.parametrize("outcome", tuple(PolicyDecisionOutcome))
def test_policy_decision_outcomes_requested_effects_and_traceability(
    outcome: PolicyDecisionOutcome,
) -> None:
    decision = PolicyDecision(
        decision_id=f"decision-{outcome.value.lower()}",
        subject_ref=ObjectReference.from_id(EventId.generate()),
        principal=_principal(),
        requested_effects=(EffectClassification.SECRET_ACCESS, EffectClassification.EXECUTION),
        resource_refs=(_provider_ref(),),
        scope="project sandbox",
        outcome=outcome,
        reason="policy record fixture",
        policy_refs=(ObjectReference.from_id(EventId.generate()),),
        approval_id=(
            "approval-required" if outcome is PolicyDecisionOutcome.REQUIRES_APPROVAL else None
        ),
        decided_at=UtcTimestamp.parse("2026-09-22T10:30:00Z"),
        observability_context=ObservabilityContext(
            trace_id=TraceId.generate(),
            correlation_id=CorrelationId.generate(),
            principal_ref=_agent_ref(),
        ),
    )

    serialized = decision.to_json_compatible()
    subject_ref = _as_json_object(serialized["subject_ref"])
    principal = _as_json_object(serialized["principal"])
    resource_refs = _as_json_list(serialized["resource_refs"])
    resource_ref = _as_json_object(resource_refs[0])
    observability_context = _as_json_object(serialized["observability_context"])

    assert serialized["outcome"] == outcome.value
    assert serialized["requested_effects"] == ["SECRET_ACCESS", "EXECUTION"]
    assert subject_ref["kind"] == ReferenceKind.EVENT.value
    assert principal["principal_type"] == "HUMAN"
    assert resource_ref["kind"] == ReferenceKind.PROVIDER.value
    assert observability_context["trace_id"]
    assert PolicyDecision.from_json_compatible(serialized) == decision


def test_policy_unknown_governed_effect_is_preserved_and_not_implicit_allow() -> None:
    decision = PolicyDecision(
        subject_ref=ObjectReference.from_id(EventId.generate()),
        principal=_principal(),
        requested_effects=(EffectClassification.SECRET_ACCESS,),
        resource_refs=(_provider_ref(),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.UNKNOWN,
        reason="policy unavailable",
        decided_at=UtcTimestamp.parse("2026-09-22T10:30:00Z"),
    )

    serialized = decision.to_json_compatible()

    assert serialized["outcome"] == "UNKNOWN"
    assert PolicyDecision.from_json_compatible(serialized).outcome is PolicyDecisionOutcome.UNKNOWN
    assert not decision.is_authorizing
    assert decision.outcome is not PolicyDecisionOutcome.DENY


def test_approval_is_scoped_expiring_and_links_evidence() -> None:
    requester = _principal()
    approver = Principal(principal_type=PrincipalType.SYSTEM, identity="control plane")
    evidence_id = EvidenceId.generate()
    approval = Approval(
        approval_id="approval-secret-read",
        requested_by=requester,
        approved_by=approver,
        subject_ref=ObjectReference.from_id(EventId.generate()),
        action="read_secret",
        requested_effects=(EffectClassification.SECRET_ACCESS,),
        scope="project sandbox",
        reason="break-glass credential lookup",
        outcome=ApprovalOutcome.APPROVED,
        requested_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
        decided_at=UtcTimestamp.parse("2026-09-22T10:05:00Z"),
        expires_at=UtcTimestamp.parse("2026-09-22T10:15:00Z"),
        conditions={"ticket": "sec_review_123"},
        evidence_refs=(evidence_id,),
    )

    serialized = approval.to_json_compatible()
    requested_by = _as_json_object(serialized["requested_by"])
    approved_by = _as_json_object(serialized["approved_by"])

    assert requested_by["principal_type"] == "HUMAN"
    assert approved_by["principal_type"] == "SYSTEM"
    assert serialized["scope"] == "project sandbox"
    assert serialized["requested_effects"] == ["SECRET_ACCESS"]
    assert serialized["expires_at"] == "2026-09-22T10:15:00Z"
    assert serialized["evidence_refs"] == [str(evidence_id)]
    assert Approval.from_json_compatible(serialized) == approval


def test_approval_actor_state_is_consistent() -> None:
    with pytest.raises(ValueError, match="approved approvals must include approved_by"):
        Approval(
            approval_id="approval-invalid",
            requested_by=_principal(),
            subject_ref=ObjectReference.from_id(EventId.generate()),
            action="read_secret",
            requested_effects=(EffectClassification.SECRET_ACCESS,),
            scope="project sandbox",
            reason="missing actor",
            outcome=ApprovalOutcome.APPROVED,
            requested_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
            decided_at=UtcTimestamp.parse("2026-09-22T10:05:00Z"),
            expires_at=UtcTimestamp.parse("2026-09-22T10:15:00Z"),
        )


def test_security_serialization_rejects_credential_bearing_urls() -> None:
    with pytest.raises(ValueError, match="credential-bearing URLs"):
        Permission(
            action="read",
            resource_type="artifact",
            scope="https://user:password@example.test/resource",
            permitted_effects=(EffectClassification.EXTERNAL_READ,),
        )


def test_no_task_011_models_or_duplicate_generic_references_are_implemented() -> None:
    security_source = (SOURCE_ROOT / "security.py").read_text(encoding="utf-8")
    package_source = "\n".join(
        path.read_text(encoding="utf-8") for path in SOURCE_ROOT.glob("*.py")
    )

    forbidden_contracts = (
        "class WorkItem:",
        "class WorkItem(",
        "class ExecutionRecord:",
        "class ExecutionRecord(",
        "class CapabilityRequirement:",
        "class CapabilityRequirement(",
        "class ProviderDescriptor:",
        "class ProviderDescriptor(",
        "class AgentDefinition:",
        "class AgentDefinition(",
        "class AgentInstance:",
        "class AgentInstance(",
    )
    for contract in forbidden_contracts:
        assert contract not in security_source

    assert package_source.count("class ObjectReference") == 1
    assert "class Reference:" not in package_source
