"""Bounded M1 verification loop and evidence binding.

TASK-M1-012 owns verification gating over recorded M1 runner output. It does
not execute work, persist state, evaluate policy, invoke providers, or expose
API behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import NoReturn

from curios_contracts import (
    EventEnvelope,
    EventId,
    EvidenceId,
    EvidenceReference,
    ObjectReference,
    ObservabilityContext,
    ReferenceKind,
    ResultStatus,
    RuntimeEventType,
    SchemaVersion,
    UtcTimestamp,
    VerificationId,
    VerificationOutcome,
    VerificationReference,
    WorkId,
    WorkItem,
    to_json_compatible,
)

from curios_runtime.executor_seam import ExecutorOutcomeStatus
from curios_runtime.m1_bounded_dag_runner import (
    M1DagRunnerNodeResult,
    M1DagRunnerNodeStatus,
)

_MAX_VERIFICATION_ITERATIONS = 8
_SCHEMA_VERSION = SchemaVersion.parse("1.0.0")


class M1VerificationCompletionDecision(StrEnum):
    """Completion gate decision derived from verification outcome."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


class M1VerificationReasonCode(StrEnum):
    """Bounded verification-loop reasons."""

    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    VERIFICATION_INCONCLUSIVE = "VERIFICATION_INCONCLUSIVE"
    NO_VERIFICATION_ATTEMPTS = "NO_VERIFICATION_ATTEMPTS"


class M1VerificationErrorCode(StrEnum):
    """Bounded validation errors for malformed verification requests."""

    EXECUTION_NOT_COMPLETED = "EXECUTION_NOT_COMPLETED"
    EVIDENCE_SUBJECT_MISMATCH = "EVIDENCE_SUBJECT_MISMATCH"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    INVALID_ITERATION_BOUND = "INVALID_ITERATION_BOUND"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"


