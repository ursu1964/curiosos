"""FastAPI application factory at the outer Curios service boundary."""

from __future__ import annotations

from typing import Annotated, Any, NoReturn

from curios_capability import CapabilityResolution
from curios_cognitive import decompose_intent
from curios_contracts import (
    AgentInstance,
    CuriosId,
    EffectClassification,
    EventEnvelope,
    EventId,
    EvidenceId,
    EvidenceReference,
    ExecutionId,
    Intent,
    IntentId,
    ObjectReference,
    ObservabilityContext,
    Result,
    ResultStatus,
    TraceId,
    UtcTimestamp,
    VerificationId,
    VerificationOutcome,
    WorkId,
    WorkItem,
    to_json_compatible,
)
from curios_dag import WorkDag, WorkDagId, WorkDagNodeReadiness
from curios_policy import M0_PROVIDER_INVENTORY_WORK_TYPE
from curios_runtime import (
    BoundedM1DagRunner,
    BoundedM1VerificationLoop,
    DeterministicM1Executor,
    ExecutorOutcome,
    ExecutorOutcomeStatus,
    M1DagRunnerError,
    M1DagRunnerErrorCode,
    M1DagRunnerNodeResult,
    M1DagRunnerNodeStatus,
    M1DagRunnerReasonCode,
    M1DagRunnerRequest,
    M1VerificationAttempt,
    M1VerificationError,
    M1VerificationErrorCode,
    M1VerificationLoopRequest,
    RepositoryError,
    RoutingDecisionRecord,
    RuntimeStoreError,
    SingleStepRuntimeError,
    SingleStepRuntimeErrorCode,
    SingleStepRuntimeRequest,
    SingleStepRuntimeResult,
    SingleStepRuntimeStatus,
    StoredWorkItem,
)
from fastapi import Body, FastAPI, HTTPException, Request, status

from curios_api.composition import ApiComposition, M0WorkApiComposition, create_api_composition

type JsonObject = dict[str, object]
type JsonBody = dict[str, object] | None

_M1_JSON_OBJECT_REQUEST_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"type": "object", "additionalProperties": True},
            }
        },
    }
}


