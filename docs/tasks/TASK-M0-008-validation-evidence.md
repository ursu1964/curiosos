---
id: TASK-M0-008-VALIDATION-EVIDENCE
title: TASK-M0-008 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-008
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-008 Independent Validation Evidence

## Decision

TASK-M0-008 VALIDATION: PASS

Validated candidate:

`9d859b5f6541432c6ef2482225f19f78536b93ad`

Starting baseline:

`02789840a311c9ed21b52b5384ea477104c6854c`

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Endpoint surface exact | PASS | Candidate adds only the authorized M0 work routes: `POST /work/provider-inventory`, `GET /work/{work_id}`, `POST /work/{work_id}/run`, `GET /work/{work_id}/executions/{execution_id}`, `GET /work/{work_id}/events`, and `GET /work/{work_id}/evidence`. Frozen `GET /health/live`, `GET /health/ready`, and `GET /providers` remain semantically unchanged. FastAPI's framework documentation routes are not product capability. |
| FastAPI ownership | PASS | FastAPI remains outer composition/translation. Route handlers translate to canonical `WorkItem`, `WorkId`, `ExecutionId`, `EffectClassification`, `ObservabilityContext`, and frozen runtime/repository/store APIs. No Pydantic/FastAPI model becomes canonical authority. |
| Work creation | PASS | `POST /work/provider-inventory` creates a canonical `WorkItem` through `M0WorkRepository`, exposes only `provider_inventory`, ignores arbitrary executor/authority/state injection, and does not declare authorization. |
| Policy/effect bypass | PASS | Unsupported, mixed, duplicate, malformed, and empty effect requests do not bypass `MinimalM0PolicyEvaluator` or `SingleStepRuntimeService`. Unsupported governed effects produce non-authorizing policy truth; malformed/empty input may fail early at the HTTP boundary. Forged policy/authority/executor/provider-routing fields do not authorize unsupported effects. |
| Run endpoint | PASS | `POST /work/{work_id}/run` invokes `SingleStepRuntimeService.run_once` and translates bounded runtime results/errors. Successful provider inventory, policy `BLOCKED`, missing work, illegal state/repeated run, conflicts, repository/runtime-store failures, and executor/provider failures remain bounded. |
| Observation/scoping | PASS | Work/execution reads use `M0WorkRepository`; event/evidence reads use `EventEvidenceRuntimeStore`. Execution reads reject cross-work `execution_id` leakage by checking stored `execution.record.work_id`. Event/evidence lists are filtered by canonical `subject_ref == ObjectReference.from_id(work_id)`. |
| Canonical serialization | PASS | Responses are derived from canonical/runtime values through `to_json_compatible`. No persistence records, SQLAlchemy/PostgreSQL rows, provider-native payloads, internal exceptions, or FastAPI/Pydantic objects become response authority. |
| HTTP error matrix | PASS | Malformed/unsupported input maps to bounded 400 details; missing work/execution to 404; policy `BLOCKED` to 403 with canonical runtime-result detail; illegal state/conflict to 409; executor/provider failure to 502 with canonical runtime-result detail; repository/runtime-store/runtime infrastructure failures to bounded 503 unless frozen error codes indicate 404/409. No native exception detail crosses HTTP. |
| Runtime composition | PASS | Explicit M0 API composition wires frozen `M0WorkRepository`, `EventEvidenceRuntimeStore`, `MinimalM0PolicyEvaluator`, `SingleStepRuntimeService`, and `ProviderInventoryExecutor`. Default app construction remains deterministic and does not require live PostgreSQL, live Ollama, external network, GPU, or model download. |
| Persistence/reconstruction | PASS | TASK-M0-008 does not require new API-owned PostgreSQL reconstruction authority. The API has no hidden in-memory domain authority; explicit composition over a persistence store preserves work/events/evidence across app reconstruction. PostgreSQL reconstruction remains owned by frozen persistence/repository/store integration and later M0 integration/acceptance scope. |
| Identity/observability | PASS | Canonical `WorkId`, `ExecutionId`, `TraceId`, `ObjectReference`, event subjects, evidence subjects, and runtime observability contexts survive HTTP-to-runtime-to-observation where defined. HTTP request fields do not become authority beyond canonical runtime inputs. |
| API topology/security | PASS | Current authorized API files are exact: `composition.py`, `service.py`, `__init__.py`, `py.typed`, and exact API test files. Representative tracked additions for scheduler, agent, model, admin, retry, tools, generic runtime routes, and unrelated integration tests were rejected by topology. Secret scanning covers new API source/tests/docs/config surfaces. |
| Architecture/dependencies | PASS | No inward package depends on `curios_api`; FastAPI/Starlette/Pydantic remain API-local; runtime/providers/contracts/core do not depend on API; contracts/core remain framework-independent. New API dependencies on `curios-persistence`, `curios-policy`, and `curios-runtime` are REQUIRED for explicit outer composition. |
| Frozen prerequisites | PASS | Diff from the starting baseline does not semantically change frozen TASK-M0-006 runtime, TASK-M0-007 executor, policy, repository, event/evidence store, persistence, or canonical contracts. |
| Test quality | PASS | Existing tests cover success, blocked policy, unsupported/malformed effects, unsupported creation, executor failure, reconstruction over the same store, and missing runtime composition. Independent adversarial probes covered cross-work execution/event/evidence leakage, duplicate/empty effects, forged policy/authority/executor fields, and tracked topology additions. |

