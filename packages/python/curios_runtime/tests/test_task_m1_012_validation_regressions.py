from __future__ import annotations

import pytest
from contract_fixtures import SCHEMA_V1, UTC_LATER, UTC_NOW, fixed_id, ref_for
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
    ReferenceKind,
    Result,
    TraceId,
    VerificationId,
    VerificationOutcome,
    WorkId,
    WorkItem,
    WorkItemState,
    to_json_compatible,
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


def test_first_terminal_attempt_stops_loop_and_later_attempt_cannot_override() -> None:
    work = _work()
    pass_evidence = _evidence(work, ordinal=1)
    fail_evidence = _evidence(work, ordinal=2)

    passed = BoundedM1VerificationLoop().verify(
        _request(
            work,
            max_iterations=3,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.PASSED,
                    evidence_refs=(pass_evidence,),
                ),
                M1VerificationAttempt(
                    outcome=VerificationOutcome.FAILED,
                    evidence_refs=(fail_evidence,),
                ),
            ),
        )
    )
    failed = BoundedM1VerificationLoop().verify(
        _request(
            work,
            max_iterations=3,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.FAILED,
                    evidence_refs=(fail_evidence,),
                ),
                M1VerificationAttempt(
                    outcome=VerificationOutcome.PASSED,
                    evidence_refs=(pass_evidence,),
                ),
            ),
        )
    )

    assert passed.completion_decision is M1VerificationCompletionDecision.APPROVED
    assert passed.reason is M1VerificationReasonCode.VERIFICATION_PASSED
    assert passed.iterations_used == 1
    assert passed.evidence_refs == (pass_evidence,)
    assert failed.completion_decision is M1VerificationCompletionDecision.REJECTED
    assert failed.reason is M1VerificationReasonCode.VERIFICATION_FAILED
    assert failed.iterations_used == 1
    assert failed.evidence_refs == (fail_evidence,)


def test_inconclusive_then_terminal_uses_terminal_attempt_within_bound() -> None:
    work = _work()
    inconclusive_evidence = _evidence(work, ordinal=1)
    terminal_evidence = _evidence(work, ordinal=2)

    result = BoundedM1VerificationLoop().verify(
        _request(
            work,
            max_iterations=2,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.INCONCLUSIVE,
                    evidence_refs=(inconclusive_evidence,),
                ),
                M1VerificationAttempt(
                    outcome=VerificationOutcome.PASSED,
                    evidence_refs=(terminal_evidence,),
                ),
            ),
        )
    )

    assert result.completion_decision is M1VerificationCompletionDecision.APPROVED
    assert result.iterations_used == 2
    assert result.evidence_refs == (terminal_evidence,)


def test_fewer_inconclusive_attempts_than_bound_defer_without_waiting_loop() -> None:
    work = _work()

    result = BoundedM1VerificationLoop().verify(
        _request(
            work,
            max_iterations=8,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.INCONCLUSIVE,
                    evidence_refs=(_evidence(work),),
                ),
            ),
        )
    )

    assert result.completion_decision is M1VerificationCompletionDecision.DEFERRED
    assert result.reason is M1VerificationReasonCode.VERIFICATION_INCONCLUSIVE
    assert result.iterations_used == 1


def test_runner_output_for_wrong_work_fails_before_evidence_can_approve() -> None:
    work = _work(0)
    other_work = _work(1)

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                runner_node_result=_executed_node(other_work),
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.PASSED,
                        evidence_refs=(_evidence(work),),
                    ),
                ),
            )
        )

    assert exc.value.code is M1VerificationErrorCode.INVALID_REQUEST


