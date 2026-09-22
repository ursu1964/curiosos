---
id: TASK-BOOT-024-EVIDENCE
title: TASK-BOOT-024 Web Bootstrap Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-BOOT-024
date: 2026-09-22
---

# TASK-BOOT-024 Web Bootstrap Evidence

## Scope

`TASK-BOOT-024` introduces the minimum web/frontend bootstrap authorized by the
BOOT task pack after frozen `TASK-BOOT-008` TypeScript package skeletons and
frozen `TASK-BOOT-022` FastAPI service composition.

Implemented package:

- `apps/web`

Implemented technology:

- React, TypeScript, Vite, Node 24 LTS, and pnpm, as frozen by the BOOT-000
  decision and architecture baselines.
- Vitest for deterministic package-local render and API-boundary smoke tests.

## Acceptance Mapping

| Criterion | Implementation/Test |
| --- | --- |
| Web application is an outer interface only. | `apps/web` is a pnpm workspace package and is not registered in the Python workspace. |
| Bootstrap scope only. | The app renders a minimal shell and frozen API endpoint list; no product workflow, scheduler, DAG/router, agent runtime, policy engine, persistence, provider behavior, or backend semantics are implemented. |
| API boundary remains bounded. | `apps/web/src/apiBoundary.ts` references only `GET /health/live`, `GET /health/ready`, and `GET /providers` from frozen TASK-BOOT-022. |
| No Python implementation internals are imported. | Architecture check `test_web_bootstrap_remains_outer_frontend_boundary` blocks backend/internal module imports from web source. |
| Frontend dependency direction remains outward. | Web package depends on React/Vite tooling and the frozen TypeScript contracts package marker only. |
| Security topology is narrowly transitioned. | Security baseline allows exactly `apps/web` as the TASK-024 application root and scans web source/config/test files for secret-shaped literals. |
| Deterministic frontend checks exist. | Package-local Vitest tests render the shell and verify the frozen API-boundary path list without network calls. |

## Dependency Changes

- Added workspace package `@curiosos/web`.
- Added runtime dependencies to `@curiosos/web`:
  - `@curiosos/curios-contracts`
  - `react`
  - `react-dom`
- Added package-local development dependencies required for the frozen frontend
  toolchain and smoke tests:
  - `@types/react`
  - `@types/react-dom`
  - `@vitejs/plugin-react`
  - `jsdom`
  - `typescript`
  - `vite`
  - `vitest`

No UI library, state framework, API SDK, generated client, Playwright browser
test, backend dependency, provider SDK, persistence dependency, or scheduler/
agent runtime dependency was added.

## Verification Evidence

Verification was run after implementation:

| Check | Result |
| --- | --- |
| `pnpm install --frozen-lockfile` before lockfile update | Failed as expected because `apps/web` and its dependencies were not yet recorded in `pnpm-lock.yaml`. |
| `pnpm install --lockfile-only` | Passed; lockfile records the new web package importer and dependency graph. |
| `pnpm install --frozen-lockfile` after lockfile update | Passed. |
| `pnpm list --depth -1 --recursive` | Passed; workspace includes `@curiosos/web`. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web build` | Passed. |
| `pnpm check` | Passed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed. |
| `uv run mypy apps/api/src packages/python/*/src` | Passed for production source roots. |
| Architecture tests | Passed. |
| Security tests | Passed. |
| Full pytest suite | Passed: 210 tests. |
| `git diff --check` | Passed. |

## Scope Compliance

Allowed task paths changed:

- `apps/web/**`
- `eslint.config.mjs`
- `pnpm-lock.yaml`
- `tsconfig.json`
- `tests/architecture/**`
- `tests/security/**`
- `docs/tasks/TASK-BOOT-024-evidence.md`
- `docs/program/status-ledger/BOOT-000-task-ledger.md`

Forbidden scope not changed:

- No `1.txt` change.
- No Python contract/core/provider implementation change.
- No `apps/api` production behavior change.
- No `TASK-BOOT-023` integration-test expansion.
- No scheduler, DAG/router, model-router, agent runtime, policy/authority
  engine, backend persistence, migrations, generated API client, or product UI.

## Final Implementation Status

`TASK-BOOT-024` is `IMPLEMENTED` and `TESTED`. This implementation does not
self-declare `VALIDATED` or `FROZEN`.