def create_application(composition: ApiComposition | None = None) -> FastAPI:
    """Create the FastAPI application without making FastAPI semantic authority."""
    app_composition = composition or create_api_composition()
    app = FastAPI(title="CuriosOS API", version="0.0.0")

    @app.get("/health/live")
    async def health_live() -> JsonObject:
        return {"status": "ok", "service": "curios-api"}

    @app.get("/health/ready")
    async def health_ready() -> JsonObject:
        profile = app_composition.configuration_provider.load_configuration_profile()
        if profile.status is ResultStatus.FAILURE:
            _raise_unavailable(profile)

        providers = app_composition.core_services.list_provider_descriptors(app_composition.context)
        if providers.status is ResultStatus.FAILURE:
            _raise_unavailable(providers)

        return {
            "status": "ready",
            "configuration_profile": to_json_compatible(profile.value),
            "providers": to_json_compatible(providers.value or ()),
        }

    @app.get("/providers")
    async def providers() -> JsonObject:
        result = app_composition.core_services.list_provider_descriptors(app_composition.context)
        if result.status is ResultStatus.FAILURE:
            _raise_unavailable(result)
        return {"providers": to_json_compatible(result.value or ())}

    @app.post("/work/provider-inventory", status_code=status.HTTP_201_CREATED)
    async def create_provider_inventory_work(
        payload: Annotated[JsonBody, Body()] = None,
    ) -> JsonObject:
        m0_work = _require_m0_work(app_composition)
        data = _require_body(payload)
        requested_type = data.get("work_type", M0_PROVIDER_INVENTORY_WORK_TYPE)
        if requested_type != M0_PROVIDER_INVENTORY_WORK_TYPE:
            _raise_bad_request(
                "M0_API_UNSUPPORTED_WORK_TYPE",
                "M0 API supports only provider_inventory work creation.",
                {"work_type": requested_type},
            )
        title = _optional_text(data, "title", "Provider inventory")
        objective = _optional_text(data, "objective", "Collect canonical provider descriptors.")
        now = UtcTimestamp.now()
        item = WorkItem(
            work_id=WorkId.generate(),
            work_type=M0_PROVIDER_INVENTORY_WORK_TYPE,
            title=title,
            objective=objective,
            created_at=now,
            updated_at=now,
            principal_ref=m0_work.principal.principal_ref,
        )
        try:
            stored = m0_work.work_repository.create_work(item)
        except RepositoryError as exc:
            _raise_repository_error(exc)
        return {"work": to_json_compatible(stored.item), "version": stored.version}

    @app.get("/work/{work_id}")
    async def get_work(work_id: str) -> JsonObject:
        m0_work = _require_m0_work(app_composition)
        stored = _read_work_or_404(m0_work, work_id)
        return {"work": to_json_compatible(stored.item), "version": stored.version}

    @app.post("/work/{work_id}/run")
    async def run_work_once(
        work_id: str,
        payload: Annotated[JsonBody, Body()] = None,
    ) -> JsonObject:
        m0_work = _require_m0_work(app_composition)
        data = _require_body(payload)
        requested_effects = _requested_effects(data)
        try:
            result = m0_work.runtime_service.run_once(
                SingleStepRuntimeRequest(
                    work_id=_parse_work_id(work_id),
                    principal=m0_work.principal,
                    producer_ref=m0_work.producer_ref,
                    executor_ref=m0_work.executor_ref,
                    scope=m0_work.scope,
                    resource_refs=m0_work.resource_refs or (m0_work.executor_ref,),
                    requested_effects=requested_effects,
                    policy_state_known=_optional_bool(data, "policy_state_known", True),
                    observability_context=_observability_context(
                        work_id,
                        trace_id=data.get("trace_id"),
                    ),
                    occurred_at=UtcTimestamp.now(),
                    execution_id=_optional_execution_id(data),
                )
            )
        except SingleStepRuntimeError as exc:
            _raise_runtime_error(exc)
        return _runtime_result_response(result)

    @app.get("/work/{work_id}/executions/{execution_id}")
    async def get_execution(work_id: str, execution_id: str) -> JsonObject:
        m0_work = _require_m0_work(app_composition)
        _read_work_or_404(m0_work, work_id)
        try:
            execution = m0_work.work_repository.read_execution(_parse_execution_id(execution_id))
        except RepositoryError as exc:
            _raise_repository_error(exc)
        if execution is None or str(execution.record.work_id) != work_id:
            _raise_not_found("M0_API_EXECUTION_NOT_FOUND", "execution was not found")
        assert execution is not None
        return {
            "execution": to_json_compatible(execution.record),
            "version": execution.version,
        }

    @app.get("/work/{work_id}/events")
    async def list_work_events(work_id: str) -> JsonObject:
        m0_work = _require_m0_work(app_composition)
        _read_work_or_404(m0_work, work_id)
        try:
            events = tuple(
                event
                for event in m0_work.event_store.list_events()
                if event.subject_ref == ObjectReference.from_id(_parse_work_id(work_id))
            )
        except RuntimeStoreError as exc:
            _raise_runtime_store_error(exc)
        return {"events": to_json_compatible(events)}

    @app.get("/work/{work_id}/evidence")
    async def list_work_evidence(work_id: str) -> JsonObject:
        m0_work = _require_m0_work(app_composition)
        _read_work_or_404(m0_work, work_id)
        try:
            evidence_refs = tuple(
                evidence
                for evidence in m0_work.event_store.list_evidence()
                if evidence.subject_ref == ObjectReference.from_id(_parse_work_id(work_id))
            )
        except RuntimeStoreError as exc:
            _raise_runtime_store_error(exc)
        return {"evidence": to_json_compatible(evidence_refs)}

    @app.post(
        "/m1/intents/decompose",
        status_code=status.HTTP_201_CREATED,
        openapi_extra=_M1_JSON_OBJECT_REQUEST_BODY,
    )
    async def decompose_m1_intent(http_request: Request) -> JsonObject:
        data = await _require_m1_body(http_request)
        try:
            intent = _m1_intent_from_body(data)
            created_at = _optional_timestamp(data, "created_at", intent.submitted_at)
            proposal = decompose_intent(intent, created_at=created_at)
            dag = (
                WorkDag.from_work_items(
                    _optional_work_dag_id(data),
                    proposal.work_items,
                    created_at=created_at,
                )
                if proposal.work_items
                else None
            )
        except TypeError:
            _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")
        except ValueError:
            _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")

        return {
            "intent": to_json_compatible(intent),
            "decomposition": proposal.to_json_compatible(),
            "dag": to_json_compatible(dag),
        }

    @app.post("/m1/dag/run-once", openapi_extra=_M1_JSON_OBJECT_REQUEST_BODY)
    async def run_m1_dag_once(http_request: Request) -> JsonObject:
        data = await _require_m1_body(http_request)
        try:
            runner_request = _m1_dag_runner_request_from_body(data)
            result = BoundedM1DagRunner(DeterministicM1Executor()).run_once(runner_request)
        except M1DagRunnerError as exc:
            _raise_m1_runner_error(exc)
        except TypeError:
            _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")
        except ValueError:
            _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")
        return {"runner_result": result.to_json_compatible()}

    @app.post("/m1/verification/complete", openapi_extra=_M1_JSON_OBJECT_REQUEST_BODY)
    async def complete_m1_verification(http_request: Request) -> JsonObject:
        data = await _require_m1_body(http_request)
        try:
            verification_request = _m1_verification_request_from_body(data)
            result = BoundedM1VerificationLoop().verify(verification_request)
        except M1VerificationError as exc:
            _raise_m1_verification_error(exc)
        except TypeError:
            _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")
        except ValueError:
            _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")
        return {"verification_result": result.to_json_compatible()}

    return app


