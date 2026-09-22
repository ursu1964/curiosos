---
id: PG-10-INTEGRATION-EVIDENCE
title: PG-10 API Integration and Web Bootstrap Integration Evidence
lifecycle: TESTED
artifact_type: integration_evidence
authority: integration
tasks:
  - TASK-BOOT-023
  - TASK-BOOT-024
---

# PG-10 API Integration and Web Bootstrap Integration Evidence

PG-10 integrated independently implemented task commits:

- TASK-BOOT-023: `d970ebb0df99496830c928d21197a6122fdd99ed`
- TASK-BOOT-024: `1d5da82ad3065616c731900add1c4aa30fbc2276`

The starting baseline was `141c6893a31f379f05904da58b6102d2190c1a4c`.

## Integration

| Subject | Result |
| --- | --- |
| TASK-BOOT-023 merge | Merged with preserved task ancestry. |
| TASK-BOOT-024 merge | Merged with preserved task ancestry after expected status-ledger conflict resolution. |
| Status reconciliation | TASK-BOOT-023 and TASK-BOOT-024 remain `IMPLEMENTED, TESTED`; neither is marked `VALIDATED` or `FROZEN`. |
| Later task status | TASK-BOOT-025+ not advanced. |

## Conflict Resolutions

`docs/program/status-ledger/BOOT-000-task-ledger.md` was reconciled to preserve
both task status rows:

- TASK-BOOT-023: `IMPLEMENTED, TESTED`
- TASK-BOOT-024: `IMPLEMENTED, TESTED`

`tests/security/test_security_baseline.py` auto-merged to the intended union:

- authorized application roots are exactly `apps/api` and `apps/web`;
- authorized integration tests include `tests/integration/test_api_integration.py`
  and `tests/integration/test_postgres_provider_integration.py`;
- deferred `services`, top-level `providers`, and later provider/runtime
  surfaces remain blocked;
- the web source and tests are included in secret scanning.

## Architecture and Scope

- `apps/web` references only frozen TASK-BOOT-022 API paths:
  `/health/live`, `/health/ready`, and `/providers`.
- Web code does not import Python implementation internals.
- API integration tests do not depend on frontend implementation.
- Frontend tests and build do not require a live backend.
- No API SDK/client architecture beyond the bootstrap API-boundary helper was
  introduced.
- No provider-native backend types leak into web code.
- No frontend semantics became backend or domain authority.
- TASK-BOOT-025+ implementation was not introduced.

## Dependency and Workspace Reconciliation

Python:

- The root dev dependency group includes `httpx>=0.28.0` for FastAPI
  integration tests.
- `uv.lock` matches the integrated Python manifests.
- No runtime dependency was added to `apps/api`, `curios_contracts`,
  `curios_core`, or provider packages by TASK-BOOT-023.

Frontend:

- `apps/web` is a pnpm workspace package.
- `pnpm-lock.yaml` records the authoritative integrated web dependency graph.
- Root TypeScript project references include `apps/web`.
- Root ESLint ignores generated build outputs while preserving source checks.

## Warning Analysis

TASK-BOOT-023 API integration tests emit two dependency deprecation warnings:

1. `StarletteDeprecationWarning`: FastAPI/Starlette `TestClient` reports that
   using `httpx` with `starlette.testclient` is deprecated and suggests
   `httpx2`.
2. `DeprecationWarning`: Starlette references the deprecated
   `anyio.abc.BlockingPortal` alias.

Both warnings originate in installed test dependencies, not Curios source. They
are benign dependency warnings and technical debt to monitor, not validation
defects for PG-10 integration.

## Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed: 37 packages checked. |
| Ruff check | Passed. |
| Ruff format check | Passed: 121 files already formatted. |
| mypy strict baseline | Passed: no issues found in 61 source files. |
| TASK-BOOT-022 and TASK-BOOT-023 tests | Passed: 15 tests, 2 dependency warnings. |
| Package-local Python tests | Passed: 152 tests. |
| Repository contract tests | Passed: 10 tests. |
| Repository schema tests | Passed: 5 tests. |
| Repository architecture tests | Passed: 13 tests. |
| Repository security tests | Passed: 20 tests. |
| TASK-019 Docker-backed PostgreSQL integration | Passed: 1 test; service stopped cleanly and persistent volume remained present. |
| Full pytest suite | Passed: 216 tests, 2 dependency warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm list --depth -1 --recursive` | Passed; root, `@curiosos/web`, and `@curiosos/curios-contracts` are present. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |
| `pnpm check` | Passed. |
| `git diff --check` | Passed. |

## Final Status

PG-10 integration is `TESTED`. Independent PG-10 validation is permitted next,
but was not performed by this integration task.
