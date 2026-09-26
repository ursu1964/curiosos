from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import cast

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_capability import (
    CapabilityResolution,
    CapabilityResolutionReason,
    CapabilityResolutionStatus,
)
from curios_cognitive import DecompositionStatus, decompose_intent
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
    Intent,
    IntentId,
    ObjectReference,
    ObservabilityContext,
    ProjectId,
    ResultStatus,
    TraceId,
    WorkId,
    WorkItem,
    WorkItemState,
    to_json_compatible,
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


def test_executor_supported_work_types_match_frozen_decomposition_outputs() -> None:
    expected = {
        "collect_recorded_context",
        "compose_recorded_summary",
        "verify_recorded_summary",
        "inspect_current_state",
        "apply_bounded_change",
        "verify_bounded_change",
    }
    observed = {
        work_item.work_type
        for objective in (
            "Summarize the recorded project status.",
            "Implement the smallest bounded change.",
        )
        for work_item in _decomposition_work_items(objective)
    }

    assert observed == expected
    for work_type in sorted(observed):
        outcome = DeterministicM1Executor().execute(_request(work=_work(work_type=work_type)))
        assert outcome.status is ExecutorOutcomeStatus.COMPLETED
        assert outcome.result.status is ResultStatus.SUCCESS
        assert outcome.event.event_type == M1_EXECUTOR_EVENT_TYPE
        assert outcome.evidence_refs


@pytest.mark.parametrize(
    "near_miss",
    (
        "collect_recorded_contexts",
        "pre_collect_recorded_context",
        "collect_recorded_context_extra",
        "inspect_current_state_extra",
        "apply_bounded_changes",
        "verify_bounded_change_extra",
        "verify_boundedchange",
        "provider_inventory",
        "execute_arbitrary_callable",
    ),
)
def test_executor_work_type_matching_is_exact_and_bounded(near_miss: str) -> None:
    outcome = DeterministicM1Executor().execute(_request(work=_work(work_type=near_miss)))

    assert outcome.status is ExecutorOutcomeStatus.FAILED
    assert outcome.result.status is ResultStatus.FAILURE
    assert outcome.result.value is None
    assert str(outcome.result.errors[0].error_code) == ExecutorErrorCode.UNSUPPORTED_WORK_TYPE
    assert outcome.evidence_refs == ()
    assert _as_mapping(outcome.event.payload)["status"] == ResultStatus.FAILURE.value
    assert (
        _as_mapping(outcome.event.metadata)["outcome_status"] == ExecutorOutcomeStatus.FAILED.value
    )


@pytest.mark.parametrize(
    ("readiness", "expected_status"),
    (
        (WorkDagNodeReadiness.READY, ExecutorOutcomeStatus.COMPLETED),
        (WorkDagNodeReadiness.WAITING, ExecutorOutcomeStatus.BLOCKED),
        (WorkDagNodeReadiness.BLOCKED, ExecutorOutcomeStatus.BLOCKED),
        (WorkDagNodeReadiness.TERMINAL, ExecutorOutcomeStatus.BLOCKED),
    ),
)
def test_executor_readiness_gate_accepts_only_ready_nodes(
    readiness: WorkDagNodeReadiness,
    expected_status: ExecutorOutcomeStatus,
) -> None:
    work = _work()

    outcome = DeterministicM1Executor().execute(_request(work=work, dag_readiness=readiness))

    assert outcome.status is expected_status
    assert work == _work()
    if readiness is WorkDagNodeReadiness.READY:
        assert outcome.result.status is ResultStatus.SUCCESS
        assert outcome.evidence_refs
    else:
        assert outcome.result.status is ResultStatus.FAILURE
        assert str(outcome.result.errors[0].error_code) == ExecutorErrorCode.WORK_NOT_READY
        assert outcome.evidence_refs == ()


