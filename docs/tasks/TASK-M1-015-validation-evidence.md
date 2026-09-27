---
id: TASK-M1-015-VALIDATION-EVIDENCE
title: TASK-M1-015 Independent Validation Evidence
task_id: TASK-M1-015
status: VALIDATED / FROZEN
artifact_type: validation_evidence
date: 2026-09-27
---

# TASK-M1-015 Independent Validation Evidence

## Scope

Independent validation covered TASK-M1-015 as a test/proof task. No production
source behavior was modified. The implementation under validation was
`ff98e439a79e0ba70fe46909c9b2feaf6157e90e` on branch
`task/m1-015-vertical-slice-integration-tests`.

Published baseline:
`a3e30fc319ad1e3c6e6d38805ca38097bc34349c`

## Delta Review

Changed implementation files were limited to:

- `tests/integration/test_m1_vertical_slice_integration.py` - REQUIRED
- `docs/tasks/TASK-M1-015-evidence.md` - REQUIRED
- `docs/program/status-ledger/M1-status-ledger.md` - REQUIRED
- `tests/security/test_security_baseline.py` - JUSTIFIED SUPPORT

Validation added stricter independent assertions to the existing M1-015
integration test file for cognitive decomposition links, DAG acyclicity, and
OpenAPI/runtime API-boundary shape. These are validation-strengthening test
assertions only; no product implementation was changed.

Production diff audit:

```text
git diff a3e30fc319ad1e3c6e6d38805ca38097bc34349c -- apps packages infrastructure
```

Result: no production source delta.

## Acceptance Mapping

| VS | Authoritative Requirement | Test | Real Boundaries | Fake Boundaries | Positive | Negative | Durable Effects | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VS-M1-001 | Submit simple intent and observe canonical cognitive records plus acyclic Work DAG. | `test_vs_m1_001_intent_to_dag_crosses_api_and_postgres_persistence` | FastAPI M1 API, deterministic decomposition, canonical Intent/Problem/Assumption/Decision/Plan/WorkItem, WorkDag, PostgreSQL DAG repository | None | Supported intent returns linked cognitive records, three work items, acyclic DAG, and persisted/recovered DAG | Unsupported near-miss returns `UNSUPPORTED` with no DAG/work items | PostgreSQL schema-local DAG persistence | PASS |
| VS-M1-002 | Deterministically match task capability requirements to a disposable agent instance. | `test_vs_m1_002_capability_agent_assignment_persists_lifecycle_truth` | Capability resolver, CapabilityRequirement, Capability, AgentDefinition, AgentInstance, agent repository, lifecycle repository, EventEvidenceRuntimeStore, PostgreSQL | None | Capability resolves to agent, instance transitions to ACTIVE, lifecycle events persist/recover | Missing and duplicate capability produce bounded `MISSING`/`AMBIGUOUS` | PostgreSQL schema-local agent/lifecycle/event persistence | PASS |
| VS-M1-003 | Execute independent DAG nodes up to fixed concurrency while dependent nodes wait. | `test_vs_m1_003_and_004_runner_uses_real_routing_capability_and_agent_gates` | FastAPI runner endpoint, WorkDag readiness, routing decision input, capability resolution input, active agent gate, BoundedM1DagRunner, deterministic executor seam | Deterministic executor boundary only; no live provider | Two independent READY nodes execute under `max_concurrency=2`; dependent node remains `WAITING`; ordering is deterministic | Inactive agent fails boundedly | No DB required by slice | PASS |
| VS-M1-004 | Record deterministic/no-model route decisions without live generation. | `test_vs_m1_003_and_004_runner_uses_real_routing_capability_and_agent_gates`; `test_m1_vertical_slices_are_deterministic_and_secret_safe` | M1 routing selection, RoutingDecisionRecord, runner route consumption, route/work compatibility | No live provider/model | Exactly one valid deterministic route is selected and consumed by runner | `NO_ROUTE` remains domain truth; incompatible route yields `ROUTE_NOT_EXECUTABLE` without executor artifacts | No DB required by slice | PASS |
| VS-M1-005 | Completion requires verification evidence, not executor self-report. | `test_vs_m1_005_verification_requires_recorded_execution_and_bound_evidence`; `test_m1_vertical_slices_are_deterministic_and_secret_safe` | FastAPI verification endpoint, recorded runner output, Result, EvidenceReference, BoundedM1VerificationLoop, VerificationReference/event | None | Successful recorded execution plus bound PASSED evidence approves; FAILED rejects; inconclusive defers | Wrong evidence subject, duplicate evidence, and non-executed runner output fail boundedly | No DB required by slice | PASS |
| VS-M1-006 | API/web display recorded cognitive/DAG/agent/routing/verification truth without becoming authority. | `test_vs_m1_006_api_and_web_boundaries_present_recorded_truth_without_ui_authority`; frozen web suite | FastAPI OpenAPI/runtime M1 endpoints, M1 transport gates, explicit web API capabilities, App authority guard, M1-014 provenance regressions | Web tests use fake fetch as the authorized inbound API-boundary seam; no browser E2E | Exact three M1 POST endpoints expose required JSON object bodies; web boundary exposes only explicit M1 capabilities; App has no direct network authority | Non-object JSON and wrong media return bounded safe errors; A+B provenance regression remains covered by web tests | No DB required by slice | PASS |

