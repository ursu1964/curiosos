---
id: TASK-M0-007-VALIDATION-EVIDENCE
title: TASK-M0-007 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-007
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-007 Independent Validation Evidence

## Decision

TASK-M0-007 VALIDATION: PASS

Validated candidate:

`be86f12edbb8b6d9ea9049d43eb5b8d521f581b4`

Starting baseline:

`bdc56b372ea98baac090c0bc11459b2f0ce43d05`

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Exact TASK-M0-007 scope | PASS | Diff adds only provider inventory executor, tests, export/dependency metadata, lifecycle docs, and narrow guardrail updates. No scheduler, DAG, retry engine, API, web, agent runtime, model routing, model generation, provider ranking, or arbitrary executor was added. |
| TASK-M0-006 seam preserved | PASS | `SingleStepExecutor`, `SingleStepExecutionRequest`, and `SingleStepExecutionOutcome` are unchanged; `ProviderInventoryExecutor.execute` implements the frozen seam. |
| Provider inventory authority | PASS | Inventory is obtained through injected `ProviderCatalog` values via `CoreServices.list_provider_descriptors`; returned payloads are canonical `ProviderDescriptor.to_json_compatible()` values. |
| `curios-core` dependency | PASS | REQUIRED. Runtime needs the frozen `ProviderCatalog`, `CoreContext`, and `CoreServices` boundary to consume provider catalogs without re-declaring the core port. Core and providers do not depend on runtime, and no cycle exists. |
| Policy/capability separation | PASS | Runtime service owns policy evaluation. Executor-side checks reject unsupported work/effect and non-authorizing decisions but do not create, grant, mutate, or rewrite authority. |
| Read-only behavior | PASS | Executor lists descriptors only; no database writes, provider configuration mutation, model generation, filesystem mutation, or arbitrary external tool effects were added. |
| Provider composition | PASS | Multiple injected catalogs are supported deterministically. Catalog failure fails the whole inventory; no partial inventory, ranking, routing, selection, or provider-to-provider coupling is introduced. |
| Determinism and duplicates | PASS | Descriptors sort by provider ID, type, and version; empty inventory succeeds; duplicate canonical provider IDs fail closed. |
| Failure boundary | PASS | Catalog `Result.failure`, raised exceptions, malformed result values, duplicate providers, unsupported work/effect, and non-authorizing decisions return bounded `ContractError` values. Native exception objects, SQLAlchemy/psycopg/Ollama payloads, URLs, credentials, and tracebacks do not cross the executor boundary. |
| Partial provider failure | PASS | For multi-catalog composition, one catalog failure fails the entire inventory with no partial value. Single-catalog composition has no partial-failure case. |
| Evidence semantics | PASS | Executor returns one canonical `EvidenceReference` of kind `PROVIDER_REPORT` for the work item and trace; actual provider inventory payload lives in `Result.value`. Evidence persistence remains the TASK-M0-006 runtime store responsibility. No verification outcome is fabricated. |
| End-to-end runtime integration | PASS | Deterministic fake catalog success flows through policy, runtime service, executor, event/evidence recording, execution `SUCCEEDED`, and work `COMPLETED`. Explicit failure probe persisted work/execution `FAILED` and no fabricated evidence. |
| Topology and security | PASS | Security topology authorizes exactly `provider_inventory_executor.py` in addition to frozen M0 runtime files. Representative unauthorized runtime additions are rejected. Secret scan covers the new runtime source/tests/docs surfaces. |
| Architecture | PASS | Contracts/core remain inward. Runtime depends outward on core as authorized for this task; providers remain independent of runtime; policy and persistence remain independent of the executor; no canonical semantic ownership moved outward. |
| Frozen prerequisites | PASS | No semantic changes to TASK-M0-006 or earlier frozen implementation files. Changes outside executor/tests/docs are lifecycle/export/dependency/guardrail updates required for TASK-M0-007. |
| Test quality | PASS | Tests cover stable ordering, empty inventory, unsupported capability rejection, catalog failure/exception translation, duplicate IDs, malformed descriptor output, and success integration. Additional validation probes covered malformed `None`, secret-bearing exception text, explicit integrated catalog failure, and topology filenames not already parametrized. |