@pytest.mark.parametrize(
    ("resolution", "expected_code"),
    (
        (
            CapabilityResolution(
                requirement=CapabilityRequirement(
                    capability_id=fixed_id(CapabilityId),
                    quality=CapabilityQuality.STANDARD,
                ),
                status=CapabilityResolutionStatus.MISSING,
                reason=CapabilityResolutionReason.CAPABILITY_NOT_OFFERED,
            ),
            ExecutorErrorCode.CAPABILITY_MISSING,
        ),
        (
            CapabilityResolution(
                requirement=CapabilityRequirement(
                    capability_id=fixed_id(CapabilityId),
                    quality=CapabilityQuality.STANDARD,
                ),
                status=CapabilityResolutionStatus.MISSING,
                reason=CapabilityResolutionReason.AGENT_NOT_ELIGIBLE,
                capability_ref=ref_for(CapabilityId),
            ),
            ExecutorErrorCode.CAPABILITY_MISSING,
        ),
        (
            CapabilityResolution(
                requirement=CapabilityRequirement(
                    capability_id=fixed_id(CapabilityId),
                    quality=CapabilityQuality.STANDARD,
                ),
                status=CapabilityResolutionStatus.AMBIGUOUS,
                reason=CapabilityResolutionReason.DUPLICATE_CAPABILITY,
                ambiguous_capability_refs=(ref_for(CapabilityId), ref_for(CapabilityId, 1)),
            ),
            ExecutorErrorCode.CAPABILITY_AMBIGUOUS,
        ),
        (
            CapabilityResolution(
                requirement=CapabilityRequirement(
                    capability_id=fixed_id(CapabilityId),
                    quality=CapabilityQuality.STANDARD,
                ),
                status=CapabilityResolutionStatus.AMBIGUOUS,
                reason=CapabilityResolutionReason.MULTIPLE_ELIGIBLE_AGENTS,
                capability_ref=ref_for(CapabilityId),
                ambiguous_agent_definition_refs=(
                    ref_for(AgentDefinitionId),
                    ref_for(AgentDefinitionId, 1),
                ),
            ),
            ExecutorErrorCode.CAPABILITY_AMBIGUOUS,
        ),
    ),
)
def test_executor_rejects_every_missing_and_ambiguous_capability_reason(
    resolution: CapabilityResolution,
    expected_code: ExecutorErrorCode,
) -> None:
    outcome = DeterministicM1Executor().execute(_request(resolutions=(resolution,)))

    assert outcome.status is ExecutorOutcomeStatus.BLOCKED
    assert outcome.result.status is ResultStatus.FAILURE
    assert str(outcome.result.errors[0].error_code) == expected_code
    assert outcome.evidence_refs == ()


def test_executor_rejects_capability_permutation_that_does_not_match_work_order() -> None:
    first = _requirement(0)
    second = _requirement(1)
    work = _work(required_capabilities=(first, second))

    outcome = DeterministicM1Executor().execute(
        _request(work=work, resolutions=(_resolution(second), _resolution(first)))
    )

    assert outcome.status is ExecutorOutcomeStatus.FAILED
    assert str(outcome.result.errors[0].error_code) == ExecutorErrorCode.CAPABILITY_SHAPE_INVALID
    assert outcome.evidence_refs == ()


@pytest.mark.parametrize("state", tuple(AgentInstanceState))
def test_executor_agent_gate_accepts_only_active_agent_instances(state: AgentInstanceState) -> None:
    outcome = DeterministicM1Executor().execute(
        _request(agent_instance=_agent_instance(state=state))
    )

    if state is AgentInstanceState.ACTIVE:
        assert outcome.status is ExecutorOutcomeStatus.COMPLETED
        assert outcome.result.status is ResultStatus.SUCCESS
    else:
        assert outcome.status is ExecutorOutcomeStatus.BLOCKED
        assert outcome.result.status is ResultStatus.FAILURE
        assert str(outcome.result.errors[0].error_code) == ExecutorErrorCode.AGENT_NOT_ACTIVE
        assert outcome.evidence_refs == ()


