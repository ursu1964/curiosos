---
id: TASK-BOOT-022-FASTAPI-SERVICE-COMPOSITION
title: TASK-BOOT-022 FastAPI Service Composition Boundary
lifecycle: FROZEN
artifact_type: architecture
authority: implementation_agent
task: TASK-BOOT-022
---

# TASK-BOOT-022 FastAPI Service Composition Boundary

TASK-BOOT-022 introduces the first API application surface at `apps/api`.
FastAPI is an outer interface framework for service composition. It is not a
Curios semantic authority.

## Authorized Surface

- Python workspace package: `apps/api`.
- Import package: `curios_api`.
- FastAPI application factory: `curios_api.create_application`.
- Composition helpers: `ApiComposition`, `CompositeProviderCatalog`,
  `create_api_composition`, and `create_provider_catalog`.
- Package-local tests: `apps/api/tests/test_fastapi_service_composition.py`.

## Boundary Rules

- `curios_contracts` remains canonical and does not depend on FastAPI.
- `curios_core` remains inward-facing and does not depend on FastAPI.
- Provider packages remain provider-local and do not depend on the API layer.
- The API layer may import frozen contracts, core ports, and authorized provider
  packages in order to compose them.
- FastAPI request/response behavior is transport-layer behavior only.
- HTTP status codes are boundary translations of bounded Curios `Result` and
  `ContractError` records.

## Implemented Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health/live` | Bounded liveness check for the API process. |
| `GET /health/ready` | Non-mutating readiness projection from configuration and provider descriptor boundaries. |
| `GET /providers` | Lists provider descriptors through the existing core `ProviderCatalog` port. |

## Explicitly Deferred

TASK-BOOT-022 does not implement scheduler, DAG, model-router, agent-runtime,
policy/authority engine, persistence repository architecture, migrations,
frontend behavior, CI, or TASK-BOOT-023+ integration-test expansion.

## Validation

Independent validation accepted this FastAPI service-composition boundary at
commit `fff9156475dbfb792e8908fcabda91922fe36650`. The accepted boundary is
`VALIDATED, FROZEN` and remains limited to the outer application composition
surface described above.
