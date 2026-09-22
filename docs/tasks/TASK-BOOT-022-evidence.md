---
id: TASK-BOOT-022-EVIDENCE
title: TASK-BOOT-022 FastAPI Service Composition Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-022
---

# TASK-BOOT-022 FastAPI Service Composition Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Work began from committed main HEAD `a5c91e107da34007fd3e5de9bcd5158a8baeec70` after PG-08 was closed. |
| 2 | IMPLEMENTED | Minimal FastAPI application package, service composition boundary, package-local tests, architecture/security transitions, workspace metadata, and documentation were added. |
| 3 | TESTED | Required deterministic checks passed; see verification evidence below. |

## Acceptance Mapping

| Criterion | Implementation/Test |
| --- | --- |
| FastAPI is an outer composition framework only. | `apps/api/src/curios_api/service.py`; architecture test `test_fastapi_service_composition_remains_outer_boundary`. |
| Canonical semantics remain in Curios contracts/core. | No `curios_contracts` or `curios_core` production files were modified; existing architecture tests continue to block FastAPI/provider imports inward. |
| Authorized providers are reused rather than duplicated. | `apps/api/src/curios_api/composition.py` composes `curios_config`, `curios_core`, `curios_observability`, `curios_ollama`, and `curios_postgres_provider` boundaries. |
| Ordinary tests remain deterministic. | Package-local tests use fake provider catalogs and fake Ollama model clients; no live Ollama, network, model download, or PostgreSQL service is required. |
| Health/readiness remain bounded interface behavior. | `/health/live`, `/health/ready`, and `/providers` are tested in `apps/api/tests/test_fastapi_service_composition.py`. |
| Canonical failures are translated at the HTTP boundary. | `test_fastapi_provider_endpoint_translates_contract_failures_to_http_boundary`. |
| Security topology is narrowly updated. | `tests/security/test_security_baseline.py` permits exactly `apps/api` as the new application surface. |
| Architecture checks recognize the new boundary. | `tests/architecture/test_architecture_conformance.py` verifies the API package remains outward and avoids direct provider-native imports. |

## Dependency Changes

- Added workspace member `apps/api`.
- Added `curios-api` runtime dependencies on frozen Curios packages required for
  outer composition.
- Added `fastapi` only to the outer application package.
- Added no FastAPI, Starlette, Pydantic, SQLAlchemy, PostgreSQL driver, Ollama,
  or OpenTelemetry implementation dependency to `curios_contracts` or
  `curios_core`.

## Verification

Verification was run after implementation:

| Check | Result |
| --- | --- |
| TASK-BOOT-022 tests | Passed: 9 tests. |
| TOML validation | Passed for root and all Python package manifests. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 118 files already formatted. |
| mypy strict baseline | Passed: no issues found in 61 source files. |
| `curios_contracts` tests | Passed: 114 tests. |
| `curios_core` tests | Passed: 9 tests. |
| TASK-018 tests | Passed: 6 configuration-provider tests. |
| TASK-019 tests | Passed: 6 provider tests and 1 Docker-backed integration test. |
| TASK-020 tests | Passed: 13 deterministic Ollama-provider tests. |
| TASK-021 tests | Passed: 4 telemetry-provider tests. |
| Repository contract tests | Passed: 10 tests. |
| Repository schema tests | Passed: 5 tests. |
| Architecture tests | Passed: 12 tests. |
| Security tests | Passed: 20 tests. |
| Full pytest suite | Passed: 209 tests. |
| Diff whitespace | Passed. |

## Scope Review

No frozen contract/core production files were changed. No policy engine,
authority/grant engine, scheduler, DAG engine, model router, agent runtime,
persistence repository architecture, migrations, frontend, CI, or TASK-BOOT-023+
implementation was introduced.

## Final Status

`TASK-BOOT-022` is `IMPLEMENTED` and `TESTED`. This task does not self-declare
`VALIDATED` or `FROZEN`.
