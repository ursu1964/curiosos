---
id: TASK-M1-007-VALIDATION-EVIDENCE
title: TASK-M1-007 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-007
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-007 Independent Validation Evidence

## Decision

TASK-M1-007 VALIDATION: PASS

Published baseline:

`e176780a94401533fdfb89c52429febe5c07c319`

Implementation:

`2489a0ad59a4804237ff4bbbfdc9fa6ae4575340`

## Reconstructed Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite authority | PASS | TASK-M1-005 and TASK-M1-006 are integrated, validated, frozen, published, and remotely CI-verified in the baseline. The integrated M1 ledger marks TASK-M1-007 `READY`. |
| Authorized ownership | PASS | TASK-M1-007 authorizes M1 runtime lifecycle modules, tests, evidence, and event/evidence integration checks. The implementation adds `curios_runtime.agent_lifecycle_repository` and no new package, manifest, lockfile, migration, API, UI, provider, or model surface. |
| Canonical agent persistence reuse | PASS | The repository reads and replaces canonical `AgentInstance` records through `PersistenceStore` and `PersistenceRecordKind.AGENT_INSTANCE`; no second agent persistence representation or alternate record kind was introduced. |
| Lifecycle transition graph | PASS | Independent validator coverage exhaustively checks every `AgentInstanceState` source/target pair. Authorized transitions succeed, self transitions are idempotent no-ops matching established M0 repository transition semantics, and every disallowed pair fails with bounded `ILLEGAL_TRANSITION`. |
| State mutation scope | PASS | Transitions preserve `agent_definition_id`, `work_id`, optional `execution_id`, `authority_ref`, `principal_ref`, observability context, and `created_at`; only `state`, `started_at`, and `ended_at` lifecycle fields change. |
| Canonical lifecycle events | PASS | Successful changed transitions emit canonical `EventEnvelope` records with event type `agent.lifecycle.transitioned`, agent-instance producer/subject references, caller-supplied `EventId`, caller-supplied `occurred_at`, canonical `ObservabilityContext`, bounded source/target payload, and TASK-M1-007 metadata. |
| Event identity and duplication | PASS | Event identity is caller-supplied canonical `EventId`; duplicate event identity conflicts roll back the state change. Repeated same-state requests do not emit duplicate events. Distinct agents with distinct event IDs keep distinct subject/producer identity. |
| Atomicity | PASS | State replacement and event insertion execute in one persistence transaction. In-memory regression tests cover replace failure, event insert failure, and event conflict rollback. PostgreSQL validator regression proves duplicate-event rollback leaves state unchanged and a retry with a new event ID succeeds. |
| Stale/concurrent safety | PASS | Replacement uses the current record payload hash as an optimistic version token. Optional caller `expected_version` and `expected_state` checks fail boundedly as `CONFLICT`. Existing persistence semantics reject lost updates when the stored payload hash changes. |
| Bounded errors | PASS | Missing instances map to `NOT_FOUND`; illegal transitions map to `ILLEGAL_TRANSITION`; stale state/version and event conflicts map to `CONFLICT`; malformed/wrong-kind records map to `CORRUPT_RECORD`; backend failures map to `PERSISTENCE_FAILURE` without provider-native leakage. |
| Work/DAG/execution boundary | PASS | `work_id` and optional `execution_id` remain logical references in `AgentInstance` and event context. TASK-M1-007 does not mutate `WorkItem`, `WorkDag`, `WorkDagState`, or `ExecutionRecord`; `ACTIVE` does not start execution and `COMPLETED` does not complete work or DAG nodes. |
| Capability boundary | PASS | The lifecycle repository does not import or invoke `curios_capability` and does not reinterpret `MATCH`, `MISSING`, or `AMBIGUOUS` capability-resolution outcomes. |
| Authority boundary | PASS | Actual imports/calls expose no scheduler, executor, routing, provider/model invocation, network access, API/UI behavior, prompt/memory behavior, policy grant, retry/cancellation execution, or DAG mutation authority. |
| PostgreSQL reconstructability | PASS | PostgreSQL integration persists READY/ACTIVE transitions and events through existing M1-006 agent tables and M0 event table, then reconstructs state and events through a new store/repository object. |
| Guard changes | PASS | Security guard changes are additive and bounded to the exact M1-007 runtime file, public declarations, package tests, evidence, ledger, and validation evidence. Previous M1 restrictions remain intact. |

## Delta Review