def _raise_unavailable(result: Result[Any]) -> NoReturn:
    raise HTTPException(status_code=503, detail=result.to_json_compatible())


def _require_m0_work(composition: ApiComposition) -> M0WorkApiComposition:
    if composition.m0_work is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "M0_API_RUNTIME_UNAVAILABLE",
                "message": "M0 work runtime is not composed for this API instance.",
            },
        )
    return composition.m0_work


def _require_body(payload: JsonBody) -> dict[str, object]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "request body must be a JSON object",
            {},
        )
    return payload


async def _require_m1_body(request: Request) -> dict[str, object]:
    try:
        payload = await request.json()
    except ValueError:
        _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")
    if not isinstance(payload, dict):
        _raise_m1_bad_request("M1_API_MALFORMED_REQUEST")
    return payload


def _m1_intent_from_body(data: dict[str, object]) -> Intent:
    submitted_at = _optional_timestamp(data, "submitted_at", UtcTimestamp.now())
    return Intent(
        intent_id=_optional_intent_id(data),
        objective=_required_text(data, "objective"),
        submitted_at=submitted_at,
        source_ref=_optional_object_reference(data.get("source_ref")),
        context_refs=tuple(
            ObjectReference.from_json_compatible(item)
            for item in _optional_sequence(data.get("context_refs"), "context_refs")
        ),
    )


def _optional_intent_id(data: dict[str, object]) -> IntentId:
    value = data.get("intent_id")
    if value is None:
        return IntentId.generate()
    if not isinstance(value, str):
        raise TypeError
    return IntentId(value)


def _optional_work_dag_id(data: dict[str, object]) -> WorkDagId:
    value = data.get("dag_id")
    if value is None:
        return WorkDagId.generate()
    if not isinstance(value, str):
        raise TypeError
    return WorkDagId(value)


def _m1_dag_runner_request_from_body(data: dict[str, object]) -> M1DagRunnerRequest:
    return M1DagRunnerRequest(
        dag=WorkDag.from_json_compatible(_required_field(data, "dag")),
        work_items=tuple(
            WorkItem.from_json_compatible(item)
            for item in _required_sequence(_required_field(data, "work_items"), "work_items")
        ),
        routing_decisions=tuple(
            RoutingDecisionRecord.from_json_compatible(item)
            for item in _required_sequence(
                _required_field(data, "routing_decisions"),
                "routing_decisions",
            )
        ),
        agent_instances=tuple(
            AgentInstance.from_json_compatible(item)
            for item in _required_sequence(
                _required_field(data, "agent_instances"),
                "agent_instances",
            )
        ),
        capability_resolutions_by_work_id=_capability_resolution_map(
            _required_field(data, "capability_resolutions_by_work_id")
        ),
        event_ids_by_work_id=_id_map(
            _required_field(data, "event_ids_by_work_id"),
            EventId,
            "event_ids_by_work_id",
        ),
        evidence_ids_by_work_id=_id_map(
            _required_field(data, "evidence_ids_by_work_id"),
            EvidenceId,
            "evidence_ids_by_work_id",
        ),
        producer_ref=ObjectReference.from_json_compatible(_required_field(data, "producer_ref")),
        occurred_at=_required_timestamp(data, "occurred_at"),
        observability_context=ObservabilityContext.from_json(
            _required_field(data, "observability_context")
        ),
        max_concurrency=_required_int(data, "max_concurrency"),
    )


