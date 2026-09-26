---
id: TASK-M1-006-EVIDENCE
title: TASK-M1-006 Agent Definition and Instance Persistence Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-006
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-006 Evidence

## Objective

Persist and retrieve canonical `AgentDefinition` and disposable
`AgentInstance` records for M1 assignment without redefining agent contracts or
implementing agent lifecycle behavior.

TASK-M1-006 does not implement capability resolution, agent selection,
agent lifecycle transitions, scheduling, execution, provider/model invocation,
policy grants, API routes, frontend behavior, prompt construction, memory, DAG
mutation, retry/cancellation behavior, or TASK-M1-007 event semantics.

## Starting Baseline

`b0b23f4fafd4ae6d9b1e692bec6160e62fd3f41d`

TASK-M1-001 through TASK-M1-005 are integrated, validated, frozen, published,
and remotely CI-verified at this baseline. TASK-M1-001 satisfies the frozen
prerequisite for TASK-M1-006, and the integrated M1 ledger records
TASK-M1-006 as `READY`.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Canonical contract reuse | PASS | `M1AgentRepository` consumes frozen `AgentDefinition` and `AgentInstance` from `curios_contracts`; no shadow agent or reference abstraction was introduced. |
| Agent definition persistence | PASS | `create_definition`, `read_definition`, and `list_definitions` persist, reconstruct, and list canonical definitions with deterministic version tokens. |
| Agent instance persistence | PASS | `create_instance`, `read_instance`, and `list_instances` persist, reconstruct, and list disposable canonical instances bound to `WorkId` and optional `ExecutionId`. |
| Definition/instance relationship | PASS | `create_instance` requires the referenced `AgentDefinition` to already be persisted and fails boundedly with `NOT_FOUND` otherwise. |
| Bounded conflicts | PASS | Duplicate definition and instance IDs translate persistence conflicts to `AgentRepositoryError(CONFLICT)` without leaking SQLAlchemy/psycopg details. |
| Bounded corrupt payloads | PASS | Malformed persisted agent-definition and agent-instance payloads raise `AgentRepositoryError(CORRUPT_RECORD)` with bounded messages. |
| Migration/schema | PASS | `PersistenceRecordKind.AGENT_DEFINITION`, `PersistenceRecordKind.AGENT_INSTANCE`, `curios_m1_agent_definition_records`, `curios_m1_agent_instance_records`, and Alembic revision `0004_m1_agent_records` extend the existing persistence boundary. |
| No lifecycle authority | PASS | The repository has no transition, assign, execute, schedule, retry, cancel, activate, or lifecycle-event methods. Agent state is persisted as canonical input only. |
| Work/execution boundaries | PASS | Agent instances carry canonical `WorkId` and optional `ExecutionId` but do not duplicate `WorkItem` or `ExecutionRecord`, mutate either record, or validate/run execution. |
| Architecture/security guards | PASS | Guard inventories authorize only `curios_runtime.agent_repository`, the persistence extension, focused tests, and evidence; later agent lifecycle/executor/scheduler/runtime surfaces remain blocked. |
| Dependency scope | PASS | No new third-party dependency, package, manifest, or lockfile change was introduced. |

## Files Changed

- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-006-evidence.md`
- `packages/python/curios_persistence/src/curios_persistence/boundary.py`
- `packages/python/curios_persistence/src/curios_persistence/kinds.py`
- `packages/python/curios_persistence/src/curios_persistence/schema.py`
- `packages/python/curios_persistence/src/curios_persistence/migrations/versions/0004_m1_agent_records.py`
- `packages/python/curios_persistence/tests/test_persistence_boundary.py`
- `packages/python/curios_persistence/tests/test_postgres_persistence_integration.py`
- `packages/python/curios_runtime/src/curios_runtime/__init__.py`
- `packages/python/curios_runtime/src/curios_runtime/agent_repository.py`
- `packages/python/curios_runtime/tests/test_agent_repository.py`
- `packages/python/curios_runtime/tests/test_postgres_agent_repository_integration.py`
- `tests/security/test_security_baseline.py`

## Authority Inventory

TASK-M1-006 introduces these authorized capabilities:

- canonical agent definition create/read/list persistence;
- canonical disposable agent instance create/read/list persistence;
- bounded repository errors for conflict, not found, corrupt records, and
  persistence failures;
- PostgreSQL schema tables for agent definitions and instances;
- deterministic reconstruction through the existing persistence primitive.

TASK-M1-006 leaves these absent:

- DAG mutation;
- capability resolution calls;
- policy evaluation or grants;
- provider/model selection or invocation;
- network access;
- agent selection/orchestration/lifecycle transitions;
- work assignment beyond carrying canonical `work_id`;
- scheduling, execution, retry, or cancellation;
- prompt construction, memory access, API behavior, or UI behavior.

## Verification

| Check | Result |
| --- | --- |
| Fresh worktree sync | PASS: `uv sync --locked --all-groups --all-packages` installed the locked workspace into `/home/user/projects/curiosos-wt-m1-006`. Initial focused tests before sync failed to import locked dependencies such as Alembic/FastAPI; after sync this did not recur. |
| Focused M1-006 unit/persistence tests | PASS: `uv run pytest -q packages/python/curios_runtime/tests/test_agent_repository.py packages/python/curios_persistence/tests/test_persistence_boundary.py` passed 31 tests. |
| Security/architecture focused tests | PASS: `uv run pytest -q tests/security/test_security_baseline.py tests/architecture/test_architecture_conformance.py` passed 391 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Python typing focused check | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 63 source files. |
| Python lint focused check | PASS: `uv run ruff check .`. |
| M1-006 PostgreSQL integration | PASS after helper correction: `uv run pytest -q packages/python/curios_runtime/tests/test_postgres_agent_repository_integration.py` passed 1 test. Initial run failed because the new test helper used a no-password PostgreSQL URL; Docker showed `curios-local-docker-postgres-1` was up and healthy. The helper now matches the existing local Docker `.env.example` URL convention. |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` installed locked workspace packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 236 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python typing | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 63 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| M1 regression, contract, schema, architecture, and security tests | PASS: combined slice passed 515 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Package/API/provider/runtime tests | PASS: non-Docker slice passed 166 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Docker-backed integrations | PASS: serial slices passed API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, Work DAG repository 1, M1-006 agent repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: `uv run pytest -q tests/acceptance` passed 8 tests with 2 known deprecation warnings. |
| Full pytest suite | PASS: `uv run pytest -q` passed 815 tests with 2 known FastAPI/Starlette deprecation warnings. |

## Lifecycle State

TASK-M1-006 is `IMPLEMENTED, TESTED`.

Independent validation/freeze is still required before TASK-M1-006 can become
an integrated prerequisite for TASK-M1-007.
