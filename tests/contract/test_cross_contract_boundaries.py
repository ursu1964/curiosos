from __future__ import annotations

from dataclasses import fields
from typing import get_args, get_type_hints

import pytest
from contract_fixtures import (
    SCHEMA_V1,
    UTC_LATER,
    UTC_NOW,
    contract_error,
    contract_ids,
    fixed_id,
    human_principal,
    ref_for,
)
from curios_contracts import (
    AGENT_INSTANCE_STATE_VALUES,
    EFFECT_CLASSIFICATION_VALUES,
    ENGINEERING_LIFECYCLE_VALUES,
    EXECUTION_STATE_VALUES,
    POLICY_DECISION_OUTCOME_VALUES,
    RESULT_STATUS_VALUES,
    RISK_CLASSIFICATION_VALUES,
    WORK_ITEM_STATE_VALUES,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    Assumption,
    AssumptionId,
    Authority,
    Capability,
    CapabilityCategory,
    CapabilityId,
    CapabilityRequirement,
    CorrelationId,
    Decision,
    DecisionId,
    EffectClassification,
    EventEnvelope,
    EventId,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    Intent,
    IntentId,
    ObjectReference,
    ObservabilityContext,
    Plan,
    PlanId,
    PolicyDecision,
    PolicyDecisionOutcome,
    Principal,
    ProblemId,
    ProjectId,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    ReferenceKind,
    Result,
    RuntimeEventType,
    SecretReference,
    TraceId,
    VerificationId,
    VerificationOutcome,
    VerificationReference,
    WorkId,
    WorkItem,
    WorkItemState,
    to_json_compatible,
)


def _annotation_contains(annotation: object, target: type[object]) -> bool:
    if annotation is target:
        return True
    return any(_annotation_contains(arg, target) for arg in get_args(annotation))


def _field_type(model: type[object], field_name: str) -> object:
    hints = get_type_hints(model)
    return hints[field_name]


def _json_keys(value: object) -> set[str]:
    assert isinstance(value, dict)
    return set(value)


def test_primitive_compatibility_across_runtime_contracts() -> None:
    ids = contract_ids()
    serialized = to_json_compatible(
        {
            "work_id": ids.work_id,
            "execution_id": ids.execution_id,
            "trace_id": ids.trace_id,
            "correlation_id": ids.correlation_id,
            "schema_version": SCHEMA_V1,
            "occurred_at": UTC_NOW,
        }
    )

    assert serialized == {
        "work_id": "wrk_00000000000000000000000000",
        "execution_id": "exe_00000000000000000000000000",
        "trace_id": "trc_00000000000000000000000000",
        "correlation_id": "cor_00000000000000000000000000",
        "schema_version": "1.0.0",
        "occurred_at": "2026-09-22T08:15:30Z",
    }
    assert TraceId(str(ids.correlation_id).replace("cor_", "trc_", 1)) != ids.correlation_id
    with pytest.raises(ValueError):
        TraceId(str(ids.correlation_id))
    assert set(ENGINEERING_LIFECYCLE_VALUES).isdisjoint(WORK_ITEM_STATE_VALUES)
    assert "IMPLEMENTED" not in EXECUTION_STATE_VALUES
    assert "ACTIVE" in AGENT_INSTANCE_STATE_VALUES
    assert "ACTIVE" not in ENGINEERING_LIFECYCLE_VALUES


def test_object_reference_is_the_generic_cross_contract_reference() -> None:
    ids = contract_ids()
    work_ref = ObjectReference.from_id(ids.work_id)

    assert work_ref.to_json_compatible() == {
        "kind": "work",
        "ref_id": "wrk_00000000000000000000000000",
    }
    assert ObjectReference.from_json_compatible(work_ref.to_json_compatible()) == work_ref
    assert _field_type(EventEnvelope, "producer") is ObjectReference
    assert _field_type(EventEnvelope, "subject_ref") is ObjectReference
    assert _field_type(ObservabilityContext, "causation_ref") == ObjectReference | None

    with pytest.raises(TypeError, match="work references require WorkId"):
        ObjectReference(kind=ReferenceKind.WORK, ref_id=ids.project_id)