def _m1_verification_request_from_body(data: dict[str, object]) -> M1VerificationLoopRequest:
    return M1VerificationLoopRequest(
        work=WorkItem.from_json_compatible(_required_field(data, "work")),
        runner_node_result=_runner_node_result_from_json(
            _required_field(data, "runner_node_result")
        ),
        attempts=tuple(
            _verification_attempt_from_json(item)
            for item in _required_sequence(_required_field(data, "attempts"), "attempts")
        ),
        max_iterations=_required_int(data, "max_iterations"),
        verification_id=_required_id(data, "verification_id", VerificationId),
        event_id=_required_id(data, "event_id", EventId),
        verified_at=_required_timestamp(data, "verified_at"),
        verifier_ref=ObjectReference.from_json_compatible(_required_field(data, "verifier_ref")),
        producer_ref=ObjectReference.from_json_compatible(_required_field(data, "producer_ref")),
        observability_context=ObservabilityContext.from_json(
            _required_field(data, "observability_context")
        ),
    )


def _runner_node_result_from_json(value: object) -> M1DagRunnerNodeResult:
    if not isinstance(value, dict):
        raise TypeError
    routing_decision_ref = value.get("routing_decision_ref")
    return M1DagRunnerNodeResult(
        work_ref=ObjectReference.from_json_compatible(_required_field(value, "work_ref")),
        readiness=WorkDagNodeReadiness(_required_text(value, "readiness")),
        status=M1DagRunnerNodeStatus(_required_text(value, "status")),
        reason=M1DagRunnerReasonCode(_required_text(value, "reason")),
        routing_decision_ref=(
            ObjectReference.from_json_compatible(routing_decision_ref)
            if routing_decision_ref is not None
            else None
        ),
        executor_outcome=_optional_executor_outcome(value.get("executor_outcome")),
    )


def _optional_executor_outcome(value: object) -> ExecutorOutcome | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError
    return ExecutorOutcome(
        status=ExecutorOutcomeStatus(_required_text(value, "status")),
        result=Result.from_json_compatible(_required_field(value, "result")),
        event=EventEnvelope.from_json(_required_field(value, "event")),
        evidence_refs=tuple(
            EvidenceReference.from_json_compatible(item)
            for item in _optional_sequence(value.get("evidence_refs"), "evidence_refs")
        ),
    )


def _verification_attempt_from_json(value: object) -> M1VerificationAttempt:
    if not isinstance(value, dict):
        raise TypeError
    return M1VerificationAttempt(
        outcome=VerificationOutcome(_required_text(value, "outcome")),
        evidence_refs=tuple(
            EvidenceReference.from_json_compatible(item)
            for item in _optional_sequence(value.get("evidence_refs"), "evidence_refs")
        ),
    )


def _capability_resolution_map(value: object) -> dict[WorkId, tuple[CapabilityResolution, ...]]:
    if not isinstance(value, dict):
        raise TypeError
    result: dict[WorkId, tuple[CapabilityResolution, ...]] = {}
    for raw_work_id, raw_resolutions in value.items():
        if not isinstance(raw_work_id, str):
            raise TypeError
        result[WorkId(raw_work_id)] = tuple(
            CapabilityResolution.from_json_compatible(item)
            for item in _required_sequence(raw_resolutions, "capability_resolutions")
        )
    return result


def _id_map[IdT: CuriosId](
    value: object,
    id_type: type[IdT],
    field_name: str,
) -> dict[WorkId, IdT]:
    if not isinstance(value, dict):
        raise TypeError
    result: dict[WorkId, IdT] = {}
    for raw_work_id, raw_id in value.items():
        if not isinstance(raw_work_id, str) or not isinstance(raw_id, str):
            raise TypeError
        result[WorkId(raw_work_id)] = id_type(raw_id)
    return result


def _required_field(data: dict[str, object], field_name: str) -> object:
    if field_name not in data:
        _raise_bad_request(
            "M1_API_MALFORMED_REQUEST",
            "M1 API request is missing a required canonical field.",
            {"field": field_name},
        )
    return data[field_name]


def _required_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if not isinstance(value, list | tuple):
        _raise_bad_request(
            "M1_API_MALFORMED_REQUEST",
            "M1 API field must be a JSON array.",
            {"field": field_name},
        )
    return tuple(value)


