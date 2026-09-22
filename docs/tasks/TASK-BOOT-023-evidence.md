---
id: TASK-BOOT-023-EVIDENCE
title: TASK-BOOT-023 API Integration Tests Evidence
lifecycle: VALIDATED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-023
---

# TASK-BOOT-023 API Integration Tests Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Work began on branch `task/boot-023-api-integration` from required baseline `141c689 Validate and freeze TASK-BOOT-022`. |
| 2 | IMPLEMENTED | Deterministic repository-level FastAPI integration tests, a test-only `httpx` dependency, and a narrow TASK-016 integration-test topology update were added. |
| 3 | TESTED | Required TASK-023 checks and repository verification passed; see verification evidence below. |
| 4 | VALIDATED | Independent PG-10 validation accepted TASK-BOOT-023 at integrated baseline `a678e1477fe2c07e3406047e978b56d0a5966675`; see `docs/tasks/PG-10-validation-evidence.md`. |
| 5 | FROZEN | The BOOT task ledger records TASK-BOOT-023 as `VALIDATED, FROZEN`. |

## Acceptance Mapping

| Criterion | Implementation/Test |
| --- | --- |
| Integrated FastAPI boundary is tested without duplicating TASK-022 unit tests. | `tests/integration/test_api_integration.py` uses `fastapi.testclient.TestClient` to exercise ASGI routing, HTTP status codes, JSON serialization, and lifespan handling. |
| Application construction is covered. | `test_application_constructs_as_asgi_app_and_liveness_stays_provider_independent` creates the application through `create_application(create_api_composition(...))` and verifies the route surface through a real client. |
| `/health/live` is covered. | The same test verifies `GET /health/live` returns HTTP 200 and does not call configuration or provider boundaries. |
| `/health/ready` is covered. | `test_readiness_serializes_configuration_and_composed_providers_over_http` verifies HTTP 200, `LOCAL_DOCKER` configuration serialization, and composed provider descriptor serialization. |
| `/providers` is covered. | `test_providers_endpoint_returns_catalog_descriptors_through_fastapi_boundary` verifies provider descriptors returned through FastAPI JSON responses. |
| Canonical `Result`/`ContractError` failures translate to HTTP. | Provider and configuration failure tests assert HTTP 503 responses with canonical result-envelope details. |
| Composed provider behavior is covered. | The readiness test combines a deterministic database descriptor catalog with the frozen fakeable Ollama provider boundary. |
| Application lifecycle/startup/shutdown is covered. | `test_application_lifespan_runs_startup_and_shutdown_around_client_context` verifies startup and shutdown handlers run around `TestClient` context management. |
| Deterministic behavior is preserved when live providers are not required. | TASK-023 tests use fakes/stubs only; no live Ollama, network, GPU, model download, or live PostgreSQL is required by the new API integration tests. |
| PostgreSQL handling remains within existing authorized live coverage. | The existing TASK-019 Docker-backed PostgreSQL integration was rerun; no new TASK-023 live PostgreSQL requirement or test was added. |
| TASK-016 protections remain narrow. | `tests/security/test_security_baseline.py` authorizes only `tests/integration/test_api_integration.py` as the new integration-test surface. |

## Integration Scenarios Established

- Application construction and liveness over the FastAPI/ASGI boundary.
- Readiness over configuration plus composed provider catalogs.
- Provider listing over the HTTP serialization boundary.
- Canonical failure translation for configuration and provider failures.
- Deterministic composed provider behavior using a fake Ollama model client.
- FastAPI lifecycle startup/shutdown participation through `TestClient`.

## Dependency Changes

- Added `httpx>=0.28.0` to the root dev dependency group because FastAPI
  `TestClient` requires it for integration testing.
- Added no runtime dependency to `apps/api`, `curios_contracts`, `curios_core`,
  or provider packages.

## Live Provider Usage

- TASK-023 API integration tests do not require live providers.
- Ollama coverage uses the frozen fakeable provider boundary and does not use
  network, GPU, or downloaded models.
- PostgreSQL was exercised only by the existing TASK-019 integration test using
  TASK-006 `LOCAL_DOCKER`; the test starts only `postgres`, waits for provider
  readiness, performs non-destructive checks, stops the service, and confirms
  the named persistent volume remains present.

## Verification

| Check | Result |
| --- | --- |
| TASK-BOOT-023 API integration tests | Passed: 6 tests, 2 dependency deprecation warnings. |
| TASK-BOOT-022 tests | Passed: 9 tests. |
| TOML validation | Passed: 8 TOML manifests parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed: 37 packages checked. |
| Ruff check | Passed. |
| Ruff format check | Passed: 119 files already formatted. |
| mypy strict baseline | Passed: no issues found in 61 source files. |
| `curios_contracts` tests | Passed: 114 tests. |
| `curios_core` tests | Passed: 9 tests. |
| TASK-018 configuration provider tests | Passed: 6 tests. |
| TASK-019 PostgreSQL provider unit tests | Passed: 6 tests. |
| TASK-019 Docker-backed PostgreSQL integration | Passed: 1 test. |
| TASK-020 Ollama provider tests | Passed: 13 tests. |
| TASK-021 telemetry provider tests | Passed: 4 tests. |
| Repository contract tests | Passed: 10 tests. |
| Repository schema tests | Passed: 5 tests. |
| Architecture tests | Passed: 12 tests. |
| Security tests | Passed: 20 tests. |
| Full pytest suite | Passed: 215 tests, 2 dependency deprecation warnings. |

## Scope Review

No TASK-BOOT-022 production behavior was changed. No frontend, scheduler,
DAG/router, agent runtime, model router, policy/authority engine, migrations,
repository architecture, new canonical semantics, or TASK-BOOT-024+ behavior was
introduced.

## Independent Validation

Independent PG-10 validation was performed against integrated baseline
`a678e1477fe2c07e3406047e978b56d0a5966675`.

| Validation Area | Result |
| --- | --- |
| Integration value | Passed: tests exercise real FastAPI `TestClient` construction, HTTP routing, JSON serialization, and lifespan handling beyond package-local TASK-022 unit tests. |
| Endpoint behavior | Passed: `/health/live`, `/health/ready`, and `/providers` preserve their frozen TASK-022 meanings and remain deterministic. |
| Failure translation | Passed: provider and configuration `Result.failure` values translate to bounded HTTP 503 responses with canonical `ContractError` detail. |
| Provider determinism | Passed: TASK-023 tests use fakes/stubs only and introduce no live Ollama, network, GPU, model download, or live PostgreSQL requirement. |
| Warning audit | Passed with technical-debt note: the two warnings originate in FastAPI/Starlette test dependencies and are not Curios validation defects. |
| Scope review | Passed: no frontend behavior, production API behavior change, scheduler, DAG/router, agent runtime, policy engine, persistence architecture, or later task implementation was introduced. |

## Final Status

`TASK-BOOT-023` is `VALIDATED, FROZEN` after independent PG-10 validation.
