---
id: TASK-M1-011-VALIDATION-EVIDENCE
title: TASK-M1-011 Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-011
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-011 Validation Evidence

## Scope

Published baseline:
`c0d119a494b3660f83dc195ed171137170c37583`

Implementation:
`15ea02437fea7554b77c9a269e442fd6f4fb16a9`

Correction 1:
`c1547bdc0b115d94657eeaa1cc2bf5c396451e81`

Validation reconstructed TASK-M1-011 from the frozen M1 task pack, M1
implementation DAG, M1 status ledger, M1-004 Work DAG readiness contracts,
M1-007 agent lifecycle contracts, M1-008 executor seam contracts, M1-010
routing decision contracts, TASK-M1-012 boundary, architecture guardrails, and
security constraints.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | TASK-M1-004, TASK-M1-007, TASK-M1-008, and TASK-M1-010 are validated/frozen/integrated/published/remote-CI-verified in the published baseline. |
| Authorized ownership | PASS | Implementation is bounded to M1 runtime modules, tests, evidence, and a narrow security inventory update. No dependency, lockfile, schema, migration, API/UI, provider/model, M1-012, or milestone-closure change is present. |
| DAG readiness | PASS | Runner derives readiness from canonical Work DAG truth. READY nodes may execute; WAITING, BLOCKED, TERMINAL, and concurrency-deferred nodes do not invoke the executor. |
| Deterministic selection | PASS | Node order is canonical work-id order. Reversed inputs and mixed readiness preserve deterministic node outcomes and aggregation order. |
| Concurrency bound | PASS | `max_concurrency` accepts 1 through 8. Invalid values fail boundedly. READY nodes beyond the selected batch are `DEFERRED`; incompatible selected routes do not create slot-refill scheduling. |
| Routing consumption | PASS | M1-010 routing decisions remain inert supplied inputs. Runner does not recompute routing, discover models, rank candidates, mutate routes, or persist replacement routes. |
| Corrected route/work compatibility | PASS | Correction 1 requires selected deterministic executor routes to support the actual `WorkItem.work_type` before executor invocation. Incompatible selected routes return `ROUTE_NOT_EXECUTABLE` with no executor call, event, or evidence. |
| Capability boundary | PASS | Capability-resolution values are passed through to the frozen M1-008 executor seam. Runner does not reimplement matching, fall back on missing capability, or silently choose ambiguous capability results. |
| Agent gate | PASS | Only active AgentInstance inputs for the routed work are eligible. Missing or duplicate active agents fail boundedly; runner does not transition agents or emit lifecycle events. |
| Executor boundary | PASS | Runner invokes only the injected `M1Executor` seam after M1-011 preconditions pass. It does not invoke providers, models, plugins, arbitrary callbacks, or network. |
| Event/evidence surfacing | PASS | Executor-owned `EventEnvelope` and `EvidenceReference` values are surfaced unchanged for executed nodes in deterministic order. Runner does not forge, persist, or mutate event/evidence records. |
| Mixed outcomes | PASS | A compatible READY node can execute while an incompatible READY node is bounded and a dependent node waits; the valid result is not corrupted by the bounded route failure. |
| No mutation/persistence | PASS | Runner has no DB/persistence imports or calls and does not mutate WorkItem, WorkDag, AgentInstance, RoutingDecisionRecord, ExecutionRecord, Result, event, or evidence state. |
| Restart/recovery boundary | PASS | Restart semantics are limited to recomputing from supplied recorded truth. Durable runner recovery, verification-gated completion, and retry orchestration remain downstream. |
| Safe-error/no-secret | PASS | Runner-generated bounded errors use fixed messages and do not expose provider/routing secret-shaped text. Executor-owned outputs are not rewritten. |
| M1-012 boundary | PASS | Verification loop, evidence binding, completion decision, recovery coordinator, API/web behavior, and milestone closure remain absent. |

## Original Defect Re-Validation

Independent validation originally failed because a selected route with:

- `selected_route.kind = DETERMINISTIC_EXECUTOR`;
- `selected_route.supported_work_types = ("apply_bounded_change",)`;
- routed `WorkItem.work_type = "inspect_current_state"`;

was treated as executable and reached the injected executor.

Correction 1 was independently rechecked:

- compatible selected deterministic route -> exactly one executor invocation;
- incompatible selected deterministic route -> `BLOCKED` /
  `ROUTE_NOT_EXECUTABLE`;
- incompatible selected route -> no executor outcome, event, or evidence;
- mixed DAG -> compatible work executes, incompatible work is bounded, waiting
  work remains waiting;
- incompatible selected route among the first READY nodes consumes the
  selected-node concurrency budget and does not create replacement scheduling.

## Route/Work Compatibility Audit

