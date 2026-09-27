---
id: TASK-M1-017-EVIDENCE
title: TASK-M1-017 Implementation Evidence
task_id: TASK-M1-017
status: IMPLEMENTED / TESTED
artifact_type: implementation_evidence
date: 2026-09-27
---

# TASK-M1-017 Implementation Evidence

## Objective

TASK-M1-017 adds the M1 milestone acceptance suite for the first recorded-truth
cognitive loop. The task is acceptance-only: no production API, web, runtime,
contract, persistence, provider/model, schema, migration, or CI workflow
behavior is changed.

## Prerequisite Proof

Baseline:
`c3ce513a08f1c123a250245b3d0aa651fd9d700e`

Prerequisite state before implementation:

| Prerequisite | Required State | Actual State |
| --- | --- | --- |
| TASK-M1-016 | VALIDATED / FROZEN / INTEGRATED / PUBLISHED / REMOTE-CI-VERIFIED | Satisfied at published baseline. |

No additional non-task entry gate was found. The M1 status ledger row for
TASK-M1-017 was stale (`BLOCKED`) and is reconciled to `IMPLEMENTED, TESTED`
only after the acceptance suite passed.

## Authorized Surface

Changed surfaces are limited to:

- `tests/acceptance/test_m1_acceptance.py`
- `tests/acceptance/test_boot_acceptance.py`
- `tests/security/test_security_baseline.py`
- `docs/tasks/TASK-M1-017-evidence.md`
- `docs/program/status-ledger/M1-status-ledger.md`

The boot acceptance update only expands the existing exact acceptance-file
inventory to include the new M1 acceptance file. The security update authorizes
only the exact TASK-M1-017 acceptance file and evidence.

## Acceptance Matrix

| Acceptance ID | Vertical Slice | Milestone Criterion | Inputs | Boundaries Crossed | Required Recorded Truth | PASS Condition | FAIL Condition | Environment | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1-ACCEPT-001 | VS-M1-001 Intent to DAG | Submit a simple intent and observe canonical cognitive records plus an acyclic durable DAG. | Supported bounded-change intent and unsupported near-miss intent | FastAPI M1 decomposition endpoint, deterministic decomposition, cognitive records, Work DAG, PostgreSQL DAG repository | Intent, Problem, Assumption, Decision, Plan, WorkItems, WorkDag | Supported intent returns linked records, three bounded work items, acyclic DAG, and persisted/recovered DAG identity | Unsupported intent returns `UNSUPPORTED` with no DAG/work items | Local Docker PostgreSQL | `test_vs_m1_001_accepts_intent_as_recorded_cognitive_dag_truth` |
| M1-ACCEPT-002 | VS-M1-002 Capability to Agent Assignment | Deterministically match capability requirement to a disposable agent and lifecycle event truth. | WorkItem capability requirement, matching/missing/duplicate capabilities, agent definition/instance | Capability resolver, agent repository, lifecycle repository, event/evidence runtime store, PostgreSQL | CapabilityResolution, AgentDefinition, AgentInstance, lifecycle events | Exact match resolves, active agent persists/reconstructs, lifecycle events are recorded | Missing/ambiguous capabilities remain bounded and do not become accepted assignment | Local Docker PostgreSQL | `test_vs_m1_002_accepts_capability_agent_assignment_as_recorded_truth` |
| M1-ACCEPT-003 | VS-M1-003 Bounded Parallel Execution | Execute READY work within max concurrency while dependent nodes wait. | Three-node DAG with two independent nodes and one dependent node | M1 API runner, WorkDag readiness, capability resolutions, active agents, routing decisions, bounded runner, deterministic executor seam | Runner node results, executor events, evidence refs | `max_concurrency=1` executes one deterministic READY node, defers the other READY node, and leaves dependent work `WAITING` | Inactive agent fails boundedly | No DB required | `test_vs_m1_003_and_004_accept_bounded_execution_and_routing_outcomes` |
| M1-ACCEPT-004 | VS-M1-004 Routing Decision Record | Route decisions are deterministic no-model records consumed by the runner. | Selected, no-route, and route/work-incompatible decisions | Routing selection, RoutingDecisionRecord, M1 API runner | Selected route, `NO_ROUTE`, `ROUTE_NOT_EXECUTABLE` | Selected deterministic route produces executor outcome without live model generation | `NO_ROUTE` and incompatible route remain domain outcomes with no executor artifacts | No live provider/model | `test_vs_m1_003_and_004_accept_bounded_execution_and_routing_outcomes` |
| M1-ACCEPT-005 | VS-M1-005 Verification-Gated Completion | Work completion is gated by verification evidence, not executor self-report. | Recorded runner output, bound evidence, failed/inconclusive/wrong/duplicate evidence | M1 API runner, evidence reference, M1 API verification endpoint, bounded verification loop | Runner result, EvidenceReference, VerificationResult, verification event | Same-work PASSED evidence approves; FAILED rejects; non-terminal attempts defer | Wrong subject, duplicate evidence, and non-executed output cannot approve | No DB required | `test_vs_m1_005_accepts_only_verification_gated_completion` |
| M1-ACCEPT-006 | VS-M1-006 Recorded-Truth Presentation | API and web present recorded truth through bounded capabilities without becoming authority. | OpenAPI, M1 API requests, malformed transport, web source/tests | FastAPI OpenAPI/runtime routes, M1 transport gates, web API boundary, App authority/provenance tests, CI acceptance command | Exact M1 endpoint surface, safe error payloads, explicit web capabilities | Exact three POST endpoints and web API capabilities exist; M1-014 provenance regression remains covered; CI acceptance command discovers this suite | Non-object JSON/wrong media are bounded safe errors; App direct network/durable storage remains absent | No live backend/model; FastAPI TestClient only | `test_vs_m1_006_accepts_recorded_truth_api_web_and_safe_error_boundaries` |

