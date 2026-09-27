from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import UTC_NOW, fixed_id, ref_for
from curios_api import create_api_composition, create_application
from curios_capability import (
    CapabilityResolution,
    CapabilityResolutionReason,
    CapabilityResolutionStatus,
    resolve_capability_requirement,
)
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    Capability,
    CapabilityCategory,
    CapabilityId,
    CapabilityRequirement,
    DecisionId,
    EventId,
    EvidenceId,
    IntentId,
    ObjectReference,
    ObservabilityContext,
    ProviderId,
    SchemaVersion,
    TraceId,
    VerificationId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_dag import M1WorkDagRepository, WorkDag, WorkDagId
from curios_persistence import PersistenceConfig, PersistenceError, PersistenceStore
from curios_runtime import (
    EventEvidenceRuntimeStore,
    M1AgentLifecycleRepository,
    M1AgentRepository,
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
from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "infrastructure/local/docker/compose.yaml"
ENV_FILE = REPO_ROOT / "infrastructure/local/docker/.env.example"
COMPOSE = (
    "docker",
    "compose",
    "--env-file",
    ENV_FILE.as_posix(),
    "-f",
    COMPOSE_FILE.as_posix(),
)
POSTGRES_VOLUME = "curios-local-docker_postgres_data"
SUPPORTED_M1_WORK_TYPES = (
    "inspect_current_state",
    "apply_bounded_change",
    "verify_bounded_change",
)

pytestmark = pytest.mark.acceptance


@dataclass(frozen=True)
class AcceptanceCriterion:
    slice_id: str
    pass_condition: str
    fail_condition: str


ACCEPTANCE_CRITERIA = (
    AcceptanceCriterion(
        "VS-M1-001",
        "supported intent produces linked cognitive records, acyclic DAG, and durable DAG truth",
        "unsupported intent remains bounded and produces no DAG/work records",
    ),
    AcceptanceCriterion(
        "VS-M1-002",
        "capability requirement resolves to a persisted active disposable agent with events",
        "missing, ambiguous, or inactive agent state prevents accepted assignment semantics",
    ),
    AcceptanceCriterion(
        "VS-M1-003",
        "runner executes only READY work within max_concurrency and leaves dependencies waiting",
        "blocked/no-route/incompatible records do not produce executor success artifacts",
    ),
    AcceptanceCriterion(
        "VS-M1-004",
        "routing records deterministically select exactly one frozen no-model route",
        "NO_ROUTE and route/work incompatibility remain recorded domain outcomes",
    ),
    AcceptanceCriterion(
        "VS-M1-005",
        "recorded execution plus same-work evidence yields a verification completion decision",
        "wrong evidence, duplicate evidence, or non-executed output cannot approve work",
    ),
    AcceptanceCriterion(
        "VS-M1-006",
        "API and web present recorded truth through explicit bounded capabilities",
        "malformed transport, direct web network authority, or draft/canonical mixing fails",
    ),
)


def test_m1_acceptance_criteria_cover_every_vertical_slice() -> None:
    assert {criterion.slice_id for criterion in ACCEPTANCE_CRITERIA} == {
        "VS-M1-001",
        "VS-M1-002",
        "VS-M1-003",
        "VS-M1-004",
        "VS-M1-005",
        "VS-M1-006",
    }
    for criterion in ACCEPTANCE_CRITERIA:
        assert criterion.pass_condition
        assert criterion.fail_condition


def test_vs_m1_001_accepts_intent_as_recorded_cognitive_dag_truth() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")
    config = PersistenceConfig(
        sqlalchemy_url=_postgres_url(),
        schema=f"m1_017_vs001_{uuid4().hex}",
    )
    store = PersistenceStore(config)
    dag_repository = M1WorkDagRepository(store)

    try:
        _wait_for_store_initialization(store)
        with TestClient(_app()) as client:
            accepted = client.post(
                "/m1/intents/decompose",
                json=_intent_payload(objective="Implement a bounded change"),
            )
            rejected = client.post(
                "/m1/intents/decompose",
                json=_intent_payload(
                    objective="Discuss the statusquo of design terms.",
                    ordinal=1,
                    dag_ordinal=1,
                ),
            )

        assert accepted.status_code == 201
        accepted_payload = accepted.json()
        decomposition = accepted_payload["decomposition"]
        assert decomposition["status"] == "SUPPORTED"
        assert accepted_payload["intent"]["objective"] == "Implement a bounded change"

        work_items = _work_items_from_decomposition(accepted_payload)
        work_ids = {str(work.work_id) for work in work_items}
        assert [work.work_type for work in work_items] == list(SUPPORTED_M1_WORK_TYPES)
        _assert_cognitive_records_bind_to_intent_and_work(
            decomposition,
            intent_id=accepted_payload["intent"]["intent_id"],
            work_ids=work_ids,
        )
        _assert_dag_is_acyclic(accepted_payload["dag"])

        dag = WorkDag.from_json_compatible(accepted_payload["dag"])
        stored = dag_repository.create_dag(dag)
        assert dag_repository.read_dag(dag.dag_id) == stored

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            recovered = M1WorkDagRepository(restarted)
            assert recovered.read_dag(dag.dag_id) == stored
        finally:
            restarted.dispose()

        assert rejected.status_code == 201
        rejected_payload = rejected.json()
        assert rejected_payload["decomposition"]["status"] == "UNSUPPORTED"
        assert rejected_payload["dag"] is None
        assert rejected_payload["decomposition"]["work_items"] == []
    finally:
        store.dispose()
        _drop_schema(config)
        _run_compose("stop", "postgres")

    subprocess.run(
        ("docker", "volume", "inspect", POSTGRES_VOLUME),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_vs_m1_002_accepts_capability_agent_assignment_as_recorded_truth() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")
    config = PersistenceConfig(
        sqlalchemy_url=_postgres_url(),
        schema=f"m1_017_vs002_{uuid4().hex}",
    )
    store = PersistenceStore(config)
    agent_repository = M1AgentRepository(store)
    lifecycle_repository = M1AgentLifecycleRepository(store)
    event_store = EventEvidenceRuntimeStore(store)

    try:
        _wait_for_store_initialization(store)
        work = _work(0, "inspect_current_state")
        requirement = work.required_capabilities[0]
        capability = _capability(requirement.capability_id)
        definition = _agent_definition(requirement.capability_id)

        matched = resolve_capability_requirement(
            requirement,
            capabilities=(capability,),
            agent_definitions=(definition,),
        )
        missing = resolve_capability_requirement(
            requirement,
            capabilities=(),
            agent_definitions=(definition,),
        )
        ambiguous = resolve_capability_requirement(
            requirement,
            capabilities=(capability, _capability(requirement.capability_id, key="duplicate")),
            agent_definitions=(definition,),
        )

        assert matched.status is CapabilityResolutionStatus.MATCHED
        assert matched.reason is CapabilityResolutionReason.EXACT_MATCH
        assert missing.status is CapabilityResolutionStatus.MISSING
        assert ambiguous.status is CapabilityResolutionStatus.AMBIGUOUS

        stored_definition = agent_repository.create_definition(definition)
        created_instance = agent_repository.create_instance(
            _agent(work, state=AgentInstanceState.CREATED)
        )
        ready = lifecycle_repository.transition_instance(
            created_instance.instance.agent_instance_id,
            AgentInstanceState.READY,
            event_id=fixed_id(EventId, 20),
            occurred_at=UTC_NOW,
        )
        active = lifecycle_repository.transition_instance(
            created_instance.instance.agent_instance_id,
            AgentInstanceState.ACTIVE,
            event_id=fixed_id(EventId, 21),
            occurred_at=UTC_NOW,
        )

        assert stored_definition.definition == definition
        assert active.instance.work_id == work.work_id
        assert active.instance.state is AgentInstanceState.ACTIVE
        assert ready.event is not None
        assert active.event is not None
        assert event_store.get_event(ready.event.event_id) == ready.event
        assert event_store.get_event(active.event.event_id) == active.event

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            recovered_agents = M1AgentRepository(restarted)
            recovered = recovered_agents.read_instance(created_instance.instance.agent_instance_id)
            assert recovered is not None
            assert recovered.instance == active.instance
        finally:
            restarted.dispose()
    finally:
        store.dispose()
        _drop_schema(config)
        _run_compose("stop", "postgres")


def test_vs_m1_003_and_004_accept_bounded_execution_and_routing_outcomes() -> None:
    first = _work(0, "inspect_current_state")
    second = _work(1, "apply_bounded_change")
    waiting = _work(2, "verify_bounded_change", dependencies=(first.work_id, second.work_id))

    with TestClient(_app()) as client:
        bounded = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(
                work_items=(waiting, second, first),
                routing_decisions=(
                    _selected_decision(waiting),
                    _selected_decision(second),
                    _selected_decision(first),
                ),
                max_concurrency=1,
            ),
        )
        selected_route = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(
                work_items=(first,),
                routing_decisions=(_selected_decision(first),),
                max_concurrency=1,
            ),
        )
        no_route = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(
                work_items=(first,),
                routing_decisions=(_no_route_decision(first),),
                max_concurrency=1,
            ),
        )
        incompatible = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(
                work_items=(first,),
                routing_decisions=(_incompatible_selected_decision(first),),
                max_concurrency=1,
            ),
        )
        inactive_agent = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(
                work_items=(first,),
                routing_decisions=(_selected_decision(first),),
                agents=(_agent(first, state=AgentInstanceState.WAITING),),
                max_concurrency=1,
            ),
        )

    assert bounded.status_code == 200
    bounded_result = bounded.json()["runner_result"]
    bounded_nodes = bounded_result["node_results"]
    assert [node["work_ref"]["ref_id"] for node in bounded_nodes] == [
        str(first.work_id),
        str(second.work_id),
        str(waiting.work_id),
    ]
    assert [node["status"] for node in bounded_nodes] == ["EXECUTED", "DEFERRED", "WAITING"]
    assert len(bounded_result["events"]) == 1
    assert len(bounded_result["evidence_refs"]) == 1

    assert selected_route.status_code == 200
    selected = selected_route.json()["runner_result"]
    assert selected["node_results"][0]["status"] == "EXECUTED"
    assert selected["events"][0]["event_type"] == "executor.deterministic.completed"

    assert no_route.status_code == 200
    assert no_route.json()["runner_result"]["node_results"][0]["reason"] == "NO_ROUTE"
    assert no_route.json()["runner_result"]["events"] == []

    assert incompatible.status_code == 200
    incompatible_result = incompatible.json()["runner_result"]
    assert incompatible_result["node_results"][0]["status"] == "BLOCKED"
    assert incompatible_result["node_results"][0]["reason"] == "ROUTE_NOT_EXECUTABLE"
    assert incompatible_result["events"] == []
    assert incompatible_result["evidence_refs"] == []

    assert inactive_agent.status_code == 409
    assert inactive_agent.json()["detail"]["code"] == "MISSING_AGENT"


