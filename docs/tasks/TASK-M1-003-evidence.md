---
id: TASK-M1-003-EVIDENCE
title: TASK-M1-003 Deterministic Intent Decomposition Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-003
milestone_id: M1
date: 2026-09-25
---

# TASK-M1-003 Evidence

## Objective

Implement deterministic/template decomposition from a simple `Intent` to an
inert bounded `Plan` plus canonical `WorkItem` proposals.

TASK-M1-003 does not implement model-backed planning, prompts, learning,
persistence, DAG records, execution, capability resolution, agent lifecycle,
API routes, frontend authority, provider coupling, DataLab analysis, or
downstream executor behavior.

## Starting Baseline

`beec99e887157383afe48ef8e120cd2b4a31caa8`

TASK-M1-002 is `VALIDATED, FROZEN`, integrated, published, and remotely
CI-verified at this baseline, satisfying the TASK-M1-003 prerequisite.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Fixed supported intent categories | PASS | `SUPPORTED_INTENT_CATEGORIES` contains only `recorded_truth_summary` and `implementation_plan`. |
| Deterministic decomposition | PASS | IDs are derived from the template version, typed ID prefix, category, intent ID, and stable component keys; repeated input returns equal JSON-compatible output. |
| Bounded plan/work-DAG proposal | PASS | Supported results return one `Problem`, one `Assumption`, one `Decision`, one `Plan`, and three canonical `WorkItem` proposals with explicit acyclic dependencies. |
| Use canonical references | PASS | Cross-record links and `Plan.work_refs` use `ObjectReference`; no parallel generic reference abstraction is introduced. |
| Do not duplicate `WorkItem` state | PASS | Work proposals are canonical `WorkItem` instances; `Plan` continues to reference work through `work_refs` only. |
| Unsupported intent failure | PASS | Unsupported input returns `UNSUPPORTED` with `NO_TEMPLATE_MATCH`, no problem, no plan, no decisions, and no work items. |
| No runtime or infrastructure authority | PASS | `curios_cognitive` depends only on `curios_contracts`; architecture/security tests reject API, persistence, provider, runtime, workflow, and deferred M1 imports. |
| No external dependency expansion | PASS | No third-party dependency was added; only the local workspace package registration changed. |

## Files Changed

- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-003-evidence.md`
- `packages/python/curios_cognitive/pyproject.toml`
- `packages/python/curios_cognitive/src/curios_cognitive/__init__.py`
- `packages/python/curios_cognitive/src/curios_cognitive/decomposition.py`
- `packages/python/curios_cognitive/src/curios_cognitive/py.typed`
- `packages/python/curios_cognitive/tests/test_task_m1_003_decomposition.py`
- `pyproject.toml`
- `tests/architecture/test_architecture_conformance.py`
- `tests/security/test_security_baseline.py`

## Verification

| Check | Result |
| --- | --- |
| Dependency lock check | PASS: `uv lock --check` resolved 48 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` built/installed all workspace packages, including `curios-cognitive`. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 217 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python type checking | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 56 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| TASK-M1-003 focused tests | PASS: `uv run pytest -q packages/python/curios_cognitive/tests/test_task_m1_003_decomposition.py` passed 9 tests. |
| TASK-M1-001/TASK-M1-002 regression and contract/schema tests | PASS: `uv run pytest -q packages/python/curios_contracts/tests/test_task_m1_002_cognitive_contracts.py tests/contract tests/schema` passed 23 tests. |
| Architecture/security tests | PASS: `uv run pytest -q tests/security/test_security_baseline.py tests/architecture/test_architecture_conformance.py` passed 390 tests. |
| Docker-backed API integration | PASS: `uv run pytest -q tests/integration/test_api_integration.py` passed 6 tests. |
| Docker-backed PostgreSQL provider integration | PASS: `uv run pytest -q tests/integration/test_postgres_provider_integration.py` passed 1 test. |
| Docker-backed persistence integration | PASS: `uv run pytest -q packages/python/curios_persistence/tests/test_postgres_persistence_integration.py` passed 2 tests. |
| Docker-backed event/evidence runtime integration | PASS: `uv run pytest -q packages/python/curios_runtime/tests/test_postgres_event_evidence_store_integration.py` passed 1 test. |
| Docker-backed work repository integration | PASS: `uv run pytest -q packages/python/curios_runtime/tests/test_postgres_work_repository_integration.py` passed 1 test. |
| M0 vertical slice integration | PASS: `uv run pytest -q tests/integration/test_m0_vertical_slice_integration.py` passed 2 tests. |
| Acceptance tests | PASS: `uv run pytest -q tests/acceptance` passed 8 tests. |
| Full pytest suite | PASS: `uv run pytest -q` passed 739 tests. |
| Repository diff integrity | PASS: `git diff --check` and `git diff --cached --check`. |

Warnings: FastAPI/Starlette `TestClient` deprecation warnings appeared in
security, integration, acceptance, and full pytest runs. `uv` also warned that
the inherited `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` did not match
the task worktree `.venv` and was ignored.

## Correction 1

Independent validation found that unsupported near-miss intents were classified
as supported because `_select_template()` used substring matching. Examples:

- `Address a philosophical question.` matched keyword `add`.
- `Discuss the statusquo of design terms.` matched keyword `status`.

Correction 1 replaces substring matching with deterministic complete-token
matching over the existing normalized objective text. It adds validator
regression coverage for:

- the two validation-discovered near misses;
- every configured keyword as a complete supported token;
- every configured keyword embedded at the beginning, end, and middle of a
  larger token;
- capitalization and punctuation adjacency for complete-token matches;
- unsupported output invariants: `UNSUPPORTED`, `NO_TEMPLATE_MATCH`, and no
  `Problem`, `Assumption`, `Decision`, `Plan`, or `WorkItem` proposal state.

Correction 1 verification:

| Check | Result |
| --- | --- |
| Pre-correction validator regression | FAIL as expected: 2 failed, 9 passed. |
| Validator regression after correction | PASS: `uv run pytest -q packages/python/curios_cognitive/tests/test_task_m1_003_validation_regressions.py` passed 42 tests. |
| M1-003 package tests after correction | PASS: `uv run pytest -q packages/python/curios_cognitive/tests` passed 51 tests. |
| M1-003 + M1-002 contract/schema regression | PASS: 74 tests. |
| Architecture/security tests | PASS: 390 tests, 2 known deprecation warnings. |
| Package/API/provider tests | PASS: 182 tests, 2 known deprecation warnings. |
| Docker-backed integrations | PASS: API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, M0 vertical slice 2. |
| Acceptance tests | PASS: 8 tests, 2 known deprecation warnings. |
| Full pytest suite | PASS on rerun: 781 tests, 2 known deprecation warnings. An earlier full-suite attempt hit a transient PostgreSQL connection-refused error after serial Docker-backed slices had already passed. |

## Lifecycle State

TASK-M1-003 is `IMPLEMENTED, TESTED`.

Independent validation/freeze is still required before TASK-M1-003 is treated
as frozen or used to unblock TASK-M1-008 integration.
