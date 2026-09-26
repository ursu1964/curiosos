from __future__ import annotations

from dataclasses import replace

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    ContractError,
    DecisionId,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    EventEnvelope,
    EventId,
    EventType,
    EvidenceId,
    ObjectReference,
    ObservabilityContext,
    ProviderId,
    Result,
    SchemaVersion,
    TraceId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_dag import WorkDag, WorkDagId, WorkDagNodeReadiness
from curios_runtime import (
    BoundedM1DagRunner,
    DeterministicM1Executor,
    ExecutorOutcome,
    ExecutorOutcomeStatus,
    ExecutorRequest,
    M1DagRunnerError,
    M1DagRunnerErrorCode,
    M1DagRunnerNodeStatus,
    M1DagRunnerReasonCode,
    M1DagRunnerRequest,
    M1DagRunnerStatus,
    RouteCandidateKind,
    RoutingCandidate,
    RoutingDecisionRequest,
    select_m1_route,
)

_SUPPORTED_WORK_TYPES = (
    "collect_recorded_context",
    "compose_recorded_summary",
    "verify_recorded_summary",
    "inspect_current_state",
    "apply_bounded_change",
    "verify_bounded_change",
)


def test_runner_executes_ready_nodes_with_fixed_concurrency_and_stable_order() -> None:
    first = _work(0, work_type="inspect_current_state")
    second = _work(1, work_type="apply_bounded_change")
    waiting = _work(2, dependencies=(first.work_id,))
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(
        _request(
            work_items=(second, waiting, first),
            decisions=(_decision(first), _decision(second), _decision(waiting)),
            agents=(_agent(first), _agent(second), _agent(waiting)),
            max_concurrency=1,
        )
    )

    assert result.status is M1DagRunnerStatus.COMPLETED
    assert [node.work_ref.ref_id for node in result.node_results] == [
        first.work_id,
        second.work_id,
        waiting.work_id,
    ]
    assert [node.status for node in result.node_results] == [
        M1DagRunnerNodeStatus.EXECUTED,
        M1DagRunnerNodeStatus.DEFERRED,
        M1DagRunnerNodeStatus.WAITING,
    ]
    assert result.node_results[1].reason is M1DagRunnerReasonCode.CONCURRENCY_LIMIT
    assert executor.executed_work_ids == (first.work_id,)
    assert len(result.events) == 1
    assert len(result.evidence_refs) == 1
    assert first.state is WorkItemState.READY
    assert second.state is WorkItemState.READY
    assert waiting.state is WorkItemState.READY


def test_runner_executes_independent_ready_nodes_while_dependent_node_waits() -> None:
    first = _work(0, work_type="inspect_current_state")
    second = _work(1, work_type="apply_bounded_change")
    waiting = _work(2, dependencies=(first.work_id, second.work_id))
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(
        _request(
            work_items=(waiting, second, first),
            decisions=(_decision(waiting), _decision(second), _decision(first)),
            agents=(_agent(waiting), _agent(second), _agent(first)),
            max_concurrency=2,
        )
    )

    assert result.status is M1DagRunnerStatus.COMPLETED
    assert [node.status for node in result.node_results] == [
        M1DagRunnerNodeStatus.EXECUTED,
        M1DagRunnerNodeStatus.EXECUTED,
        M1DagRunnerNodeStatus.WAITING,
    ]
    assert executor.executed_work_ids == (first.work_id, second.work_id)


def test_restart_recomputes_from_recorded_work_truth_without_runner_cache() -> None:
    upstream = _work(0)
    downstream = _work(1, dependencies=(upstream.work_id,))
    first_request = _request(
        work_items=(upstream, downstream),
        decisions=(_decision(upstream), _decision(downstream)),
        agents=(_agent(upstream), _agent(downstream)),
        max_concurrency=2,
    )
    first_result = BoundedM1DagRunner(_RecordingExecutor()).run_once(first_request)

    completed_upstream = replace(upstream, state=WorkItemState.COMPLETED, updated_at=UTC_LATER)
    restarted_request = _request(
        work_items=(completed_upstream, downstream),
        decisions=(_decision(completed_upstream), _decision(downstream)),
        agents=(_agent(completed_upstream), _agent(downstream)),
        max_concurrency=2,
    )
    restarted_result = BoundedM1DagRunner(_RecordingExecutor()).run_once(restarted_request)

    assert [node.status for node in first_result.node_results] == [
        M1DagRunnerNodeStatus.EXECUTED,
        M1DagRunnerNodeStatus.WAITING,
    ]
    assert [node.status for node in restarted_result.node_results] == [
        M1DagRunnerNodeStatus.TERMINAL,
        M1DagRunnerNodeStatus.EXECUTED,
    ]
    assert (
        BoundedM1DagRunner(_RecordingExecutor()).run_once(restarted_request).to_json_compatible()
        == restarted_result.to_json_compatible()
    )


