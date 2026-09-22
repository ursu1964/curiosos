---
id: TASK-M0-005-EVIDENCE
title: TASK-M0-005 Work Repository and State Transitions Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-005
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-005 Evidence

## Objective

Implement persisted `WorkItem` and `ExecutionRecord` repository behavior and
deterministic M0 state transitions using TASK-M0-002 persistence primitives.

## Starting Baseline

`eb835ec39cde3eb57eceda6fb5045c9cbb124bfd`

## Implemented Surface

- `packages/python/curios_runtime/**`
- narrow `curios_persistence` primitive update for version-checked record
  replacement using the existing payload hash
- TASK-M0-005 unit and PostgreSQL integration tests
- topology/security test updates authorizing `packages/python/curios_runtime`
  for TASK-M0-005
- M0 ledger transition to `IMPLEMENTED, TESTED`

## Repository API

- `M0WorkRepository.create_work`
- `M0WorkRepository.read_work`
- `M0WorkRepository.transition_work`
- `M0WorkRepository.create_execution`
- `M0WorkRepository.read_execution`
- `M0WorkRepository.transition_execution`
- pure helpers `transition_work_item` and `transition_execution_record`

Repository reads return stored canonical records with a deterministic version
token derived from the persistence payload hash.

## State Transition Model

Work transitions:

| Source | Allowed target states |
| --- | --- |
| `CREATED` | `READY`, `CANCELLED` |
| `READY` | `RUNNING`, `CANCELLED` |
| `RUNNING` | `WAITING`, `COMPLETED`, `FAILED`, `CANCELLED` |
| `WAITING` | `RUNNING`, `FAILED`, `CANCELLED` |
| `COMPLETED` | none |
| `FAILED` | none |
| `CANCELLED` | none |

Execution transitions:

| Source | Allowed target states |
| --- | --- |
| `CREATED` | `RUNNING`, `CANCELLED` |
| `RUNNING` | `WAITING`, `SUCCEEDED`, `FAILED`, `CANCELLED` |
| `WAITING` | `RUNNING`, `FAILED`, `CANCELLED` |
| `SUCCEEDED` | none |
| `FAILED` | none |
| `CANCELLED` | none |

Repeated same-state transitions are idempotent and return the current persisted
record unchanged.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Create/read work records | PASS | PostgreSQL integration creates and rereads `WorkItem` records. |
| Create/read execution records | PASS | PostgreSQL integration creates and rereads `ExecutionRecord` records. |
| Missing records | PASS | Repository returns `None` for reads and bounded `NOT_FOUND` for transitions. |
| Legal transitions | PASS | Unit tests enumerate authorized work and execution transitions. |
| Illegal transitions | PASS | Unit and PostgreSQL tests reject invalid transitions with `ILLEGAL_TRANSITION`. |
| Repeated/idempotent transitions | PASS | Same-state transitions return the current record unchanged. |
| Conflict/concurrency behavior | PASS | Stale expected versions produce bounded `CONFLICT`. |
| Persistence/reconstruction | PASS | Live integration rereads final work/execution records after store disposal and repository reconstruction. |
| Bounded persistence failures | PASS | Persistence failures translate to `RepositoryError` without native SQLAlchemy/PostgreSQL detail leakage. |

## Boundary Evidence

- Canonical `WorkItem`, `ExecutionRecord`, `WorkItemState`, and
  `ExecutionState` remain semantic authority.
- `WorkItem` remains distinct from `ExecutionRecord`.
- `EngineeringLifecycle` is not reused for runtime state.
- SQLAlchemy/PostgreSQL details stay inside `curios_persistence`.
- No scheduler, queue, DAG dependency execution, retry system, executor,
  policy evaluator, event/evidence runtime store, API endpoint, or web behavior
  was introduced.
- TASK-M0-004 remains independent and absent on this branch.
- TASK-M0-006 through TASK-M0-014 remain blocked.

## Verification Snapshot

- `uv lock`: PASS
- `uv sync --all-packages --locked`: PASS
- `pytest packages/python/curios_runtime/tests/test_work_repository.py -q`:
  35 passed
- `pytest packages/python/curios_runtime/tests/test_postgres_work_repository_integration.py -q`:
  1 passed against LOCAL_DOCKER PostgreSQL with isolated schema, preserved
  volume, and clean `stop`
- targeted `ruff check`: PASS
- targeted `mypy` with fixture path: PASS

Full repository regression was run separately before commit.

## Lifecycle

TASK-M0-005 is `IMPLEMENTED, TESTED` only.

Independent validation is required before `VALIDATED, FROZEN` or any downstream
readiness transition. TASK-M0-004 remains unchanged. TASK-M0-006 through
TASK-M0-014 remain `BLOCKED`.
