"""Single-step M0 work runtime service.

This module coordinates the frozen M0 policy, work repository, and
event/evidence store boundaries for one local work step. It intentionally
does not implement scheduling, provider inventory collection, retries, model
routing, or agent runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import NoReturn, Protocol

from curios_contracts import (
    EffectClassification,
    EventEnvelope,
    EventId,
    EvidenceReference,
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    ObjectReference,
    ObservabilityContext,
    PolicyDecision,
    Principal,
    Result,
    ResultStatus,
    RuntimeEventType,
    SchemaVersion,
    UtcTimestamp,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_policy import (
    M0PolicyEvaluationRequest,
    MinimalM0PolicyEvaluator,
)

from curios_runtime.event_evidence_store import (
    EventEvidenceRuntimeStore,
    RuntimeStoreError,
)
from curios_runtime.work_repository import (
    M0WorkRepository,
    RepositoryError,
    StoredExecutionRecord,
    StoredWorkItem,
)

_SCHEMA_VERSION = SchemaVersion.parse("1.0.0")
_READ_ONLY_EFFECT = (EffectClassification.READ_ONLY,)
_STARTABLE_WORK_STATES = frozenset({WorkItemState.CREATED, WorkItemState.READY})


class SingleStepRuntimeErrorCode(StrEnum):
    """Bounded TASK-M0-006 runtime-service failure categories."""

    CONFLICT = "CONFLICT"
    EXECUTOR_FAILURE = "EXECUTOR_FAILURE"
    ILLEGAL_STATE = "ILLEGAL_STATE"
    INVALID_EXECUTOR_RESULT = "INVALID_EXECUTOR_RESULT"
    NOT_FOUND = "NOT_FOUND"
    POLICY_FAILURE = "POLICY_FAILURE"
    POLICY_NOT_AUTHORIZED = "POLICY_NOT_AUTHORIZED"
    REPOSITORY_FAILURE = "REPOSITORY_FAILURE"
    RUNTIME_STORE_FAILURE = "RUNTIME_STORE_FAILURE"


class SingleStepRuntimeStatus(StrEnum):
    """Stable result statuses for one M0 runtime step."""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class SingleStepRuntimeError(RuntimeError):
    """Curios-owned runtime-service error without lower-layer leakage."""

    def __init__(
        self,
        code: SingleStepRuntimeErrorCode,
        message: str,
        *,
        operation: str,
        retryable: bool = False,
        detail: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = SingleStepRuntimeErrorCode(code)
        self.operation = operation
        self.retryable = retryable
        self.detail = dict(detail or {})

    def to_json_compatible(self) -> dict[str, object]:
        """Return bounded, non-native runtime-service error details."""
        serialized: dict[str, object] = {
            "code": self.code.value,
            "message": str(self),
            "operation": self.operation,
            "retryable": self.retryable,
        }
        if self.detail:
            serialized["detail"] = dict(self.detail)
        return serialized


@dataclass(frozen=True, slots=True)
class SingleStepRuntimeRequest:
    """Input for one bounded M0 runtime step."""

    work_id: WorkId
    principal: Principal
    producer_ref: ObjectReference
    executor_ref: ObjectReference
    scope: str
    resource_refs: tuple[ObjectReference, ...] = ()
    requested_effects: tuple[EffectClassification, ...] = _READ_ONLY_EFFECT
    policy_state_known: bool = True
    observability_context: ObservabilityContext | None = None
    occurred_at: UtcTimestamp | None = None
    execution_id: ExecutionId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.work_id, WorkId):
            msg = "work_id must be a WorkId"
            raise TypeError(msg)
        if not isinstance(self.principal, Principal):
            msg = "principal must be a Principal"
            raise TypeError(msg)
        if not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.executor_ref, ObjectReference):
            msg = "executor_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.scope, str):
            msg = "scope must be a string"
            raise TypeError(msg)
        _require_object_refs(self.resource_refs, "resource_refs")
        object.__setattr__(
            self,
            "requested_effects",
            tuple(EffectClassification(effect) for effect in self.requested_effects),
        )
        if not self.requested_effects:
            msg = "requested_effects must contain at least one effect"
            raise ValueError(msg)
        if not isinstance(self.policy_state_known, bool):
            msg = "policy_state_known must be a bool"
            raise TypeError(msg)
        if self.observability_context is not None and not isinstance(
            self.observability_context,
            ObservabilityContext,
        ):
            msg = "observability_context must be an ObservabilityContext when provided"
            raise TypeError(msg)
        if self.occurred_at is not None:
            object.__setattr__(self, "occurred_at", UtcTimestamp(self.occurred_at))
        if self.execution_id is not None and not isinstance(self.execution_id, ExecutionId):
            msg = "execution_id must be an ExecutionId when provided"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class SingleStepExecutionRequest:
    """Curios-owned fakeable executor input for TASK-M0-007."""

    work: WorkItem
    execution: ExecutionRecord
    policy_decision: PolicyDecision
    observability_context: ObservabilityContext


@dataclass(frozen=True, slots=True)
class SingleStepExecutionOutcome:
    """Executor seam output consumed by the runtime service."""

    result: Result[object]
    evidence_refs: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.result, Result):
            msg = "result must be a Result"
            raise TypeError(msg)
        for evidence_ref in self.evidence_refs:
            if not isinstance(evidence_ref, EvidenceReference):
                msg = "evidence_refs must contain EvidenceReference values"
                raise TypeError(msg)


class SingleStepExecutor(Protocol):
    """Fakeable executor seam; TASK-M0-007 owns concrete provider behavior."""

    def execute(self, request: SingleStepExecutionRequest) -> SingleStepExecutionOutcome:
        """Execute one already-authorized M0 work step."""


@dataclass(frozen=True, slots=True)
class SingleStepRuntimeResult:
    """Outcome of one runtime-service step."""

    status: SingleStepRuntimeStatus
    work: StoredWorkItem
    policy_decision: PolicyDecision
    execution: StoredExecutionRecord | None = None
    executor_result: Result[object] | None = None
    events: tuple[EventEnvelope, ...] = ()
    evidence_refs: tuple[EvidenceReference, ...] = ()
    recording_errors: tuple[SingleStepRuntimeError, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", SingleStepRuntimeStatus(self.status))
        if not isinstance(self.work, StoredWorkItem):
            msg = "work must be a StoredWorkItem"
            raise TypeError(msg)
        if not isinstance(self.policy_decision, PolicyDecision):
            msg = "policy_decision must be a PolicyDecision"
            raise TypeError(msg)
        if self.execution is not None and not isinstance(self.execution, StoredExecutionRecord):
            msg = "execution must be a StoredExecutionRecord when provided"
            raise TypeError(msg)
        if self.executor_result is not None and not isinstance(self.executor_result, Result):
            msg = "executor_result must be a Result when provided"
            raise TypeError(msg)
        for event in self.events:
            if not isinstance(event, EventEnvelope):
                msg = "events must contain EventEnvelope values"
                raise TypeError(msg)
        for evidence_ref in self.evidence_refs:
            if not isinstance(evidence_ref, EvidenceReference):
                msg = "evidence_refs must contain EvidenceReference values"
                raise TypeError(msg)
        for error in self.recording_errors:
            if not isinstance(error, SingleStepRuntimeError):
                msg = "recording_errors must contain SingleStepRuntimeError values"
                raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class SingleStepRuntimeService:
    """Coordinate one authorized M0 work step through frozen boundaries."""

    work_repository: M0WorkRepository
    event_store: EventEvidenceRuntimeStore
    policy_evaluator: MinimalM0PolicyEvaluator
    executor: SingleStepExecutor

    def run_once(self, request: SingleStepRuntimeRequest) -> SingleStepRuntimeResult:
        """Run one bounded work item step if minimal M0 policy authorizes it."""
        if not isinstance(request, SingleStepRuntimeRequest):
            msg = "request must be a SingleStepRuntimeRequest"
            raise TypeError(msg)

        observed_at = request.occurred_at or UtcTimestamp.now()
        stored_work = self._read_work(request.work_id)
        policy_decision = self._evaluate_policy(stored_work.item, request, observed_at)
        policy_event = self._append_event(
            RuntimeEventType.POLICY_EVALUATED,
            work=stored_work.item,
            request=request,
            occurred_at=observed_at,
            payload={
                "work_id": str(stored_work.item.work_id),
                "outcome": policy_decision.outcome.value,
                "is_authorizing": policy_decision.is_authorizing,
            },
        )

        if not policy_decision.is_authorizing:
            return SingleStepRuntimeResult(
                status=SingleStepRuntimeStatus.BLOCKED,
                work=stored_work,
                policy_decision=policy_decision,
                events=(policy_event,),
            )

        self._require_startable(stored_work.item)
        running_work = self._start_work(stored_work, observed_at)
        running_execution = self._start_execution(request, running_work.item, observed_at)
        started_event = self._append_event(
            RuntimeEventType.EXECUTION_STARTED,
            work=running_work.item,
            request=request,
            occurred_at=observed_at,
            execution=running_execution.record,
            payload={
                "work_id": str(running_work.item.work_id),
                "execution_id": str(running_execution.record.execution_id),
            },
        )

        execution_request = SingleStepExecutionRequest(
            work=running_work.item,
            execution=running_execution.record,
            policy_decision=policy_decision,
            observability_context=_observability_for(
                request,
                running_work.item.work_id,
                running_execution.record.execution_id,
            ),
        )
        executor_error: Exception | None = None
        try:
            execution_outcome = self.executor.execute(execution_request)
        except Exception as exc:
            executor_error = exc
        if executor_error is not None:
            error = SingleStepRuntimeError(
                SingleStepRuntimeErrorCode.EXECUTOR_FAILURE,
                "Single-step executor failed.",
                operation="execute",
                retryable=False,
                detail={"cause_type": type(executor_error).__name__},
            )
            return self._finalize_executor_failure(
                primary_error=error,
                executor_result=None,
                running_execution=running_execution,
                running_work=running_work,
                request=request,
                occurred_at=observed_at,
                reason="executor raised bounded runtime failure",
                prior_events=(policy_event, started_event),
                policy_decision=policy_decision,
                evidence_refs=(),
            )

        if not isinstance(execution_outcome, SingleStepExecutionOutcome):
            error = SingleStepRuntimeError(
                SingleStepRuntimeErrorCode.INVALID_EXECUTOR_RESULT,
                "Single-step executor returned an invalid outcome.",
                operation="execute",
            )
            return self._finalize_executor_failure(
                primary_error=error,
                executor_result=None,
                running_execution=running_execution,
                running_work=running_work,
                request=request,
                occurred_at=observed_at,
                reason="executor returned invalid outcome",
                prior_events=(policy_event, started_event),
                policy_decision=policy_decision,
                evidence_refs=(),
            )

        if execution_outcome.result.status is ResultStatus.FAILURE:
            return self._finalize_executor_failure(
                primary_error=None,
                executor_result=execution_outcome.result,
                running_execution=running_execution,
                running_work=running_work,
                request=request,
                occurred_at=observed_at,
                reason="executor returned failure result",
                prior_events=(policy_event, started_event),
                policy_decision=policy_decision,
                evidence_refs=execution_outcome.evidence_refs,
            )

        evidence_events: list[EventEnvelope] = []
        for evidence_ref in execution_outcome.evidence_refs:
            evidence_event, evidence_error = self._try_record_evidence(
                evidence_ref,
                request,
                running_work.item,
                observed_at,
            )
            if evidence_error is not None:
                self._finalize_post_success_failure(
                    primary_error=evidence_error,
                    running_execution=running_execution,
                    running_work=running_work,
                    request=request,
                    occurred_at=observed_at,
                    reason="executor succeeded but evidence recording failed",
                )
            if evidence_event is not None:
                evidence_events.append(evidence_event)

        completed_execution, execution_error = self._try_transition_execution(
            running_execution,
            ExecutionState.SUCCEEDED,
            observed_at,
        )
        if execution_error is not None or completed_execution is None:
            self._finalize_post_success_failure(
                primary_error=execution_error
                or SingleStepRuntimeError(
                    SingleStepRuntimeErrorCode.REPOSITORY_FAILURE,
                    "Work runtime repository operation failed.",
                    operation="transition_execution",
                ),
                running_execution=running_execution,
                running_work=running_work,
                request=request,
                occurred_at=observed_at,
                reason="executor succeeded but execution finalization failed",
                skip_execution_success=True,
            )

        completed_work, work_error = self._try_transition_work(
            running_work,
            WorkItemState.COMPLETED,
            observed_at,
        )
        if work_error is not None or completed_work is None:
            self._finalize_post_success_failure(
                primary_error=work_error
                or SingleStepRuntimeError(
                    SingleStepRuntimeErrorCode.REPOSITORY_FAILURE,
                    "Work runtime repository operation failed.",
                    operation="transition_work",
                ),
                running_execution=completed_execution,
                running_work=running_work,
                request=request,
                occurred_at=observed_at,
                reason="executor succeeded but work finalization failed",
                execution_already_succeeded=True,
            )

        completed_event, recording_error = self._try_append_event(
            RuntimeEventType.EXECUTION_COMPLETED,
            work=completed_work.item,
            request=request,
            occurred_at=observed_at,
            execution=completed_execution.record,
            payload={
                "work_id": str(completed_work.item.work_id),
                "execution_id": str(completed_execution.record.execution_id),
                "evidence_count": len(execution_outcome.evidence_refs),
            },
        )
        recording_errors = (recording_error,) if recording_error is not None else ()
        completed_events = (completed_event,) if completed_event is not None else ()
        return SingleStepRuntimeResult(
            status=SingleStepRuntimeStatus.COMPLETED,
            work=completed_work,
            execution=completed_execution,
            policy_decision=policy_decision,
            executor_result=execution_outcome.result,
            events=(policy_event, started_event, *evidence_events, *completed_events),
            evidence_refs=execution_outcome.evidence_refs,
            recording_errors=recording_errors,
        )

    def _read_work(self, work_id: WorkId) -> StoredWorkItem:
        error: SingleStepRuntimeError | None = None
        try:
            stored_work = self.work_repository.read_work(work_id)
        except RepositoryError as exc:
            error = _error_from_repository(exc, operation="read_work")
        if error is not None:
            _raise_runtime_error(error)
        if stored_work is None:
            error = SingleStepRuntimeError(
                SingleStepRuntimeErrorCode.NOT_FOUND,
                f"Work item {work_id} was not found.",
                operation="read_work",
            )
            _raise_runtime_error(error)
        return stored_work

    def _evaluate_policy(
        self,
        item: WorkItem,
        request: SingleStepRuntimeRequest,
        decided_at: UtcTimestamp,
    ) -> PolicyDecision:
        error: SingleStepRuntimeError | None = None
        try:
            decision = self.policy_evaluator.evaluate(
                M0PolicyEvaluationRequest(
                    subject_ref=ObjectReference.from_id(item.work_id),
                    principal=request.principal,
                    work_type=item.work_type,
                    requested_effects=request.requested_effects,
                    resource_refs=request.resource_refs or (request.executor_ref,),
                    scope=request.scope,
                    decided_at=decided_at,
                    policy_refs=item.policy_constraint_refs,
                    observability_context=request.observability_context,
                    policy_state_known=request.policy_state_known,
                )
            )
        except Exception as exc:
            error = SingleStepRuntimeError(
                SingleStepRuntimeErrorCode.POLICY_FAILURE,
                "Minimal M0 policy evaluation failed.",
                operation="evaluate_policy",
                retryable=False,
                detail={"cause_type": type(exc).__name__},
            )
        if error is not None:
            _raise_runtime_error(error)
        return decision

    def _start_work(
        self,
        stored_work: StoredWorkItem,
        occurred_at: UtcTimestamp,
    ) -> StoredWorkItem:
        if stored_work.item.state is WorkItemState.CREATED:
            stored_work = self._transition_work(stored_work, WorkItemState.READY, occurred_at)
        return self._transition_work(stored_work, WorkItemState.RUNNING, occurred_at)

    def _start_execution(
        self,
        request: SingleStepRuntimeRequest,
        item: WorkItem,
        occurred_at: UtcTimestamp,
    ) -> StoredExecutionRecord:
        execution_id = request.execution_id or ExecutionId.generate()
        error: SingleStepRuntimeError | None = None
        try:
            created = self.work_repository.create_execution(
                ExecutionRecord(
                    execution_id=execution_id,
                    work_id=item.work_id,
                    executor_ref=request.executor_ref,
                    started_at=occurred_at,
                    state=ExecutionState.CREATED,
                    observability_context=_observability_for(request, item.work_id, execution_id),
                )
            )
            running = self.work_repository.transition_execution(
                created.record.execution_id,
                ExecutionState.RUNNING,
                occurred_at=occurred_at,
                expected_version=created.version,
            )
        except RepositoryError as exc:
            error = _error_from_repository(exc, operation="start_execution")
        if error is not None:
            _raise_runtime_error(error)
        return running

    def _transition_work(
        self,
        stored_work: StoredWorkItem,
        target: WorkItemState,
        occurred_at: UtcTimestamp,
    ) -> StoredWorkItem:
        error: SingleStepRuntimeError | None = None
        try:
            transitioned = self.work_repository.transition_work(
                stored_work.item.work_id,
                target,
                occurred_at=occurred_at,
                expected_version=stored_work.version,
            )
        except RepositoryError as exc:
            error = _error_from_repository(exc, operation="transition_work")
        if error is not None:
            _raise_runtime_error(error)
        return transitioned

    def _transition_execution(
        self,
        stored_execution: StoredExecutionRecord,
        target: ExecutionState,
        occurred_at: UtcTimestamp,
    ) -> StoredExecutionRecord:
        error: SingleStepRuntimeError | None = None
        try:
            transitioned = self.work_repository.transition_execution(
                stored_execution.record.execution_id,
                target,
                occurred_at=occurred_at,
                expected_version=stored_execution.version,
            )
        except RepositoryError as exc:
            error = _error_from_repository(exc, operation="transition_execution")
        if error is not None:
            _raise_runtime_error(error)
        return transitioned

    def _try_transition_work(
        self,
        stored_work: StoredWorkItem,
        target: WorkItemState,
        occurred_at: UtcTimestamp,
    ) -> tuple[StoredWorkItem | None, SingleStepRuntimeError | None]:
        try:
            transitioned = self.work_repository.transition_work(
                stored_work.item.work_id,
                target,
                occurred_at=occurred_at,
                expected_version=stored_work.version,
            )
        except RepositoryError as exc:
            return None, _error_from_repository(exc, operation="transition_work")
        return transitioned, None

    def _try_transition_execution(
        self,
        stored_execution: StoredExecutionRecord,
        target: ExecutionState,
        occurred_at: UtcTimestamp,
    ) -> tuple[StoredExecutionRecord | None, SingleStepRuntimeError | None]:
        try:
            transitioned = self.work_repository.transition_execution(
                stored_execution.record.execution_id,
                target,
                occurred_at=occurred_at,
                expected_version=stored_execution.version,
            )
        except RepositoryError as exc:
            return None, _error_from_repository(exc, operation="transition_execution")
        return transitioned, None

    def _finalize_executor_failure(
        self,
        *,
        primary_error: SingleStepRuntimeError | None,
        executor_result: Result[object] | None,
        running_execution: StoredExecutionRecord,
        running_work: StoredWorkItem,
        request: SingleStepRuntimeRequest,
        occurred_at: UtcTimestamp,
        reason: str,
        prior_events: tuple[EventEnvelope, ...],
        policy_decision: PolicyDecision,
        evidence_refs: tuple[EvidenceReference, ...],
    ) -> SingleStepRuntimeResult:
        failed_work, work_error = self._try_transition_work(
            running_work,
            WorkItemState.FAILED,
            occurred_at,
        )
        failed_execution, execution_error = self._try_transition_execution(
            running_execution,
            ExecutionState.FAILED,
            occurred_at,
        )
        cleanup_errors = tuple(
            error for error in (work_error, execution_error) if error is not None
        )
        if cleanup_errors:
            error = primary_error or SingleStepRuntimeError(
                SingleStepRuntimeErrorCode.EXECUTOR_FAILURE,
                "Single-step executor failed and failure finalization was incomplete.",
                operation="finalize_failure",
                detail={"executor_result_status": "failure"},
            )
            _raise_runtime_error(_with_cleanup_detail(error, cleanup_errors))

        assert failed_work is not None
        assert failed_execution is not None
        failed_event, recording_error = self._try_append_event(
            RuntimeEventType.EXECUTION_FAILED,
            work=failed_work.item,
            request=request,
            occurred_at=occurred_at,
            execution=failed_execution.record,
            payload={
                "work_id": str(failed_work.item.work_id),
                "execution_id": str(failed_execution.record.execution_id),
                "reason": reason,
            },
        )
        if primary_error is not None:
            if recording_error is not None:
                primary_error = _with_cleanup_detail(primary_error, (recording_error,))
            _raise_runtime_error(primary_error)

        events = prior_events + ((failed_event,) if failed_event is not None else ())
        recording_errors = (recording_error,) if recording_error is not None else ()
        return SingleStepRuntimeResult(
            status=SingleStepRuntimeStatus.FAILED,
            work=failed_work,
            execution=failed_execution,
            policy_decision=policy_decision,
            executor_result=executor_result,
            events=events,
            evidence_refs=evidence_refs,
            recording_errors=recording_errors,
        )

    # Post-executor failures cannot pretend the governed invocation did not
    # happen. These helpers terminalize work first for executor failures, but
    # preserve executor-success truth when later evidence/finalization fails.
    def _finalize_post_success_failure(
        self,
        *,
        primary_error: SingleStepRuntimeError,
        running_execution: StoredExecutionRecord,
        running_work: StoredWorkItem,
        request: SingleStepRuntimeRequest,
        occurred_at: UtcTimestamp,
        reason: str,
        execution_already_succeeded: bool = False,
        skip_execution_success: bool = False,
    ) -> NoReturn:
        terminal_execution: StoredExecutionRecord | None = None
        cleanup_errors: list[SingleStepRuntimeError] = []
        if execution_already_succeeded:
            terminal_execution = running_execution
        elif skip_execution_success:
            terminal_execution, execution_failed_error = self._try_transition_execution(
                running_execution,
                ExecutionState.FAILED,
                occurred_at,
            )
            if execution_failed_error is not None:
                cleanup_errors.append(execution_failed_error)
        else:
            terminal_execution, execution_success_error = self._try_transition_execution(
                running_execution,
                ExecutionState.SUCCEEDED,
                occurred_at,
            )
            if execution_success_error is not None:
                cleanup_errors.append(execution_success_error)
                terminal_execution, execution_failed_error = self._try_transition_execution(
                    running_execution,
                    ExecutionState.FAILED,
                    occurred_at,
                )
                if execution_failed_error is not None:
                    cleanup_errors.append(execution_failed_error)

        failed_work, work_error = self._try_transition_work(
            running_work,
            WorkItemState.FAILED,
            occurred_at,
        )
        if work_error is not None:
            cleanup_errors.append(work_error)

        if failed_work is not None and terminal_execution is not None:
            _, recording_error = self._try_append_event(
                RuntimeEventType.EXECUTION_FAILED,
                work=failed_work.item,
                request=request,
                occurred_at=occurred_at,
                execution=terminal_execution.record,
                payload={
                    "work_id": str(failed_work.item.work_id),
                    "execution_id": str(terminal_execution.record.execution_id),
                    "reason": reason,
                    "executor_effect": "succeeded",
                },
            )
            if recording_error is not None:
                cleanup_errors.append(recording_error)

        detail = dict(primary_error.detail)
        detail["executor_effect"] = "succeeded"
        detail["finalization_status"] = "incomplete"
        primary_error = SingleStepRuntimeError(
            primary_error.code,
            str(primary_error),
            operation=primary_error.operation,
            retryable=primary_error.retryable,
            detail=detail,
        )
        _raise_runtime_error(_with_cleanup_detail(primary_error, tuple(cleanup_errors)))

    def _append_event(
        self,
        event_type: RuntimeEventType,
        *,
        work: WorkItem,
        request: SingleStepRuntimeRequest,
        occurred_at: UtcTimestamp,
        payload: dict[str, object],
        execution: ExecutionRecord | None = None,
    ) -> EventEnvelope:
        event = EventEnvelope(
            event_id=EventId.generate(),
            event_type=event_type.value,
            schema_version=_SCHEMA_VERSION,
            occurred_at=occurred_at,
            producer=request.producer_ref,
            subject_ref=ObjectReference.from_id(work.work_id),
            observability_context=_observability_for(
                request,
                work.work_id,
                execution.execution_id if execution is not None else None,
            ),
            payload=payload,
            metadata={"source": "task-m0-006-single-step-runtime"},
        )
        error: SingleStepRuntimeError | None = None
        try:
            appended = self.event_store.append_event(event)
        except RuntimeStoreError as exc:
            error = _error_from_store(exc, operation="append_event")
        if error is not None:
            _raise_runtime_error(error)
        return appended

    def _try_append_event(
        self,
        event_type: RuntimeEventType,
        *,
        work: WorkItem,
        request: SingleStepRuntimeRequest,
        occurred_at: UtcTimestamp,
        payload: dict[str, object],
        execution: ExecutionRecord | None = None,
    ) -> tuple[EventEnvelope | None, SingleStepRuntimeError | None]:
        try:
            event = self._append_event(
                event_type,
                work=work,
                request=request,
                occurred_at=occurred_at,
                payload=payload,
                execution=execution,
            )
        except SingleStepRuntimeError as exc:
            return None, exc
        return event, None

    def _record_evidence(
        self,
        evidence_ref: EvidenceReference,
        request: SingleStepRuntimeRequest,
        work: WorkItem,
        occurred_at: UtcTimestamp,
    ) -> EventEnvelope:
        error: SingleStepRuntimeError | None = None
        try:
            self.event_store.append_evidence(evidence_ref)
        except RuntimeStoreError as exc:
            error = _error_from_store(exc, operation="append_evidence")
        if error is not None:
            _raise_runtime_error(error)
        return self._append_event(
            RuntimeEventType.EVIDENCE_PRODUCED,
            work=work,
            request=request,
            occurred_at=occurred_at,
            payload={
                "work_id": str(work.work_id),
                "evidence_id": str(evidence_ref.evidence_id),
                "evidence_kind": evidence_ref.kind.value,
            },
        )

    def _try_record_evidence(
        self,
        evidence_ref: EvidenceReference,
        request: SingleStepRuntimeRequest,
        work: WorkItem,
        occurred_at: UtcTimestamp,
    ) -> tuple[EventEnvelope | None, SingleStepRuntimeError | None]:
        try:
            event = self._record_evidence(evidence_ref, request, work, occurred_at)
        except SingleStepRuntimeError as exc:
            return None, exc
        return event, None

    @staticmethod
    def _require_startable(item: WorkItem) -> None:
        if item.state not in _STARTABLE_WORK_STATES:
            error = SingleStepRuntimeError(
                SingleStepRuntimeErrorCode.ILLEGAL_STATE,
                "Work item is not in a startable M0 state.",
                operation="run_once",
                detail={"work_state": item.state.value},
            )
            _raise_runtime_error(error)


def _observability_for(
    request: SingleStepRuntimeRequest,
    work_id: WorkId,
    execution_id: ExecutionId | None,
) -> ObservabilityContext:
    current = request.observability_context or ObservabilityContext()
    return ObservabilityContext(
        project_id=current.project_id,
        application_id=current.application_id,
        milestone_id=current.milestone_id,
        workstream_id=current.workstream_id,
        work_id=work_id,
        execution_id=execution_id,
        agent_instance_id=current.agent_instance_id,
        principal_ref=current.principal_ref,
        trace_id=current.trace_id,
        correlation_id=current.correlation_id,
        causation_ref=current.causation_ref,
    )


def _error_from_repository(exc: RepositoryError, *, operation: str) -> SingleStepRuntimeError:
    if exc.code.value == "NOT_FOUND":
        code = SingleStepRuntimeErrorCode.NOT_FOUND
    elif exc.code.value == "CONFLICT":
        code = SingleStepRuntimeErrorCode.CONFLICT
    elif exc.code.value == "ILLEGAL_TRANSITION":
        code = SingleStepRuntimeErrorCode.ILLEGAL_STATE
    else:
        code = SingleStepRuntimeErrorCode.REPOSITORY_FAILURE
    return SingleStepRuntimeError(
        code,
        "Work runtime repository operation failed.",
        operation=operation,
        retryable=exc.retryable,
        detail={"repository_code": exc.code.value, "repository_operation": exc.operation},
    )


def _error_from_store(exc: RuntimeStoreError, *, operation: str) -> SingleStepRuntimeError:
    return SingleStepRuntimeError(
        SingleStepRuntimeErrorCode.RUNTIME_STORE_FAILURE,
        "Work runtime event/evidence operation failed.",
        operation=operation,
        retryable=exc.retryable,
        detail={"store_code": exc.code.value, "store_operation": exc.operation},
    )


def _with_cleanup_detail(
    error: SingleStepRuntimeError,
    cleanup_errors: tuple[SingleStepRuntimeError, ...],
) -> SingleStepRuntimeError:
    if not cleanup_errors:
        return error
    detail = dict(error.detail)
    detail["cleanup_errors"] = tuple(
        cleanup_error.to_json_compatible() for cleanup_error in cleanup_errors
    )
    return SingleStepRuntimeError(
        error.code,
        str(error),
        operation=error.operation,
        retryable=error.retryable
        or any(cleanup_error.retryable for cleanup_error in cleanup_errors),
        detail=detail,
    )


def _require_object_refs(values: tuple[ObjectReference, ...], field_name: str) -> None:
    for value in values:
        if not isinstance(value, ObjectReference):
            msg = f"{field_name} must contain ObjectReference values"
            raise TypeError(msg)


def _raise_runtime_error(error: SingleStepRuntimeError) -> NoReturn:
    raise error from None
