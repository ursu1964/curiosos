---
id: TASK-M1-006-VALIDATION-EVIDENCE
title: TASK-M1-006 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-006
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-006 Independent Validation Evidence

## Decision

TASK-M1-006 VALIDATION: PASS

Published baseline:

`b0b23f4fafd4ae6d9b1e692bec6160e62fd3f41d`

Implementation:

`c8fb4be434fa55133644339af6b922dff252f4da`

## Reconstructed Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite authority | PASS | TASK-M1-001 is integrated, validated, frozen, published, and remotely CI-verified in the baseline. The integrated M1 ledger marks TASK-M1-006 `READY` before implementation. |
| Authorized ownership | PASS | TASK-M1-006 authorizes M1 agent persistence in `curios_runtime.agent_repository` backed by the existing `curios_persistence` boundary. No new package, manifest, or lockfile change was introduced. |
| Canonical agent contracts | PASS | The repository stores and reconstructs frozen `AgentDefinition`, `AgentDefinitionId`, `AgentInstance`, and `AgentInstanceId` values from `curios_contracts`. No shadow DTO/domain representation was introduced. |
| Agent definition persistence | PASS | `create_definition`, `read_definition`, and `list_definitions` persist, reconstruct, and list canonical definitions with deterministic payload-version tokens. Minimal and full-field definitions round-trip exactly. |
| Agent instance persistence | PASS | `create_instance`, `read_instance`, and `list_instances` persist, reconstruct, and list canonical disposable instances with `WorkId` and optional `ExecutionId`. Full-field instances round-trip exactly. |
| Referential semantics | PASS | `create_instance` requires the referenced `AgentDefinition` to exist and fails with bounded `NOT_FOUND` if absent. `WorkId` and optional `ExecutionId` are preserved as logical references only; no WorkItem or ExecutionRecord existence check, mutation, or side effect is introduced. |
| Bounded error semantics | PASS | Duplicate IDs map to `CONFLICT`; malformed/wrong-kind stored records map to `CORRUPT_RECORD`; unknown reads return `None`; backend failures map to `PERSISTENCE_FAILURE` without leaking SQLAlchemy/psycopg/native details. |
| Failure atomicity | PASS | Missing definitions and simulated insert failures do not leave partial agent-instance records. Existing persistence transaction conventions provide database atomicity for PostgreSQL-backed operations. |
| Migration/schema | PASS | `PersistenceRecordKind.AGENT_DEFINITION`, `PersistenceRecordKind.AGENT_INSTANCE`, `curios_m1_agent_definition_records`, `curios_m1_agent_instance_records`, and Alembic revision `0004_m1_agent_records` extend the persistence boundary after `0003_m1_work_dag_records`. |
| Lifecycle boundary | PASS | The repository does not activate, deactivate, start, stop, transition, emit lifecycle events, assign work, claim work, complete work, fail work, retry, cancel, schedule, or execute. Agent state is persisted/reconstructed only as canonical data. |
| Execution and WorkItem boundary | PASS | `execution_id` and `work_id` are referential only. The repository does not create or mutate `ExecutionRecord`, mutate `WorkItem`, derive DAG readiness, alter `WorkDag`, or persist duplicate WorkItem/ExecutionRecord state. |
| Architecture direction | PASS | `curios_contracts` and core packages do not depend on runtime or persistence implementation. Runtime depends on contracts and the persistence boundary, matching established M0 repository patterns. |
| Guard changes | PASS | Security guard changes are additive and bounded to `curios_runtime.agent_repository`, the persistence extension, focused tests, and evidence. They do not authorize lifecycle transitions, executor/scheduler behavior, provider/model invocation, API/UI behavior, policy grants, network access, or DAG mutation. |

## Delta Review

