---
id: TASK-M0-010-VALIDATION-EVIDENCE
title: TASK-M0-010 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-010
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-010 Independent Validation Evidence

## Decision

TASK-M0-010 VALIDATION: PASS

Validated candidate:

`1fc97295eb389ae5b4f501b12d2e9df19232f062`

Starting baseline:

`245447c133264b5e4e1bf140c8ed3ad72b7f72ef`

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Scope exact | PASS | Candidate adds integration tests, evidence, lifecycle docs, and guardrail authorization only. Diff from baseline has no production changes under contracts, core, persistence, policy, runtime, provider executor, API, or web. |
| No CI or acceptance implementation | PASS | No `.github/**` or `tests/acceptance/**` changes were introduced. TASK-M0-011 through TASK-M0-014 remain unimplemented. |
| Test value | PASS | The new suite composes API, policy, runtime service, work repository, event/evidence store, provider executor/catalog seam, and PostgreSQL; it is not a pure unit-test duplicate. |
| VS-M0-001 provider inventory | PASS | API-created `provider_inventory` work runs through policy and `SingleStepRuntimeService`, invokes `ProviderInventoryExecutor` twice for two independent successful works, records deterministic sorted provider descriptors, evidence, events, `SUCCEEDED` execution, and `COMPLETED` work. |
| VS-M0-002 governed-effect blocking | PASS | `policy_state_known=false` produces `UNKNOWN`/403 and unsupported `EXTERNAL_READ` produces `DENY`/403 through the frozen API request body without changing API surface. Executor call count remains unchanged and no execution is created for blocked work. |
| VS-M0-003 PostgreSQL reconstruction | PASS | Runtime/API/store objects are disposed, reconstructed against the same isolated PostgreSQL schema, and work, execution, event, and evidence truth is reread from PostgreSQL rather than retained Python objects. |
| VS-M0-004 API recorded truth preparation | PASS | API observation routes return the work, execution, events, evidence, and provider result produced by runtime and persisted through PostgreSQL. Full browser/backend acceptance remains TASK-M0-012 scope. |
| Web/API alignment | PASS | Test checks frozen FastAPI route paths and methods and verifies `apps/web/src/apiBoundary.ts` names the same M0 routes. This catches route path/method drift in the covered frozen route set; response-shape depth remains covered by TASK-M0-009 web tests and later acceptance. |
| Cross-work isolation | PASS | Work A and Work B are independently created and run. Cross-work execution lookup returns 404, event/evidence subjects remain scoped to each work, and no A evidence/events appear under B before reconstruction. Reconstruction rechecks persisted A truth; no in-memory fixture authority is used for persisted reads. |
| Ordering and identity | PASS | Canonical work and execution IDs are distinct, descriptor ordering is deterministic despite reversed catalog input, event ordering follows append order, and execution/work references are coherent. |
| Provider failure translation | PASS | A deterministic failing catalog crosses provider executor, runtime, repository, event store, and API translation. API returns bounded 502 detail without SQLAlchemy, psycopg, traceback, credentials, or raw provider-native leakage, while persisted work/execution/event truth remains coherent. |
| Additional failure scope | PASS | TASK-M0-010 does not explicitly require duplicating TASK-M0-006's complete failure matrix. The representative provider/catalog failure required for integration behavior is present. |
| Provider determinism | PASS | Tests use deterministic fake provider catalogs and no live Ollama, GPU, downloaded model, external provider, browser automation, or external network. PostgreSQL is the only authorized live dependency. |
| PostgreSQL lifecycle | PASS | Docker-backed tests use `postgres:18` `LOCAL_DOCKER`, isolated generated schemas, serial PostgreSQL execution where required, clean `docker compose stop postgres`, named volume preservation, and no `docker compose down -v`. |
| Frozen prerequisites | PASS | TASK-M0-001 through TASK-M0-009 remain validated/frozen and no frozen production behavior changed. |
| Security topology | PASS | Security topology authorizes exactly `tests/integration/test_m0_vertical_slice_integration.py` for TASK-M0-010, secret-scans `tests/integration`, and rejects representative scheduler, agent, model-router, DataLab, acceptance-suite, and unrelated M0 integration files. |
| Architecture | PASS | Tests compose frozen packages without introducing production dependencies on tests, production helper APIs, or dependency-direction changes. |
| Test quality | PASS | Material cross-boundary behaviors cannot break silently in the covered scenarios without failing the new integration tests. Remaining response-shape/browser depth is intentionally deferred to TASK-M0-012 acceptance. |
| Dependency audit | PASS | No dependency manifest or lockfile changed. |