def test_cognitive_records_reference_existing_contracts_without_redefining_work() -> None:
    intent = Intent(
        intent_id=fixed_id(IntentId),
        objective="Summarize recorded project status.",
        source_ref=ref_for(ProjectId),
        submitted_at=UTC_NOW,
    )
    assumption = Assumption(
        assumption_id=fixed_id(AssumptionId),
        subject_ref=ref_for(IntentId),
        statement="Recorded evidence is authoritative.",
        created_at=UTC_NOW,
    )
    decision = Decision(
        decision_id=fixed_id(DecisionId),
        subject_ref=ref_for(IntentId),
        question="Which plan shape is bounded?",
        selected_option="recorded_truth_summary",
        rationale="The request only requires recorded truth observation.",
        decided_at=UTC_NOW,
    )
    plan = Plan(
        plan_id=fixed_id(PlanId),
        problem_ref=ref_for(ProblemId),
        objective="Create work references for the recorded truth summary.",
        assumption_refs=(ref_for(AssumptionId),),
        decision_refs=(ref_for(DecisionId),),
        work_refs=(ref_for(WorkId),),
        created_at=UTC_NOW,
    )

    assert ObjectReference.from_id(intent.intent_id).kind is ReferenceKind.INTENT
    assert assumption.subject_ref.kind is ReferenceKind.INTENT
    assert decision.subject_ref.kind is ReferenceKind.INTENT
    assert plan.work_refs == (ref_for(WorkId),)
    assert _field_type(Plan, "work_refs") == tuple[ObjectReference, ...]
    assert "work_id" not in _json_keys(plan.to_json_compatible())
    assert "state" not in _json_keys(plan.to_json_compatible())
    assert "dependencies" not in _json_keys(plan.to_json_compatible())
    assert "required_capabilities" not in _json_keys(plan.to_json_compatible())


def test_work_items_keep_security_and_policy_links_as_references() -> None:
    policy_ref = ref_for(ArtifactId, 1)
    work = WorkItem(
        work_id=fixed_id(WorkId),
        work_type="contract_check",
        title="Verify frozen contracts",
        objective="Prove repository-level contract coherence.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
        required_capabilities=(
            CapabilityRequirement(
                capability_id=fixed_id(CapabilityId),
                policy_constraint_refs=(policy_ref,),
            ),
        ),
        policy_constraint_refs=(policy_ref,),
        authority_ref=ref_for(ArtifactId, 2),
        principal_ref=ref_for(AgentInstanceId),
        evidence_requirement_refs=(ref_for(EvidenceId),),
    )

    serialized = work.to_json_compatible()

    assert _field_type(WorkItem, "authority_ref") == ObjectReference | None
    assert _field_type(WorkItem, "principal_ref") == ObjectReference | None
    assert _annotation_contains(_field_type(WorkItem, "policy_constraint_refs"), ObjectReference)
    assert not _annotation_contains(_field_type(WorkItem, "authority_ref"), Authority)
    assert not _annotation_contains(_field_type(WorkItem, "principal_ref"), Principal)
    assert not _annotation_contains(_field_type(WorkItem, "policy_constraint_refs"), PolicyDecision)
    assert serialized["authority_ref"] == ref_for(ArtifactId, 2).to_json_compatible()
    assert serialized["principal_ref"] == ref_for(AgentInstanceId).to_json_compatible()
    assert "authority" not in serialized
    assert "principal" not in serialized
    assert "policy_decision" not in serialized


def test_execution_and_agent_security_links_remain_bounded() -> None:
    record = ExecutionRecord(
        execution_id=fixed_id(ExecutionId),
        work_id=fixed_id(WorkId),
        executor_ref=ref_for(AgentInstanceId),
        agent_instance_id=fixed_id(AgentInstanceId),
        provider_refs=(ref_for(ProviderId),),
        started_at=UTC_NOW,
        ended_at=UTC_LATER,
        state=ExecutionState.SUCCEEDED,
        result=Result.success(value={"ok": True}, evidence_refs=(fixed_id(EvidenceId),)),
        evidence_refs=(fixed_id(EvidenceId),),
        error_refs=(ref_for(ArtifactId),),
        observability_context=ObservabilityContext(
            execution_id=fixed_id(ExecutionId),
            trace_id=fixed_id(TraceId),
        ),
    )
    agent = AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=fixed_id(WorkId),
        execution_id=fixed_id(ExecutionId),
        state=AgentInstanceState.ACTIVE,
        created_at=UTC_NOW,
        authority_ref=ref_for(ArtifactId, 3),
        principal_ref=ref_for(AgentInstanceId),
    )

    assert _field_type(ExecutionRecord, "executor_ref") is ObjectReference
    assert _annotation_contains(_field_type(ExecutionRecord, "provider_refs"), ObjectReference)
    assert _field_type(AgentInstance, "authority_ref") == ObjectReference | None
    assert _field_type(AgentInstance, "principal_ref") == ObjectReference | None
    assert "secret" not in _json_keys(agent.to_json_compatible())
    assert "authority" not in _json_keys(agent.to_json_compatible())
    assert "principal" not in _json_keys(agent.to_json_compatible())
    assert ExecutionRecord.from_json_compatible(record.to_json_compatible()) == record

    with pytest.raises(ValueError, match="provider_refs must reference provider objects"):
        ExecutionRecord(
            execution_id=fixed_id(ExecutionId, 1),
            work_id=fixed_id(WorkId),
            executor_ref=ref_for(AgentInstanceId),
            provider_refs=(ref_for(ArtifactId),),
            started_at=UTC_NOW,
            state=ExecutionState.CREATED,
        )


