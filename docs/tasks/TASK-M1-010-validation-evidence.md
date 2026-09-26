---
id: TASK-M1-010-VALIDATION-EVIDENCE
title: TASK-M1-010 Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-010
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-010 Validation Evidence

## Scope

Published baseline:
`d75700510a11e19e63bbb832d32804372dbd5225`

Implementation:
`31be8aa9ac63d191aa0d156d78068cd74e855e2d`

Correction 1:
`ae41a82f10d25bc1ddd7a86c0a74e91591b7c1b6`

Validation reconstructed TASK-M1-010 from the frozen M1 task pack, M1
implementation DAG, M1 status ledger, M0 persistence contracts,
ObjectReference/ReferenceKind contracts, frozen M1-008 executor contracts,
frozen M1-009 profile-discovery contracts, M1-011 boundary, architecture
guardrails, and security constraints.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | TASK-M1-008 and TASK-M1-009 are validated/frozen/integrated/published/remote-CI-verified in the published baseline. |
| Authorized ownership | PASS | Implementation is bounded to M1 runtime/persistence modules, tests, evidence, migration 0005, and a narrow security inventory update. No dependency, lockfile, pnpm, API, UI, M1-009, or M1-011 implementation change is present. |
| Routing candidate records | PASS | `RoutingCandidate` records inert deterministic-executor, model-profile, and no-model candidates for a specific WorkItem reference without callables, provider clients, secrets, or raw provider payloads. |
| Routing request consistency | PASS | Candidate work refs must match request work; duplicate candidate keys fail boundedly; selected-route/work consistency is enforced; malformed provider constraints fail before route selection or persistence. |
| Corrected provider constraint | PASS | `required_provider_ref` now requires `ReferenceKind.PROVIDER`. Wrong-kind work, agent-instance, and execution references fail as `INVALID_CONSTRAINT`; malformed payloads fail boundedly; valid provider references with no matching candidate remain valid `NO_ROUTE`. |
| Deterministic routing | PASS | Exactly one valid candidate selects a route. Zero valid candidates produce `NO_ROUTE` / `NO_VALID_ROUTE`. Multiple valid candidates produce `NO_ROUTE` / `AMBIGUOUS_ROUTE`. Candidate ordering is normalized by candidate key. |
| Constraint semantics | PASS | Supported constraints are exactly `local_only`, `required_route_kind`, and `required_provider_ref`. Unknown constraints, non-local routing, unsupported route kinds, wrong provider-ref kinds, malformed references, unsafe text, and secret-shaped values fail boundedly. |
| No-route semantics | PASS | Empty candidate sets, no-model-only sets, unavailable model profiles, unsupported executor work types, unsatisfied valid constraints, and ambiguous routes create reconstructable `NO_ROUTE` records without fallback execution. |
| Rationale/no-secret boundary | PASS | `RoutingDecisionRationale` uses bounded reason codes and safe details. Secret-shaped constraint values do not appear in public error JSON or persisted route decisions. |
| Routing decision record | PASS | `RoutingDecisionRecord` preserves canonical identity, work reference, status, candidates, selected route, rationale, constraints, timestamp, producer reference, observability context, schema version, deterministic serialization, and reconstruction. |
| Identity/idempotency | PASS | Route selection is deterministic for equivalent requests. Persisted record identity is supplied by `DecisionId`; duplicate persistence is a bounded conflict. Repeated selection does not mutate external state. |
| Persistence repository | PASS | `M1RoutingDecisionRepository` creates, reads, lists, reconstructs, bounds duplicate/corrupt/wrong-kind/backend failures, and preserves append ordering. Invalid requests cannot create records because request construction fails before repository calls. |
| Migration 0005 | PASS | `0005_m1_routing_decision_records` follows `0004_m1_agent_records`, creates only `curios_m1_routing_decision_records`, supports clean upgrade, 0004-to-0005 upgrade, downgrade `-1`, and re-upgrade. |
| M1-009 boundary | PASS | M1-010 consumes supplied model-profile candidates and does not call Ollama discovery, `list_models`, provider catalogs, cloud discovery, profile mutation, or live provider lookup. |
| M1-011 boundary | PASS | No runner, orchestration loop, scheduler, work claiming, executor invocation, agent lifecycle transition, WorkItem/WorkDag/ExecutionRecord mutation, retry/cancellation, provider/model inference, API, or UI behavior is added. |
| Authority/guard boundary | PASS | Imports and calls remain limited to contracts and persistence. Security guard changes are additive and bounded to the exact routing-decision surface and validation evidence. |

