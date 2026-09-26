from __future__ import annotations

import pytest
from contract_fixtures import SCHEMA_V1, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    AgentInstanceId,
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
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    Result,
    RuntimeEventType,
    TraceId,
    VerificationId,
    VerificationOutcome,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_dag import WorkDagNodeReadiness
from curios_runtime import (
    BoundedM1VerificationLoop,
    ExecutorOutcome,
    ExecutorOutcomeStatus,
    M1DagRunnerNodeResult,
    M1DagRunnerNodeStatus,
    M1DagRunnerReasonCode,
    M1VerificationAttempt,
    M1VerificationCompletionDecision,
    M1VerificationError,
    M1VerificationErrorCode,
    M1VerificationLoopRequest,
    M1VerificationReasonCode,
)


def test_passed_verification_approves_completion_and_binds_evidence() -> None:
    work = _work()
    evidence = _evidence(work, ordinal=2)

    result = BoundedM1VerificationLoop().verify(
        _request(
            work,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.PASSED,
                    evidence_refs=(evidence,),
                ),
            ),
        )
    )

    assert result.completion_decision is M1VerificationCompletionDecision.APPROVED
    assert result.reason is M1VerificationReasonCode.VERIFICATION_PASSED
    assert result.outcome is VerificationOutcome.PASSED
    assert result.iterations_used == 1
    assert result.verification_ref is not None
    assert result.verification_ref.subject_ref == ObjectReference.from_id(work.work_id)
    assert result.verification_ref.evidence_refs == (evidence,)
    assert result.event is not None
    assert result.event.event_type == RuntimeEventType.VERIFICATION_COMPLETED.value
    assert result.event.subject_ref == ObjectReference.from_id(work.work_id)
    assert result.event.payload["completion_decision"] == "APPROVED"
    assert result.event.payload["evidence_ids"] == (str(evidence.evidence_id),)


def test_failed_verification_rejects_completion_without_mutating_work() -> None:
    work = _work()
    evidence = _evidence(work)

    result = BoundedM1VerificationLoop().verify(
        _request(
            work,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.FAILED,
                    evidence_refs=(evidence,),
                ),
            ),
        )
    )

    assert result.completion_decision is M1VerificationCompletionDecision.REJECTED
    assert result.reason is M1VerificationReasonCode.VERIFICATION_FAILED
    assert result.outcome is VerificationOutcome.FAILED
    assert work.state is WorkItemState.READY


def test_inconclusive_attempts_exhaust_bound_without_completion() -> None:
    work = _work()
    first = _evidence(work, ordinal=2)
    second = _evidence(work, ordinal=1)

    result = BoundedM1VerificationLoop().verify(
        _request(
            work,
            max_iterations=2,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.INCONCLUSIVE,
                    evidence_refs=(first,),
                ),
                M1VerificationAttempt(
                    outcome=VerificationOutcome.NOT_EVALUATED,
                    evidence_refs=(second,),
                ),
            ),
        )
    )

    assert result.completion_decision is M1VerificationCompletionDecision.DEFERRED
    assert result.reason is M1VerificationReasonCode.VERIFICATION_INCONCLUSIVE
    assert result.outcome is VerificationOutcome.INCONCLUSIVE
    assert result.iterations_used == 2
    assert result.evidence_refs == (second,)


def test_no_attempts_are_inconclusive_without_event_or_record() -> None:
    work = _work()

    result = BoundedM1VerificationLoop().verify(_request(work, attempts=()))

    assert result.completion_decision is M1VerificationCompletionDecision.DEFERRED
    assert result.reason is M1VerificationReasonCode.NO_VERIFICATION_ATTEMPTS
    assert result.outcome is VerificationOutcome.INCONCLUSIVE
    assert result.iterations_used == 0
    assert result.verification_ref is None
    assert result.event is None
    assert result.evidence_refs == ()


@pytest.mark.parametrize("max_iterations", (0, -1, 9))
def test_invalid_iteration_bounds_fail_boundedly(max_iterations: int) -> None:
    work = _work()

    with pytest.raises(M1VerificationError) as exc:
        _request(work, attempts=(), max_iterations=max_iterations)

    assert exc.value.code is M1VerificationErrorCode.INVALID_ITERATION_BOUND
    assert exc.value.retryable is False


