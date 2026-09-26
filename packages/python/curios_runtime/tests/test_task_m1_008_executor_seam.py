from __future__ import annotations

import json
from typing import cast

from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_capability import (
    CapabilityResolution,
    CapabilityResolutionReason,
    CapabilityResolutionStatus,
)
from curios_contracts import (
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    CapabilityId,
    CapabilityQuality,
    CapabilityRequirement,
    EventId,
    EvidenceId,
    ObjectReference,
    ObservabilityContext,
    ProjectId,
    ReferenceKind,
    TraceId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_dag import WorkDagNodeReadiness
from curios_runtime import (
    M1_EXECUTOR_EVENT_TYPE,
    DeterministicM1Executor,
    ExecutorErrorCode,
    ExecutorOutcomeStatus,
    ExecutorRequest,
)

_DEFAULT_AGENT_INSTANCE = object()


def test_deterministic_executor_completes_supported_ready_work_with_event_and_evidence() -> None:
    request = _request()

    outcome = DeterministicM1Executor().execute(request)

    assert outcome.status is ExecutorOutcomeStatus.COMPLETED
    assert outcome.result.value == {
        "output_kind": "current_state_inspection",
        "work_id": str(fixed_id(WorkId)),
        "input_refs": [],
        "input_count": 0,
    }
    assert outcome.evidence_refs == tuple(outcome.result.evidence_refs)
    assert outcome.evidence_refs[0].evidence_id == fixed_id(EvidenceId)
    assert outcome.evidence_refs[0].subject_ref == ref_for(WorkId)
    assert outcome.evidence_refs[0].trace_id == fixed_id(TraceId)
    assert outcome.event.event_id == fixed_id(EventId)
    assert outcome.event.event_type == M1_EXECUTOR_EVENT_TYPE
    assert outcome.event.producer == ref_for(AgentInstanceId)
    assert outcome.event.subject_ref == ref_for(WorkId)
    assert outcome.event.payload == {
        "status": ExecutorOutcomeStatus.COMPLETED.value,
        "work_id": str(fixed_id(WorkId)),
        "work_type": "inspect_current_state",
        "evidence_ids": (str(fixed_id(EvidenceId)),),
    }
    assert outcome.event.metadata == {
        "task_id": "TASK-M1-008",
        "executor": "deterministic_m1",
        "outcome_status": ExecutorOutcomeStatus.COMPLETED.value,
    }
    assert _round_trip(outcome.to_json_compatible()) == outcome.to_json_compatible()


def test_repeated_identical_input_produces_identical_output() -> None:
    request = _request()
    executor = DeterministicM1Executor()

    assert executor.execute(request) == executor.execute(request)
    assert (
        executor.execute(request).to_json_compatible()
        == executor.execute(request).to_json_compatible()
    )


def test_all_supported_work_types_have_stable_deterministic_payloads() -> None:
    payloads = tuple(
        DeterministicM1Executor().execute(_request(work=_work(work_type=work_type))).result.value
        for work_type in (
            "collect_recorded_context",
            "compose_recorded_summary",
            "verify_recorded_summary",
            "inspect_current_state",
            "apply_bounded_change",
            "verify_bounded_change",
        )
    )

    assert [payload["output_kind"] for payload in payloads] == [
        "recorded_context",
        "recorded_summary",
        "recorded_summary_verification",
        "current_state_inspection",
        "bounded_change_record",
        "bounded_change_verification",
    ]
    assert payloads[4]["side_effects"] == "none"


def test_unsupported_work_type_fails_boundedly_without_evidence_or_native_leakage() -> None:
    outcome = DeterministicM1Executor().execute(
        _request(work=_work(work_type="provider_inventory"))
    )

    assert outcome.status is ExecutorOutcomeStatus.FAILED
    assert outcome.evidence_refs == ()
    assert outcome.result.value is None
    assert outcome.result.errors[0].error_code == ExecutorErrorCode.UNSUPPORTED_WORK_TYPE
    assert outcome.result.errors[0].details == {"work_type": "provider_inventory"}
    assert "provider_inventory" not in outcome.result.errors[0].message


def test_non_ready_dag_state_blocks_without_scheduling_or_mutation() -> None:
    work = _work()

    outcome = DeterministicM1Executor().execute(
        _request(work=work, dag_readiness=WorkDagNodeReadiness.WAITING)
    )

    assert outcome.status is ExecutorOutcomeStatus.BLOCKED
    assert outcome.result.errors[0].error_code == ExecutorErrorCode.WORK_NOT_READY
    assert outcome.result.errors[0].details == {"dag_readiness": "WAITING"}
    assert work.state is WorkItemState.READY


def test_missing_and_ambiguous_capabilities_fail_boundedly() -> None:
    missing = CapabilityResolution(
        requirement=_requirement(),
        status=CapabilityResolutionStatus.MISSING,
        reason=CapabilityResolutionReason.CAPABILITY_NOT_OFFERED,
    )
    ambiguous = CapabilityResolution(
        requirement=_requirement(),
        status=CapabilityResolutionStatus.AMBIGUOUS,
        reason=CapabilityResolutionReason.MULTIPLE_ELIGIBLE_AGENTS,
        capability_ref=ref_for(CapabilityId),
        ambiguous_agent_definition_refs=(ref_for(AgentDefinitionId), ref_for(AgentDefinitionId, 1)),
    )

    missing_outcome = DeterministicM1Executor().execute(_request(resolutions=(missing,)))
    ambiguous_outcome = DeterministicM1Executor().execute(_request(resolutions=(ambiguous,)))

    assert missing_outcome.status is ExecutorOutcomeStatus.BLOCKED
    assert missing_outcome.result.errors[0].error_code == ExecutorErrorCode.CAPABILITY_MISSING
    assert ambiguous_outcome.status is ExecutorOutcomeStatus.BLOCKED
    assert ambiguous_outcome.result.errors[0].error_code == ExecutorErrorCode.CAPABILITY_AMBIGUOUS


def test_capability_shape_must_match_work_requirements_exactly() -> None:
    wrong = CapabilityResolution(
        requirement=CapabilityRequirement(
            capability_id=fixed_id(CapabilityId, 1),
            quality=CapabilityQuality.STANDARD,
        ),
        status=CapabilityResolutionStatus.MATCHED,
        reason=CapabilityResolutionReason.EXACT_MATCH,
        capability_ref=ObjectReference.from_id(fixed_id(CapabilityId, 1)),
        agent_definition_ref=ref_for(AgentDefinitionId),
    )

    count_outcome = DeterministicM1Executor().execute(_request(resolutions=()))
    mismatch_outcome = DeterministicM1Executor().execute(_request(resolutions=(wrong,)))

    assert count_outcome.status is ExecutorOutcomeStatus.FAILED
    assert count_outcome.result.errors[0].error_code == ExecutorErrorCode.CAPABILITY_SHAPE_INVALID
    assert mismatch_outcome.status is ExecutorOutcomeStatus.FAILED
    assert (
        mismatch_outcome.result.errors[0].error_code == ExecutorErrorCode.CAPABILITY_SHAPE_INVALID
    )


def test_agent_instance_is_required_active_and_bound_to_work_and_resolution() -> None:
    missing = DeterministicM1Executor().execute(_request(agent_instance=None))
    wrong_work = DeterministicM1Executor().execute(
        _request(agent_instance=_agent_instance(work_id=fixed_id(WorkId, 1)))
    )
    not_active = DeterministicM1Executor().execute(
        _request(agent_instance=_agent_instance(state=AgentInstanceState.READY))
    )
    wrong_definition = DeterministicM1Executor().execute(
        _request(agent_instance=_agent_instance(agent_definition_id=fixed_id(AgentDefinitionId, 1)))
    )

    assert missing.status is ExecutorOutcomeStatus.BLOCKED
    assert missing.result.errors[0].error_code == ExecutorErrorCode.MISSING_AGENT_INSTANCE
    assert wrong_work.status is ExecutorOutcomeStatus.BLOCKED
    assert wrong_work.result.errors[0].error_code == ExecutorErrorCode.AGENT_WORK_MISMATCH
    assert not_active.status is ExecutorOutcomeStatus.BLOCKED
    assert not_active.result.errors[0].error_code == ExecutorErrorCode.AGENT_NOT_ACTIVE
    assert wrong_definition.status is ExecutorOutcomeStatus.BLOCKED
    assert (
        wrong_definition.result.errors[0].error_code == ExecutorErrorCode.AGENT_DEFINITION_MISMATCH
    )


def test_failure_outputs_do_not_include_work_dag_agent_execution_or_provider_state() -> None:
    outcome = DeterministicM1Executor().execute(
        _request(dag_readiness=WorkDagNodeReadiness.BLOCKED)
    )
    payload_text = json.dumps(
        {
            "result": outcome.result.to_json_compatible(),
            "payload": outcome.event.payload,
            "metadata": outcome.event.metadata,
        },
        sort_keys=True,
    )

    assert outcome.evidence_refs == ()
    assert "provider_refs" not in payload_text
    assert "execution_id" not in payload_text
    assert "agent_definition_id" not in payload_text
    assert "agent_instance_id" not in payload_text
    assert "dependencies" not in payload_text
    assert "required_capabilities" not in payload_text


def test_request_producer_remains_canonical_reference() -> None:
    with_agent = _request(producer_ref=ref_for(AgentInstanceId))
    with_project = _request(producer_ref=ref_for(ProjectId))

    assert with_agent.producer_ref.kind is ReferenceKind.AGENT_INSTANCE
    assert with_project.producer_ref.kind is ReferenceKind.PROJECT


def _request(
    *,
    work: WorkItem | None = None,
    dag_readiness: WorkDagNodeReadiness = WorkDagNodeReadiness.READY,
    resolutions: tuple[CapabilityResolution, ...] | None = None,
    agent_instance: AgentInstance | None | object = _DEFAULT_AGENT_INSTANCE,
    producer_ref: ObjectReference | None = None,
) -> ExecutorRequest:
    selected_work = work or _work()
    selected_agent = (
        _agent_instance()
        if agent_instance is _DEFAULT_AGENT_INSTANCE
        else cast(AgentInstance | None, agent_instance)
    )
    return ExecutorRequest(
        work=selected_work,
        dag_readiness=dag_readiness,
        capability_resolutions=resolutions if resolutions is not None else (_resolution(),),
        agent_instance=selected_agent,
        producer_ref=producer_ref or ref_for(AgentInstanceId),
        event_id=fixed_id(EventId),
        evidence_id=fixed_id(EvidenceId),
        occurred_at=UTC_LATER,
        observability_context=_observability(),
    )


def _work(
    *,
    work_type: str = "inspect_current_state",
    state: WorkItemState = WorkItemState.READY,
) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId),
        work_type=work_type,
        title="Inspect current state",
        objective="Inspect relevant repository artifacts before changing implementation.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=state,
        required_capabilities=(_requirement(),),
    )


