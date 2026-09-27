from __future__ import annotations

import json

from contract_fixtures import UTC_NOW, fixed_id, ref_for
from curios_api import create_api_composition, create_application
from curios_capability import (
    CapabilityResolution,
    CapabilityResolutionReason,
    CapabilityResolutionStatus,
)
from curios_contracts import (
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    CapabilityId,
    CapabilityRequirement,
    DecisionId,
    EventId,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    IntentId,
    ObjectReference,
    ObservabilityContext,
    ProviderId,
    TraceId,
    VerificationId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_dag import WorkDag, WorkDagId
from curios_runtime import (
    RouteCandidateKind,
    RoutingCandidate,
    RoutingDecisionRationale,
    RoutingDecisionRecord,
    RoutingDecisionRequest,
    RoutingDecisionStatus,
    RoutingRationaleCode,
    select_m1_route,
)
from fastapi.testclient import TestClient


def test_submit_simple_intent_returns_canonical_decomposition_and_dag() -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            "/m1/intents/decompose",
            json={
                "intent_id": str(fixed_id(IntentId)),
                "objective": "Implement a bounded change",
                "submitted_at": str(UTC_NOW),
                "created_at": str(UTC_NOW),
                "dag_id": str(fixed_id(WorkDagId)),
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["intent"]["objective"] == "Implement a bounded change"
    assert payload["decomposition"]["status"] == "SUPPORTED"
    assert payload["decomposition"]["problem"]["intent_ref"] == {
        "kind": "intent",
        "ref_id": str(fixed_id(IntentId)),
    }
    assert [item["work_type"] for item in payload["decomposition"]["work_items"]] == [
        "inspect_current_state",
        "apply_bounded_change",
        "verify_bounded_change",
    ]
    assert payload["dag"]["dag_id"] == str(fixed_id(WorkDagId))
    assert len(payload["dag"]["nodes"]) == 3


def test_runner_endpoint_delegates_to_bounded_runner_without_bypassing_route_gate() -> None:
    work = _work()
    compatible = _runner_payload(work, decision=_selected_decision(work))
    incompatible = _runner_payload(work, decision=_incompatible_selected_decision(work))
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        selected = client.post("/m1/dag/run-once", json=compatible)
        blocked = client.post("/m1/dag/run-once", json=incompatible)

    assert selected.status_code == 200
    selected_result = selected.json()["runner_result"]
    assert selected_result["node_results"][0]["status"] == "EXECUTED"
    assert len(selected_result["events"]) == 1
    assert len(selected_result["evidence_refs"]) == 1

    assert blocked.status_code == 200
    blocked_result = blocked.json()["runner_result"]
    assert blocked_result["node_results"][0]["status"] == "BLOCKED"
    assert blocked_result["node_results"][0]["reason"] == "ROUTE_NOT_EXECUTABLE"
    assert blocked_result["events"] == []
    assert blocked_result["evidence_refs"] == []


def test_runner_endpoint_preserves_no_route_as_domain_result() -> None:
    work = _work()
    payload = _runner_payload(work, decision=_no_route_decision(work))
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post("/m1/dag/run-once", json=payload)

    assert response.status_code == 200
    node = response.json()["runner_result"]["node_results"][0]
    assert node["status"] == "BLOCKED"
    assert node["reason"] == "NO_ROUTE"


def test_verification_endpoint_delegates_to_bounded_loop_and_binds_evidence() -> None:
    work = _work()
    runner = _executed_runner_result(work)
    executor_outcome = runner["executor_outcome"]
    assert isinstance(executor_outcome, dict)
    evidence = executor_outcome["evidence_refs"][0]
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        approved = client.post(
            "/m1/verification/complete",
            json=_verification_payload(work, runner, attempts=[_attempt("passed", [evidence])]),
        )
        duplicate = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                runner,
                attempts=[_attempt("passed", [evidence, evidence])],
            ),
        )

    assert approved.status_code == 200
    result = approved.json()["verification_result"]
    assert result["completion_decision"] == "APPROVED"
    assert result["event"]["event_type"] == "verification.completed"
    assert (
        result["verification_ref"]["subject_ref"]
        == ObjectReference.from_id(work.work_id).to_json_compatible()
    )

    assert duplicate.status_code == 400
    assert duplicate.json()["detail"]["code"] == "INVALID_EVIDENCE"


def test_verification_endpoint_rejects_wrong_work_without_raw_secret_leakage() -> None:
    work = _work()
    other_work = _work(ordinal=4)
    secret_evidence = EvidenceReference(
        evidence_id=fixed_id(EvidenceId),
        kind=EvidenceKind.OTHER,
        subject_ref=ObjectReference.from_id(other_work.work_id),
        collected_at=UTC_NOW,
        summary="Authorization Bearer secret token",
    ).to_json_compatible()
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        response = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                _executed_runner_result(work),
                attempts=[_attempt("passed", [secret_evidence])],
            ),
        )

    assert response.status_code == 409
    body = json.dumps(response.json()).lower()
    assert "evidence_subject_mismatch" in body
    assert "authorization bearer" not in body
    assert "secret token" not in body


def test_m1_endpoints_fail_closed_for_malformed_canonical_input() -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        malformed_intent = client.post("/m1/intents/decompose", json={"objective": 10})
        malformed_runner = client.post("/m1/dag/run-once", json={"max_concurrency": True})
        malformed_verification = client.post(
            "/m1/verification/complete",
            json={"max_iterations": True},
        )

    assert malformed_intent.status_code == 400
    assert malformed_intent.json()["detail"]["error_code"] == "M1_API_MALFORMED_REQUEST"
    assert malformed_runner.status_code == 400
    assert malformed_runner.json()["detail"]["error_code"] == "M1_API_MALFORMED_REQUEST"
    assert malformed_verification.status_code == 400
    assert malformed_verification.json()["detail"]["error_code"] == "M1_API_MALFORMED_REQUEST"