## Scenario Matrix

| Scenario | Cross-component invariant |
| --- | --- |
| Successful provider inventory work | API-created canonical work is authorized by policy, executed exactly once by the provider inventory executor, persisted by repository/store boundaries, and observed through API as `COMPLETED`/`SUCCEEDED` with deterministic provider descriptors. |
| Governed-effect blocking | Non-authorizing policy outcomes prevent executor invocation and execution creation while preserving bounded work/policy/runtime truth through API. |
| PostgreSQL reconstruction | PostgreSQL, not first-runtime Python memory, remains the source of truth after disposing and recreating process-level runtime/API/store objects. |
| API recorded truth | API observation is backed by repository and event/evidence store reads, not API-local fabricated state. |
| Web/API route alignment | The web boundary references the frozen TASK-M0-008 route paths that FastAPI exposes. |
| Cross-work isolation | Work, execution, event, evidence, and subject/reference identities do not cross-contaminate between independently executed work items. |
| Provider failure translation | Provider/catalog failure is bounded through executor, runtime, persistence, and API without native exception leakage. |

## Mechanical Verification

| Check | Result |
| --- | --- |
| TASK-M0-010 integration tests | PASS: 2 passed, 2 known dependency warnings. |
| TASK-M0-008 API/API integration/TASK-M0-010 tests | PASS: 24 passed, 2 known dependency warnings. |
| TASK-M0-006/007 runtime tests | PASS: 91 passed. |
| Policy, persistence-boundary, contracts/core, contract/schema | PASS: 167 passed. |
| Provider/config/observability packages | PASS: 29 passed. |
| Architecture/security/BOOT acceptance | PASS: 82 passed, 2 known dependency warnings. |
| PostgreSQL integrations serially | PASS: 7 passed, 2 known dependency warnings; named volume preserved and Compose service stopped. |
| Full pytest serially | PASS: 406 passed, 2 known dependency warnings. |
| TOML validation | PASS: 11 TOML files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS. |
| Ruff | PASS. |
| Ruff format | PASS: 187 files already formatted. |
| Authoritative mypy source scope | PASS: no issues found in 53 source files. |
| `pnpm install --frozen-lockfile` | PASS; an initial local `node_modules` integrity issue was corrected by a forced reinstall from the frozen lockfile before frontend gates were accepted. |
| `pnpm check` | PASS. |
| Web tests | PASS: 1 file, 6 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |

Known warnings are the existing Starlette/FastAPI `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings.

## Lifecycle And Downstream Readiness

TASK-M0-010 is `VALIDATED, FROZEN`.

A validation/freeze commit is required and must be integrated into `main`
before downstream readiness changes. Under the frozen M0 DAG, TASK-M0-011
becomes `READY` only after the TASK-M0-010 validation/freeze commit is
integrated into `main`.

TASK-M0-011 through TASK-M0-014 remain blocked at this validation point. No
merge, push, CI implementation, acceptance implementation, or TASK-M0-011+
work was performed.

## Files Modified

- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-010-evidence.md`
- `docs/tasks/TASK-M0-010-validation-evidence.md`

## Final Git Status

```text
M  docs/program/status-ledger/M0-status-ledger.md
M  docs/tasks/TASK-M0-010-evidence.md
?? docs/tasks/TASK-M0-010-validation-evidence.md
```