def test_executor_rejects_individually_valid_cross_domain_mismatches() -> None:
    work = _work()
    cases = (
        (
            _request(work=work, agent_instance=_agent_instance(work_id=fixed_id(WorkId, 1))),
            ExecutorErrorCode.AGENT_WORK_MISMATCH,
        ),
        (
            _request(
                work=work,
                resolutions=(_resolution(_requirement(), agent_definition_ordinal=1),),
                agent_instance=_agent_instance(),
            ),
            ExecutorErrorCode.AGENT_DEFINITION_MISMATCH,
        ),
        (
            _request(
                work=work,
                dag_readiness=WorkDagNodeReadiness.TERMINAL,
                agent_instance=_agent_instance(),
            ),
            ExecutorErrorCode.WORK_NOT_READY,
        ),
        (
            _request(
                work=work,
                resolutions=(
                    CapabilityResolution(
                        requirement=_requirement(),
                        status=CapabilityResolutionStatus.AMBIGUOUS,
                        reason=CapabilityResolutionReason.MULTIPLE_ELIGIBLE_AGENTS,
                        capability_ref=ref_for(CapabilityId),
                        ambiguous_agent_definition_refs=(
                            ref_for(AgentDefinitionId),
                            ref_for(AgentDefinitionId, 1),
                        ),
                    ),
                ),
                agent_instance=_agent_instance(),
            ),
            ExecutorErrorCode.CAPABILITY_AMBIGUOUS,
        ),
    )

    for request, expected_code in cases:
        outcome = DeterministicM1Executor().execute(request)
        assert outcome.result.status is ResultStatus.FAILURE
        assert str(outcome.result.errors[0].error_code) == expected_code
        assert outcome.evidence_refs == ()


def test_executor_outcome_serialization_is_stable_and_does_not_mutate_inputs() -> None:
    request = _request()
    before = to_json_compatible(request.work)

    first = DeterministicM1Executor().execute(request)
    second = DeterministicM1Executor().execute(request)

    assert to_json_compatible(request.work) == before
    assert first.to_json_compatible() == second.to_json_compatible()
    assert json.loads(json.dumps(first.to_json_compatible(), sort_keys=True)) == (
        first.to_json_compatible()
    )


def test_executor_source_has_no_persistence_provider_network_or_callback_authority() -> None:
    module_path = (
        Path(__file__).resolve().parents[1] / "src" / "curios_runtime" / "executor_seam.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    calls: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    assert {
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "sqlalchemy",
        "curios_persistence",
        "curios_postgres_provider",
        "curios_ollama",
        "curios_policy",
    }.isdisjoint(imports)
    assert {"open", "exec", "eval", "compile", "__import__"}.isdisjoint(calls)


def _decomposition_work_items(objective: str) -> tuple[WorkItem, ...]:
    proposal = decompose_intent(
        Intent(
            intent_id=fixed_id(IntentId),
            objective=objective,
            submitted_at=UTC_NOW,
            source_ref=ref_for(ProjectId),
        ),
        created_at=UTC_LATER,
    )
    assert proposal.status is DecompositionStatus.SUPPORTED
    return proposal.work_items


def _request(
    *,
    work: WorkItem | None = None,
    dag_readiness: WorkDagNodeReadiness = WorkDagNodeReadiness.READY,
    resolutions: tuple[CapabilityResolution, ...] | None = None,
    agent_instance: AgentInstance | None | object = _DEFAULT_AGENT_INSTANCE,
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
        producer_ref=ref_for(AgentInstanceId),
        event_id=fixed_id(EventId),
        evidence_id=fixed_id(EvidenceId),
        occurred_at=UTC_LATER,
        observability_context=_observability(),
    )


def _work(
    *,
    work_type: str = "inspect_current_state",
    required_capabilities: tuple[CapabilityRequirement, ...] | None = None,
) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId),
        work_type=work_type,
        title="Inspect current state",
        objective="Inspect relevant repository artifacts before changing implementation.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
        required_capabilities=required_capabilities
        if required_capabilities is not None
        else (_requirement(),),
    )


def _requirement(ordinal: int = 0) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=fixed_id(CapabilityId, ordinal),
        quality=CapabilityQuality.STANDARD,
    )


def _resolution(
    requirement: CapabilityRequirement | None = None,
    *,
    agent_definition_ordinal: int = 0,
) -> CapabilityResolution:
    return CapabilityResolution(
        requirement=requirement or _requirement(),
        status=CapabilityResolutionStatus.MATCHED,
        reason=CapabilityResolutionReason.EXACT_MATCH,
        capability_ref=ObjectReference.from_id((requirement or _requirement()).capability_id),
        agent_definition_ref=ref_for(AgentDefinitionId, agent_definition_ordinal),
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
    )


def _observability() -> ObservabilityContext:
    return ObservabilityContext(
        project_id=fixed_id(ProjectId),
        work_id=fixed_id(WorkId),
        agent_instance_id=fixed_id(AgentInstanceId),
        trace_id=fixed_id(TraceId),
    )


def _as_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return value