def test_completed_executor_status_with_failed_result_is_not_verifiable() -> None:
    work = _work()

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                runner_node_result=_executed_node(
                    work,
                    executor_status=ExecutorOutcomeStatus.COMPLETED,
                    result_status="failure",
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


@pytest.mark.parametrize(
    ("status", "reason"),
    (
        (M1DagRunnerNodeStatus.BLOCKED, M1DagRunnerReasonCode.NO_ROUTE),
        (M1DagRunnerNodeStatus.BLOCKED, M1DagRunnerReasonCode.ROUTE_NOT_EXECUTABLE),
        (M1DagRunnerNodeStatus.WAITING, M1DagRunnerReasonCode.WAITING_ON_DEPENDENCY),
        (M1DagRunnerNodeStatus.TERMINAL, M1DagRunnerReasonCode.TERMINAL_WORK),
        (M1DagRunnerNodeStatus.DEFERRED, M1DagRunnerReasonCode.CONCURRENCY_LIMIT),
        (M1DagRunnerNodeStatus.FAILED, M1DagRunnerReasonCode.EXECUTOR_FAILED),
    ),
)
def test_non_successful_runner_node_states_cannot_approve_completion(
    status: M1DagRunnerNodeStatus,
    reason: M1DagRunnerReasonCode,
) -> None:
    work = _work()

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                runner_node_result=M1DagRunnerNodeResult(
                    work_ref=ObjectReference.from_id(work.work_id),
                    readiness=WorkDagNodeReadiness.READY,
                    status=status,
                    reason=reason,
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


def test_same_evidence_id_with_different_fields_is_duplicate() -> None:
    work = _work()
    first = _evidence(work, ordinal=1)
    duplicate = EvidenceReference(
        evidence_id=first.evidence_id,
        kind=EvidenceKind.TEST_RESULT,
        subject_ref=ObjectReference.from_id(work.work_id),
        collected_at=UTC_LATER,
        summary="Different body, same identity.",
        trace_id=fixed_id(TraceId, ordinal=2),
    )

    with pytest.raises(M1VerificationError) as exc:
        BoundedM1VerificationLoop().verify(
            _request(
                work,
                attempts=(
                    M1VerificationAttempt(
                        outcome=VerificationOutcome.PASSED,
                        evidence_refs=(first, duplicate),
                    ),
                ),
            )
        )

    assert exc.value.code is M1VerificationErrorCode.INVALID_EVIDENCE


def test_wrong_kind_evidence_subject_does_not_satisfy_work_binding() -> None:
    work = _work()
    evidence = EvidenceReference(
        evidence_id=fixed_id(EvidenceId),
        kind=EvidenceKind.INSPECTION,
        subject_ref=ObjectReference(
            kind=ReferenceKind.EXECUTION,
            ref_id=fixed_id(ExecutionId),
        ),
        collected_at=UTC_NOW,
        summary="Evidence for an execution is not work-bound evidence.",
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

    assert exc.value.code is M1VerificationErrorCode.EVIDENCE_SUBJECT_MISMATCH


def test_subject_bound_evidence_is_trusted_without_extra_provenance_requirement() -> None:
    work = _work()
    suspicious_text = "to" + "ken=" + "super" + "-secret"
    evidence = EvidenceReference(
        evidence_id=fixed_id(EvidenceId),
        kind=EvidenceKind.LOG_EXCERPT,
        subject_ref=ObjectReference.from_id(work.work_id),
        collected_at=UTC_NOW,
        summary=f"{suspicious_text} upstream evidence text is preserved as evidence.",
        trace_id=fixed_id(TraceId, ordinal=9),
    )

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
    assert result.verification_ref is not None
    assert result.verification_ref.evidence_refs == (evidence,)
    assert result.event is not None
    assert suspicious_text not in str(result.event.payload)
    assert result.event.payload["evidence_ids"] == (str(evidence.evidence_id),)


def test_maximum_loop_bound_is_valid_and_maximum_plus_one_is_rejected() -> None:
    work = _work()
    attempts = tuple(
        M1VerificationAttempt(
            outcome=VerificationOutcome.INCONCLUSIVE,
            evidence_refs=(_evidence(work, ordinal=ordinal),),
        )
        for ordinal in range(8)
    )

    result = BoundedM1VerificationLoop().verify(_request(work, max_iterations=8, attempts=attempts))

    assert result.iterations_used == 8
    assert result.completion_decision is M1VerificationCompletionDecision.DEFERRED
    with pytest.raises(M1VerificationError) as exc:
        _request(
            work,
            max_iterations=8,
            attempts=(
                *attempts,
                M1VerificationAttempt(
                    outcome=VerificationOutcome.INCONCLUSIVE,
                    evidence_refs=(_evidence(work, ordinal=9),),
                ),
            ),
        )
    assert exc.value.code is M1VerificationErrorCode.INVALID_ITERATION_BOUND


def test_non_integer_loop_bound_is_rejected_without_unbounded_execution() -> None:
    work = _work()

    with pytest.raises(TypeError, match="max_iterations must be an integer"):
        _request(  # type: ignore[arg-type]
            work,
            max_iterations="8",
            attempts=(),
        )


def test_verification_event_payload_does_not_claim_state_mutation() -> None:
    work = _work()

    result = BoundedM1VerificationLoop().verify(
        _request(
            work,
            attempts=(
                M1VerificationAttempt(
                    outcome=VerificationOutcome.FAILED,
                    evidence_refs=(_evidence(work),),
                ),
            ),
        )
    )

    assert result.event is not None
    payload = result.event.payload
    assert payload["completion_decision"] == "REJECTED"
    assert "work_state" not in payload
    assert "dag_state" not in payload
    assert "completed" not in payload
    assert work.state is WorkItemState.READY


def test_repeated_equivalent_requests_have_stable_semantic_serialization() -> None:
    work = _work()
    request = _request(
        work,
        attempts=(
            M1VerificationAttempt(
                outcome=VerificationOutcome.PASSED,
                evidence_refs=(_evidence(work),),
            ),
        ),
    )

    first = BoundedM1VerificationLoop().verify(request)
    second = BoundedM1VerificationLoop().verify(request)

    assert first.to_json_compatible() == second.to_json_compatible()
    assert to_json_compatible(first.verification_ref) == to_json_compatible(second.verification_ref)


def test_validation_boundary_has_no_execution_persistence_or_api_authority() -> None:
    source = (
        __import__("pathlib").Path(__file__).parents[1]
        / "src"
        / "curios_runtime"
        / "m1_verification_loop.py"
    ).read_text(encoding="utf-8")

    forbidden = (
        "EventEvidenceRuntimeStore",
        "PersistenceStore",
        "M1Executor",
        "BoundedM1DagRunner(",
        "select_m1_route",
        "transition_work_item",
        "transition_agent_instance",
        "FastAPI",
        "APIRouter",
        "Ollama",
        ".generate(",
        ".chat(",
        ".embed(",
        "import httpx",
        "import requests",
        "from requests",
        "while True",
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
    result_status: str = "success",
) -> M1DagRunnerNodeResult:
    if result_status == "success":
        result = Result.success(
            {"work_id": str(work.work_id), "work_type": work.work_type},
            evidence_refs=(_evidence(work),),
        )
    else:
        result = _failure_result()
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


def _failure_result() -> Result[object]:
    return Result.failure(
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


def _evidence(work: WorkItem, *, ordinal: int = 0) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=fixed_id(EvidenceId, ordinal=ordinal),
        kind=EvidenceKind.INSPECTION,
        subject_ref=ObjectReference.from_id(work.work_id),
        collected_at=UTC_NOW,
        summary="Validation evidence fixture.",
        trace_id=fixed_id(TraceId),
    )


def _work(ordinal: int = 0) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal=ordinal),
        work_type="verify_bounded_change",
        title="Ready work",
        objective="Validate M1 verification loop.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
    )