## Provider Inventory Semantics

Authoritative M0 semantics are: collect canonical `ProviderDescriptor` values
from Curios-owned provider catalogs through the `ProviderCatalog` /
`CoreServices` boundary and return a canonical bounded result plus evidence
reference. Provider-native Ollama JSON, SQLAlchemy rows, PostgreSQL-native
structures, provider SDK types, HTTP payloads, URLs, credentials, and native
exceptions remain provider-local.

The executor returns:

- `work_type`: `provider_inventory`;
- `provider_count`: descriptor count;
- `providers`: ordered canonical descriptor JSON-compatible objects.

## Policy And Capability Review

The executor checks:

| Check | Classification |
| --- | --- |
| `request.work.work_type == provider_inventory` | Capability/input validation. |
| `request.policy_decision.requested_effects == (READ_ONLY,)` | Capability/input validation ensuring this executor is not used for unsupported effects. |
| `request.policy_decision.is_authorizing` | Fail-closed validation of the frozen runtime precondition. |

These checks do not independently authorize execution. Authorization remains the
TASK-M0-006 runtime service call to `MinimalM0PolicyEvaluator`.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS: 11 `pyproject.toml` files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS. |
| Ruff | PASS. |
| Ruff format | PASS: 179 files already formatted. |
| Authoritative mypy | PASS: `uv run mypy apps/api/src packages/python/*/src`; 53 source files. |
| TASK-M0-007 tests | PASS: 8 passed. |
| TASK-M0-006 tests | PASS: 25 passed. |
| Policy tests | PASS: 20 passed. |
| Event/evidence and work repository tests | PASS: 56 passed. |
| Persistence boundary tests | PASS: 19 passed. |
| Contracts/core tests | PASS: 123 passed. |
| Provider/API package tests | PASS: 28 passed. |
| Config/observability package tests | PASS: 10 passed. |
| Contract/schema tests | PASS: 15 passed. |
| Architecture/security tests | PASS: 56 passed. |
| API integration | PASS: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration | PASS: 1 passed serially. |
| PostgreSQL runtime event/evidence integration | PASS: 1 passed serially. |
| PostgreSQL runtime work repository integration | PASS: 1 passed serially. |
| PostgreSQL persistence integration | PASS: 2 passed serially. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| Full pytest | PASS: 377 passed, 2 known dependency warnings. |
| `pnpm install --frozen-lockfile` | PASS. |
| `pnpm check` | PASS. |
| Web tests | PASS: 1 test file, 2 tests. |
| Web typecheck | PASS: no TypeScript errors. |
| Web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |
| Additional topology probe | PASS: 8 representative unauthorized runtime additions rejected. |
| Additional executor probes | PASS: malformed `None`, secret-bearing exception text, and integrated catalog failure remained bounded. |

The known warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings.

## Lifecycle And Downstream Readiness

TASK-M0-007 is `VALIDATED, FROZEN`.

The validation/freeze commit must be integrated into `main` before downstream
readiness changes. Under the frozen M0 DAG, TASK-M0-008 remains `BLOCKED` on
this task branch and becomes `READY` only after this validation/freeze commit is
integrated into `main`.

TASK-M0-008 was not implemented, started, or otherwise advanced by this
validation.

## Files Modified

- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-007-evidence.md`
- `docs/tasks/TASK-M0-007-validation-evidence.md`

## Commit And Integration Requirements

This validation produced documentation-only lifecycle changes. A
validation/freeze commit is required for these changes, and that commit must be
integrated into `main` before TASK-M0-008 can become `READY`.

No merge, push, or TASK-M0-008 implementation was performed.

## Final Git Status

```text
 M docs/program/status-ledger/M0-status-ledger.md
 M docs/tasks/TASK-M0-007-evidence.md
?? docs/tasks/TASK-M0-007-validation-evidence.md
```