| Relationship | Result |
| --- | --- |
| routing decision `work_ref` -> WorkItem | PASS: decisions are keyed by canonical work ref; wrong-kind work refs fail through `_work_id()`. |
| selected route `work_ref` -> decision work | PASS: enforced by `RoutingDecisionRecord`. |
| selected route kind | PASS: only `DETERMINISTIC_EXECUTOR` can reach executor request construction. |
| selected route supported work type | PASS: Correction 1 requires exact `WorkItem.work_type` membership in `supported_work_types`. |
| model-profile selected route | PASS: bounded `ROUTE_NOT_EXECUTABLE`, no provider/model/executor invocation. |
| no-route decision | PASS: bounded `NO_ROUTE`, no fallback route selection. |
| route rationale/provider metadata | PASS: not copied into runner-generated error or node-result surfaces. |

## Authority And Guard Review

The runner remains a bounded in-memory local pass over supplied canonical
inputs. It has:

- no scheduler daemon, external queue, retry engine, or cancellation engine;
- no provider/model/Ollama/cloud import or call;
- no persistence store, database write, repository mutation, or event/evidence
  persistence;
- no WorkItem, WorkDag, AgentInstance, RoutingDecisionRecord, or
  ExecutionRecord mutation;
- no API, UI, prompt, memory, or policy-grant authority.

Security guard changes remain bounded to the exact M1-011 runner surface and
validation evidence. No broad `curios_runtime` authority exemption was added.

## Delta Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_runtime/src/curios_runtime/m1_bounded_dag_runner.py` | REQUIRED | Owns the bounded runner and Correction 1 route/work compatibility gate. |
| `packages/python/curios_runtime/src/curios_runtime/__init__.py` | JUSTIFIED SUPPORT | Exports authorized M1-011 runner symbols from the implementation commit. |
| `packages/python/curios_runtime/tests/test_task_m1_011_bounded_dag_runner.py` | REQUIRED | Focused implementation tests for runner behavior. |
| `packages/python/curios_runtime/tests/test_task_m1_011_validation_regressions.py` | REQUIRED VALIDATION SUPPORT | Preserves Correction 1 and route/work compatibility regressions. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Adds bounded authorization for the exact M1-011 runner surface and evidence files. |
| `docs/tasks/TASK-M1-011-evidence.md` | REQUIRED | Implementation and Correction 1 evidence. |
| `docs/tasks/TASK-M1-011-validation-evidence.md` | REQUIRED | Independent validation/freeze evidence. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Advances TASK-M1-011 from `IMPLEMENTED, TESTED` to `VALIDATED, FROZEN`. |

No changed file was classified as out of scope.

## Verification

Pre-record validation checks:

| Check | Result |
| --- | --- |
| History | PASS: `c0d119a -> 15ea024 -> c1547bd` ancestry verified. |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker Compose configuration | PASS: `docker compose -f infrastructure/local/docker/compose.yaml config -q`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 264 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python typing | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 69 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests/typecheck/build | PASS: 6 web tests, direct web typecheck, and production build transformed 18 modules. |
| Contract/schema/architecture/security | PASS: 406 tests with 2 inherited FastAPI/Starlette warnings. |
| M1-001 through M1-011 focused regressions | PASS: 200 tests. |
| Package/API/provider/runtime/persistence non-Docker suite | PASS: 523 tests with 2 inherited FastAPI/Starlette warnings. |
| Docker-backed serial integrations | PASS: API 6, PostgreSQL provider 1, persistence 2, event/evidence 1, work repository 1, Work DAG repository 1, agent repository 1, agent lifecycle repository 1, routing repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: 8 tests with 2 inherited FastAPI/Starlette warnings. |
| Full pytest | INITIAL: 953 passed, then Work DAG PostgreSQL integration failed with `Connection refused`; Docker inspection showed `curios-local-docker-postgres-1` exited cleanly and the expected `curios-local-docker_postgres_data` volume remained. ISOLATED RERUN: affected Work DAG integration passed 1 test. FINAL FULL RERUN: 954 passed with 2 inherited FastAPI/Starlette warnings. |

Post-record verification reran:

- `uv run ruff format --check .`;
- `uv run ruff check .`;
- `uv run mypy apps/api/src packages/python/*/src`;
- `uv run pytest tests/security -q`;
- `uv run pytest packages/python/curios_runtime/tests/test_task_m1_011_bounded_dag_runner.py packages/python/curios_runtime/tests/test_task_m1_011_validation_regressions.py -q`;
- `uv run pytest -q`;
- `git diff --check`;
- `git diff --cached --check`.

Known warnings:

- `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` does not match the task
  worktree `.venv`; `uv` ignored it.
- FastAPI/Starlette `TestClient` deprecation warnings remain inherited.

No skipped or deselected tests were counted as passed.

## Decision

TASK-M1-011 is `VALIDATED, FROZEN`.

TASK-M1-012 remains blocked until TASK-M1-011 is integrated into the main M1
baseline. TASK-M1-013 and later tasks remain blocked by their documented
prerequisite chains.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-012 implementation, or milestone closure was performed.