## Original Defect Re-Validation

Previous validation found that a structurally valid non-provider
`ObjectReference` could be accepted as `required_provider_ref` and converted to
`NO_ROUTE`.

Correction 1 was independently rechecked:

- valid provider reference matching a candidate -> `SELECTED`;
- valid provider reference matching no candidate -> `NO_ROUTE` /
  `NO_VALID_ROUTE`;
- wrong-kind work, agent-instance, and execution references ->
  `INVALID_CONSTRAINT`;
- malformed reference payloads and missing canonical fields ->
  bounded `INVALID_CONSTRAINT` or pre-normalization `INVALID_REQUEST`;
- secret-shaped malformed payloads do not expose raw input text in public error
  JSON.

## Semantic Reference-Kind Audit

| Field | Required semantic kind | Result |
| --- | --- | --- |
| `required_provider_ref` constraint | `ReferenceKind.PROVIDER` | PASS: enforced by Correction 1. |
| `RoutingCandidate.work_ref` | `ReferenceKind.WORK` | PASS: enforced by `_require_ref_kind`. |
| `RoutingCandidate.provider_ref` | `ReferenceKind.PROVIDER` when present | PASS: enforced for model-profile candidates. |
| `RoutingDecisionRecord.work_ref` | `ReferenceKind.WORK` | PASS: enforced before candidate reconstruction. |
| selected route | Same `work_ref` as decision | PASS: mismatches fail boundedly. |
| request `work` | Canonical `WorkItem` | PASS: typed object check and candidate work matching. |
| `producer_ref` | Generic canonical `ObjectReference` | PASS: intentionally generic; no narrower frozen kind is imposed. |
| `observability_context` | Canonical context with typed optional IDs | PASS: typed object check reuses frozen contract. |

## Adversarial Cases

Validation covered:

- every supported constraint type;
- malformed constraint shapes;
- wrong-kind canonical references;
- valid provider constraint with no match;
- valid provider constraint with exactly one match;
- valid provider constraint with multiple otherwise-valid candidates;
- reversed candidate ordering and repeated route selection;
- duplicate candidate identity;
- cross-work candidate mismatch;
- unavailable profile status;
- unsupported executor work type;
- secret-shaped values;
- corrupt persisted route;
- wrong persistence record kind;
- duplicate route ID;
- backend persistence failure;
- no provider/model/executor invocation.