| Surface | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_runtime/src/curios_runtime/agent_repository.py` | REQUIRED | Owns canonical M1 agent definition/instance persistence and bounded repository errors. |
| `packages/python/curios_runtime/src/curios_runtime/__init__.py` | JUSTIFIED SUPPORT | Exposes the authorized repository classes from the runtime package. |
| `packages/python/curios_persistence/src/curios_persistence/{boundary,kinds,schema}.py` | REQUIRED | Adds agent definition/instance record kinds, canonical routing, and table registration. |
| `packages/python/curios_persistence/src/curios_persistence/migrations/versions/0004_m1_agent_records.py` | REQUIRED | Adds the M1 agent definition and instance record tables. |
| `packages/python/curios_runtime/tests/test_agent_repository.py` | REQUIRED | Covers core create/read/list, duplicate, missing-definition, corrupt-payload, and bounded failure behavior. |
| `packages/python/curios_runtime/tests/test_postgres_agent_repository_integration.py` | REQUIRED | Proves PostgreSQL-backed create/read/list/restart behavior and table creation. |
| `packages/python/curios_runtime/tests/test_task_m1_006_validation_regressions.py` | REQUIRED VALIDATION SUPPORT | Independent validator coverage for full-field round-trip, cross-typed IDs, missing-definition atomicity, insert-failure atomicity, wrong-kind corruption, and canonical payload preservation. |
| `packages/python/curios_persistence/tests/test_persistence_boundary.py` | JUSTIFIED SUPPORT | Extends canonical persistence round-trip and schema inventory tests for the new record kinds/tables. |
| `packages/python/curios_persistence/tests/test_postgres_persistence_integration.py` | JUSTIFIED SUPPORT | Updates downgrade table assertions to include M1 tables. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Adds bounded authorization for the exact M1-006 runtime and persistence surfaces while preserving future-surface rejection. |
| `docs/program/status-ledger/M1-status-ledger.md`, `docs/tasks/TASK-M1-006-evidence.md`, `docs/tasks/TASK-M1-006-validation-evidence.md` | REQUIRED | Repository lifecycle and evidence convention. |

No changed file was classified as out of scope.

## Independent Adversarial Coverage

Additional validator tests checked:

- full `AgentDefinition` fields, including constraints and canonical references, round-trip exactly;
- full `AgentInstance` fields, including `work_id`, `execution_id`, state, authority/principal refs, and timestamps, round-trip exactly;
- persisted agent-instance payloads do not contain WorkItem fields, ExecutionRecord fields, provider fields, result fields, evidence fields, dependency state, or execution errors;
- cross-typed `AgentDefinitionId`/`AgentInstanceId` reads fail before persistence lookup;
- missing referenced definitions fail boundedly and leave no partial instance record;
- simulated backend failure during instance insert after definition read returns bounded `PERSISTENCE_FAILURE` and leaves no partial instance record;
- wrong-kind persistence records fail as `CORRUPT_RECORD` and are not reinterpreted as the requested canonical type;
- `canonical_to_record` preserves exact canonical payloads for both agent definition and agent instance.

## Migration Validation

An isolated PostgreSQL schema migration probe verified:

- applying revision `0003_m1_work_dag_records` leaves no M1 agent tables;
- upgrading to head creates `curios_m1_agent_definition_records` and
  `curios_m1_agent_instance_records`;
- both tables have the standard persistence columns:
  `append_ordinal`, `canonical_id`, `payload`, `payload_sha256`, `created_at`,
  and `updated_at`;
- `downgrade -1` removes only the two M1-006 agent tables and preserves the
  M1 Work DAG table;
- re-upgrade to head restores the two M1-006 tables.

## Authority Audit

`curios_runtime.agent_repository` imports only stdlib modules,
`curios_contracts`, and `curios_persistence`.

It contains no imports or call paths for:

- API/FastAPI/web/frontend behavior;
- providers, model/LLM invocation, prompts, memory, network access, routing, or
  provider selection;
- policy evaluation/grants, principal mutation, approvals, or evidence
  mutation;
- lifecycle transition/event ownership;
- work assignment, scheduling, execution, retry, cancellation, or DAG mutation;
- SQLAlchemy, psycopg, Alembic, or database-native APIs outside the canonical
  persistence boundary.

## Verification

| Check | Result |
| --- | --- |
| Implementation ancestry | PASS: `b0b23f4fafd4ae6d9b1e692bec6160e62fd3f41d..c8fb4be434fa55133644339af6b922dff252f4da` is the TASK-M1-006 implementation commit. |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 237 files already formatted before validation records and 238 files after validation records. |
| Python lint | PASS: `uv run ruff check .`. |
| Python type checking | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 63 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| Contract/schema/architecture/security and M1 regression slice | PASS: 636 passed with 2 known FastAPI/Starlette deprecation warnings. |
| Package/API/provider/runtime/persistence non-Docker slice | PASS: 200 passed, 5 deselected, with 2 known FastAPI/Starlette deprecation warnings. |
| Focused validation regressions | PASS: 6 passed. |
| Docker-backed integrations | PASS: serial slices passed API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, Work DAG repository 1, M1-006 agent repository 1, and M0 vertical slice 2. |
| Migration probe | PASS: isolated PostgreSQL 0003 -> head -> downgrade -1 -> head sequence completed and inspected the resulting tables/columns. |
| Acceptance tests | PASS: `uv run pytest -q tests/acceptance` passed 8 tests with 2 known deprecation warnings. |
| Full pytest suite | PASS: `uv run pytest -q` passed 821 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Post-record verification | PASS: after ledger/evidence updates, `uv run ruff format --check .`, `uv run ruff check .`, the targeted guard/contract/schema/acceptance/validator slice passed 421 tests, full `uv run pytest -q` passed 821 tests, and `git diff --check` / `git diff --cached --check` passed. |
| Repository diff checks | PASS before and after validation-record changes: `git diff --check` and `git diff --cached --check`. |

Known warnings:

- `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` does not match the task
  worktree `.venv`; `uv` ignored it and used the project environment.
- FastAPI/Starlette `TestClient` deprecation warnings.

One invalid local command used a non-existent package test path and was
corrected to the actual repository test roots; no product test failed.

## Lifecycle Transition

TASK-M1-006 is `VALIDATED, FROZEN`.

According to the frozen M1 DAG, TASK-M1-007 becomes eligible after this
TASK-M1-006 validation/freeze commit is integrated into the main M1 baseline.
TASK-M1-008, TASK-M1-010, and TASK-M1-011 remain blocked by their documented
downstream prerequisites. TASK-M1-009 remains READY.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-007 implementation, or TASK-M1-009 implementation was
performed.
