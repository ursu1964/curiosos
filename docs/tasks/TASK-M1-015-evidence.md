---
id: TASK-M1-015-EVIDENCE
title: TASK-M1-015 Implementation Evidence
task_id: TASK-M1-015
status: IMPLEMENTED / TESTED
artifact_type: implementation_evidence
date: 2026-09-27
---

# TASK-M1-015 Implementation Evidence

## Objective

TASK-M1-015 adds M1 vertical-slice integration tests for VS-M1-001 through
VS-M1-006. The task is test-only: no production API, web, runtime, contract,
persistence, routing, executor, verification, provider, schema, migration, CI,
or acceptance-suite behavior is changed.

## Prerequisite Proof

Baseline:
`a3e30fc319ad1e3c6e6d38805ca38097bc34349c`

Prerequisites were satisfied before implementation started:

| Prerequisite | Required State | Actual State |
| --- | --- | --- |
| TASK-M1-013 | VALIDATED / FROZEN / INTEGRATED / PUBLISHED / REMOTE-CI-VERIFIED | Satisfied at published baseline. |
| TASK-M1-014 | VALIDATED / FROZEN / INTEGRATED / PUBLISHED / REMOTE-CI-VERIFIED | Satisfied at published baseline. |

No additional non-task entry gate was found. The stale M1 status-ledger row was
reconciled from `BLOCKED` to `IMPLEMENTED, TESTED` after the vertical-slice
tests passed.

## Added Test Surface

`tests/integration/test_m1_vertical_slice_integration.py`

The test surface is authorized by the TASK-M1-015 task pack entry and by the
security baseline registry. M1-016 owns CI quality-gate wiring, so no GitHub
Actions or CI workflow files are modified. M1-017 owns milestone acceptance, so
no acceptance-suite files are modified.

## Vertical-Slice Matrix

| Slice | Test(s) | Boundaries Crossed | Positive Case | Negative Case | DB? | Fake Provider? | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VS-M1-001 Intent to DAG | `test_vs_m1_001_intent_to_dag_crosses_api_and_postgres_persistence` | FastAPI M1 endpoint, canonical intent/decomposition contracts, Work DAG records, PostgreSQL DAG repository | Supported intent decomposes into canonical intent/problem/plan/work DAG and survives repository restart | Unsupported near-miss intent returns canonical `UNSUPPORTED` with no DAG/work items | Yes | No live provider | PASS |
| VS-M1-002 Capability to Agent Assignment | `test_vs_m1_002_capability_agent_assignment_persists_lifecycle_truth` | Capability resolver, agent definition/instance repository, lifecycle repository, event/evidence runtime store, PostgreSQL | Required capability resolves to a disposable agent, transitions to ACTIVE, lifecycle events persist | Missing capability and duplicate capability produce bounded `MISSING`/`AMBIGUOUS` results | Yes | No live provider | PASS |
| VS-M1-003 Bounded Parallel Execution | `test_vs_m1_003_and_004_runner_uses_real_routing_capability_and_agent_gates` | FastAPI M1 runner endpoint, Work DAG readiness, capability resolution, active agent gate, routing decision, bounded DAG runner, deterministic executor seam | Two independent READY nodes execute under `max_concurrency=2`; dependent node remains `WAITING` | Inactive agent fails boundedly; incompatible route blocks without executor artifacts | No | Deterministic executor only | PASS |
| VS-M1-004 Routing Decision Record | `test_vs_m1_003_and_004_runner_uses_real_routing_capability_and_agent_gates`, `test_m1_vertical_slices_are_deterministic_and_secret_safe` | Routing request/decision records, no-route semantics, route/work compatibility, API runner adapter | Deterministic selected route drives runner execution without model generation | `NO_ROUTE` remains a domain outcome; unsupported work type yields `ROUTE_NOT_EXECUTABLE` and no executor evidence | No | No live provider | PASS |
| VS-M1-005 Verification-Gated Completion | `test_vs_m1_005_verification_requires_recorded_execution_and_bound_evidence`, `test_m1_vertical_slices_are_deterministic_and_secret_safe` | FastAPI verification endpoint, recorded runner output, evidence references, bounded verification loop | Recorded execution plus PASSED evidence approves; FAILED evidence rejects; inconclusive attempts defer | Wrong evidence subject, duplicate evidence, and non-executed runner output fail boundedly | No | No live provider | PASS |
| VS-M1-006 Recorded-Truth Presentation | `test_vs_m1_006_api_and_web_boundaries_present_recorded_truth_without_ui_authority` | OpenAPI route surface, M1 API transport gates, frontend API boundary, App authority guard, M1-014 provenance tests | Exact three M1 API endpoints and explicit web API capabilities are present | Non-object JSON and wrong media are bounded safe errors; App has no direct network authority | No | No live provider | PASS |