def test_capability_and_provider_boundaries_do_not_encode_authority() -> None:
    capability = Capability(
        capability_id=fixed_id(CapabilityId),
        key="summarize",
        version=SCHEMA_V1,
        description="Summarize bounded work inputs.",
        category=CapabilityCategory.COGNITIVE,
    )
    requirement = CapabilityRequirement(
        capability_id=fixed_id(CapabilityId),
        policy_constraint_refs=(ref_for(ArtifactId, 1),),
    )
    provider = ProviderDescriptor(
        provider_id=fixed_id(ProviderId),
        provider_type=ProviderType.MODEL,
        version=SCHEMA_V1,
        declared_capability_ids=(fixed_id(CapabilityId),),
        configuration_requirement_refs=(ref_for(ArtifactId, 2),),
        status=ProviderStatus.AVAILABLE,
        implementation_metadata={"runtime": "synthetic"},
    )

    assert "provider_id" not in _json_keys(capability.to_json_compatible())
    assert "provider_ref" not in _json_keys(requirement.to_json_compatible())
    assert "implementation" not in _json_keys(requirement.to_json_compatible())
    assert provider.to_json_compatible()["declared_capability_ids"] == [
        "cap_00000000000000000000000000"
    ]
    assert "authority" not in _json_keys(provider.to_json_compatible())
    assert "principal" not in _json_keys(provider.to_json_compatible())


def test_event_and_observability_boundaries_are_reference_based_and_transport_neutral() -> None:
    context = ObservabilityContext(
        work_id=fixed_id(WorkId),
        trace_id=fixed_id(TraceId),
        correlation_id=fixed_id(CorrelationId),
        causation_ref=ref_for(EventId),
    )
    event = EventEnvelope(
        event_id=fixed_id(EventId),
        event_type=RuntimeEventType.EXECUTION_STARTED.value,
        schema_version=SCHEMA_V1,
        occurred_at=UTC_NOW,
        producer=ref_for(ProviderId),
        subject_ref=ref_for(WorkId),
        observability_context=context,
        payload={"attempt": 1},
    )
    serialized = event.to_json()

    assert serialized["producer"] == ref_for(ProviderId).to_json_compatible()
    assert serialized["subject_ref"] == ref_for(WorkId).to_json_compatible()
    assert serialized["observability_context"] == context.to_json()
    assert context.trace_id != context.correlation_id
    assert context.to_json()["causation_ref"] == ref_for(EventId).to_json_compatible()
    assert set(serialized).isdisjoint({"broker", "topic", "queue", "headers", "exchange"})
    assert ObservabilityContext().to_json() == {}
    assert ObservabilityContext.from_json({}) == ObservabilityContext()
    assert EventEnvelope.from_json(serialized) == event