def _requirement() -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=fixed_id(CapabilityId),
        quality=CapabilityQuality.STANDARD,
    )


def _resolution() -> CapabilityResolution:
    return CapabilityResolution(
        requirement=_requirement(),
        status=CapabilityResolutionStatus.MATCHED,
        reason=CapabilityResolutionReason.EXACT_MATCH,
        capability_ref=ref_for(CapabilityId),
        agent_definition_ref=ref_for(AgentDefinitionId),
    )


def _agent_instance(
    *,
    work_id: WorkId | None = None,
    state: AgentInstanceState = AgentInstanceState.ACTIVE,
    agent_definition_id: AgentDefinitionId | None = None,
) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId),
        agent_definition_id=agent_definition_id or fixed_id(AgentDefinitionId),
        work_id=work_id or fixed_id(WorkId),
        state=state,
        created_at=UTC_NOW,
        started_at=UTC_LATER if state is AgentInstanceState.ACTIVE else None,
        observability_context=_observability(),
    )


def _observability() -> ObservabilityContext:
    return ObservabilityContext(
        project_id=fixed_id(ProjectId),
        work_id=fixed_id(WorkId),
        agent_instance_id=fixed_id(AgentInstanceId),
        trace_id=fixed_id(TraceId),
    )


def _round_trip(value: dict[str, object]) -> object:
    return json.loads(json.dumps(value, sort_keys=True))