def test_attempts_cannot_exceed_configured_loop_bound() -> None:
    work = _work()

    with pytest.raises(M1VerificationError) as exc:
        _request(
            work,
            max_iterations=1,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.INCONCLUSIVE,
                    evidence_refs=(_evidence(work, ordinal=1),),
                ),
                M1VerificationAttempt(
                    outcome=VerificationOutcome.PASSED,
                    evidence_refs=(_evidence(work, ordinal=2),),
                ),
            ),
        )

    assert exc.value.code is M1VerificationErrorCode.INVALID_ITERATION_BOUND


def test_terminal_verification_attempt_requires_evidence() -> None:
    work = _work()

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.PASSED,
                        evidence_refs=(),
                    ),
                ),
            )
        )

    assert exc.value.code is M1VerificationErrorCode.MISSING_EVIDENCE


def test_evidence_must_be_bound_to_requested_work() -> None:
    work = _work()
    other_work = _work(ordinal=8)

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.PASSED,
                        evidence_refs=(_evidence(other_work),),
                    ),
                ),
            )
        )

    assert exc.value.code is M1VerificationErrorCode.EVIDENCE_SUBJECT_MISMATCH


def test_duplicate_evidence_is_rejected() -> None:
    work = _work()
    evidence = _evidence(work)

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.FAILED,
                        evidence_refs=(evidence, evidence),
                    ),
                ),
            )
        )

    assert exc.value.code is M1VerificationErrorCode.INVALID_EVIDENCE


@pytest.mark.parametrize(
    "node_result",
    (
        M1DagRunnerNodeResult(
            work_ref=ref_for(WorkId),
            readiness=WorkDagNodeReadiness.WAITING,
            status=M1DagRunnerNodeStatus.WAITING,
            reason=M1DagRunnerReasonCode.WAITING_ON_DEPENDENCY,
        ),
        M1DagRunnerNodeResult(
            work_ref=ref_for(WorkId),
            readiness=WorkDagNodeReadiness.READY,
            status=M1DagRunnerNodeStatus.BLOCKED,
            reason=M1DagRunnerReasonCode.NO_ROUTE,
        ),
    ),
)
def test_non_executed_runner_output_cannot_be_verified_as_completion(
    node_result: M1DagRunnerNodeResult,
) -> None:
    work = _work()

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                runner_node_result=node_result,
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.PASSED,
                        evidence_refs=(_evidence(work),),
                    ),
                ),
            )
        )

    assert exc.value.code is M1VerificationErrorCode.EXECUTION_NOT_COMPLETED


def test_executor_failure_cannot_be_verified_as_completion() -> None:
    work = _work()

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                runner_node_result=_executed_node(
                    work, executor_status=ExecutorOutcomeStatus.FAILED
                ),
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.PASSED,
                        evidence_refs=(_evidence(work),),
                    ),
                ),
            )
        )

    assert exc.value.code is M1VerificationErrorCode.EXECUTION_NOT_COMPLETED


def test_reversed_evidence_order_has_deterministic_binding_order() -> None:
    work = _work()
    earlier = _evidence(work, ordinal=1)
    later = _evidence(work, ordinal=2)

    first = BoundedM1VerificationLoop().verify(
        _request(
            work,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.PASSED,
                    evidence_refs=(later, earlier),
                ),
            ),
        )
    )
    second = BoundedM1VerificationLoop().verify(
        _request(
            work,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.PASSED,
                    evidence_refs=(earlier, later),
                ),
            ),
        )
    )

    assert first.to_json_compatible() == second.to_json_compatible()
    assert first.evidence_refs == (earlier, later)


def test_verification_public_error_surfaces_do_not_copy_secret_shaped_values() -> None:
    work = _work()
    secret_text = "token=super-secret password=hunter2"
    evidence = EvidenceReference(
        evidence_id=fixed_id(EvidenceId),
        kind=EvidenceKind.INSPECTION,
        subject_ref=ObjectReference.from_id(fixed_id(ExecutionId)),
        collected_at=UTC_NOW,
        summary=secret_text,
        trace_id=fixed_id(TraceId),
    )

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.PASSED,
                        evidence_refs=(evidence,),
                    ),
                ),
            )
        )

    public = exc.value.to_json_compatible()
    assert "super-secret" not in str(exc.value)
    assert "hunter2" not in str(public)