def test_vs_m1_005_accepts_only_verification_gated_completion() -> None:
    work = _work(0, "inspect_current_state")
    with TestClient(_app()) as client:
        runner = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(
                work_items=(work,),
                routing_decisions=(_selected_decision(work),),
                max_concurrency=1,
            ),
        )
        assert runner.status_code == 200
        executed_node = runner.json()["runner_result"]["node_results"][0]
        evidence = executed_node["executor_outcome"]["evidence_refs"][0]

        approved = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                executed_node,
                attempts=[_attempt("passed", [evidence])],
            ),
        )
        rejected = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                executed_node,
                attempts=[_attempt("failed", [evidence])],
            ),
        )
        deferred = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                executed_node,
                attempts=[
                    _attempt("inconclusive", [evidence]),
                    _attempt("not_evaluated", [evidence]),
                ],
            ),
        )
        wrong_subject = dict(evidence)
        wrong_subject["subject_ref"] = ObjectReference.from_id(
            fixed_id(WorkId, 9)
        ).to_json_compatible()
        mismatch = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                executed_node,
                attempts=[_attempt("passed", [wrong_subject])],
            ),
        )
        duplicate = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                executed_node,
                attempts=[_attempt("passed", [evidence, evidence])],
            ),
        )
        blocked_runner = client.post(
            "/m1/dag/run-once",
            json=_runner_payload(
                work_items=(work,),
                routing_decisions=(_no_route_decision(work),),
                max_concurrency=1,
            ),
        )
        non_executed = client.post(
            "/m1/verification/complete",
            json=_verification_payload(
                work,
                blocked_runner.json()["runner_result"]["node_results"][0],
                attempts=[_attempt("passed", [evidence])],
            ),
        )

    assert approved.status_code == 200
    assert approved.json()["verification_result"]["completion_decision"] == "APPROVED"
    assert rejected.status_code == 200
    assert rejected.json()["verification_result"]["completion_decision"] == "REJECTED"
    assert deferred.status_code == 200
    assert deferred.json()["verification_result"]["completion_decision"] == "DEFERRED"
    assert mismatch.status_code == 409
    assert mismatch.json()["detail"]["code"] == "EVIDENCE_SUBJECT_MISMATCH"
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"]["code"] == "INVALID_EVIDENCE"
    assert non_executed.status_code == 409
    assert non_executed.json()["detail"]["code"] == "EXECUTION_NOT_COMPLETED"


