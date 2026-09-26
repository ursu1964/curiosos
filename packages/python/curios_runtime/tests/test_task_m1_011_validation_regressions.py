from __future__ import annotations

from contract_fixtures import UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    DecisionId,
    EventId,
    EvidenceId,
    ObjectReference,
    ObservabilityContext,
    TraceId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_dag import WorkDag, WorkDagId
from curios_runtime import (
    BoundedM1DagRunner,
    DeterministicM1Executor,
    ExecutorOutcome,
    ExecutorRequest,
    M1DagRunnerNodeStatus,
    M1DagRunnerReasonCode,
    M1DagRunnerRequest,
    M1DagRunnerStatus,
    RoutingCandidate,
    RoutingDecisionRationale,
    RoutingDecisionRecord,
    RoutingDecisionStatus,
    RoutingRationaleCode,
)


def test_selected_executor_route_must_support_routed_work_type_before_invocation() -> None:
    work = _work(0, work_type="inspect_current_state")
    decision = _selected_executor_decision(
        work,
        supported_work_types=("apply_bounded_change",),
    )
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(_request((work,), (decision,)))

    assert executor.executed_work_ids == ()
    assert result.status is M1DagRunnerStatus.BLOCKED
    assert result.node_results[0].status is M1DagRunnerNodeStatus.BLOCKED
    assert result.node_results[0].reason is M1DagRunnerReasonCode.ROUTE_NOT_EXECUTABLE
    assert result.node_results[0].executor_outcome is None
    assert result.events == ()
    assert result.evidence_refs == ()


def test_compatible_selected_executor_route_invokes_executor_once() -> None:
    work = _work(0, work_type="inspect_current_state")
    decision = _selected_executor_decision(
        work,
        supported_work_types=("apply_bounded_change", "inspect_current_state"),
    )
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(_request((work,), (decision,)))

    assert executor.executed_work_ids == (work.work_id,)
    assert result.status is M1DagRunnerStatus.COMPLETED
    assert result.node_results[0].status is M1DagRunnerNodeStatus.EXECUTED
    assert result.node_results[0].reason is M1DagRunnerReasonCode.EXECUTOR_COMPLETED
    assert result.node_results[0].executor_outcome is not None
    assert len(result.events) == 1
    assert len(result.evidence_refs) == 1


def test_mixed_ready_nodes_preserve_order_and_do_not_corrupt_valid_execution() -> None:
    compatible = _work(0, work_type="apply_bounded_change")
    incompatible = _work(1, work_type="inspect_current_state")
    waiting = _work(2, work_type="verify_bounded_change", dependencies=(compatible.work_id,))
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(
        _request(
            (waiting, incompatible, compatible),
            (
                _selected_executor_decision(
                    waiting, supported_work_types=("verify_bounded_change",)
                ),
                _selected_executor_decision(
                    incompatible, supported_work_types=("apply_bounded_change",)
                ),
                _selected_executor_decision(
                    compatible, supported_work_types=("apply_bounded_change",)
                ),
            ),
            max_concurrency=2,
        )
    )

    assert [node.work_ref.ref_id for node in result.node_results] == [
        compatible.work_id,
        incompatible.work_id,
        waiting.work_id,
    ]
    assert [node.status for node in result.node_results] == [
        M1DagRunnerNodeStatus.EXECUTED,
        M1DagRunnerNodeStatus.BLOCKED,
        M1DagRunnerNodeStatus.WAITING,
    ]
    assert [node.reason for node in result.node_results] == [
        M1DagRunnerReasonCode.EXECUTOR_COMPLETED,
        M1DagRunnerReasonCode.ROUTE_NOT_EXECUTABLE,
        M1DagRunnerReasonCode.WAITING_ON_DEPENDENCY,
    ]
    assert executor.executed_work_ids == (compatible.work_id,)
    assert result.status is M1DagRunnerStatus.COMPLETED
    assert len(result.events) == 1
    assert len(result.evidence_refs) == 1