## Delta Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_runtime/src/curios_runtime/routing_decision_repository.py` | REQUIRED | Owns route decision records, corrected provider-reference constraint validation, deterministic selection, and bounded errors. |
| `packages/python/curios_runtime/src/curios_runtime/__init__.py` | JUSTIFIED SUPPORT | Exports the authorized routing symbols. |
| `packages/python/curios_persistence/src/curios_persistence/kinds.py` | REQUIRED | Adds the authorized `ROUTING_DECISION` record kind. |
| `packages/python/curios_persistence/src/curios_persistence/schema.py` | REQUIRED | Maps routing decisions to the M1 routing table. |
| `packages/python/curios_persistence/src/curios_persistence/boundary.py` | JUSTIFIED SUPPORT | Keeps generic persistence decoding bounded; runtime repository owns route reconstruction. |
| `packages/python/curios_persistence/src/curios_persistence/migrations/versions/0005_m1_routing_decision_records.py` | REQUIRED | Adds the authorized routing decision table. |
| `packages/python/curios_runtime/tests/test_task_m1_010_routing_decision_records.py` | REQUIRED | Covers implementation behavior. |
| `packages/python/curios_runtime/tests/test_task_m1_010_validation_regressions.py` | REQUIRED VALIDATION SUPPORT | Preserves Correction 1 and constraint-boundary regressions. |
| `packages/python/curios_runtime/tests/test_postgres_routing_decision_repository_integration.py` | REQUIRED | Proves PostgreSQL persistence and migration behavior. |
| `packages/python/curios_persistence/tests/test_persistence_boundary.py` | JUSTIFIED SUPPORT | Updates canonical persistence kind/table expectations. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Adds bounded authorization for the exact M1-010 routing-decision surface and validation evidence. |
| `docs/tasks/TASK-M1-010-evidence.md` | REQUIRED | Implementation and Correction 1 evidence. |
| `docs/tasks/TASK-M1-010-validation-evidence.md` | REQUIRED | Independent validation/freeze evidence. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Advances TASK-M1-010 from `IMPLEMENTED, TESTED` to `VALIDATED, FROZEN`. |

No changed file was classified as out of scope.

## Verification

Pre-validation-record checks:

| Check | Result |
| --- | --- |
| History | PASS: `d757005 -> 31be8aa9 -> ae41a82f` ancestry verified. |
| Correction scope | PASS: Correction 1 is limited to provider-ref semantic-kind validation, validation regression coverage, and implementation evidence. |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose -f infrastructure/local/docker/compose.yaml config -q`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 259 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python typing | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 68 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests/typecheck/build | PASS: 6 web tests, direct web typecheck, and production build transformed 18 modules. |
| Contract/schema/architecture/security | PASS: 407 tests with 2 inherited FastAPI/Starlette warnings. |
| M1-001 through M1-010 focused regressions | PASS: 166 tests. |
| Package/API/provider/runtime/persistence non-Docker suite | PASS: 506 tests with 2 inherited FastAPI/Starlette warnings. |
| Docker-backed serial integrations | PASS: API 6, PostgreSQL provider 1, persistence 2, event/evidence 1, work repository 1, Work DAG repository 1, agent repository 1, agent lifecycle repository 1, routing repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: 8 tests with 2 inherited FastAPI/Starlette warnings. |
| Full pytest | INITIAL: 936 passed then Work DAG PostgreSQL integration failed with `Connection refused`; Docker inspection showed no running Postgres container and intact `curios-local-docker_postgres_data` volume. ISOLATED RERUN: affected Work DAG integration passed 1 test. FINAL FULL RERUN: 937 passed with 2 inherited FastAPI/Starlette warnings. |

Post-record verification reran doc-sensitive and repository checks:

- `uv run ruff format --check .`;
- `uv run ruff check .`;
- `uv run mypy apps/api/src packages/python/*/src`;
- `uv run pytest tests/security -q`;
- `uv run pytest packages/python/curios_runtime/tests/test_task_m1_010_validation_regressions.py -q`;
- `uv run pytest packages/python/curios_runtime/tests/test_task_m1_010_routing_decision_records.py -q`;
- `uv run pytest -q`;
- `git diff --check`;
- `git diff --cached --check`.

Known warnings:

- `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` does not match the task
  worktree `.venv`; `uv` ignored it.
- FastAPI/Starlette `TestClient` deprecation warnings remain inherited.

No skipped or deselected tests were counted as passed.

## Decision

TASK-M1-010 is `VALIDATED, FROZEN`.

TASK-M1-011 remains blocked until TASK-M1-010 is integrated into the main M1
baseline with TASK-M1-004, TASK-M1-007, and TASK-M1-008 already available as
validated/frozen integrated prerequisites.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, or TASK-M1-011 implementation was performed.
