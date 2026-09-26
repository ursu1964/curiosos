"""M1 deterministic executor seam.

This module owns only the bounded executor request/outcome protocol and fixed
deterministic executor behavior authorized by TASK-M1-008. It does not schedule
work, mutate work/DAG/agent state, invoke providers, or call models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from curios_capability import (
    CapabilityResolution,
    CapabilityResolutionReason,
    CapabilityResolutionStatus,
)
from curios_contracts import (
    AgentInstance,
    AgentInstanceState,
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    EventEnvelope,
    EventId,
    EventType,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ObjectReference,
    ObservabilityContext,
    Result,
    SchemaVersion,
    UtcTimestamp,
    WorkItem,
    to_json_compatible,
)
from curios_dag import WorkDagNodeReadiness

M1_EXECUTOR_EVENT_TYPE = EventType("executor.deterministic.completed")
_SCHEMA_VERSION = SchemaVersion.parse("1.0.0")
_SUPPORTED_WORK_TYPES = frozenset(
    {
        "collect_recorded_context",
        "compose_recorded_summary",
        "verify_recorded_summary",
        "inspect_current_state",
        "apply_bounded_change",
        "verify_bounded_change",
    }
)


class ExecutorOutcomeStatus(StrEnum):
    """Stable TASK-M1-008 executor outcome statuses."""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ExecutorErrorCode(StrEnum):
    """Bounded deterministic executor failure categories."""

    AGENT_DEFINITION_MISMATCH = "AGENT_DEFINITION_MISMATCH"
    AGENT_NOT_ACTIVE = "AGENT_NOT_ACTIVE"
    AGENT_WORK_MISMATCH = "AGENT_WORK_MISMATCH"
    CAPABILITY_AMBIGUOUS = "CAPABILITY_AMBIGUOUS"
    CAPABILITY_MISSING = "CAPABILITY_MISSING"
    CAPABILITY_SHAPE_INVALID = "CAPABILITY_SHAPE_INVALID"
    EXECUTOR_FAILURE = "EXECUTOR_FAILURE"
    MISSING_AGENT_INSTANCE = "MISSING_AGENT_INSTANCE"
    UNSUPPORTED_WORK_TYPE = "UNSUPPORTED_WORK_TYPE"
    WORK_NOT_READY = "WORK_NOT_READY"


@dataclass(frozen=True, slots=True)
class ExecutorRequest:
    """Input to one deterministic M1 executor invocation."""

    work: WorkItem
    dag_readiness: WorkDagNodeReadiness
    capability_resolutions: tuple[CapabilityResolution, ...]
    agent_instance: AgentInstance | None
    producer_ref: ObjectReference
    event_id: EventId
    evidence_id: EvidenceId
    occurred_at: UtcTimestamp
    observability_context: ObservabilityContext

    def __post_init__(self) -> None:
        if not isinstance(self.work, WorkItem):
            msg = "work must be a WorkItem"
            raise TypeError(msg)
        object.__setattr__(self, "dag_readiness", WorkDagNodeReadiness(self.dag_readiness))
        object.__setattr__(
            self,
            "capability_resolutions",
            _require_capability_resolutions(self.capability_resolutions),
        )
        if self.agent_instance is not None and not isinstance(self.agent_instance, AgentInstance):
            msg = "agent_instance must be an AgentInstance when provided"
            raise TypeError(msg)
        if not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.event_id, EventId):
            msg = "event_id must be an EventId"
            raise TypeError(msg)
        if not isinstance(self.evidence_id, EvidenceId):
            msg = "evidence_id must be an EvidenceId"
            raise TypeError(msg)
        object.__setattr__(self, "occurred_at", UtcTimestamp(self.occurred_at))
        if not isinstance(self.observability_context, ObservabilityContext):
            msg = "observability_context must be an ObservabilityContext"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class ExecutorOutcome:
    """Canonical inert outcome from one deterministic M1 executor."""

    status: ExecutorOutcomeStatus
    result: Result[object]
    event: EventEnvelope
    evidence_refs: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", ExecutorOutcomeStatus(self.status))
        if not isinstance(self.result, Result):
            msg = "result must be a Result"
            raise TypeError(msg)
        if not isinstance(self.event, EventEnvelope):
            msg = "event must be an EventEnvelope"
            raise TypeError(msg)
        for evidence_ref in self.evidence_refs:
            if not isinstance(evidence_ref, EvidenceReference):
                msg = "evidence_refs must contain EvidenceReference values"
                raise TypeError(msg)

    def to_json_compatible(self) -> dict[str, object]:
        """Return a stable JSON-compatible executor outcome representation."""
        return {
            "status": self.status.value,
            "result": to_json_compatible(self.result),
            "event": to_json_compatible(self.event),
            "evidence_refs": to_json_compatible(self.evidence_refs),
        }


class M1Executor(Protocol):
    """Fakeable M1 executor seam."""

    def execute(self, request: ExecutorRequest) -> ExecutorOutcome:
        """Execute one bounded deterministic M1 request."""


@dataclass(frozen=True, slots=True)
class DeterministicM1Executor:
    """Fixed deterministic executor for TASK-M1-003 work proposal types."""

    def execute(self, request: ExecutorRequest) -> ExecutorOutcome:
        """Return a deterministic outcome without scheduling or provider authority."""
        if not isinstance(request, ExecutorRequest):
            msg = "request must be an ExecutorRequest"
            raise TypeError(msg)

        preflight_error = _preflight_error(request)
        if preflight_error is not None:
            return _failure_outcome(request, preflight_error)

        try:
            value = _execute_supported_work(request)
        except Exception as exc:
            return _failure_outcome(
                request,
                _contract_error(
                    request,
                    ExecutorErrorCode.EXECUTOR_FAILURE,
                    "Deterministic M1 executor failed.",
                    category=ErrorCategory.INTERNAL,
                    retryable=False,
                    details={"cause_type": type(exc).__name__},
                ),
            )

        evidence = EvidenceReference(
            evidence_id=request.evidence_id,
            kind=EvidenceKind.OTHER,
            subject_ref=ObjectReference.from_id(request.work.work_id),
            collected_at=request.occurred_at,
            summary=f"Deterministic M1 executor completed {request.work.work_type}.",
            trace_id=request.observability_context.trace_id,
        )
        result: Result[object] = Result.success(value, evidence_refs=(evidence,))
        event = _event(
            request,
            status=ExecutorOutcomeStatus.COMPLETED,
            payload={
                "status": ExecutorOutcomeStatus.COMPLETED.value,
                "work_id": str(request.work.work_id),
                "work_type": request.work.work_type,
                "evidence_ids": (str(evidence.evidence_id),),
            },
        )
        return ExecutorOutcome(
            status=ExecutorOutcomeStatus.COMPLETED,
            result=result,
            event=event,
            evidence_refs=(evidence,),
        )


def _preflight_error(request: ExecutorRequest) -> ContractError | None:
    if request.work.work_type not in _SUPPORTED_WORK_TYPES:
        return _contract_error(
            request,
            ExecutorErrorCode.UNSUPPORTED_WORK_TYPE,
            "Deterministic M1 executor does not support this work type.",
            category=ErrorCategory.VALIDATION,
            retryable=False,
            details={"work_type": request.work.work_type},
        )
    if request.dag_readiness is not WorkDagNodeReadiness.READY:
        return _contract_error(
            request,
            ExecutorErrorCode.WORK_NOT_READY,
            "Deterministic M1 executor requires READY DAG node state.",
            category=ErrorCategory.CONFLICT,
            retryable=False,
            details={"dag_readiness": request.dag_readiness.value},
        )

    capability_error = _capability_error(request)
    if capability_error is not None:
        return capability_error

    if request.agent_instance is None:
        return _contract_error(
            request,
            ExecutorErrorCode.MISSING_AGENT_INSTANCE,
            "Deterministic M1 executor requires a selected agent instance.",
            category=ErrorCategory.NOT_FOUND,
            retryable=False,
        )
    if request.agent_instance.work_id != request.work.work_id:
        return _contract_error(
            request,
            ExecutorErrorCode.AGENT_WORK_MISMATCH,
            "Selected agent instance is bound to different work.",
            category=ErrorCategory.CONFLICT,
            retryable=False,
            details={"agent_work_id": str(request.agent_instance.work_id)},
        )
    if request.agent_instance.state is not AgentInstanceState.ACTIVE:
        return _contract_error(
            request,
            ExecutorErrorCode.AGENT_NOT_ACTIVE,
            "Selected agent instance must already be ACTIVE.",
            category=ErrorCategory.CONFLICT,
            retryable=False,
            details={"agent_state": request.agent_instance.state.value},
        )
    for resolution in request.capability_resolutions:
        if resolution.agent_definition_ref is None:
            continue
        if resolution.agent_definition_ref.ref_id != request.agent_instance.agent_definition_id:
            return _contract_error(
                request,
                ExecutorErrorCode.AGENT_DEFINITION_MISMATCH,
                "Capability resolution selected a different agent definition.",
                category=ErrorCategory.CONFLICT,
                retryable=False,
                details={
                    "resolution_agent_definition_id": str(resolution.agent_definition_ref.ref_id),
                    "agent_definition_id": str(request.agent_instance.agent_definition_id),
                },
            )
    return None


def _capability_error(request: ExecutorRequest) -> ContractError | None:
    requirements = request.work.required_capabilities
    resolutions = request.capability_resolutions
    if len(requirements) != len(resolutions):
        return _contract_error(
            request,
            ExecutorErrorCode.CAPABILITY_SHAPE_INVALID,
            "Capability resolution count must match work requirements.",
            category=ErrorCategory.VALIDATION,
            retryable=False,
            details={
                "required_count": len(requirements),
                "resolution_count": len(resolutions),
            },
        )
    for index, (requirement, resolution) in enumerate(zip(requirements, resolutions, strict=True)):
        if resolution.requirement != requirement:
            return _contract_error(
                request,
                ExecutorErrorCode.CAPABILITY_SHAPE_INVALID,
                "Capability resolution requirement does not match work requirement.",
                category=ErrorCategory.VALIDATION,
                retryable=False,
                details={"index": index},
            )
        if resolution.status is CapabilityResolutionStatus.MATCHED:
            if resolution.reason is not CapabilityResolutionReason.EXACT_MATCH:
                return _contract_error(
                    request,
                    ExecutorErrorCode.CAPABILITY_SHAPE_INVALID,
                    "Matched capability resolution must use EXACT_MATCH reason.",
                    category=ErrorCategory.VALIDATION,
                    retryable=False,
                    details={"index": index, "reason": resolution.reason.value},
                )
            continue
        if resolution.status is CapabilityResolutionStatus.MISSING:
            return _contract_error(
                request,
                ExecutorErrorCode.CAPABILITY_MISSING,
                "Required capability is missing.",
                category=ErrorCategory.NOT_FOUND,
                retryable=False,
                details={"index": index, "reason": resolution.reason.value},
            )
        if resolution.status is CapabilityResolutionStatus.AMBIGUOUS:
            return _contract_error(
                request,
                ExecutorErrorCode.CAPABILITY_AMBIGUOUS,
                "Required capability resolution is ambiguous.",
                category=ErrorCategory.CONFLICT,
                retryable=False,
                details={"index": index, "reason": resolution.reason.value},
            )
    return None


def _execute_supported_work(request: ExecutorRequest) -> dict[str, object]:
    work = request.work
    match work.work_type:
        case "collect_recorded_context":
            return {
                "output_kind": "recorded_context",
                "work_id": str(work.work_id),
                "input_refs": to_json_compatible(work.inputs),
                "input_count": len(work.inputs),
            }
        case "compose_recorded_summary":
            return {
                "output_kind": "recorded_summary",
                "work_id": str(work.work_id),
                "summary": f"Deterministic recorded summary for {work.title}.",
                "dependency_count": len(work.dependencies),
            }
        case "verify_recorded_summary":
            return {
                "output_kind": "recorded_summary_verification",
                "work_id": str(work.work_id),
                "verified": True,
                "dependency_count": len(work.dependencies),
            }
        case "inspect_current_state":
            return {
                "output_kind": "current_state_inspection",
                "work_id": str(work.work_id),
                "input_refs": to_json_compatible(work.inputs),
                "input_count": len(work.inputs),
            }
        case "apply_bounded_change":
            return {
                "output_kind": "bounded_change_record",
                "work_id": str(work.work_id),
                "side_effects": "none",
                "change_recorded": True,
            }
        case "verify_bounded_change":
            return {
                "output_kind": "bounded_change_verification",
                "work_id": str(work.work_id),
                "verified": True,
                "dependency_count": len(work.dependencies),
            }
        case _:
            msg = "unreachable unsupported work type"
            raise AssertionError(msg)


def _failure_outcome(request: ExecutorRequest, error: ContractError) -> ExecutorOutcome:
    result: Result[object] = Result.failure((error,))
    event = _event(
        request,
        status=ExecutorOutcomeStatus.BLOCKED
        if error.category in {ErrorCategory.CONFLICT, ErrorCategory.NOT_FOUND}
        else ExecutorOutcomeStatus.FAILED,
        payload={
            "status": result.status.value,
            "work_id": str(request.work.work_id),
            "work_type": request.work.work_type,
            "error_code": str(error.error_code),
            "error_category": error.category.value,
        },
    )
    status = (
        ExecutorOutcomeStatus.BLOCKED
        if error.category in {ErrorCategory.CONFLICT, ErrorCategory.NOT_FOUND}
        else ExecutorOutcomeStatus.FAILED
    )
    return ExecutorOutcome(status=status, result=result, event=event)


def _event(
    request: ExecutorRequest,
    *,
    status: ExecutorOutcomeStatus,
    payload: dict[str, object],
) -> EventEnvelope:
    return EventEnvelope(
        event_id=request.event_id,
        event_type=M1_EXECUTOR_EVENT_TYPE,
        schema_version=_SCHEMA_VERSION,
        occurred_at=request.occurred_at,
        producer=request.producer_ref,
        subject_ref=ObjectReference.from_id(request.work.work_id),
        observability_context=request.observability_context,
        payload=payload,
        metadata={
            "task_id": "TASK-M1-008",
            "executor": "deterministic_m1",
            "outcome_status": status.value,
        },
    )


def _contract_error(
    request: ExecutorRequest,
    code: ExecutorErrorCode,
    message: str,
    *,
    category: ErrorCategory,
    retryable: bool,
    details: dict[str, object] | None = None,
) -> ContractError:
    return ContractError(
        error_code=ErrorCode(code.value),
        message=message,
        category=category,
        severity=ErrorSeverity.ERROR,
        retryable=retryable,
        subject_ref=ObjectReference.from_id(request.work.work_id),
        trace_id=request.observability_context.trace_id,
        details=details,
    )


def _require_capability_resolutions(
    resolutions: tuple[CapabilityResolution, ...],
) -> tuple[CapabilityResolution, ...]:
    normalized = tuple(resolutions)
    for resolution in normalized:
        if not isinstance(resolution, CapabilityResolution):
            msg = "capability_resolutions must contain CapabilityResolution values"
            raise TypeError(msg)
    return normalized
