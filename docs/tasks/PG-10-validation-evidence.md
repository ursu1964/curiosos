---
id: PG-10-VALIDATION-EVIDENCE
title: PG-10 API Integration and Web Bootstrap Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: verification_evidence
authority: independent_verification
tasks:
  - TASK-BOOT-023
  - TASK-BOOT-024
---

# PG-10 API Integration and Web Bootstrap Independent Validation Evidence

Independent PG-10 validation was performed against integrated baseline
`a678e1477fe2c07e3406047e978b56d0a5966675`.

## Scope

PG-10 validates the integrated API integration-test and web-bootstrap
foundation:

- TASK-BOOT-023 API integration tests;
- TASK-BOOT-024 web bootstrap.

This validation does not start TASK-BOOT-025.

## Acceptance Summary

| Task | Result | Basis |
| --- | --- | --- |
| TASK-BOOT-023 | PASS | API integration tests exercise real FastAPI `TestClient` application construction, `/health/live`, `/health/ready`, `/providers`, provider/configuration failure translation, composed provider behavior, and lifespan handling without live Ollama, network, GPU, model download, or a new live PostgreSQL requirement. |
| TASK-BOOT-024 | PASS | `apps/web` is a minimal React/TypeScript/Vite bootstrap that references only frozen TASK-BOOT-022 API paths, reuses the TypeScript contracts package marker, remains outside the Python workspace, and introduces no product workflow or backend/provider implementation dependency. |

## Warning Audit

TASK-BOOT-023 API integration tests emit two dependency deprecation warnings:

1. `StarletteDeprecationWarning`: FastAPI/Starlette `TestClient` reports that
   using `httpx` with `starlette.testclient` is deprecated and suggests
   `httpx2`.
2. `DeprecationWarning`: Starlette references the deprecated
   `anyio.abc.BlockingPortal` alias.

Both warnings originate in installed test dependencies, not Curios source. They
are benign dependency warnings and technical debt to monitor, not validation
defects for PG-10.

## Dependency Validation

| Package/Surface | Dependency | Validation |
| --- | --- | --- |
| Root Python dev group | `httpx>=0.28.0` | REQUIRED: FastAPI/Starlette `TestClient` depends on httpx for TASK-BOOT-023 integration tests. It remains a dev/test dependency and does not leak into inner packages. |
| `apps/web` runtime | `@curiosos/curios-contracts` | REQUIRED: displays the frozen TypeScript contracts package marker without redefining canonical semantics. |
| `apps/web` runtime | `react`, `react-dom` | REQUIRED: authorized React bootstrap runtime. |
| `apps/web` development | `@types/react`, `@types/react-dom` | REQUIRED: TypeScript typing for React bootstrap. |
| `apps/web` development | `@vitejs/plugin-react`, `vite` | REQUIRED: authorized Vite React build pipeline. |
| `apps/web` development | `jsdom`, `vitest` | REQUIRED: deterministic render/smoke tests without a browser or live backend. |
| `apps/web` development | `typescript` | REQUIRED: package-local type checking and build validation. |

No unused or architecturally invalid dependency was identified.

## Security and Architecture

- The reconciled TASK-BOOT-016 security baseline permits exactly the authorized
  current application roots `apps/api` and `apps/web`.
- Authorized integration tests are exactly
  `tests/integration/test_api_integration.py` and
  `tests/integration/test_postgres_provider_integration.py`.
- Frozen PG-08 provider package roots remain allowed; arbitrary new providers,
  top-level `providers`, `services`, unrelated apps, and later runtime surfaces
  remain blocked.
- Secret scanning includes `apps/web` and the API integration-test surface.
- `curios_contracts` and `curios_core` remain free of FastAPI, frontend,
  provider-runtime, persistence, and infrastructure dependencies.
- `apps/web` does not import Python implementation internals, backend/provider
  packages, or provider-native objects.
- `apps/api` does not depend on `apps/web`, and TASK-BOOT-023 tests do not
  become architecture authority.

## Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed: 8 Python manifests parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed: 37 packages checked. |
| Ruff check | Passed. |
| Ruff format check | Passed: 122 files already formatted. |
| mypy strict baseline | Passed: no issues found in 61 source files. |
| TASK-BOOT-022 and TASK-BOOT-023 tests | Passed: 15 tests, 2 dependency deprecation warnings. |
| Package-local Python tests | Passed: 152 tests. |
| Repository contract tests | Passed: 10 tests. |
| Repository schema tests | Passed: 5 tests. |
| Repository architecture tests | Passed: 13 tests. |
| Repository security tests | Passed: 20 tests. |
| TASK-019 Docker-backed PostgreSQL integration | Passed: 1 test; PostgreSQL reached healthy state, `pg_isready` accepted connections, service stopped cleanly, and persistent named volume `curios-local-docker_postgres_data` remained present at `/var/lib/postgresql`. |
| Full pytest suite | Passed: 216 tests, 2 dependency deprecation warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |
| Diff whitespace | Passed. |

## Final Status

PG-10 validation passes. TASK-BOOT-023 and TASK-BOOT-024 are
`VALIDATED, FROZEN`; PG-10 is closed.
