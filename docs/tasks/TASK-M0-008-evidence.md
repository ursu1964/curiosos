---
id: TASK-M0-008-EVIDENCE
title: TASK-M0-008 M0 API Work Endpoints Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-008
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-008 Evidence

## Objective

Expose the frozen M0 governed-work vertical slice through the existing FastAPI
outer boundary.

TASK-M0-008 adds API composition/translation only. Canonical contracts,
runtime state transitions, policy evaluation, persistence primitives,
event/evidence storage, and provider inventory execution remain owned by their
frozen M0 packages.

## Starting Baseline

`02789840a311c9ed21b52b5384ea477104c6854c`

## Implemented Surface

- `apps/api/src/curios_api/composition.py`
- `apps/api/src/curios_api/service.py`
- `apps/api/src/curios_api/__init__.py`
- `apps/api/tests/test_m0_work_endpoints.py`
- `apps/api/pyproject.toml`
- narrow security/architecture guardrail updates for the exact API files/tests
- M0 ledger transition to `IMPLEMENTED, TESTED`

No API route moves policy, persistence, event/evidence, state-machine, provider
inventory execution, scheduling, DAG execution, model routing/generation, agent
runtime, or web behavior into FastAPI.

## Endpoint Surface

TASK-M0-008 adds:

- `POST /work/provider-inventory`
- `GET /work/{work_id}`
- `POST /work/{work_id}/run`
- `GET /work/{work_id}/executions/{execution_id}`
- `GET /work/{work_id}/events`
- `GET /work/{work_id}/evidence`

Existing frozen endpoints remain unchanged:

- `GET /health/live`
- `GET /health/ready`
- `GET /providers`

## Runtime Composition

The API may explicitly compose:

- `M0WorkRepository`
- `EventEvidenceRuntimeStore`
- `MinimalM0PolicyEvaluator`
- `SingleStepRuntimeService`
- `ProviderInventoryExecutor`
- injected `ProviderCatalog` implementations

Default API construction remains deterministic and does not create live
PostgreSQL, live Ollama, network, GPU, downloaded model, or telemetry collector
requirements. M0 runtime endpoints fail closed with bounded HTTP 503 until an
M0 runtime composition is supplied.

## Request and Response Semantics

API request bodies are transport-layer dictionaries only. They are translated
into canonical Curios values such as `WorkItem`, `WorkId`,
`SingleStepRuntimeRequest`, `EffectClassification`, `ExecutionId`, and
`ObservabilityContext`.

Responses are derived from canonical/runtime Curios-owned values using
canonical JSON-compatible serialization. FastAPI, Pydantic, Starlette,
PostgreSQL/SQLAlchemy, and provider-native objects do not cross the HTTP
response boundary.

## Failure Semantics

TASK-M0-008 translates bounded Curios failures at the HTTP boundary:

- malformed API input: HTTP 400 with `M0_API_MALFORMED_REQUEST`;
- unsupported work creation: HTTP 400 with `M0_API_UNSUPPORTED_WORK_TYPE`;
- missing work/execution: HTTP 404 with bounded API detail;
- non-authorizing policy result: HTTP 403 with canonical runtime result detail;
- executor/provider inventory failure: HTTP 502 with canonical runtime result
  detail;
- repository/runtime-store/runtime infrastructure failure: bounded HTTP error
  detail without lower-layer native exception leakage;
- M0 runtime not composed: HTTP 503 with `M0_API_RUNTIME_UNAVAILABLE`.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| FastAPI remains outer boundary | PASS | Routes translate to frozen runtime/repository/store APIs and do not redefine canonical contracts. |
| Existing health/provider endpoints preserved | PASS | Existing API tests and integration tests pass. |
| Provider-inventory work creation | PASS | API test creates canonical provider-inventory `WorkItem`. |
| Single-step execution through frozen runtime | PASS | API test runs work through `SingleStepRuntimeService` with `ProviderInventoryExecutor`. |
| Work observation | PASS | `GET /work/{work_id}` returns canonical work state. |
| Execution observation | PASS | `GET /work/{work_id}/executions/{execution_id}` returns canonical execution state. |
| Event/evidence observation | PASS | Event/evidence endpoints read through `EventEvidenceRuntimeStore`. |
| Unsupported/malformed inputs fail closed | PASS | API tests cover unsupported work type, unsupported/mixed effects, and malformed effect token. |
| Non-authorizing policy is not bypassed | PASS | API test shows `UNKNOWN` policy returns HTTP 403 and does not invoke the provider catalog. |
| Provider/executor failure bounded | PASS | API test translates provider catalog failure to bounded HTTP 502 detail. |
| Restart/readback behavior | PASS | API test reconstructs the application over the same persistence store and rereads work/events/evidence. |
| Topology exact | PASS | Security tests authorize only the TASK-M0-008 API files/tests and continue rejecting arbitrary API/runtime/web surfaces. |

## Verification

Focused implementation verification:

- TOML validation: passed
- `uv lock --check`: passed
- `uv lock`: passed
- `uv sync --locked --all-groups --all-packages`: passed
- Docker Compose config: passed
- Ruff check/format on API files: passed
- TASK-M0-008 API endpoint tests: `7 passed`, with the two expected
  FastAPI/TestClient dependency warnings.
- existing API and API integration tests: `22 passed`, with the same two
  expected dependency warnings.
- `curios_runtime` tests: `91 passed`
- policy tests: `20 passed`
- persistence boundary tests: `19 passed`
- contracts/core tests: `123 passed`
- provider package tests: `29 passed`
- contract/schema/security/architecture/BOOT acceptance focused regression:
  `85 passed`, with the two expected dependency warnings.
- PostgreSQL integration tests: `5 passed`; postgres reached healthy state,
  `pg_isready` accepted connections, the service stopped cleanly, and the
  persistent named volume remained present.
- mypy source scope: `53 source files`, passed
- full pytest: `392 passed`, with the two expected dependency warnings.
- `pnpm install --frozen-lockfile`: passed
- `pnpm check`: passed
- apps/web tests: `1 file`, `2 passed`
- apps/web typecheck: passed
- apps/web production build: passed
- `git diff --check`: passed

## Lifecycle

TASK-M0-008 is `IMPLEMENTED, TESTED`.

It is not `VALIDATED` or `FROZEN`. Independent validation must decide whether
TASK-M0-008 can freeze and whether TASK-M0-009 may become ready.