## Integration Architecture

The integration tests cross real frozen boundaries where required:

- API participation: `POST /m1/intents/decompose`,
  `POST /m1/dag/run-once`, and `POST /m1/verification/complete` are exercised
  through FastAPI `TestClient` request/response serialization.
- Web participation: the frozen web API boundary is checked for exact explicit
  M1 capabilities and paths, and the frozen M1-014 regression coverage is
  retained as the web presentation/provenance guard.
- DAG/capability/agent/routing participation: tests compose canonical
  `WorkItem`, `WorkDag`, `CapabilityResolution`, `AgentDefinition`,
  `AgentInstance`, and `RoutingDecisionRecord` objects.
- Runner participation: tests exercise `BoundedM1DagRunner` through the M1 API
  adapter, including readiness, ordering, concurrency, capability, agent, and
  route/work compatibility gates.
- Verification/evidence participation: tests exercise
  `BoundedM1VerificationLoop` through the M1 API adapter and require recorded
  execution evidence for completion.
- Persistence participation: PostgreSQL-backed DAG, agent, lifecycle, and event
  repositories are used where VS-M1-001 and VS-M1-002 require durable records.
- Provider/model participation: no live provider, model generation, chat,
  embeddings, cloud request, or Ollama dependency is required or invoked.

## Negative, Determinism, And Isolation Coverage

The integration test file includes required negative paths for unsupported
intent, missing/ambiguous capability, inactive agent, `NO_ROUTE`,
`ROUTE_NOT_EXECUTABLE`, wrong evidence subject, duplicate evidence, deferred and
rejected verification, malformed body handling, unsupported media handling, and
safe-error/no-secret boundaries.

Determinism coverage checks stable route decisions and repeated runner results
while treating fresh IDs/timestamps as canonical inputs. PostgreSQL tests use
unique schemas and drop them after execution. No module-global mutable state,
browser durable storage, or live provider state is introduced.

## Production Diff Guard

M1-015 makes no production source changes. The intended implementation diff is
limited to:

- `tests/integration/test_m1_vertical_slice_integration.py`
- `tests/security/test_security_baseline.py`
- `docs/tasks/TASK-M1-015-evidence.md`
- `docs/program/status-ledger/M1-status-ledger.md`

## Verification Snapshot

Focused M1-015 vertical-slice integration execution:

```text
uv run pytest tests/integration/test_m1_vertical_slice_integration.py -q
6 passed, 2 warnings
```

Full implementation verification:

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS |
| `uv sync --locked --all-groups --all-packages` | PASS, 47 packages checked |
| `pnpm install --frozen-lockfile` | PASS |
| Docker Compose config | PASS |
| `ruff format --check .` | PASS, 279 files already formatted |
| `ruff check .` | PASS |
| `mypy apps/api/src packages/python/*/src` | PASS, 70 source files |
| `pnpm check` | PASS |
| Web tests | PASS, 26 passed |
| Web typecheck | PASS |
| Web build | PASS |
| Contract/schema/architecture/security | PASS, 405 passed |
| API suite | PASS, 183 passed |
| Package/provider/runtime/persistence suites | PASS, 484 passed |
| Acceptance | PASS, 8 passed |
| M1-011/M1-012/M1-013/M1-015 regression block | PASS, 220 passed |
| Full pytest | PASS, 1162 passed |

Docker/PostgreSQL serial verification:

| Slice | Result |
| --- | --- |
| PostgreSQL persistence | PASS, 2 passed |
| PostgreSQL provider | PASS, 1 passed |
| Event/evidence repository | PASS, 1 passed |
| Work repository | PASS, 1 passed |
| Work DAG repository | PASS, 1 passed |
| Agent repository | PASS, 1 passed |
| Agent lifecycle repository | PASS, 1 passed |
| Routing repository | PASS, 1 passed |
| API integration | PASS, 6 passed |
| M0 vertical slice | PASS, 2 passed |
| M1 vertical slices | PASS, 6 passed |

Initial Docker/PostgreSQL transient evidence: a package regression run started
concurrently with the M1 vertical-slice integration file failed once with
`connection refused` while the shared local PostgreSQL service was being stopped
by another Docker-backed test. The affected agent-repository slice passed when
rerun serially, all DB-backed slices passed serially, the full package suite
passed (`484 passed`), and full pytest passed (`1162 passed`).

The warning set is limited to existing Starlette/httpx and anyio deprecation
warnings observed through the FastAPI test client, plus the existing local
`VIRTUAL_ENV` mismatch warning emitted by `uv` under the shared shell
environment. Docker/PostgreSQL-backed M1-015 slices passed after starting the
local PostgreSQL service and cleaning their task-local schemas.

TASK-M1-015 remains awaiting independent validation/freeze.