| Surface | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_runtime/src/curios_runtime/agent_lifecycle_repository.py` | REQUIRED | Owns persisted M1 agent lifecycle transitions and canonical lifecycle event creation. |
| `packages/python/curios_runtime/src/curios_runtime/__init__.py` | JUSTIFIED SUPPORT | Exposes the authorized lifecycle repository and helper symbols from the runtime package. |
| `packages/python/curios_runtime/tests/test_agent_lifecycle_repository.py` | REQUIRED | Covers legal/illegal transitions, idempotency, bounded errors, state/event atomicity, corruption handling, and state vocabulary reuse. |
| `packages/python/curios_runtime/tests/test_postgres_agent_lifecycle_repository_integration.py` | REQUIRED | Proves PostgreSQL-backed lifecycle persistence, event storage, and reconstruction. |
| `packages/python/curios_runtime/tests/test_task_m1_007_validation_regressions.py` | REQUIRED VALIDATION SUPPORT | Adds exhaustive state-pair validation, two-agent event identity checks, and PostgreSQL event-conflict rollback/retry coverage. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Adds bounded authorization for the exact M1-007 runtime and evidence surfaces while preserving future executor/scheduler/provider/API restrictions. |
| `docs/program/status-ledger/M1-status-ledger.md`, `docs/tasks/TASK-M1-007-evidence.md`, `docs/tasks/TASK-M1-007-validation-evidence.md` | REQUIRED | Repository lifecycle and evidence convention. |

No changed file was classified as out of scope.

## State Machine Result

The authoritative M1 task requires lifecycle handling for the frozen
`AgentInstanceState` vocabulary. Validation accepted this graph:

| Source | Authorized targets |
| --- | --- |
| `CREATED` | `READY`, `CANCELLED` |
| `READY` | `ACTIVE`, `CANCELLED` |
| `ACTIVE` | `WAITING`, `COMPLETED`, `FAILED`, `CANCELLED` |
| `WAITING` | `ACTIVE`, `FAILED`, `CANCELLED` |
| `COMPLETED` | none |
| `FAILED` | none |
| `CANCELLED` | none |

Self transitions are idempotent no-ops with no event, matching the existing M0
`transition_work_item` and `transition_execution_record` repository convention.

## Event and Atomicity Result

Validation confirmed `agent.lifecycle.transitioned` is a bounded domain event
type built with the canonical `EventType` primitive and persisted as a canonical
`EventEnvelope`. Payloads include only lifecycle facts and IDs, not embedded
WorkItem, WorkDag, ExecutionRecord, provider, result, or evidence state.

The repository records the replaced `AgentInstance` and lifecycle event in the
same persistence transaction. PostgreSQL validation proved that a duplicate
event conflict rolls back the agent state and that retrying with a new
`EventId` records exactly one new transition event.

## Authority Audit

`curios_runtime.agent_lifecycle_repository` imports only stdlib modules,
`curios_contracts`, and `curios_persistence`.

It contains no imports or call paths for:

- API/FastAPI/web/frontend behavior;
- providers, model/LLM invocation, prompts, memory, network access, routing, or
  provider selection;
- policy evaluation/grants, approvals, evidence mutation, or principal
  mutation;
- capability matching or agent selection;
- WorkItem mutation, WorkDag mutation, ExecutionRecord creation/mutation, DAG
  readiness, scheduling, execution, retry, or cancellation.

## Independent Adversarial Coverage

Additional validator tests checked:

- every legal and illegal source/target state pair;
- same-state idempotency;
- terminal-state rejection;
- event subject/producer reference kind and ID;
- causation reference preservation;
- event payload exclusion of WorkItem/provider/executor fields;
- distinct event/subject identity for two different agents;
- PostgreSQL duplicate-event rollback;
- retry after rollback with a new event ID;
- reconstruction through the existing agent and event repositories.

## Verification

| Check | Result |
| --- | --- |
| Implementation ancestry | PASS: `e176780a94401533fdfb89c52429febe5c07c319..2489a0ad59a4804237ff4bbbfdc9fa6ae4575340` is the TASK-M1-007 implementation commit. |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 243 files already formatted before validation records. |
| Python lint | PASS: `uv run ruff check .`. |
| Python type checking | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 64 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| Contract/schema/architecture/security and M1 regression slice | PASS: 649 passed with 2 known FastAPI/Starlette deprecation warnings. |
| Focused validation regressions | PASS: 3 passed. |
| Docker-backed integrations | PASS: serial slices passed API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, Work DAG repository 1, M1-006 agent repository 1, M1-007 agent lifecycle repository 1, M1-007 validation rollback 3, and M0 vertical slice 2. |
| Acceptance tests | PASS: `uv run pytest -q tests/acceptance` passed 8 tests with 2 known deprecation warnings. |
| Full pytest suite | PASS: `uv run pytest -q` passed 841 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Post-record verification | PASS: after ledger/security/evidence updates, dependency, compose, format, lint, type, frontend, 649-test regression, 8-test acceptance, 841-test full suite, serial Docker-backed integration, and repository diff checks passed. |

Known warnings:

- `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` does not match the task
  worktree `.venv`; `uv` ignored it and used the project environment.
- FastAPI/Starlette `TestClient` deprecation warnings.

No Docker/PostgreSQL lifecycle instability occurred during validation.

## Lifecycle Transition

TASK-M1-007 is `VALIDATED, FROZEN`.

According to the frozen M1 DAG, TASK-M1-008 remains blocked until this
TASK-M1-007 validation/freeze commit is integrated into the main M1 baseline.
TASK-M1-009 remains READY. TASK-M1-010 and TASK-M1-011 remain blocked by their
documented downstream prerequisites.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-008 implementation, or TASK-M1-009 implementation was
performed.