def _optional_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if value is None:
        return ()
    return _required_sequence(value, field_name)


def _required_text(data: dict[str, object], field_name: str) -> str:
    value = _required_field(data, field_name)
    if not isinstance(value, str):
        _raise_bad_request(
            "M1_API_MALFORMED_REQUEST",
            "M1 API field must be a string.",
            {"field": field_name},
        )
    return value


def _required_int(data: dict[str, object], field_name: str) -> int:
    value = _required_field(data, field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        _raise_bad_request(
            "M1_API_MALFORMED_REQUEST",
            "M1 API field must be an integer.",
            {"field": field_name},
        )
    return value


def _required_timestamp(data: dict[str, object], field_name: str) -> UtcTimestamp:
    value = _required_text(data, field_name)
    return UtcTimestamp(value)


def _optional_timestamp(
    data: dict[str, object],
    field_name: str,
    default: UtcTimestamp,
) -> UtcTimestamp:
    value = data.get(field_name)
    if value is None:
        return default
    if not isinstance(value, str):
        raise TypeError
    return UtcTimestamp(value)


def _required_id[IdT: CuriosId](
    data: dict[str, object],
    field_name: str,
    id_type: type[IdT],
) -> IdT:
    return id_type(_required_text(data, field_name))


def _optional_object_reference(value: object) -> ObjectReference | None:
    if value is None:
        return None
    return ObjectReference.from_json_compatible(value)


def _optional_text(data: dict[str, object], field_name: str, default: str) -> str:
    value = data.get(field_name, default)
    if not isinstance(value, str):
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            f"{field_name} must be a string",
            {"field": field_name},
        )
    return value


def _optional_bool(data: dict[str, object], field_name: str, default: bool) -> bool:
    value = data.get(field_name, default)
    if not isinstance(value, bool):
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            f"{field_name} must be a boolean",
            {"field": field_name},
        )
    return value


def _requested_effects(data: dict[str, object]) -> tuple[EffectClassification, ...]:
    raw_effects = data.get("requested_effects", ("READ_ONLY",))
    if not isinstance(raw_effects, list | tuple):
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "requested_effects must be a list",
            {"field": "requested_effects"},
        )
    try:
        effects = tuple(EffectClassification(effect) for effect in raw_effects)
    except TypeError, ValueError:
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "requested_effects contains an unsupported effect token",
            {"field": "requested_effects"},
        )
    if not effects:
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "requested_effects must not be empty",
            {"field": "requested_effects"},
        )
    return effects


def _optional_execution_id(data: dict[str, object]) -> ExecutionId | None:
    value = data.get("execution_id")
    if value is None:
        return None
    if not isinstance(value, str):
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "execution_id must be a string",
            {"field": "execution_id"},
        )
    try:
        return ExecutionId(value)
    except ValueError:
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "execution_id is not a canonical ExecutionId",
            {"field": "execution_id"},
        )


def _observability_context(work_id: str, *, trace_id: object) -> ObservabilityContext:
    parsed_trace_id: TraceId | None = None
    if trace_id is not None:
        if not isinstance(trace_id, str):
            _raise_bad_request(
                "M0_API_MALFORMED_REQUEST",
                "trace_id must be a string",
                {"field": "trace_id"},
            )
        try:
            parsed_trace_id = TraceId(trace_id)
        except ValueError:
            _raise_bad_request(
                "M0_API_MALFORMED_REQUEST",
                "trace_id is not a canonical TraceId",
                {"field": "trace_id"},
            )
    return ObservabilityContext(work_id=_parse_work_id(work_id), trace_id=parsed_trace_id)


def _parse_work_id(work_id: str) -> WorkId:
    try:
        return WorkId(work_id)
    except ValueError:
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "work_id is not a canonical WorkId",
            {"field": "work_id"},
        )


def _parse_execution_id(execution_id: str) -> ExecutionId:
    try:
        return ExecutionId(execution_id)
    except ValueError:
        _raise_bad_request(
            "M0_API_MALFORMED_REQUEST",
            "execution_id is not a canonical ExecutionId",
            {"field": "execution_id"},
        )


def _read_work_or_404(m0_work: M0WorkApiComposition, work_id: str) -> StoredWorkItem:
    try:
        stored = m0_work.work_repository.read_work(_parse_work_id(work_id))
    except RepositoryError as exc:
        _raise_repository_error(exc)
    if stored is None:
        _raise_not_found("M0_API_WORK_NOT_FOUND", "work was not found")
    return stored