def test_vs_m1_006_accepts_recorded_truth_api_web_and_safe_error_boundaries() -> None:
    app = _app()
    with TestClient(app) as client:
        openapi = client.get("/openapi.json").json()
        supported = client.post(
            "/m1/intents/decompose",
            json=_intent_payload(objective="Implement a bounded change"),
        )
        scalar_secret = client.post(
            "/m1/intents/decompose",
            content='"token=super-secret password=hunter2"',
            headers={"content-type": "application/json"},
        )
        wrong_media = client.post(
            "/m1/intents/decompose",
            content=json.dumps(_intent_payload(objective="Implement a bounded change")),
            headers={"content-type": "text/plain; Authorization=Bearer secret-token"},
        )

    m1_paths = {path for path in openapi["paths"] if path.startswith("/m1/")}
    assert m1_paths == {
        "/m1/intents/decompose",
        "/m1/dag/run-once",
        "/m1/verification/complete",
    }
    for path in m1_paths:
        operations = openapi["paths"][path]
        assert set(operations) == {"post"}
        request_body = operations["post"]["requestBody"]
        assert request_body["required"] is True
        assert set(request_body["content"]) == {"application/json"}
        assert request_body["content"]["application/json"]["schema"]["type"] == "object"

    assert supported.status_code == 201
    assert supported.json()["decomposition"]["status"] == "SUPPORTED"
    for response in (scalar_secret, wrong_media):
        assert response.status_code == 400
        serialized = json.dumps(dict(response.headers)) + json.dumps(response.json())
        lowered = serialized.lower()
        assert "m1_api_malformed_request" in lowered
        assert "super-secret" not in lowered
        assert "hunter2" not in lowered
        assert "secret-token" not in lowered

    api_boundary = (REPO_ROOT / "apps/web/src/apiBoundary.ts").read_text(encoding="utf-8")
    app_source = (REPO_ROOT / "apps/web/src/App.tsx").read_text(encoding="utf-8")
    app_tests = (REPO_ROOT / "apps/web/src/App.test.tsx").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github/workflows/quality-gates.yml").read_text(encoding="utf-8")

    assert _m1_request_paths_from_api_boundary(api_boundary) == m1_paths
    assert "decomposeM1Intent" in api_boundary
    assert "runM1DagOnce" in api_boundary
    assert "completeM1Verification" in api_boundary
    assert "export async function requestJson" not in api_boundary
    for prohibited in (
        "fetch(",
        "globalThis.fetch",
        "window.fetch",
        "XMLHttpRequest",
        "WebSocket",
        "EventSource",
        "sendBeacon",
        "localStorage",
        "sessionStorage",
        "indexedDB",
    ):
        assert prohibited not in app_source
    assert "does not combine selected intent identity with unsubmitted objective text" in app_tests
    assert "clears downstream M1 truth when a new unsupported intent is accepted" in app_tests
    assert "uv run pytest tests/acceptance -q" in workflow
    assert "docker compose up -d ollama" not in workflow


