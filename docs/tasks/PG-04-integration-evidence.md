---
id: PG-04-INTEGRATION-EVIDENCE
title: PG-04 Integration Evidence
lifecycle: TESTED
artifact_type: integration_evidence
authority: evidence
workstream: PG-04
---

# PG-04 Integration Evidence

## Scope

This record covers integration of the accepted PG-04 task outputs into `main`.

Integrated task commits:

- `TASK-BOOT-007`: `507f12362e9588470f3c556ebf30c36e15b3d141`
- `TASK-BOOT-008`: `45b1e7f0e2b99f2e19edb86e7cf02214c90b6097`

The PG-04 integration baseline is the `main` commit containing this evidence record.

## Conflict Resolution

Conflicts occurred only in `docs/program/status-ledger/BOOT-000-task-ledger.md`.

Resolution:

- preserved both task implementation outputs;
- recorded `TASK-BOOT-007` and `TASK-BOOT-008` as `VALIDATED, FROZEN`;
- preserved `BOOT-VERIFY-PG-READINESS-001` from PG-03;
- did not alter `TASK-BOOT-009` or later implementation lifecycle states;
- did not implement canonical contracts while reconciling package skeletons.

## Python Integrated Checks

| Check | Result |
| --- | --- |
| root and package `pyproject.toml` parsed with Python `tomllib` | passed |
| `uv lock --check` | passed |
| `uv sync --locked --all-groups` | passed |
| `uv sync --locked --all-groups --all-packages` | passed |
| Python workspace package recognition | passed; three package skeletons built/installed by uv |
| import `curios_contracts` | passed |
| import `curios_core` | passed |
| import `curios_observability` | passed |
| `uv run ruff check .` | passed |
| `uv run ruff format --check .` | passed |
| `uv run mypy packages/python` | passed |
| `uv run pytest --collect-only` | parsed configuration; collected 0 tests as expected for current bootstrap scope |

## TypeScript Integrated Checks

| Check | Result |
| --- | --- |
| `pnpm install --frozen-lockfile` | passed |
| `pnpm list --depth -1 --recursive` | passed; root and `@curiosos/curios-contracts` recognized |
| `pnpm typecheck` | passed |
| `pnpm lint` | passed |
| `pnpm format:check` | passed |
| `pnpm check` | passed |
| `pnpm --filter @curiosos/curios-contracts build` | passed |
| React/Vite dependency check | passed; no React or Vite package dependency was introduced |
| `apps/web` absence | passed |

## Architecture And Scope Checks

| Check | Result |
| --- | --- |
| no provider packages | passed |
| no API service | passed |
| no root test architecture | passed |
| no database schemas or migrations | passed |
| no SQLAlchemy/FastAPI/Ollama/OpenTelemetry/Pydantic implementation dependency in package manifests | passed |
| TypeScript package exports only package/version markers | passed |
| no TASK-BOOT-009 contract implementation | passed |
| `git diff --check` | passed |

## Tracked Package Skeletons

Python:

- `packages/python/curios_contracts/pyproject.toml`
- `packages/python/curios_contracts/src/curios_contracts/__init__.py`
- `packages/python/curios_core/pyproject.toml`
- `packages/python/curios_core/src/curios_core/__init__.py`
- `packages/python/curios_observability/pyproject.toml`
- `packages/python/curios_observability/src/curios_observability/__init__.py`

TypeScript:

- `packages/typescript/curios-contracts/README.md`
- `packages/typescript/curios-contracts/package.json`
- `packages/typescript/curios-contracts/src/index.ts`
- `packages/typescript/curios-contracts/tsconfig.json`

## Preserved Deferred Item

`BOOT-VERIFY-PG-READINESS-001` remains open:

Start the TASK-BOOT-006 PostgreSQL service, verify health/readiness, and stop it cleanly without destroying the persistent volume.

This must be completed before final BOOT-000 acceptance.