## PASS/FAIL Semantics

The acceptance suite asserts externally meaningful milestone behavior. It would
fail if cognitive records are mislinked, DAGs become cyclic or non-durable,
capability matching accepts missing/ambiguous capabilities, lifecycle events are
not recorded, max concurrency is ignored, `NO_ROUTE` or `ROUTE_NOT_EXECUTABLE`
are misclassified, verification accepts unbound evidence, M1 API errors leak
secret-shaped input, the web App gains direct network authority, or M1-014's
draft/canonical separation regresses.

## Boundary Results

- Real boundaries: FastAPI M1 API, deterministic decomposition, canonical
  cognitive records, WorkDag, PostgreSQL DAG repository, capability resolver,
  agent repository, lifecycle repository, event/evidence store, routing records,
  bounded DAG runner, deterministic executor seam, verification loop, OpenAPI,
  and web API-boundary source.
- Fakeable boundary: no live provider/model is invoked. Deterministic executor
  and routing records remain the frozen M1 fakeable seams.
- PostgreSQL: VS-M1-001 and VS-M1-002 use local Docker PostgreSQL with unique
  schemas, canonical readback, restart/reconstruction where required, and schema
  cleanup.
- CI discovery: the frozen M1-016 command `uv run pytest tests/acceptance -q`
  discovers the new M1 acceptance file automatically. Acceptance count changed
  from 8 to 14, including six M1 acceptance tests.

## Scope Boundaries

M1-017/M1-018: this task does not create an independent verification record,
declare M1 independently verified, or modify TASK-M1-018 evidence.

M1-017/M1-019: this task does not close M1, create a final freeze record,
release, tag, deploy, or identify a final freeze baseline.

M1-017/M1-016: the existing Quality Gates workflow already invokes
`tests/acceptance`; no CI workflow change was made.

## Verification Snapshot

Focused M1 acceptance execution:

```text
uv run pytest tests/acceptance/test_m1_acceptance.py -q
6 passed, 2 warnings
```

Frozen CI acceptance command:

```text
uv run pytest tests/acceptance -q
14 passed, 2 warnings
```

Complete implementation verification:

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS, 50 packages resolved |
| `uv sync --locked --all-groups --all-packages` | PASS, locked workspace synced |
| `pnpm install --frozen-lockfile` | PASS |
| Docker Compose config | PASS |
| `ruff format --check .` | PASS, 284 files already formatted |
| `ruff check .` | PASS |
| `mypy apps/api/src packages/python/*/src` | PASS, 70 source files |
| `pnpm check` | PASS |
| Web tests | PASS, 26 passed |
| Web typecheck | PASS |
| Web build | PASS |
| Contract/schema | PASS, 16 passed |
| Architecture | PASS, 36 passed |
| Security | PASS, 360 passed |
| M1 package/API gate | PASS, 618 passed, 9 deselected |
| Package-local Python/API/provider suites | PASS, 366 passed |
| M0 runtime/persistence/policy non-integration | PASS, 287 passed, 10 deselected |
| API integration | PASS, 6 passed |
| PostgreSQL provider | PASS, 1 passed |
| M0 PostgreSQL repositories | PASS, 4 passed |
| M1 PostgreSQL repositories | PASS, 4 passed |
| M0 vertical slice | PASS, 2 passed |
| M1 vertical-slice integration | PASS, 6 passed |
| New M1 acceptance suite | PASS, 6 passed |
| Existing and new acceptance suite | PASS, 14 passed |
| Full pytest | PASS, 1175 passed |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |

Docker/PostgreSQL-backed checks were run serially. No PostgreSQL transient
occurred during implementation verification.

Warnings are limited to existing Starlette/httpx and anyio deprecation warnings
emitted through FastAPI `TestClient`, plus the local `VIRTUAL_ENV` mismatch
warning emitted by `uv` in the shared shell environment.

TASK-M1-017 remains awaiting independent validation/freeze.