class M1VerificationError(RuntimeError):
    """Bounded M1 verification error without native/upstream detail leakage."""

    def __init__(
        self,
        code: M1VerificationErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
    ) -> None:
        super().__init__(message)
        self.code = M1VerificationErrorCode(code)
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
class M1VerificationAttempt:
    """One recorded verification attempt supplied to the bounded loop."""

    outcome: VerificationOutcome
    evidence_refs: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcome", VerificationOutcome(self.outcome))
        object.__setattr__(self, "evidence_refs", _normalize_evidence_refs(self.evidence_refs))

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "outcome": self.outcome.value,
            "evidence_refs": to_json_compatible(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class M1VerificationLoopRequest:
    """Input for one deterministic M1 verification loop pass."""

    work: WorkItem
    runner_node_result: M1DagRunnerNodeResult
    attempts: tuple[M1VerificationAttempt, ...]
    max_iterations: int
    verification_id: VerificationId
    event_id: EventId
    verified_at: UtcTimestamp
    verifier_ref: ObjectReference
    producer_ref: ObjectReference
    observability_context: ObservabilityContext

    def __post_init__(self) -> None:
        if not isinstance(self.work, WorkItem):
            msg = "work must be a WorkItem"
            raise TypeError(msg)
        if not isinstance(self.runner_node_result, M1DagRunnerNodeResult):
            msg = "runner_node_result must be an M1DagRunnerNodeResult"
            raise TypeError(msg)
        attempts = tuple(self.attempts)
        for attempt in attempts:
            if not isinstance(attempt, M1VerificationAttempt):
                msg = "attempts must contain M1VerificationAttempt values"
                raise TypeError(msg)
        object.__setattr__(self, "attempts", attempts)
        if not isinstance(self.max_iterations, int):
            msg = "max_iterations must be an integer"
            raise TypeError(msg)
        if self.max_iterations < 1 or self.max_iterations > _MAX_VERIFICATION_ITERATIONS:
            _raise_verification_error(
                M1VerificationError(
                    M1VerificationErrorCode.INVALID_ITERATION_BOUND,
                    "M1 verification loop iterations must be between 1 and 8.",
                    retryable=False,
                    operation="construct_request",
                )
            )
        if len(attempts) > self.max_iterations:
            _raise_verification_error(
                M1VerificationError(
                    M1VerificationErrorCode.INVALID_ITERATION_BOUND,
                    "M1 verification attempts must not exceed the configured iteration bound.",
                    retryable=False,
                    operation="construct_request",
                )
            )
        if not isinstance(self.verification_id, VerificationId):
            msg = "verification_id must be a VerificationId"
            raise TypeError(msg)
        if not isinstance(self.event_id, EventId):
            msg = "event_id must be an EventId"
            raise TypeError(msg)
        object.__setattr__(self, "verified_at", UtcTimestamp(self.verified_at))
        if not isinstance(self.verifier_ref, ObjectReference):
            msg = "verifier_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.observability_context, ObservabilityContext):
            msg = "observability_context must be an ObservabilityContext"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class M1VerificationLoopResult:
    """Outcome of one bounded verification loop pass."""

    completion_decision: M1VerificationCompletionDecision
    reason: M1VerificationReasonCode
    work_ref: ObjectReference
    outcome: VerificationOutcome
    iterations_used: int
    verification_ref: VerificationReference | None = None
    event: EventEnvelope | None = None
    evidence_refs: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "completion_decision",
            M1VerificationCompletionDecision(self.completion_decision),
        )
        object.__setattr__(self, "reason", M1VerificationReasonCode(self.reason))
        object.__setattr__(self, "work_ref", _require_ref_kind(self.work_ref, ReferenceKind.WORK))
        object.__setattr__(self, "outcome", VerificationOutcome(self.outcome))
        if self.iterations_used < 0 or self.iterations_used > _MAX_VERIFICATION_ITERATIONS:
            msg = "iterations_used must be within the M1 verification loop bound"
            raise ValueError(msg)
        if self.verification_ref is not None and not isinstance(
            self.verification_ref,
            VerificationReference,
        ):
            msg = "verification_ref must be a VerificationReference when provided"
            raise TypeError(msg)
        if self.event is not None and not isinstance(self.event, EventEnvelope):
            msg = "event must be an EventEnvelope when provided"
            raise TypeError(msg)
        object.__setattr__(self, "evidence_refs", _normalize_evidence_refs(self.evidence_refs))

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "completion_decision": self.completion_decision.value,
            "reason": self.reason.value,
            "work_ref": to_json_compatible(self.work_ref),
            "outcome": self.outcome.value,
            "iterations_used": self.iterations_used,
            "verification_ref": to_json_compatible(self.verification_ref),
            "event": to_json_compatible(self.event),
            "evidence_refs": to_json_compatible(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class BoundedM1VerificationLoop:
    """Gate recorded execution completion on bounded verification evidence."""

    def verify(self, request: M1VerificationLoopRequest) -> M1VerificationLoopResult:
        """Return a deterministic completion gate without persistence or execution."""
        if not isinstance(request, M1VerificationLoopRequest):
            msg = "request must be an M1VerificationLoopRequest"
            raise TypeError(msg)

        _validate_recorded_execution(request)
        if not request.attempts:
            return M1VerificationLoopResult(
                completion_decision=M1VerificationCompletionDecision.DEFERRED,
                reason=M1VerificationReasonCode.NO_VERIFICATION_ATTEMPTS,
                work_ref=ObjectReference.from_id(request.work.work_id),
                outcome=VerificationOutcome.INCONCLUSIVE,
                iterations_used=0,
            )

        selected_attempt = request.attempts[-1]
        iterations_used = 0
        for attempt in request.attempts:
            iterations_used += 1
            _validate_attempt_evidence(request, attempt)
            selected_attempt = attempt
            if attempt.outcome in {VerificationOutcome.PASSED, VerificationOutcome.FAILED}:
                break

        evidence_refs = selected_attempt.evidence_refs
        outcome = _final_outcome(selected_attempt.outcome)
        completion_decision = _completion_decision(outcome)
        reason = _reason(outcome)
        verification_ref = VerificationReference(
            verification_id=request.verification_id,
            subject_ref=ObjectReference.from_id(request.work.work_id),
            outcome=outcome,
            evidence_refs=evidence_refs,
            verified_at=request.verified_at,
            verifier_ref=request.verifier_ref,
        )
        event = _verification_event(
            request,
            verification_ref=verification_ref,
            completion_decision=completion_decision,
            reason=reason,
            evidence_refs=evidence_refs,
            iterations_used=iterations_used,
        )
        return M1VerificationLoopResult(
            completion_decision=completion_decision,
            reason=reason,
            work_ref=ObjectReference.from_id(request.work.work_id),
            outcome=outcome,
            iterations_used=iterations_used,
            verification_ref=verification_ref,
            event=event,
            evidence_refs=evidence_refs,
        )


def _validate_recorded_execution(request: M1VerificationLoopRequest) -> None:
    work_ref = ObjectReference.from_id(request.work.work_id)
    if request.runner_node_result.work_ref != work_ref:
        _raise_verification_error(
            M1VerificationError(
                M1VerificationErrorCode.INVALID_REQUEST,
                "Verification requires runner output for the requested work.",
                retryable=False,
                operation="verify",
            )
        )
    if request.runner_node_result.status is not M1DagRunnerNodeStatus.EXECUTED:
        _execution_not_completed()
    outcome = request.runner_node_result.executor_outcome
    if outcome is None or outcome.status is not ExecutorOutcomeStatus.COMPLETED:
        _execution_not_completed()
    if outcome.result.status is not ResultStatus.SUCCESS:
        _execution_not_completed()


def _validate_attempt_evidence(
    request: M1VerificationLoopRequest,
    attempt: M1VerificationAttempt,
) -> None:
    if (
        attempt.outcome in {VerificationOutcome.PASSED, VerificationOutcome.FAILED}
        and not attempt.evidence_refs
    ):
        _raise_verification_error(
            M1VerificationError(
                M1VerificationErrorCode.MISSING_EVIDENCE,
                "Verification completion requires bound evidence.",
                retryable=False,
                operation="verify",
            )
        )
    if attempt.evidence_refs:
        _require_evidence_bound_to_work(request.work.work_id, attempt.evidence_refs)


def _require_evidence_bound_to_work(
    work_id: WorkId,
    evidence_refs: tuple[EvidenceReference, ...],
) -> None:
    work_ref = ObjectReference.from_id(work_id)
    seen: set[EvidenceId] = set()
    for evidence_ref in evidence_refs:
        if evidence_ref.evidence_id in seen:
            _raise_verification_error(
                M1VerificationError(
                    M1VerificationErrorCode.INVALID_EVIDENCE,
                    "Verification evidence references must be distinct.",
                    retryable=False,
                    operation="verify",
                )
            )
        seen.add(evidence_ref.evidence_id)
        if evidence_ref.subject_ref != work_ref:
            _raise_verification_error(
                M1VerificationError(
                    M1VerificationErrorCode.EVIDENCE_SUBJECT_MISMATCH,
                    "Verification evidence must be bound to the requested work.",
                    retryable=False,
                    operation="verify",
                )
            )


def _verification_event(
    request: M1VerificationLoopRequest,
    *,
    verification_ref: VerificationReference,
    completion_decision: M1VerificationCompletionDecision,
    reason: M1VerificationReasonCode,
    evidence_refs: tuple[EvidenceReference, ...],
    iterations_used: int,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=request.event_id,
        event_type=RuntimeEventType.VERIFICATION_COMPLETED.value,
        schema_version=_SCHEMA_VERSION,
        occurred_at=request.verified_at,
        producer=request.producer_ref,
        subject_ref=ObjectReference.from_id(request.work.work_id),
        observability_context=request.observability_context,
        payload={
            "completion_decision": completion_decision.value,
            "evidence_ids": tuple(str(evidence.evidence_id) for evidence in evidence_refs),
            "iterations_used": iterations_used,
            "outcome": verification_ref.outcome.value,
            "reason": reason.value,
            "verification_id": str(verification_ref.verification_id),
            "work_id": str(request.work.work_id),
        },
    )


def _normalize_evidence_refs(
    evidence_refs: tuple[EvidenceReference, ...],
) -> tuple[EvidenceReference, ...]:
    normalized = tuple(evidence_refs)
    for evidence_ref in normalized:
        if not isinstance(evidence_ref, EvidenceReference):
            msg = "evidence_refs must contain EvidenceReference values"
            raise TypeError(msg)
    return tuple(sorted(normalized, key=lambda evidence: str(evidence.evidence_id)))


def _completion_decision(outcome: VerificationOutcome) -> M1VerificationCompletionDecision:
    if outcome is VerificationOutcome.PASSED:
        return M1VerificationCompletionDecision.APPROVED
    if outcome is VerificationOutcome.FAILED:
        return M1VerificationCompletionDecision.REJECTED
    return M1VerificationCompletionDecision.DEFERRED


def _final_outcome(outcome: VerificationOutcome) -> VerificationOutcome:
    if outcome is VerificationOutcome.NOT_EVALUATED:
        return VerificationOutcome.INCONCLUSIVE
    return outcome


def _reason(outcome: VerificationOutcome) -> M1VerificationReasonCode:
    if outcome is VerificationOutcome.PASSED:
        return M1VerificationReasonCode.VERIFICATION_PASSED
    if outcome is VerificationOutcome.FAILED:
        return M1VerificationReasonCode.VERIFICATION_FAILED
    return M1VerificationReasonCode.VERIFICATION_INCONCLUSIVE


def _execution_not_completed() -> NoReturn:
    _raise_verification_error(
        M1VerificationError(
            M1VerificationErrorCode.EXECUTION_NOT_COMPLETED,
            "Verification requires a completed recorded executor outcome.",
            retryable=False,
            operation="verify",
        )
    )


def _require_ref_kind(reference: ObjectReference, expected: ReferenceKind) -> ObjectReference:
    if not isinstance(reference, ObjectReference):
        msg = "reference must be an ObjectReference"
        raise TypeError(msg)
    if reference.kind is not expected:
        _raise_verification_error(
            M1VerificationError(
                M1VerificationErrorCode.INVALID_REQUEST,
                f"Verification reference must be {expected.value}.",
                retryable=False,
                operation="verify",
            )
        )
    return reference


def _raise_verification_error(error: M1VerificationError) -> NoReturn:
    raise error from None