@pytest.mark.parametrize("terminal_state", (WorkItemState.FAILED, WorkItemState.CANCELLED))
def test_failed_or_cancelled_dependency_blocks_downstream_without_execution(
    terminal_state: WorkItemState,
) -> None:
    upstream = _work(0, state=terminal_state)
    downstream = _work(1, dependencies=(upstream.work_id,))
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(
        _request(
            work_items=(upstream, downstream),
            decisions=(_decision(upstream), _decision(downstream)),
            agents=(_agent(upstream), _agent(downstream)),
            max_concurrency=2,
        )
    )

    assert result.status is M1DagRunnerStatus.BLOCKED
    assert [node.status for node in result.node_results] == [
        M1DagRunnerNodeStatus.TERMINAL,
        M1DagRunnerNodeStatus.BLOCKED,
    ]
    assert result.node_results[1].readiness is WorkDagNodeReadiness.BLOCKED
    assert executor.executed_work_ids == ()


def test_no_route_and_model_profile_routes_do_not_invoke_provider_or_executor() -> None:
    no_route_work = _work(0)
    model_route_work = _work(1, work_type="apply_bounded_change")
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(
        _request(
            work_items=(no_route_work, model_route_work),
            decisions=(_no_route_decision(no_route_work), _model_route_decision(model_route_work)),
            agents=(_agent(no_route_work), _agent(model_route_work)),
            max_concurrency=2,
        )
    )

    assert result.status is M1DagRunnerStatus.BLOCKED
    assert [node.reason for node in result.node_results] == [
        M1DagRunnerReasonCode.NO_ROUTE,
        M1DagRunnerReasonCode.ROUTE_NOT_EXECUTABLE,
    ]
    assert executor.executed_work_ids == ()
    assert result.events == ()
    assert result.evidence_refs == ()


@pytest.mark.parametrize(
    ("request_kwargs", "code"),
    (
        ({"max_concurrency": 0}, M1DagRunnerErrorCode.INVALID_CONCURRENCY),
        ({"decisions": ()}, M1DagRunnerErrorCode.MISSING_ROUTING_DECISION),
        ({"agents": ()}, M1DagRunnerErrorCode.MISSING_AGENT),
        ({"event_ids": {}}, M1DagRunnerErrorCode.MISSING_EXECUTOR_IDENTITY),
        ({"evidence_ids": {}}, M1DagRunnerErrorCode.MISSING_EXECUTOR_IDENTITY),
    ),
)
def test_malformed_runner_requests_fail_boundedly_before_executor_invocation(
    request_kwargs: dict[str, object],
    code: M1DagRunnerErrorCode,
) -> None:
    work = _work(0)
    executor = _RecordingExecutor()
    kwargs: dict[str, object] = {
        "work_items": (work,),
        "decisions": (_decision(work),),
        "agents": (_agent(work),),
    }
    kwargs.update(request_kwargs)

    with pytest.raises(M1DagRunnerError) as exc:
        BoundedM1DagRunner(executor).run_once(_request(**kwargs))  # type: ignore[arg-type]

    assert exc.value.code is code
    assert exc.value.retryable is False
    assert "secret" not in str(exc.value).lower()
    assert executor.executed_work_ids == ()


def test_duplicate_active_agents_for_same_work_are_rejected_before_execution() -> None:
    work = _work(0)
    executor = _RecordingExecutor()

    with pytest.raises(M1DagRunnerError) as exc:
        BoundedM1DagRunner(executor).run_once(
            _request(
                work_items=(work,),
                decisions=(_decision(work),),
                agents=(_agent(work), _agent(work, ordinal=1)),
            )
        )

    assert exc.value.code is M1DagRunnerErrorCode.INVALID_REQUEST
    assert executor.executed_work_ids == ()


def test_executor_failure_is_reported_without_work_or_agent_mutation() -> None:
    work = _work(0)
    agent = _agent(work)

    result = BoundedM1DagRunner(_FailingExecutor()).run_once(
        _request(work_items=(work,), decisions=(_decision(work),), agents=(agent,))
    )

    assert result.status is M1DagRunnerStatus.FAILED
    assert result.node_results[0].status is M1DagRunnerNodeStatus.FAILED
    assert result.node_results[0].executor_outcome is not None
    assert result.node_results[0].executor_outcome.status is ExecutorOutcomeStatus.FAILED
    assert work.state is WorkItemState.READY
    assert agent.state is AgentInstanceState.ACTIVE


def test_runner_surface_has_no_provider_model_scheduler_or_persistence_authority() -> None:
    source = (
        __import__("pathlib")
        .Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("src", "curios_runtime", "m1_bounded_dag_runner.py")
        .read_text(encoding="utf-8")
    )

    forbidden = {
        "Ollama",
        "list_models",
        "generate",
        "chat",
        "embed",
        "PersistenceStore",
        "M0WorkRepository",
        "M1AgentLifecycleRepository",
        "threading",
        "asyncio",
        "subprocess",
        "requests",
        "httpx",
        "socket",
    }

    assert forbidden.isdisjoint(source)