def _app():
    return create_application(create_api_composition())


def _intent_payload(
    *,
    objective: str,
    ordinal: int = 0,
    dag_ordinal: int = 0,
) -> dict[str, object]:
    return {
        "intent_id": str(fixed_id(IntentId, ordinal)),
        "objective": objective,
        "submitted_at": str(UTC_NOW),
        "created_at": str(UTC_NOW),
        "dag_id": str(fixed_id(WorkDagId, dag_ordinal)),
    }


def _work_items_from_decomposition(payload: dict[str, object]) -> tuple[WorkItem, ...]:
    decomposition = payload["decomposition"]
    assert isinstance(decomposition, dict)
    raw_work_items = decomposition["work_items"]
    assert isinstance(raw_work_items, list)
    return tuple(WorkItem.from_json_compatible(item) for item in raw_work_items)


def _assert_cognitive_records_bind_to_intent_and_work(
    decomposition: dict[str, object],
    *,
    intent_id: str,
    work_ids: set[str],
) -> None:
    assert decomposition["intent_ref"] == {"kind": "intent", "ref_id": intent_id}
    problem = decomposition["problem"]
    plan = decomposition["plan"]
    assumptions = decomposition["assumptions"]
    decisions = decomposition["decisions"]
    assert isinstance(problem, dict)
    assert isinstance(plan, dict)
    assert isinstance(assumptions, list)
    assert isinstance(decisions, list)
    assert problem["intent_ref"] == {"kind": "intent", "ref_id": intent_id}
    assert len(assumptions) == 1
    assert len(decisions) == 1
    assumption = assumptions[0]
    decision = decisions[0]
    assert isinstance(assumption, dict)
    assert isinstance(decision, dict)
    assert assumption["subject_ref"] == {
        "kind": "problem",
        "ref_id": problem["problem_id"],
    }
    assert decision["subject_ref"] == {
        "kind": "problem",
        "ref_id": problem["problem_id"],
    }
    assert plan["problem_ref"] == {"kind": "problem", "ref_id": problem["problem_id"]}
    assert plan["assumption_refs"] == [
        {"kind": "assumption", "ref_id": assumption["assumption_id"]}
    ]
    assert plan["decision_refs"] == [{"kind": "decision", "ref_id": decision["decision_id"]}]
    assert {ref["ref_id"] for ref in plan["work_refs"]} == work_ids
    assert all(ref["kind"] == "work" for ref in plan["work_refs"])