def test_verification_loop_has_no_provider_persistence_or_api_authority() -> None:
    source = (
        __import__("pathlib").Path(__file__).parents[1]
        / "src"
        / "curios_runtime"
        / "m1_verification_loop.py"
    ).read_text(encoding="utf-8")

    forbidden = (
        "from curios_ollama",
        "import curios_ollama",
        "Ollama",
        "import requests",
        "from requests",
        "httpx",
        "FastAPI",
        "EventEvidenceRuntimeStore",
        "M1Executor",
        "BoundedM1DagRunner(",
        "select_m1_route",
        "transition_work_item",
        "transition_agent_instance",
    )
    assert all(token not in source for token in forbidden)


def _request(
    work: WorkItem,
    *,
    attempts: tuple[M1VerificationAttempt, ...],
    max_iterations: int = 3,
    runner_node_result: M1DagRunnerNodeResult | None = None,
) -> M1VerificationLoopRequest:
    return M1VerificationLoopRequest(
        work=work,
        runner_node_result=runner_node_result or _executed_node(work),
        attempts=attempts,
        max_iterations=max_iterations,
        verification_id=fixed_id(VerificationId),
        event_id=fixed_id(EventId),
        verified_at=UTC_NOW,
        verifier_ref=ref_for(AgentInstanceId),
        producer_ref=ref_for(AgentInstanceId),
        observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
    )


def _executed_node(
    work: WorkItem,
    *,
    executor_status: ExecutorOutcomeStatus = ExecutorOutcomeStatus.COMPLETED,
) -> M1DagRunnerNodeResult:
    if executor_status is ExecutorOutcomeStatus.COMPLETED:
        result = Result.success(
            {"work_id": str(work.work_id), "work_type": work.work_type},
            evidence_refs=(_evidence(work),),
        )
    else:
        result = Result.failure(
            errors=(
                ContractError(
                    error_code=ErrorCode("EXECUTOR_FAILED"),
                    message="Executor failed.",
                    category=ErrorCategory.INTERNAL,
                    severity=ErrorSeverity.ERROR,
                    retryable=False,
                ),
            ),
        )
    event = EventEnvelope(
        event_id=fixed_id(EventId, ordinal=3),
        event_type=EventType("executor.deterministic.completed"),
        schema_version=SCHEMA_V1,
        occurred_at=UTC_NOW,
        producer=ref_for(AgentInstanceId),
        subject_ref=ObjectReference.from_id(work.work_id),
        observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
        payload={"status": executor_status.value, "work_id": str(work.work_id)},
    )
    return M1DagRunnerNodeResult(
        work_ref=ObjectReference.from_id(work.work_id),
        readiness=WorkDagNodeReadiness.READY,
        status=(
            M1DagRunnerNodeStatus.EXECUTED
            if executor_status is ExecutorOutcomeStatus.COMPLETED
            else M1DagRunnerNodeStatus.FAILED
        ),
        reason=(
            M1DagRunnerReasonCode.EXECUTOR_COMPLETED
            if executor_status is ExecutorOutcomeStatus.COMPLETED
            else M1DagRunnerReasonCode.EXECUTOR_FAILED
        ),
        executor_outcome=ExecutorOutcome(
            status=executor_status,
            result=result,
            event=event,
            evidence_refs=(_evidence(work),),
        ),
    )


def _evidence(work: WorkItem, *, ordinal: int = 0) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=fixed_id(EvidenceId, ordinal=ordinal),
        kind=EvidenceKind.INSPECTION,
        subject_ref=ObjectReference.from_id(work.work_id),
        collected_at=UTC_NOW,
        summary="Verification evidence fixture.",
        trace_id=fixed_id(TraceId),
    )


def _work(ordinal: int = 0) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal=ordinal),
        work_type="verify_bounded_change",
        title="Ready work",
        objective="Exercise M1 verification loop.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
    )
