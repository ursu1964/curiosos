---
id: TASK-M1-004-EVIDENCE
title: TASK-M1-004 Work DAG Records and State Evidence
lifecycle: VALIDATED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-004
milestone_id: M1
date: 2026-09-25
---

# TASK-M1-004 Evidence

## Objective

Persist bounded DAG nodes and edges over canonical `WorkItem` references and
derive readiness/terminal dependency state without duplicating work state or
introducing execution authority.

TASK-M1-004 does not implement a production scheduler, distributed execution,
retries, external queues, graph database behavior, executor seams, agent
lifecycle, capability resolution, routing, model/profile discovery, API routes,
frontend authority, prompt/model invocation, or downstream runner behavior.

## Starting Baseline

`e600ca6d665d5996f04c1ccf109cd671742cee68`

TASK-M1-001, TASK-M1-002, and TASK-M1-003 are integrated, validated, frozen,
published, and remotely CI-verified at this baseline. TASK-M1-002 satisfies
the frozen prerequisite for TASK-M1-004.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| DAG identity and bounded shape | PASS | `WorkDagId`, `WorkDag`, `WorkDagNode`, and `WorkDagEdge` define bounded DAG records with maximum node/edge limits and deterministic node/edge ordering. |
| Work references only | PASS | DAG nodes and edges store `ObjectReference` values whose kind must be `work`; no duplicate generic reference abstraction is introduced. |
| No duplicated `WorkItem` state | PASS | Persisted DAG records contain DAG identity, timestamp, work refs, and dependency edges only; canonical `WorkItem` state/capabilities/inputs/outputs remain outside the DAG record. |
| Acyclic dependency edges | PASS | Construction rejects self edges, duplicate nodes, duplicate edges, missing dependency nodes, and cycles with bounded `WorkDagError` codes. |
| Readiness and terminal dependency state | PASS | `derive_work_dag_state()` computes `READY`, `WAITING`, `BLOCKED`, and `TERMINAL` read models from canonical `WorkItem` inputs without mutating or persisting state. |
| Failure/cancellation propagation | PASS | Failed or cancelled dependencies make downstream nodes `BLOCKED`; blocking propagates through dependent nodes while preserving canonical work state unchanged. |
| Reconstruction and serialization | PASS | `WorkDag.to_json_compatible()` and `WorkDag.from_json_compatible()` round-trip deterministically; repository reads reconstruct the same `WorkDag`. |
| Persistence | PASS | `PersistenceRecordKind.WORK_DAG`, `curios_m1_work_dag_records`, and Alembic migration `0003_m1_work_dag_records` persist DAG records through the existing primitive persistence boundary. |
| Architecture direction | PASS | `curios_dag` depends only on authorized inward surfaces: `curios_contracts` and `curios_persistence`; `curios_persistence` does not import `curios_dag`. |
| No unauthorized authority | PASS | No API, UI, provider, network, model, prompt, executor, scheduler, routing, graph runtime, agent, memory, or learning authority is introduced. |
| Dependency scope | PASS | `uv.lock` adds only the local workspace package `curios-dag`; no third-party dependency was added. |

## Files Changed

- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-004-evidence.md`
- `packages/python/curios_dag/pyproject.toml`
- `packages/python/curios_dag/src/curios_dag/__init__.py`
- `packages/python/curios_dag/src/curios_dag/records.py`
- `packages/python/curios_dag/src/curios_dag/py.typed`
- `packages/python/curios_dag/tests/test_task_m1_004_work_dag.py`
- `packages/python/curios_dag/tests/test_postgres_work_dag_repository_integration.py`
- `packages/python/curios_persistence/src/curios_persistence/boundary.py`
- `packages/python/curios_persistence/src/curios_persistence/kinds.py`
- `packages/python/curios_persistence/src/curios_persistence/schema.py`
- `packages/python/curios_persistence/src/curios_persistence/migrations/versions/0003_m1_work_dag_records.py`
- `packages/python/curios_persistence/tests/test_persistence_boundary.py`
- `pyproject.toml`
- `tests/architecture/test_architecture_conformance.py`
- `tests/security/test_security_baseline.py`
- `uv.lock`

## Verification

| Check | Result |
| --- | --- |
| Dependency lock check | PASS: `uv lock --check` resolved 49 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked the locked workspace and installed `curios-dag`. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 225 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python type checking | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 59 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| Focused M1-004 unit tests | PASS: `uv run pytest -q packages/python/curios_dag/tests/test_task_m1_004_work_dag.py` passed 8 tests. |
| Persistence boundary tests | PASS: `uv run pytest -q packages/python/curios_persistence/tests/test_persistence_boundary.py` passed 20 tests. |
| Architecture/security guard slice | PASS: `uv run pytest -q tests/architecture/test_architecture_conformance.py tests/security/test_security_baseline.py` passed 390 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Combined focused implementation slice | PASS: `uv run pytest -q packages/python/curios_dag/tests/test_task_m1_004_work_dag.py packages/python/curios_persistence/tests/test_persistence_boundary.py tests/architecture/test_architecture_conformance.py tests/security/test_security_baseline.py` passed 418 tests with 2 known deprecation warnings. |
| M1-001/M1-002/M1-003 regressions and contract/schema tests | PASS: combined contract/schema/M1/architecture/security slice passed 492 tests with 2 known deprecation warnings. BOOT contract architecture regressions passed 14 tests. |
| Package/API/provider tests | PASS: non-Docker package/API/provider slice passed 157 tests with 2 known deprecation warnings. |
| Docker-backed M1-004 repository integration | PASS: `uv run pytest -q packages/python/curios_dag/tests/test_postgres_work_dag_repository_integration.py` passed 1 test. |
| Docker-backed integrations | PASS: serial Docker slices passed API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, M1-004 DAG repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: `uv run pytest -q tests/acceptance` passed 8 tests with 2 known deprecation warnings. |
| Full pytest suite | PASS on rerun: `uv run pytest -q` passed 791 tests with 2 known deprecation warnings. Initial full-suite attempt passed 790 tests and hit a PostgreSQL connection-refused failure in the M1-004 Docker repository test; the exact failed slice passed immediately in isolation, and full pytest passed on rerun. |

Warnings: `uv` reported that the inherited
`VIRTUAL_ENV=/home/user/projects/curiosos/.venv` did not match the task
worktree `.venv` and was ignored. Architecture/security tests reported the
known FastAPI/Starlette `TestClient` deprecation warnings. The initial
full-suite PostgreSQL failure matched the known local Docker/PostgreSQL
lifecycle/connectivity instability: Docker state showed no running Curios
PostgreSQL container after rapid start/fast-shutdown cycles, and the failure
did not reproduce in the isolated slice or full-suite rerun.

## Lifecycle State

TASK-M1-004 is `VALIDATED, FROZEN`.

Independent validation accepted implementation commit
`f93b4e610c4ac4cff79fa4dfacd8799d9c5ab888`. TASK-M1-004 still requires
integration into the main M1 baseline before downstream tasks may consume it as
an integrated prerequisite.
