---
id: TASK-M0-007-EVIDENCE
title: TASK-M0-007 Provider Inventory Executor Evidence
lifecycle: VALIDATED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-007
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-007 Evidence

## Objective

Implement the single authorized M0 executor capability:

`provider_inventory`

The executor plugs into the frozen TASK-M0-006 `SingleStepExecutor` seam and
collects canonical `ProviderDescriptor` values through the frozen
`ProviderCatalog` / `CoreServices` boundary.

## Starting Baseline

`bdc56b372ea98baac090c0bc11459b2f0ce43d05`

## Implemented Surface

- `packages/python/curios_runtime/src/curios_runtime/provider_inventory_executor.py`
- `packages/python/curios_runtime/tests/test_provider_inventory_executor.py`
- `curios_runtime` export update
- `curios-runtime` dependency metadata update adding workspace `curios-core`
- narrow security/architecture guardrail updates authorizing exactly the
  TASK-M0-007 runtime executor module
- M0 ledger transition to `IMPLEMENTED, TESTED`

No API route, web surface, scheduler, DAG engine, retry framework, agent
runtime, model router/generation behavior, arbitrary tool execution, provider
ranking, provider selection, or live provider dependency was added.

## Executor API

TASK-M0-007 adds:

- `ProviderInventoryExecutor`

The executor implements the frozen `SingleStepExecutor` seam:

`execute(SingleStepExecutionRequest) -> SingleStepExecutionOutcome`

It accepts injected `ProviderCatalog` instances. It does not import concrete
Ollama, PostgreSQL, FastAPI, SQLAlchemy, or provider-native implementation
objects.

## Provider Inventory Semantics

The executor:

1. validates the request is for `provider_inventory`;
2. validates the request carries exactly the READ_ONLY policy effect;
3. validates the policy decision is authorizing;
4. calls each injected catalog through `CoreServices(...).list_provider_descriptors`;
5. validates returned values are canonical `ProviderDescriptor` objects;
6. rejects duplicate provider IDs;
7. sorts descriptors deterministically by provider ID, provider type, and
   version;
8. returns a canonical JSON-compatible inventory value inside `Result.success`;
9. returns a canonical `EvidenceReference(PROVIDER_REPORT)` for TASK-M0-006 to
   record.

The executor does not implement provider health orchestration, provider
selection/ranking, model generation, model routing, or provider-specific calls.

## Failure Semantics

TASK-M0-007 fails closed:

- unsupported work type returns bounded `PROVIDER_INVENTORY_UNSUPPORTED_WORK`;
- unsupported effect returns bounded `PROVIDER_INVENTORY_UNSUPPORTED_EFFECT`;
- non-authorizing policy decision returns bounded
  `PROVIDER_INVENTORY_NOT_AUTHORIZED`;
- provider catalog `Result.failure` fails the whole inventory with bounded
  `PROVIDER_INVENTORY_CATALOG_FAILURE`;
- provider catalog exception fails the whole inventory with bounded
  `PROVIDER_INVENTORY_CATALOG_EXCEPTION`;
- malformed catalog output fails with bounded
  `PROVIDER_INVENTORY_MALFORMED_RESULT`;
- duplicate provider IDs fail with bounded
  `PROVIDER_INVENTORY_DUPLICATE_PROVIDER`.

No partial inventory is returned when a participating catalog fails. No
provider-native exception object, SQLAlchemy/psycopg detail, Ollama-native
payload, URL, credential, or traceback crosses the executor boundary.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Implements frozen executor seam | PASS | `ProviderInventoryExecutor.execute` accepts `SingleStepExecutionRequest` and returns `SingleStepExecutionOutcome`. |
| Uses ProviderCatalog/CoreServices | PASS | Executor calls injected catalogs through `CoreServices.list_provider_descriptors`. |
| Returns canonical descriptors | PASS | Result value contains `ProviderDescriptor.to_json_compatible()` objects only. |
| Deterministic ordering | PASS | Tests pass unsorted catalog responses and assert sorted output. |
| Empty inventory deterministic | PASS | Empty catalog output returns success with `provider_count=0` and evidence. |
| Unsupported work/effects fail closed | PASS | Tests prove no catalog invocation. |
| Catalog failure/exception bounded | PASS | Tests prove fail-whole behavior and safe metadata. |
| Duplicate descriptors rejected | PASS | Tests reject duplicate provider IDs. |
| Runtime integration | PASS | Test injects executor into `SingleStepRuntimeService` and observes completed work/execution, evidence, and events. |
| No live provider requirement | PASS | Tests use deterministic fake catalogs only. |
| Topology exact | PASS | Security tests authorize `provider_inventory_executor.py` only and continue rejecting arbitrary executor/router/scheduler modules. |

## Verification

Implementation verification:

- TOML validation: passed
- `uv lock --check`: passed
- `uv lock`: passed
- `uv sync --locked --all-groups --all-packages`: passed
- Docker Compose config: passed
- Ruff: passed
- Ruff format check: passed
- mypy source scope: `53 source files`, passed
- TASK-M0-007 executor tests: `8 passed`
- `curios_runtime` tests: `91 passed`
- policy tests: `20 passed`
- persistence boundary tests: `19 passed`
- contracts/core tests: `123 passed`
- provider/API package tests: `38 passed`
- contract/schema/security/architecture/API integration/BOOT acceptance focused
  regression: `83 passed`, with the two expected dependency warnings from
  FastAPI/TestClient and anyio.
- PostgreSQL integration tests: `5 passed`
- TASK-M0-007 executor tests plus TASK-M0-006/security/architecture focused
  regression: `89 passed`
- full pytest: `377 passed`, with the two expected dependency warnings from
  FastAPI/TestClient and anyio.
- `pnpm install --frozen-lockfile`: passed
- `pnpm check`: passed
- apps/web tests: `1 file`, `2 passed`
- apps/web typecheck: passed
- apps/web production build: passed
- `git diff --check`: passed

## Lifecycle

TASK-M0-007 is `VALIDATED, FROZEN`.

Independent validation accepted candidate
`be86f12edbb8b6d9ea9049d43eb5b8d521f581b4`.

The frozen DAG requires TASK-M0-007 to be validated, frozen, and integrated
before TASK-M0-008 can become ready. Therefore TASK-M0-008 remains `BLOCKED` on
this task branch. After the validation/freeze commit is integrated into `main`,
TASK-M0-008 may become `READY`; it is not implemented by this validation.
