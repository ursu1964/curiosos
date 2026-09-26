"""Bounded M1 DAG runner over frozen DAG, routing, agent, and executor records.

TASK-M1-011 owns only a local deterministic runner. It does not discover
models, select routes, invoke providers, mutate persisted state, retry work,
or run as a daemon.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import NoReturn

from curios_capability import CapabilityResolution
from curios_contracts import (
    AgentInstance,
    AgentInstanceState,
    EventEnvelope,
    EventId,
    EvidenceId,
    EvidenceReference,
    ObjectReference,
    ObservabilityContext,
    ReferenceKind,
    UtcTimestamp,
    WorkId,
    WorkItem,
    to_json_compatible,
)
from curios_dag import WorkDag, WorkDagNodeReadiness, WorkDagState, derive_work_dag_state

from curios_runtime.executor_seam import (
    ExecutorOutcome,
    ExecutorOutcomeStatus,
    ExecutorRequest,
    M1Executor,
)
from curios_runtime.routing_decision_repository import (
    RouteCandidateKind,
    RoutingDecisionRecord,
    RoutingDecisionStatus,
)

_MAX_CONCURRENCY = 8


class M1DagRunnerStatus(StrEnum):
    """Stable outcome for one bounded DAG runner invocation."""

    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class M1DagRunnerNodeStatus(StrEnum):
    """Stable per-node outcome without mutating canonical WorkItem state."""

    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    WAITING = "WAITING"
    TERMINAL = "TERMINAL"
    DEFERRED = "DEFERRED"


class M1DagRunnerReasonCode(StrEnum):
    """Bounded runner reasons derived from canonical recorded inputs."""

    EXECUTOR_COMPLETED = "EXECUTOR_COMPLETED"
    EXECUTOR_BLOCKED = "EXECUTOR_BLOCKED"
    EXECUTOR_FAILED = "EXECUTOR_FAILED"
    WAITING_ON_DEPENDENCY = "WAITING_ON_DEPENDENCY"
    BLOCKED_BY_DEPENDENCY_FAILURE = "BLOCKED_BY_DEPENDENCY_FAILURE"
    TERMINAL_WORK = "TERMINAL_WORK"
    CONCURRENCY_LIMIT = "CONCURRENCY_LIMIT"
    NO_ROUTE = "NO_ROUTE"
    ROUTE_NOT_EXECUTABLE = "ROUTE_NOT_EXECUTABLE"


class M1DagRunnerErrorCode(StrEnum):
    """Bounded validation errors for malformed runner requests."""

    INVALID_CONCURRENCY = "INVALID_CONCURRENCY"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_AGENT = "MISSING_AGENT"
    MISSING_EXECUTOR_IDENTITY = "MISSING_EXECUTOR_IDENTITY"
    MISSING_ROUTING_DECISION = "MISSING_ROUTING_DECISION"


class M1DagRunnerError(RuntimeError):
    """Bounded M1 DAG runner error without native/provider detail leakage."""

    def __init__(
        self,
        code: M1DagRunnerErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
    ) -> None:
        super().__init__(message)
        self.code = M1DagRunnerErrorCode(code)
        self.retryable = retryable
        self.operation = operation

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": str(self),
            "retryable": self.retryable,
            "operation": self.operation,
        }


@dataclass(frozen=True, slots=True)
class M1DagRunnerRequest:
    """Input for one bounded local DAG runner pass."""

    dag: WorkDag
    work_items: tuple[WorkItem, ...]
    routing_decisions: tuple[RoutingDecisionRecord, ...]
    agent_instances: tuple[AgentInstance, ...]
    capability_resolutions_by_work_id: Mapping[WorkId, tuple[CapabilityResolution, ...]]
    event_ids_by_work_id: Mapping[WorkId, EventId]
    evidence_ids_by_work_id: Mapping[WorkId, EvidenceId]
    producer_ref: ObjectReference
    occurred_at: UtcTimestamp
    observability_context: ObservabilityContext
    max_concurrency: int

    def __post_init__(self) -> None:
        if not isinstance(self.dag, WorkDag):
            msg = "dag must be a WorkDag"
            raise TypeError(msg)
        object.__setattr__(self, "work_items", _normalize_work_items(self.work_items))
        object.__setattr__(
            self,
            "routing_decisions",
            _normalize_routing_decisions(self.routing_decisions),
        )
        object.__setattr__(
            self,
            "agent_instances",
            _normalize_agent_instances(self.agent_instances),
        )
        object.__setattr__(
            self,
            "capability_resolutions_by_work_id",
            _normalize_capability_resolution_map(self.capability_resolutions_by_work_id),
        )
        object.__setattr__(
            self,
            "event_ids_by_work_id",
            _normalize_id_map(self.event_ids_by_work_id, EventId, "event_ids_by_work_id"),
        )
        object.__setattr__(
            self,
            "evidence_ids_by_work_id",
            _normalize_id_map(
                self.evidence_ids_by_work_id,
                EvidenceId,
                "evidence_ids_by_work_id",
            ),
        )
        if not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be an ObjectReference"
            raise TypeError(msg)
        object.__setattr__(self, "occurred_at", UtcTimestamp(self.occurred_at))
        if not isinstance(self.observability_context, ObservabilityContext):
            msg = "observability_context must be an ObservabilityContext"
            raise TypeError(msg)
        if not isinstance(self.max_concurrency, int):
            msg = "max_concurrency must be an integer"
            raise TypeError(msg)
        if self.max_concurrency < 1 or self.max_concurrency > _MAX_CONCURRENCY:
            _raise_runner_error(
                M1DagRunnerError(
                    M1DagRunnerErrorCode.INVALID_CONCURRENCY,
                    "M1 DAG runner concurrency must be between 1 and 8.",
                    retryable=False,
                    operation="construct_request",
                )
            )


@dataclass(frozen=True, slots=True)
class M1DagRunnerNodeResult:
    """Per-node result from a bounded runner pass."""

    work_ref: ObjectReference
    readiness: WorkDagNodeReadiness
    status: M1DagRunnerNodeStatus
    reason: M1DagRunnerReasonCode
    routing_decision_ref: ObjectReference | None = None
    executor_outcome: ExecutorOutcome | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "work_ref", _require_ref_kind(self.work_ref, ReferenceKind.WORK))
        object.__setattr__(self, "readiness", WorkDagNodeReadiness(self.readiness))
        object.__setattr__(self, "status", M1DagRunnerNodeStatus(self.status))
        object.__setattr__(self, "reason", M1DagRunnerReasonCode(self.reason))
        if self.routing_decision_ref is not None:
            object.__setattr__(
                self,
                "routing_decision_ref",
                _require_ref_kind(self.routing_decision_ref, ReferenceKind.DECISION),
            )
        if self.executor_outcome is not None and not isinstance(
            self.executor_outcome,
            ExecutorOutcome,
        ):
            msg = "executor_outcome must be an ExecutorOutcome when provided"
            raise TypeError(msg)

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "work_ref": to_json_compatible(self.work_ref),
            "readiness": self.readiness.value,
            "status": self.status.value,
            "reason": self.reason.value,
            "routing_decision_ref": to_json_compatible(self.routing_decision_ref),
            "executor_outcome": to_json_compatible(self.executor_outcome),
        }


@dataclass(frozen=True, slots=True)
class M1DagRunnerResult:
    """Outcome of one bounded local DAG runner pass."""

    status: M1DagRunnerStatus
    dag_state: WorkDagState
    node_results: tuple[M1DagRunnerNodeResult, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", M1DagRunnerStatus(self.status))
        if not isinstance(self.dag_state, WorkDagState):
            msg = "dag_state must be a WorkDagState"
            raise TypeError(msg)
        for result in self.node_results:
            if not isinstance(result, M1DagRunnerNodeResult):
                msg = "node_results must contain M1DagRunnerNodeResult values"
                raise TypeError(msg)

    @property
    def events(self) -> tuple[EventEnvelope, ...]:
        """Executor events emitted by executed nodes, in deterministic node order."""
        return tuple(
            result.executor_outcome.event
            for result in self.node_results
            if result.executor_outcome is not None
        )

    @property
    def evidence_refs(self) -> tuple[EvidenceReference, ...]:
        """Evidence references emitted by executed nodes, in deterministic node order."""
        refs: list[EvidenceReference] = []
        for result in self.node_results:
            if result.executor_outcome is not None:
                refs.extend(result.executor_outcome.evidence_refs)
        return tuple(refs)

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "dag_state": self.dag_state.to_json_compatible(),
            "node_results": to_json_compatible(self.node_results),
            "events": to_json_compatible(self.events),
            "evidence_refs": to_json_compatible(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class BoundedM1DagRunner:
    """Run one deterministic bounded pass over ready M1 DAG nodes."""

    executor: M1Executor

    def run_once(self, request: M1DagRunnerRequest) -> M1DagRunnerResult:
        """Execute at most ``max_concurrency`` ready nodes without persistence."""
        if not isinstance(request, M1DagRunnerRequest):
            msg = "request must be an M1DagRunnerRequest"
            raise TypeError(msg)

        dag_state = derive_work_dag_state(request.dag, request.work_items)
        work_by_id = {item.work_id: item for item in request.work_items}
        decisions_by_work = _routing_decisions_by_work(request.routing_decisions)
        agents_by_work = _active_agents_by_work(request.agent_instances)
        _validate_selected_ready_nodes(
            dag_state,
            work_by_id=work_by_id,
            decisions_by_work=decisions_by_work,
            agents_by_work=agents_by_work,
            request=request,
        )

        ready_seen = 0
        results: list[M1DagRunnerNodeResult] = []
        for node_state in dag_state.node_states:
            work_id = _work_id(node_state.work_ref)
            match node_state.readiness:
                case WorkDagNodeReadiness.WAITING:
                    results.append(
                        M1DagRunnerNodeResult(
                            work_ref=node_state.work_ref,
                            readiness=node_state.readiness,
                            status=M1DagRunnerNodeStatus.WAITING,
                            reason=M1DagRunnerReasonCode.WAITING_ON_DEPENDENCY,
                        )
                    )
                case WorkDagNodeReadiness.BLOCKED:
                    results.append(
                        M1DagRunnerNodeResult(
                            work_ref=node_state.work_ref,
                            readiness=node_state.readiness,
                            status=M1DagRunnerNodeStatus.BLOCKED,
                            reason=M1DagRunnerReasonCode.BLOCKED_BY_DEPENDENCY_FAILURE,
                        )
                    )
                case WorkDagNodeReadiness.TERMINAL:
                    results.append(
                        M1DagRunnerNodeResult(
                            work_ref=node_state.work_ref,
                            readiness=node_state.readiness,
                            status=M1DagRunnerNodeStatus.TERMINAL,
                            reason=M1DagRunnerReasonCode.TERMINAL_WORK,
                        )
                    )
                case WorkDagNodeReadiness.READY:
                    ready_seen += 1
                    if ready_seen > request.max_concurrency:
                        results.append(
                            M1DagRunnerNodeResult(
                                work_ref=node_state.work_ref,
                                readiness=node_state.readiness,
                                status=M1DagRunnerNodeStatus.DEFERRED,
                                reason=M1DagRunnerReasonCode.CONCURRENCY_LIMIT,
                            )
                        )
                        continue
                    results.append(
                        _run_ready_node(
                            work_by_id[work_id],
                            node_state.readiness,
                            decision=decisions_by_work[work_id],
                            agent=agents_by_work[work_id],
                            request=request,
                            executor=self.executor,
                        )
                    )

        return M1DagRunnerResult(
            status=_runner_status(tuple(results)),
            dag_state=dag_state,
            node_results=tuple(results),
        )


def _run_ready_node(
    work: WorkItem,
    readiness: WorkDagNodeReadiness,
    *,
    decision: RoutingDecisionRecord,
    agent: AgentInstance,
    request: M1DagRunnerRequest,
    executor: M1Executor,
) -> M1DagRunnerNodeResult:
    decision_ref = ObjectReference.from_id(decision.decision_id)
    if decision.status is RoutingDecisionStatus.NO_ROUTE:
        return M1DagRunnerNodeResult(
            work_ref=ObjectReference.from_id(work.work_id),
            readiness=readiness,
            status=M1DagRunnerNodeStatus.BLOCKED,
            reason=M1DagRunnerReasonCode.NO_ROUTE,
            routing_decision_ref=decision_ref,
        )
    if (
        decision.selected_route is None
        or decision.selected_route.kind is not RouteCandidateKind.DETERMINISTIC_EXECUTOR
        or work.work_type not in decision.selected_route.supported_work_types
    ):
        return M1DagRunnerNodeResult(
            work_ref=ObjectReference.from_id(work.work_id),
            readiness=readiness,
            status=M1DagRunnerNodeStatus.BLOCKED,
            reason=M1DagRunnerReasonCode.ROUTE_NOT_EXECUTABLE,
            routing_decision_ref=decision_ref,
        )

    outcome = executor.execute(
        ExecutorRequest(
            work=work,
            dag_readiness=readiness,
            capability_resolutions=request.capability_resolutions_by_work_id.get(work.work_id, ()),
            agent_instance=agent,
            producer_ref=request.producer_ref,
            event_id=_required_id(request.event_ids_by_work_id, work.work_id, "event ID"),
            evidence_id=_required_id(
                request.evidence_ids_by_work_id,
                work.work_id,
                "evidence ID",
            ),
            occurred_at=request.occurred_at,
            observability_context=request.observability_context,
        )
    )
    status = {
        ExecutorOutcomeStatus.COMPLETED: M1DagRunnerNodeStatus.EXECUTED,
        ExecutorOutcomeStatus.BLOCKED: M1DagRunnerNodeStatus.BLOCKED,
        ExecutorOutcomeStatus.FAILED: M1DagRunnerNodeStatus.FAILED,
    }[outcome.status]
    reason = {
        ExecutorOutcomeStatus.COMPLETED: M1DagRunnerReasonCode.EXECUTOR_COMPLETED,
        ExecutorOutcomeStatus.BLOCKED: M1DagRunnerReasonCode.EXECUTOR_BLOCKED,
        ExecutorOutcomeStatus.FAILED: M1DagRunnerReasonCode.EXECUTOR_FAILED,
    }[outcome.status]
    return M1DagRunnerNodeResult(
        work_ref=ObjectReference.from_id(work.work_id),
        readiness=readiness,
        status=status,
        reason=reason,
        routing_decision_ref=decision_ref,
        executor_outcome=outcome,
    )


def _validate_selected_ready_nodes(
    dag_state: WorkDagState,
    *,
    work_by_id: Mapping[WorkId, WorkItem],
    decisions_by_work: Mapping[WorkId, RoutingDecisionRecord],
    agents_by_work: Mapping[WorkId, AgentInstance],
    request: M1DagRunnerRequest,
) -> None:
    selected_ready = tuple(
        state for state in dag_state.node_states if state.readiness is WorkDagNodeReadiness.READY
    )[: request.max_concurrency]
    for node_state in selected_ready:
        work_id = _work_id(node_state.work_ref)
        if work_id not in decisions_by_work:
            _raise_runner_error(
                M1DagRunnerError(
                    M1DagRunnerErrorCode.MISSING_ROUTING_DECISION,
                    "Ready DAG work requires a routing decision record.",
                    retryable=False,
                    operation="run_once",
                )
            )
        if work_id not in agents_by_work:
            _raise_runner_error(
                M1DagRunnerError(
                    M1DagRunnerErrorCode.MISSING_AGENT,
                    "Ready DAG work requires exactly one active agent instance.",
                    retryable=False,
                    operation="run_once",
                )
            )
        if (
            work_id not in request.event_ids_by_work_id
            or work_id not in request.evidence_ids_by_work_id
        ):
            _raise_runner_error(
                M1DagRunnerError(
                    M1DagRunnerErrorCode.MISSING_EXECUTOR_IDENTITY,
                    "Ready DAG work requires executor event and evidence identifiers.",
                    retryable=False,
                    operation="run_once",
                )
            )
        if work_id not in work_by_id:
            _invalid_request("DAG readiness referenced unknown work.")


def _runner_status(results: tuple[M1DagRunnerNodeResult, ...]) -> M1DagRunnerStatus:
    if any(result.status is M1DagRunnerNodeStatus.FAILED for result in results):
        return M1DagRunnerStatus.FAILED
    if any(result.status is M1DagRunnerNodeStatus.EXECUTED for result in results):
        return M1DagRunnerStatus.COMPLETED
    return M1DagRunnerStatus.BLOCKED


def _normalize_work_items(items: tuple[WorkItem, ...]) -> tuple[WorkItem, ...]:
    normalized = tuple(items)
    seen: set[WorkId] = set()
    for item in normalized:
        if not isinstance(item, WorkItem):
            msg = "work_items must contain WorkItem values"
            raise TypeError(msg)
        if item.work_id in seen:
            _invalid_request("Runner work items must have distinct work IDs.")
        seen.add(item.work_id)
    return tuple(sorted(normalized, key=lambda item: str(item.work_id)))


def _normalize_routing_decisions(
    decisions: tuple[RoutingDecisionRecord, ...],
) -> tuple[RoutingDecisionRecord, ...]:
    normalized = tuple(decisions)
    for decision in normalized:
        if not isinstance(decision, RoutingDecisionRecord):
            msg = "routing_decisions must contain RoutingDecisionRecord values"
            raise TypeError(msg)
    return tuple(sorted(normalized, key=lambda decision: str(decision.decision_id)))


def _normalize_agent_instances(instances: tuple[AgentInstance, ...]) -> tuple[AgentInstance, ...]:
    normalized = tuple(instances)
    for instance in normalized:
        if not isinstance(instance, AgentInstance):
            msg = "agent_instances must contain AgentInstance values"
            raise TypeError(msg)
    return tuple(sorted(normalized, key=lambda instance: str(instance.agent_instance_id)))


def _normalize_capability_resolution_map(
    value: Mapping[WorkId, tuple[CapabilityResolution, ...]],
) -> Mapping[WorkId, tuple[CapabilityResolution, ...]]:
    if not isinstance(value, Mapping):
        msg = "capability_resolutions_by_work_id must be a mapping"
        raise TypeError(msg)
    normalized: dict[WorkId, tuple[CapabilityResolution, ...]] = {}
    for work_id, resolutions in value.items():
        if not isinstance(work_id, WorkId):
            msg = "capability resolution map keys must be WorkId values"
            raise TypeError(msg)
        normalized_resolutions = tuple(resolutions)
        for resolution in normalized_resolutions:
            if not isinstance(resolution, CapabilityResolution):
                msg = "capability resolution map values must contain CapabilityResolution values"
                raise TypeError(msg)
        normalized[work_id] = normalized_resolutions
    return normalized


def _normalize_id_map[IdT](
    value: Mapping[WorkId, IdT],
    id_type: type[IdT],
    field_name: str,
) -> Mapping[WorkId, IdT]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be a mapping"
        raise TypeError(msg)
    normalized: dict[WorkId, IdT] = {}
    for work_id, identifier in value.items():
        if not isinstance(work_id, WorkId):
            msg = f"{field_name} keys must be WorkId values"
            raise TypeError(msg)
        if not isinstance(identifier, id_type):
            msg = f"{field_name} values must be {id_type.__name__} values"
            raise TypeError(msg)
        normalized[work_id] = identifier
    return normalized


def _routing_decisions_by_work(
    decisions: tuple[RoutingDecisionRecord, ...],
) -> Mapping[WorkId, RoutingDecisionRecord]:
    by_work: dict[WorkId, RoutingDecisionRecord] = {}
    for decision in decisions:
        work_id = _work_id(decision.work_ref)
        if work_id in by_work:
            _invalid_request("Runner routing decisions must have distinct work references.")
        by_work[work_id] = decision
    return by_work


def _active_agents_by_work(instances: tuple[AgentInstance, ...]) -> Mapping[WorkId, AgentInstance]:
    by_work: dict[WorkId, AgentInstance] = {}
    for instance in instances:
        if instance.state is not AgentInstanceState.ACTIVE:
            continue
        if instance.work_id in by_work:
            _invalid_request("Runner requires at most one active agent per work item.")
        by_work[instance.work_id] = instance
    return by_work


def _required_id[IdT](value: Mapping[WorkId, IdT], work_id: WorkId, label: str) -> IdT:
    try:
        return value[work_id]
    except KeyError:
        _raise_runner_error(
            M1DagRunnerError(
                M1DagRunnerErrorCode.MISSING_EXECUTOR_IDENTITY,
                f"Ready DAG work is missing required executor {label}.",
                retryable=False,
                operation="run_once",
            )
        )


def _require_ref_kind(reference: ObjectReference, expected: ReferenceKind) -> ObjectReference:
    if not isinstance(reference, ObjectReference):
        msg = "reference must be an ObjectReference"
        raise TypeError(msg)
    if reference.kind is not expected:
        _invalid_request(f"Runner reference must be {expected.value}.")
    return reference


def _work_id(reference: ObjectReference) -> WorkId:
    _require_ref_kind(reference, ReferenceKind.WORK)
    if not isinstance(reference.ref_id, WorkId):
        _invalid_request("Work reference ID must be a WorkId.")
    return reference.ref_id


def _invalid_request(message: str) -> NoReturn:
    _raise_runner_error(
        M1DagRunnerError(
            M1DagRunnerErrorCode.INVALID_REQUEST,
            message,
            retryable=False,
            operation="run_once",
        )
    )


def _raise_runner_error(error: M1DagRunnerError) -> NoReturn:
    raise error from None