def _assert_dag_is_acyclic(raw_dag: object) -> None:
    assert isinstance(raw_dag, dict)
    raw_nodes = raw_dag["nodes"]
    raw_edges = raw_dag["edges"]
    assert isinstance(raw_nodes, list)
    assert isinstance(raw_edges, list)
    dependencies_by_work_id: dict[str, list[str]] = {}
    for raw_node in raw_nodes:
        assert isinstance(raw_node, dict)
        work_ref = raw_node["work_ref"]
        assert isinstance(work_ref, dict)
        dependencies_by_work_id[work_ref["ref_id"]] = []
    for raw_edge in raw_edges:
        assert isinstance(raw_edge, dict)
        upstream_ref = raw_edge["upstream_work_ref"]
        downstream_ref = raw_edge["downstream_work_ref"]
        assert isinstance(upstream_ref, dict)
        assert isinstance(downstream_ref, dict)
        assert upstream_ref["kind"] == "work"
        assert downstream_ref["kind"] == "work"
        dependencies_by_work_id[downstream_ref["ref_id"]].append(upstream_ref["ref_id"])

    visited: set[str] = set()
    active: set[str] = set()

    def visit(work_id: str) -> None:
        assert work_id not in active
        if work_id in visited:
            return
        active.add(work_id)
        for dependency in dependencies_by_work_id[work_id]:
            assert dependency in dependencies_by_work_id
            visit(dependency)
        active.remove(work_id)
        visited.add(work_id)

    for work_id in dependencies_by_work_id:
        visit(work_id)
    assert visited == set(dependencies_by_work_id)