def test_openapi_exposes_only_the_authorized_m1_endpoint_surface() -> None:
    app = create_application(create_api_composition())

    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]

    assert "/m1/intents/decompose" in paths
    assert "/m1/dag/run-once" in paths
    assert "/m1/verification/complete" in paths
    assert not any("model-generation" in path for path in paths)
    assert not any("web-console" in path for path in paths)


def _work(ordinal: int = 0) -> WorkItem:
    requirement = CapabilityRequirement(capability_id=fixed_id(CapabilityId, ordinal))
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal),
        work_type="inspect_current_state",
        title="Inspect current state",
        objective="Inspect repository state.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
        required_capabilities=(requirement,),
    )


def _agent(work: WorkItem, ordinal: int = 0) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId, ordinal),
        agent_definition_id=fixed_id(AgentDefinitionId, ordinal),
        work_id=work.work_id,
        state=AgentInstanceState.ACTIVE,
        created_at=UTC_NOW,
    )


def _resolution(work: WorkItem, ordinal: int = 0) -> CapabilityResolution:
    return CapabilityResolution(
        requirement=work.required_capabilities[0],
        status=CapabilityResolutionStatus.MATCHED,
        reason=CapabilityResolutionReason.EXACT_MATCH,
        capability_ref=ObjectReference.from_id(fixed_id(CapabilityId, ordinal)),
        agent_definition_ref=ObjectReference.from_id(fixed_id(AgentDefinitionId, ordinal)),
    )


def _selected_decision(
    work: WorkItem,
    *,
    supported_work_types: tuple[str, ...] = ("inspect_current_state",),
):
    return select_m1_route(
        RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId),
            work=work,
            candidates=(
                RoutingCandidate.deterministic_executor(
                    work_id=work.work_id,
                    executor_name="deterministic_m1",
                    supported_work_types=supported_work_types,
                ),
            ),
            requested_at=UTC_NOW,
            producer_ref=ref_for(ProviderId),
            observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
        )
    )


def _no_route_decision(work: WorkItem):
    return select_m1_route(
        RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId, 1),
            work=work,
            candidates=(RoutingCandidate.no_model(work_id=work.work_id),),
            requested_at=UTC_NOW,
            producer_ref=ref_for(ProviderId),
            observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
        )
    )


def _incompatible_selected_decision(work: WorkItem) -> RoutingDecisionRecord:
    candidate = RoutingCandidate(
        candidate_key="executor_deterministic_m1",
        kind=RouteCandidateKind.DETERMINISTIC_EXECUTOR,
        work_ref=ObjectReference.from_id(work.work_id),
        executor_name="deterministic_m1",
        supported_work_types=("apply_bounded_change",),
    )
    return RoutingDecisionRecord(
        decision_id=fixed_id(DecisionId, 2),
        work_ref=ObjectReference.from_id(work.work_id),
        status=RoutingDecisionStatus.SELECTED,
        candidates=(candidate,),
        selected_route=candidate,
        rationale=RoutingDecisionRationale(
            code=RoutingRationaleCode.SELECTED_SINGLE_VALID_ROUTE,
            message="Selected the only valid M1 route candidate.",
            details={"valid_candidate_count": 1},
        ),
        resource_constraints=None,
        decided_at=UTC_NOW,
        producer_ref=ref_for(ProviderId),
        observability_context=ObservabilityContext(trace_id=fixed_id(TraceId)),
    )


def _runner_payload(work: WorkItem, *, decision) -> dict[str, object]:
    return {
        "dag": WorkDag.from_work_items(
            fixed_id(WorkDagId),
            (work,),
            created_at=UTC_NOW,
        ).to_json_compatible(),
        "work_items": [work.to_json_compatible()],
        "routing_decisions": [decision.to_json_compatible()],
        "agent_instances": [_agent(work).to_json_compatible()],
        "capability_resolutions_by_work_id": {
            str(work.work_id): [_resolution(work).to_json_compatible()]
        },
        "event_ids_by_work_id": {str(work.work_id): str(fixed_id(EventId))},
        "evidence_ids_by_work_id": {str(work.work_id): str(fixed_id(EvidenceId))},
        "producer_ref": ref_for(ProviderId).to_json_compatible(),
        "occurred_at": str(UTC_NOW),
        "observability_context": ObservabilityContext(
            work_id=work.work_id,
            trace_id=fixed_id(TraceId),
        ).to_json_compatible(),
        "max_concurrency": 1,
    }


def _executed_runner_result(work: WorkItem) -> dict[str, object]:
    app = create_application(create_api_composition())
    with TestClient(app) as client:
        response = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(work, decision=_selected_decision(work)),
        )
    assert response.status_code == 200
    return response.json()["runner_result"]["node_results"][0]


def _verification_payload(
    work: WorkItem,
    runner_result: dict[str, object],
    *,
    attempts: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "work": work.to_json_compatible(),
        "runner_node_result": runner_result,
        "attempts": attempts,
        "max_iterations": 2,
        "verification_id": str(fixed_id(VerificationId)),
        "event_id": str(fixed_id(EventId, 1)),
        "verified_at": str(UTC_NOW),
        "verifier_ref": ref_for(ProviderId).to_json_compatible(),
        "producer_ref": ref_for(ProviderId).to_json_compatible(),
        "observability_context": ObservabilityContext(
            work_id=work.work_id,
            trace_id=fixed_id(TraceId),
        ).to_json_compatible(),
    }


def _attempt(outcome: str, evidence_refs: list[dict[str, object]]) -> dict[str, object]:
    return {"outcome": outcome, "evidence_refs": evidence_refs}