## Test Strength

The M1-015 tests would fail if:

- decomposition omitted or mis-linked Problem/Assumption/Decision/Plan records;
- Work DAG node refs no longer matched WorkItems or introduced a cycle;
- PostgreSQL repositories stopped preserving DAG/agent/event identity;
- capability matching returned wrong missing/ambiguous outcomes;
- lifecycle transitions stopped persisting canonical events;
- bounded runner ignored readiness, deterministic ordering, active-agent gates,
  route/work compatibility, or `max_concurrency`;
- routing returned `NO_ROUTE`/selected-route semantics incorrectly;
- verification accepted wrong-work evidence, duplicate evidence, or non-executed
  runner output;
- API transport corrections leaked raw malformed body/media text;
- M1 OpenAPI stopped declaring the exact three application/json object POST
  endpoints;
- App gained direct network authority or M1-014 provenance regressions were
  removed.

## Boundary Audit

Real Curios boundaries used: canonical contracts, deterministic decomposition,
WorkDag construction/repository, capability resolver, agent repositories,
lifecycle events, routing selection/records, bounded DAG runner, deterministic
executor seam, verification loop, FastAPI M1 adapter, OpenAPI generation, web
API-boundary declarations, and existing web component tests.

Faked boundary: external provider/model behavior is represented only by frozen
deterministic local records/seams. This is authorized because M1-015 explicitly
requires no live model.

No test uses SQLite, repository stubs, live Ollama, chat/generation/embedding,
cloud APIs, credentials, or browser durable state.

## PostgreSQL Authenticity And Isolation

DB-backed slices use local Docker PostgreSQL through the established compose
file and `PersistenceStore`. Each slice uses a unique schema and drops it after
the test. Repository readback is performed after persistence and after store
restart where required. This proves durable reconstruction separately from the
known shared Docker service lifecycle behavior.

## Scope Boundaries

M1-015/M1-016: no CI workflow, CI command, matrix, branch-protection, release,
deployment, or GitHub Actions change was made.

M1-015/M1-017: no acceptance-suite ownership was claimed. Existing acceptance
tests were run as regression only; M1-017 remains the owner of M1 acceptance.

TASK-M1-016 remains blocked until TASK-M1-015 is integrated/published according
to the program lifecycle.

## Verification

Focused validation after strengthened assertions:

```text
uv run pytest tests/integration/test_m1_vertical_slice_integration.py -q
6 passed, 2 warnings
```

Complete verification was rerun after validation records changed; final counts
were:

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS |
| `uv sync --locked --all-groups --all-packages` | PASS, 47 packages checked |
| `pnpm install --frozen-lockfile` | PASS |
| Docker Compose config | PASS |
| `ruff format --check .` | PASS, 280 files already formatted |
| `ruff check .` | PASS |
| `mypy apps/api/src packages/python/*/src` | PASS, 70 source files |
| `pnpm check` | PASS |
| Web tests | PASS, 26 passed |
| Web typecheck | PASS |
| Web build | PASS |
| Contract/schema/architecture/security | PASS, 405 passed |
| API suite | PASS, 183 passed |
| M1-015 vertical slices | PASS, 6 passed |
| M1-011/M1-012 focused regressions | PASS, 31 passed |
| Package/provider/runtime/persistence suites | PASS, 484 passed |
| Docker-backed serial API slice | PASS, 6 passed |
| Docker-backed serial provider/persistence slices | PASS, 3 passed |
| Docker-backed serial event/work/DAG slices | PASS, 3 passed |
| Docker-backed serial agent/lifecycle/routing/M0/M1 slices | PASS, 11 passed |
| Acceptance | PASS, 8 passed |
| Full pytest | PASS, 1162 passed |

No Docker/PostgreSQL transient occurred during the validation verification run.
The implementation evidence retains the earlier implementation-time transient
record separately.

TASK-M1-015 is validated and frozen. It remains unmerged and unpublished.