## Endpoint Surface

Authorized product routes:

- `GET /health/live`
- `GET /health/ready`
- `GET /providers`
- `POST /work/provider-inventory`
- `GET /work/{work_id}`
- `POST /work/{work_id}/run`
- `GET /work/{work_id}/executions/{execution_id}`
- `GET /work/{work_id}/events`
- `GET /work/{work_id}/evidence`

The M0 work routes are the exact route contract for TASK-M0-009 consumers after
integration.

## Adversarial Probes

Validation exercised additional HTTP scenarios beyond the candidate tests:

- cross-work execution lookup returned 404 and did not leak another work's execution;
- events and evidence for two completed works were scoped to their canonical work subjects;
- duplicate `READ_ONLY` effects reached policy and produced `DENY`/`BLOCKED`;
- empty effect set failed early as malformed input;
- unsupported `EXTERNAL_WRITE` plus forged policy/authority/executor/provider-routing fields still produced policy `DENY`/`BLOCKED`;
- work creation with injected state/executor/authority fields persisted a canonical `CREATED` provider-inventory work item only.

Representative staged topology additions were rejected:

- `scheduler_routes.py`
- `agent_routes.py`
- `model_routes.py`
- `arbitrary_admin.py`
- `retry_routes.py`
- `tools.py`
- `generic_runtime_routes.py`
- an unrelated integration test under `tests/integration`

Probe files were removed after validation.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS: 11 `pyproject.toml` files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS: `infrastructure/local/docker/compose.yaml`. |
| Ruff | PASS. |
| Ruff format | PASS: 182 files already formatted. |
| Authoritative mypy | PASS: `uv run mypy apps/api/src packages/python/*/src`; 53 source files. |
| TASK-M0-008 tests | PASS: 7 passed, 2 known dependency warnings. |
| TASK-BOOT-022 API tests plus TASK-BOOT-023 API integration | PASS: 15 passed, 2 known dependency warnings. |
| TASK-M0-006 tests | PASS: 25 passed. |
| TASK-M0-007 tests | PASS: 8 passed. |
| Policy tests | PASS: 20 passed. |
| Runtime-store/work-repository tests | PASS: 56 passed. |
| Persistence tests | PASS: 21 passed. |
| Contracts/core tests | PASS: 123 passed. |
| Provider packages | PASS: 29 passed. |
| Contract/schema tests | PASS: 15 passed. |
| Architecture/security | PASS: 64 passed. |
| API integration | PASS: included in the 15-test API group. |
| PostgreSQL provider integration | PASS: 1 passed serially. |
| PostgreSQL runtime event/evidence integration | PASS: 1 passed serially. |
| PostgreSQL runtime work repository integration | PASS: 1 passed serially. |
| PostgreSQL persistence integration | PASS: 2 passed serially. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| Full pytest serially | PASS: 392 passed, 2 known dependency warnings. |
| `pnpm install --frozen-lockfile` | PASS. |
| `pnpm check` | PASS. |
| Web tests | PASS: 1 test file, 2 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |

The known warnings are the existing Starlette/FastAPI `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings.

PostgreSQL-dependent checks were run serially. The named PostgreSQL volume was
preserved; no `docker compose down -v` was used.

## Lifecycle And Downstream Readiness

TASK-M0-008 is `VALIDATED, FROZEN`.

The validation/freeze commit is required and must be integrated into `main`
before downstream readiness changes. Under the frozen M0 DAG, TASK-M0-009
remains `BLOCKED` on this task branch and becomes `READY` only after the
TASK-M0-008 validation/freeze commit is integrated into `main`.

TASK-M0-009 was not implemented, started, or otherwise advanced by this
validation.

## Files Modified

- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-008-evidence.md`
- `docs/tasks/TASK-M0-008-validation-evidence.md`

## Commit And Integration Requirements

This validation produced documentation-only lifecycle changes. A
validation/freeze commit is required for these changes, and that commit must be
integrated into `main` before TASK-M0-009 can become `READY`.

No merge, push, or TASK-M0-009 implementation was performed.

## Final Git Status

```text
 M docs/program/status-ledger/M0-status-ledger.md
 M docs/tasks/TASK-M0-008-evidence.md
?? docs/tasks/TASK-M0-008-validation-evidence.md
```