def test_security_vocabularies_are_exact_and_separate() -> None:
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
    assert RISK_CLASSIFICATION_VALUES == ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert POLICY_DECISION_OUTCOME_VALUES == ("ALLOW", "DENY", "REQUIRES_APPROVAL", "UNKNOWN")
    assert RESULT_STATUS_VALUES == ("success", "failure")
    assert "APPROVAL_REQUIRED" not in EFFECT_CLASSIFICATION_VALUES
    assert "REQUIRES_APPROVAL" not in EFFECT_CLASSIFICATION_VALUES
    assert PolicyDecisionOutcome.UNKNOWN is not PolicyDecisionOutcome.DENY

    unknown = PolicyDecision(
        subject_ref=ref_for(WorkId),
        principal=human_principal(),
        requested_effects=(EffectClassification.EXTERNAL_WRITE,),
        resource_refs=(ref_for(ArtifactId),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.UNKNOWN,
        reason="No matching policy was available.",
        decided_at=UTC_NOW,
    )
    deny = PolicyDecision(
        subject_ref=ref_for(WorkId),
        principal=human_principal(),
        requested_effects=(EffectClassification.EXTERNAL_WRITE,),
        resource_refs=(ref_for(ArtifactId),),
        scope="project sandbox",
        outcome=PolicyDecisionOutcome.DENY,
        reason="Policy denied the request.",
        decided_at=UTC_NOW,
    )

    assert unknown.to_json_compatible()["outcome"] == "UNKNOWN"
    assert deny.to_json_compatible()["outcome"] == "DENY"
    assert not unknown.is_authorizing
    assert not deny.is_authorizing


def test_secret_reference_contains_metadata_and_references_never_secret_values() -> None:
    secret = SecretReference(
        secret_provider_ref=ref_for(ProviderId),
        name="openai_api_key",
        key="current",
        scope="local docker project",
        purpose="model provider credential lookup",
    )
    serialized = secret.to_json_compatible()

    assert serialized["secret_provider_ref"] == ref_for(ProviderId).to_json_compatible()
    assert "secret_value" not in serialized
    assert "value" not in serialized
    assert "credential" not in serialized
    assert SecretReference.from_json_compatible(serialized) == secret

    with pytest.raises(ValueError, match="unexpected field"):
        SecretReference.from_json_compatible(
            {
                **serialized,
                "secret_value": "sk-test-not-real",
            }
        )


def test_result_evidence_verification_and_artifact_boundaries_are_reference_only() -> None:
    evidence = EvidenceReference(
        evidence_id=fixed_id(EvidenceId),
        kind=EvidenceKind.TEST_RESULT,
        subject_ref=ref_for(WorkId),
        collected_at=UTC_NOW,
        artifact_refs=(fixed_id(ArtifactId),),
        trace_id=fixed_id(TraceId),
    )
    verification = VerificationReference(
        verification_id=fixed_id(VerificationId),
        subject_ref=ref_for(WorkId),
        outcome=VerificationOutcome.PASSED,
        evidence_refs=(evidence,),
        verifier_ref=ref_for(AgentInstanceId),
        verified_at=UTC_LATER,
    )
    artifact = ArtifactReference(
        artifact_id=fixed_id(ArtifactId),
        kind=ArtifactKind.LOG,
        locator="curios://artifact/contract-log",
        created_at=UTC_NOW,
        storage_provider_ref=ref_for(ProviderId),
        producer_ref=ref_for(ExecutionId),
    )

    success = Result.success(value={"artifact": artifact.to_json_compatible()})

    assert success.status.value == "success"
    assert Result.failure((contract_error(),)).to_json_compatible()["errors"]
    with pytest.raises(ValueError, match="successful results must not contain errors"):
        Result(status="success", errors=(contract_error(),))
    with pytest.raises(ValueError, match="failure results must contain at least one error"):
        Result(status="failure")

    assert _field_type(EvidenceReference, "subject_ref") is ObjectReference
    assert _field_type(VerificationReference, "subject_ref") is ObjectReference
    assert _field_type(VerificationReference, "verifier_ref") == ObjectReference | None
    assert "engine" not in _json_keys(evidence.to_json_compatible())
    assert "engine" not in _json_keys(verification.to_json_compatible())
    assert "provider" not in artifact.to_json_compatible()["locator"]
    assert (
        artifact.to_json_compatible()["storage_provider_ref"]
        == ref_for(ProviderId).to_json_compatible()
    )


def test_reference_fields_do_not_introduce_parallel_generic_reference_types() -> None:
    generic_reference_fields: dict[str, list[str]] = {}
    for model in (
        WorkItem,
        ExecutionRecord,
        AgentInstance,
        CapabilityRequirement,
        ProviderDescriptor,
        EventEnvelope,
        ObservabilityContext,
        PolicyDecision,
    ):
        hints = get_type_hints(model)
        generic_reference_fields[model.__name__] = [
            field.name
            for field in fields(model)
            if _annotation_contains(hints[field.name], ObjectReference)
        ]

    assert generic_reference_fields == {
        "WorkItem": [
            "inputs",
            "expected_outputs",
            "policy_constraint_refs",
            "authority_ref",
            "principal_ref",
            "evidence_requirement_refs",
        ],
        "ExecutionRecord": ["executor_ref", "provider_refs", "error_refs"],
        "AgentInstance": ["authority_ref", "principal_ref"],
        "CapabilityRequirement": ["policy_constraint_refs"],
        "ProviderDescriptor": ["configuration_requirement_refs"],
        "EventEnvelope": ["producer", "subject_ref"],
        "ObservabilityContext": ["principal_ref", "causation_ref"],
        "PolicyDecision": ["subject_ref", "resource_refs", "policy_refs"],
    }

    for model_name, field_names in generic_reference_fields.items():
        assert field_names, model_name
