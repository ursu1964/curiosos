---
id: TASK-M0-010-EVIDENCE
title: TASK-M0-010 M0 Integration Test Foundation Evidence
lifecycle: VALIDATED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-010
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-010 Evidence

## Objective

Add deterministic M0 cross-boundary integration tests proving that the frozen
M0 components operate as one coherent provider-inventory vertical slice.

TASK-M0-010 owns tests/evidence only. It does not add runtime, API, web,
policy, persistence, provider, CI, acceptance, or product behavior.

## Starting Baseline

`245447c133264b5e4e1bf140c8ed3ad72b7f72ef`

## Implemented Surface

- `tests/integration/test_m0_vertical_slice_integration.py`
- `tests/security/test_security_baseline.py`
- `docs/security/TASK-M0-001-topology-guardrails.md`
- `docs/architecture/TASK-M0-001-topology-guardrails.md`
- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-010-evidence.md`

No production code, dependency manifest, lockfile, CI workflow, acceptance
surface, API route, runtime service, web console behavior, policy rule,
persistence schema, provider executor, scheduler, DAG runtime, agent runtime,
model router, DataLab, or M1+ surface was added.

## Scenario Matrix

| Scenario | Vertical Slice | Frozen Components Exercised | Invariant Proven |
| --- | --- | --- | --- |
| Successful provider inventory work | VS-M0-001 | FastAPI work routes, `SingleStepRuntimeService`, `MinimalM0PolicyEvaluator`, `M0WorkRepository`, `EventEvidenceRuntimeStore`, `ProviderInventoryExecutor`, `ProviderCatalog`, PostgreSQL persistence | READ_ONLY `provider_inventory` work completes once, produces deterministic canonical provider descriptors, records evidence/events, and reaches persisted `COMPLETED` / `SUCCEEDED` truth. |
| Governed effect blocking | VS-M0-002 | API run endpoint, policy evaluator, runtime service, work repository, persistence | `UNKNOWN` policy and unsupported governed effects fail closed, do not invoke the executor, do not create executions, and return bounded API truth. |
| Runtime truth after disposal | VS-M0-003 | PostgreSQL 18 `LOCAL_DOCKER`, persistence store, work repository, event/evidence store, API reconstruction | Work, execution, event, and evidence facts remain readable after application/runtime/store objects are disposed and reconstructed against the same isolated schema. |
| API recorded truth and web/API route alignment | VS-M0-004 preparation | FastAPI route table and `apps/web/src/apiBoundary.ts` | The web API boundary names the same frozen M0 work routes that FastAPI exposes, without requiring a live browser or backend. |
| Cross-work isolation | VS-M0-001 / VS-M0-003 | API observation routes, runtime event/evidence store, PostgreSQL persistence | Work A execution/events/evidence cannot appear under Work B, and reconstruction preserves scoped identity. |
| Provider failure translation | VS-M0-001 failure path | Provider catalog, executor, runtime service, work repository, event store, API translation | Provider failure becomes bounded runtime/API failure without SQLAlchemy, psycopg, stack trace, or provider-native detail leakage. |

## Live Dependencies

The primary vertical-slice test uses the frozen `LOCAL_DOCKER` PostgreSQL 18
service and an isolated generated schema. It starts only the `postgres`
service, stops it cleanly, drops only the generated schema, and verifies the
named volume remains present. It never uses `docker compose down -v`.

Provider inventory uses deterministic fake provider catalogs. No live Ollama,
GPU, downloaded model, external provider, browser automation, or external
network dependency is required.

## Security and Topology Transition

TASK-M0-010 authorizes exactly:

- `tests/integration/test_m0_vertical_slice_integration.py`

The security baseline now secret-scans `tests/integration` and rejects
additional integration files such as scheduler, agent runtime, model router,
DataLab, acceptance-suite, or other future surfaces until their owning tasks
authorize them.

TASK-M0-011 CI changes and TASK-M0-012 acceptance surfaces remain blocked.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Integration tests prove cross-boundary behavior | PASS | New test composes API, runtime, policy, repository, event/evidence store, executor, provider catalog, and PostgreSQL. |
| VS-M0-001 success path | PASS | Provider inventory work reaches `COMPLETED`; execution reaches `SUCCEEDED`; canonical descriptors, evidence, and events are observed through API. |
| VS-M0-002 blocking path | PASS | `UNKNOWN` and unsupported effects return `BLOCKED`/403 and do not invoke the executor. |
| VS-M0-003 persisted recovery | PASS | Runtime/API objects are disposed and reconstructed against the same PostgreSQL schema; recorded truth is reread. |
| API recorded truth | PASS | Work, execution, events, evidence, and provider inventory result are read from API observations after runtime execution. |
| Web/API alignment | PASS | Test compares FastAPI route table with `apps/web/src/apiBoundary.ts` route strings without a live browser. |
| Cross-work isolation | PASS | Execution/event/evidence observations are scoped by work ID; cross-work execution read returns 404. |
| Failure integration | PASS | Provider catalog failure translates to bounded API/runtime failure without native detail leakage. |
| Deterministic provider boundary | PASS | Fake catalogs are used; no live Ollama/network/GPU/model is required. |
| Topology exact | PASS | Security tests authorize only the new TASK-M0-010 integration test file. |
| No production semantics changed | PASS | No production source or dependency manifest changed. |

## Verification

Focused verification performed during implementation:

- TASK-M0-010 integration tests: `2 passed`, `2` known dependency warnings
- security baseline tests: `60 passed`

Repository verification performed:

- TOML validation: passed
- `uv lock --check`: passed
- `uv sync --locked --all-groups --all-packages`: passed
- Docker Compose config: passed
- Ruff: passed
- Ruff format check: passed
- mypy: passed, `53 source files`
- API/API integration/TASK-M0-010 tests: `24 passed`, `2` known dependency
  warnings
- `curios_runtime` tests: `91 passed`
- policy/persistence-boundary/contracts/core tests: `162 passed`
- provider package tests: `29 passed`
- contract/schema/architecture/security/acceptance tests: `97 passed`, `2`
  known dependency warnings
- serial PostgreSQL integration tests: `7 passed`, `2` known dependency
  warnings; postgres service stopped cleanly and the named volume remained
  present
- full pytest: `406 passed`, `2` known dependency warnings
- `pnpm install --frozen-lockfile`: passed
- `pnpm check`: passed
- apps/web tests: `1 file`, `6 passed`
- apps/web typecheck: passed
- apps/web production build: passed

## Lifecycle

TASK-M0-010 is `VALIDATED, FROZEN`.

Independent validation accepted the deterministic M0 integration test
foundation. A validation/freeze commit is required and must be integrated into
`main` before TASK-M0-011 can become ready.