def _m1_request_paths_from_api_boundary(source: str) -> set[str]:
    return set(re.findall(r'return requestJson<[^>]+>\("(/m1/[^"]+)"', source))


def _capability(capability_id: CapabilityId, *, key: str = "bounded_m1") -> Capability:
    return Capability(
        capability_id=capability_id,
        key=key,
        version=SchemaVersion(1, 0, 0),
        description="Deterministic M1 acceptance capability.",
        category=CapabilityCategory.EXECUTION,
    )


def _agent_definition(capability_id: CapabilityId, ordinal: int = 0) -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId, ordinal),
        name=f"m1_acceptance_agent_{ordinal}",
        version=SchemaVersion(1, 0, 0),
        purpose="Handle deterministic M1 acceptance work.",
        allowed_capability_ids=(capability_id,),
    )


def _agent(
    work: WorkItem,
    *,
    ordinal: int = 0,
    state: AgentInstanceState = AgentInstanceState.ACTIVE,
) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId, ordinal),
        agent_definition_id=fixed_id(AgentDefinitionId, ordinal),
        work_id=work.work_id,
        state=state,
        created_at=UTC_NOW,
        started_at=UTC_NOW if state is AgentInstanceState.ACTIVE else None,
    )


def _work(
    ordinal: int,
    work_type: str,
    *,
    dependencies: tuple[WorkId, ...] = (),
    state: WorkItemState = WorkItemState.READY,
) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal),
        work_type=work_type,
        title=work_type.replace("_", " ").title(),
        objective=f"Accept {work_type}.",
        dependencies=dependencies,
        required_capabilities=(
            CapabilityRequirement(capability_id=fixed_id(CapabilityId, ordinal)),
        ),
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=state,
    )


def _selected_decision(work: WorkItem) -> RoutingDecisionRecord:
    return select_m1_route(
        RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId, _ordinal_from_id(work.work_id)),
            work=work,
            candidates=(
                RoutingCandidate.deterministic_executor(
                    work_id=work.work_id,
                    executor_name="deterministic_m1",
                    supported_work_types=SUPPORTED_M1_WORK_TYPES,
                ),
            ),
            requested_at=UTC_NOW,
            producer_ref=ref_for(ProviderId),
            observability_context=ObservabilityContext(
                work_id=work.work_id,
                trace_id=fixed_id(TraceId),
            ),
            resource_constraints={"local_only": True},
        )
    )


def _no_route_decision(work: WorkItem) -> RoutingDecisionRecord:
    return select_m1_route(
        RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId, 8),
            work=work,
            candidates=(),
            requested_at=UTC_NOW,
            producer_ref=ref_for(ProviderId),
            observability_context=ObservabilityContext(
                work_id=work.work_id,
                trace_id=fixed_id(TraceId),
            ),
            resource_constraints={"local_only": True},
        )
    )


def _incompatible_selected_decision(work: WorkItem) -> RoutingDecisionRecord:
    candidate = RoutingCandidate(
        candidate_key="executor_deterministic_m1",
        kind=RouteCandidateKind.DETERMINISTIC_EXECUTOR,
        work_ref=ObjectReference.from_id(work.work_id),
        executor_name="deterministic_m1",
        supported_work_types=("unrelated_work_type",),
    )
    return RoutingDecisionRecord(
        decision_id=fixed_id(DecisionId, 9),
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
        observability_context=ObservabilityContext(
            work_id=work.work_id,
            trace_id=fixed_id(TraceId),
        ),
    )