def test_incompatible_selected_route_consumes_ready_concurrency_without_slot_refill() -> None:
    incompatible = _work(0, work_type="inspect_current_state")
    compatible = _work(1, work_type="apply_bounded_change")
    executor = _RecordingExecutor()

    result = BoundedM1DagRunner(executor).run_once(
        _request(
            (compatible, incompatible),
            (
                _selected_executor_decision(
                    compatible, supported_work_types=("apply_bounded_change",)
                ),
                _selected_executor_decision(
                    incompatible, supported_work_types=("verify_bounded_change",)
                ),
            ),
            max_concurrency=1,
        )
    )

    assert [node.work_ref.ref_id for node in result.node_results] == [
        incompatible.work_id,
        compatible.work_id,
    ]
    assert [node.status for node in result.node_results] == [
        M1DagRunnerNodeStatus.BLOCKED,
        M1DagRunnerNodeStatus.DEFERRED,
    ]
    assert [node.reason for node in result.node_results] == [
        M1DagRunnerReasonCode.ROUTE_NOT_EXECUTABLE,
        M1DagRunnerReasonCode.CONCURRENCY_LIMIT,
    ]
    assert executor.executed_work_ids == ()
    assert result.events == ()
    assert result.evidence_refs == ()


class _RecordingExecutor:
    def __init__(self) -> None:
        self._delegate = DeterministicM1Executor()
        self.executed_work_ids: tuple[WorkId, ...] = ()

    def execute(self, request: ExecutorRequest) -> ExecutorOutcome:
        self.executed_work_ids = (*self.executed_work_ids, request.work.work_id)
        return self._delegate.execute(request)


def _request(
    work_items: tuple[WorkItem, ...],
    decisions: tuple[RoutingDecisionRecord, ...],
    *,
    max_concurrency: int = 1,
) -> M1DagRunnerRequest:
    return M1DagRunnerRequest(
        dag=WorkDag.from_work_items(fixed_id(WorkDagId), work_items, created_at=UTC_NOW),
        work_items=work_items,
        routing_decisions=decisions,
        agent_instances=tuple(_agent(work, ordinal) for ordinal, work in enumerate(work_items)),
        capability_resolutions_by_work_id={work.work_id: () for work in work_items},
        event_ids_by_work_id={
            work.work_id: fixed_id(EventId, ordinal) for ordinal, work in enumerate(work_items)
        },
        evidence_ids_by_work_id={
            work.work_id: fixed_id(EvidenceId, ordinal) for ordinal, work in enumerate(work_items)
        },
        producer_ref=ref_for(AgentInstanceId),
        occurred_at=UTC_NOW,
        observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
        max_concurrency=max_concurrency,
    )


def _selected_executor_decision(
    work: WorkItem,
    *,
    supported_work_types: tuple[str, ...],
) -> RoutingDecisionRecord:
    selected_route = RoutingCandidate.deterministic_executor(
        work_id=work.work_id,
        executor_name="deterministic_m1",
        supported_work_types=supported_work_types,
    )
    return RoutingDecisionRecord(
        decision_id=fixed_id(DecisionId, int(str(work.work_id)[-1], 36) % 10),
        work_ref=ObjectReference.from_id(work.work_id),
        status=RoutingDecisionStatus.SELECTED,
        candidates=(selected_route,),
        selected_route=selected_route,
        rationale=RoutingDecisionRationale(
            code=RoutingRationaleCode.SELECTED_SINGLE_VALID_ROUTE,
            message="Selected route fixture for validation.",
        ),
        resource_constraints={"local_only": True},
        decided_at=UTC_NOW,
        producer_ref=ref_for(AgentInstanceId),
        observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
    )


def _work(
    ordinal: int,
    *,
    work_type: str,
    dependencies: tuple[WorkId, ...] = (),
) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal),
        work_type=work_type,
        title="Ready work",
        objective="Validate runner route/work consistency.",
        dependencies=dependencies,
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
    )


def _agent(work: WorkItem, ordinal: int) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId, ordinal),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=work.work_id,
        state=AgentInstanceState.ACTIVE,
        created_at=UTC_NOW,
        started_at=UTC_NOW,
    )