def _runtime_result_response(result: SingleStepRuntimeResult) -> JsonObject:
    payload = {
        "status": result.status.value,
        "work": to_json_compatible(result.work.item),
        "work_version": result.work.version,
        "policy_decision": to_json_compatible(result.policy_decision),
        "execution": to_json_compatible(result.execution.record if result.execution else None),
        "execution_version": result.execution.version if result.execution else None,
        "executor_result": to_json_compatible(result.executor_result),
        "events": to_json_compatible(result.events),
        "evidence_refs": to_json_compatible(result.evidence_refs),
        "recording_errors": tuple(error.to_json_compatible() for error in result.recording_errors),
    }
    if result.status is SingleStepRuntimeStatus.BLOCKED:
        raise HTTPException(status_code=403, detail=payload)
    if result.status is SingleStepRuntimeStatus.FAILED:
        raise HTTPException(status_code=502, detail=payload)
    return payload


def _raise_repository_error(exc: RepositoryError) -> NoReturn:
    status_code = (
        404 if exc.code.value == "NOT_FOUND" else 409 if exc.code.value == "CONFLICT" else 503
    )
    raise HTTPException(status_code=status_code, detail=exc.to_json_compatible())


def _raise_runtime_store_error(exc: RuntimeStoreError) -> NoReturn:
    status_code = (
        404 if exc.code.value == "NOT_FOUND" else 409 if exc.code.value == "CONFLICT" else 503
    )
    raise HTTPException(status_code=status_code, detail=exc.to_json_compatible())


def _raise_runtime_error(exc: SingleStepRuntimeError) -> NoReturn:
    status_code_by_code = {
        SingleStepRuntimeErrorCode.NOT_FOUND: 404,
        SingleStepRuntimeErrorCode.CONFLICT: 409,
        SingleStepRuntimeErrorCode.ILLEGAL_STATE: 409,
        SingleStepRuntimeErrorCode.POLICY_NOT_AUTHORIZED: 403,
        SingleStepRuntimeErrorCode.EXECUTOR_FAILURE: 502,
        SingleStepRuntimeErrorCode.INVALID_EXECUTOR_RESULT: 502,
    }
    raise HTTPException(
        status_code=status_code_by_code.get(exc.code, 503),
        detail=exc.to_json_compatible(),
    )


def _raise_m1_runner_error(exc: M1DagRunnerError) -> NoReturn:
    status_code_by_code = {
        M1DagRunnerErrorCode.INVALID_CONCURRENCY: 400,
        M1DagRunnerErrorCode.INVALID_REQUEST: 400,
        M1DagRunnerErrorCode.MISSING_AGENT: 409,
        M1DagRunnerErrorCode.MISSING_EXECUTOR_IDENTITY: 409,
        M1DagRunnerErrorCode.MISSING_ROUTING_DECISION: 409,
    }
    raise HTTPException(
        status_code=status_code_by_code.get(exc.code, 409),
        detail=exc.to_json_compatible(),
    )


def _raise_m1_verification_error(exc: M1VerificationError) -> NoReturn:
    status_code_by_code = {
        M1VerificationErrorCode.INVALID_ITERATION_BOUND: 400,
        M1VerificationErrorCode.INVALID_REQUEST: 400,
        M1VerificationErrorCode.INVALID_EVIDENCE: 400,
        M1VerificationErrorCode.EVIDENCE_SUBJECT_MISMATCH: 409,
        M1VerificationErrorCode.EXECUTION_NOT_COMPLETED: 409,
        M1VerificationErrorCode.MISSING_EVIDENCE: 409,
    }
    raise HTTPException(
        status_code=status_code_by_code.get(exc.code, 409),
        detail=exc.to_json_compatible(),
    )


def _raise_m1_bad_request(error_code: str) -> NoReturn:
    _raise_bad_request(
        error_code,
        "M1 API request is not canonical.",
        {},
    )


def _raise_bad_request(
    error_code: str,
    message: str,
    details: dict[str, object],
) -> NoReturn:
    raise HTTPException(
        status_code=400,
        detail={"error_code": error_code, "message": message, "details": details},
    )


def _raise_not_found(error_code: str, message: str) -> NoReturn:
    raise HTTPException(status_code=404, detail={"error_code": error_code, "message": message})