def _runner_payload(
    *,
    work_items: tuple[WorkItem, ...],
    routing_decisions: tuple[RoutingDecisionRecord, ...],
    max_concurrency: int,
    agents: tuple[AgentInstance, ...] | None = None,
) -> dict[str, object]:
    active_agents = agents or tuple(
        _agent(work, ordinal=index) for index, work in enumerate(work_items)
    )
    return {
        "dag": WorkDag.from_work_items(
            fixed_id(WorkDagId),
            work_items,
            created_at=UTC_NOW,
        ).to_json_compatible(),
        "work_items": [work.to_json_compatible() for work in work_items],
        "routing_decisions": [decision.to_json_compatible() for decision in routing_decisions],
        "agent_instances": [agent.to_json_compatible() for agent in active_agents],
        "capability_resolutions_by_work_id": {
            str(work.work_id): [_resolution(work, ordinal=index).to_json_compatible()]
            for index, work in enumerate(work_items)
        },
        "event_ids_by_work_id": {
            str(work.work_id): str(fixed_id(EventId, index))
            for index, work in enumerate(work_items)
        },
        "evidence_ids_by_work_id": {
            str(work.work_id): str(fixed_id(EvidenceId, index))
            for index, work in enumerate(work_items)
        },
        "producer_ref": ref_for(ProviderId).to_json_compatible(),
        "occurred_at": str(UTC_NOW),
        "observability_context": ObservabilityContext(
            trace_id=fixed_id(TraceId),
            work_id=work_items[0].work_id if work_items else None,
        ).to_json_compatible(),
        "max_concurrency": max_concurrency,
    }


def _resolution(work: WorkItem, ordinal: int) -> CapabilityResolution:
    return CapabilityResolution(
        requirement=work.required_capabilities[0],
        status=CapabilityResolutionStatus.MATCHED,
        reason=CapabilityResolutionReason.EXACT_MATCH,
        capability_ref=ObjectReference.from_id(work.required_capabilities[0].capability_id),
        agent_definition_ref=ObjectReference.from_id(fixed_id(AgentDefinitionId, ordinal)),
    )


def _verification_payload(
    work: WorkItem,
    runner_node_result: dict[str, object],
    *,
    attempts: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "work": work.to_json_compatible(),
        "runner_node_result": runner_node_result,
        "attempts": attempts,
        "max_iterations": 2,
        "verification_id": str(fixed_id(VerificationId)),
        "event_id": str(fixed_id(EventId, 30)),
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


def _ordinal_from_id(work_id: WorkId) -> int:
    return int(str(work_id)[-1], 36) % 10


def _wait_for_store_initialization(store: PersistenceStore) -> None:
    last_error: PersistenceError | None = None
    for _ in range(30):
        try:
            store.initialize()
            return
        except PersistenceError as exc:
            last_error = exc
            time.sleep(1)
    assert last_error is not None
    raise last_error


def _drop_schema(config: PersistenceConfig) -> None:
    if config.schema is None:
        return
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{config.schema}" CASCADE'))
    finally:
        engine.dispose()


def _postgres_url() -> str:
    user = quote(_env_value("CURIOS_POSTGRES_USER"), safe="")
    credential = quote(_env_value("CURIOS_POSTGRES_PASSWORD"), safe="")
    host = os.environ.get("CURIOS_POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("CURIOS_POSTGRES_PORT", _env_value("CURIOS_POSTGRES_PORT"))
    database = quote(_env_value("CURIOS_POSTGRES_DB"), safe="")
    return f"postgresql+psycopg://{user}:{credential}@{host}:{port}/{database}"


def _env_value(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    prefix = f"{name}="
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    msg = f"missing {name}"
    raise RuntimeError(msg)


def _require_docker() -> None:
    result = subprocess.run(
        ("docker", "info"),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Docker is unavailable: {result.stderr.strip() or result.stdout.strip()}")


def _run_compose(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (*COMPOSE, *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