class _RecordingExecutor:
    def __init__(self) -> None:
        self._delegate = DeterministicM1Executor()
        self.executed_work_ids: tuple[WorkId, ...] = ()

    def execute(self, request: ExecutorRequest) -> ExecutorOutcome:
        self.executed_work_ids = (*self.executed_work_ids, request.work.work_id)
        return self._delegate.execute(request)


class _FailingExecutor:
    def execute(self, request: ExecutorRequest) -> ExecutorOutcome:
        error = ContractError(
            error_code=ErrorCode("M1_TEST_EXECUTOR_FAILURE"),
            message="Deterministic executor test failure.",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.ERROR,
            retryable=False,
            subject_ref=ObjectReference.from_id(request.work.work_id),
            trace_id=fixed_id(TraceId),
        )
        return ExecutorOutcome(
            status=ExecutorOutcomeStatus.FAILED,
            result=Result.failure((error,)),
            event=EventEnvelope(
                event_id=request.event_id,
                event_type=EventType("executor.deterministic.completed"),
                schema_version=SchemaVersion.parse("1.0.0"),
                occurred_at=request.occurred_at,
                producer=request.producer_ref,
                subject_ref=ObjectReference.from_id(request.work.work_id),
                observability_context=request.observability_context,
                payload={"status": "FAILED", "work_id": str(request.work.work_id)},
            ),
        )


def _request(
    *,
    work_items: tuple[WorkItem, ...],
    decisions: tuple[object, ...],
    agents: tuple[AgentInstance, ...],
    max_concurrency: int = 2,
    event_ids: dict[WorkId, EventId] | None = None,
    evidence_ids: dict[WorkId, EvidenceId] | None = None,
) -> M1DagRunnerRequest:
    return M1DagRunnerRequest(
        dag=WorkDag.from_work_items(
            fixed_id(WorkDagId),
            work_items,
            created_at=UTC_NOW,
        ),
        work_items=work_items,
        routing_decisions=decisions,  # type: ignore[arg-type]
        agent_instances=agents,
        capability_resolutions_by_work_id={item.work_id: () for item in work_items},
        event_ids_by_work_id=event_ids
        if event_ids is not None
        else {item.work_id: fixed_id(EventId, index) for index, item in enumerate(work_items)},
        evidence_ids_by_work_id=evidence_ids
        if evidence_ids is not None
        else {item.work_id: fixed_id(EvidenceId, index) for index, item in enumerate(work_items)},
        producer_ref=ref_for(AgentInstanceId),
        occurred_at=UTC_NOW,
        observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
        max_concurrency=max_concurrency,
    )


def _work(
    ordinal: int,
    *,
    work_type: str = "inspect_current_state",
    dependencies: tuple[WorkId, ...] = (),
    state: WorkItemState = WorkItemState.READY,
) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal),
        work_type=work_type,
        title=f"Work {ordinal}",
        objective="Execute bounded M1 runner work.",
        dependencies=dependencies,
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=state,
    )


def _agent(work: WorkItem, *, ordinal: int = 0) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId, ordinal),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=work.work_id,
        state=AgentInstanceState.ACTIVE,
        created_at=UTC_NOW,
        started_at=UTC_NOW,
    )


def _decision(work: WorkItem) -> object:
    return select_m1_route(
        RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId, int(str(work.work_id)[-1], 36) % 10),
            work=work,
            candidates=(
                RoutingCandidate.deterministic_executor(
                    work_id=work.work_id,
                    executor_name="deterministic_m1",
                    supported_work_types=_SUPPORTED_WORK_TYPES,
                ),
            ),
            requested_at=UTC_NOW,
            producer_ref=ref_for(AgentInstanceId),
            observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
            resource_constraints={"local_only": True},
        )
    )


def _no_route_decision(work: WorkItem) -> object:
    return select_m1_route(
        RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId, 8),
            work=work,
            candidates=(),
            requested_at=UTC_NOW,
            producer_ref=ref_for(AgentInstanceId),
            observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
            resource_constraints={"local_only": True},
        )
    )


def _model_route_decision(work: WorkItem) -> object:
    return select_m1_route(
        RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId, 9),
            work=work,
            candidates=(
                RoutingCandidate(
                    candidate_key="model_profile_local_llama",
                    kind=RouteCandidateKind.MODEL_PROFILE,
                    work_ref=ObjectReference.from_id(work.work_id),
                    provider_ref=ObjectReference.from_id(fixed_id(ProviderId)),
                    model_name="llama3.2:latest",
                    model_status="available",
                ),
            ),
            requested_at=UTC_NOW,
            producer_ref=ref_for(AgentInstanceId),
            observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
            resource_constraints={"local_only": True},
        )
    )
