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

## Corrective Evidence After Validation Failure

Independent validation of candidate
`595f9d868136df78c81d946b729463ec87073441` failed because corrupt persisted
canonical payloads could cross the public repository boundary as raw canonical
parser exceptions. A malformed `WORK` payload with the correct persistence
record kind could reach `WorkItem.from_json_compatible(...)` and expose a raw
`KeyError`; the same decode-boundary defect structurally applied to
`ExecutionRecord` reads and to transition paths that read persisted state first.

The correction keeps TASK-M0-005 state and concurrency semantics unchanged and
adds bounded decode handling for persisted canonical records:

- corrupt persisted `WorkItem` payloads now raise
  `RepositoryError(PERSISTENCE_FAILURE)`;
- corrupt persisted `ExecutionRecord` payloads now raise
  `RepositoryError(PERSISTENCE_FAILURE)`;
- read operations preserve `read_work` / `read_execution` operation metadata;
- transition read failures preserve `transition_work` /
  `transition_execution` operation metadata;
- public `RepositoryError` values do not expose the raw parser exception through
  `__cause__` or `__context__`.

Adversarial unit coverage now includes missing required fields, invalid state
enum values, and structurally malformed canonical payloads for:

- `read_work`;
- `transition_work`;
- `read_execution`;
- `transition_execution`.

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
| Bounded corrupt canonical payloads | PASS | Malformed persisted work/execution payloads translate to `RepositoryError(PERSISTENCE_FAILURE)` across read and transition paths. |

## Boundary Evidence

- Canonical `WorkItem`, `ExecutionRecord`, `WorkItemState`, and
  `ExecutionState` remain semantic authority.
- `WorkItem` remains distinct from `ExecutionRecord`.
- `EngineeringLifecycle` is not reused for runtime state.
- SQLAlchemy/PostgreSQL details stay inside `curios_persistence`.
- Canonical decode/parser exceptions from corrupt persisted payloads stay
  behind `RepositoryError(PERSISTENCE_FAILURE)`.
- No scheduler, queue, DAG dependency execution, retry system, executor,
  policy evaluator, event/evidence runtime store, API endpoint, or web behavior
  was introduced.
- TASK-M0-004 remains independent and absent on this branch.
- TASK-M0-006 through TASK-M0-014 remain blocked.

## Verification Snapshot

- TOML validation: PASS, 11 `pyproject.toml` files parsed
- `uv lock --check`: PASS, resolved 46 packages
- `uv sync --locked --all-groups --all-packages`: PASS, checked 43 packages
- Docker Compose config: PASS
- `ruff check .`: PASS
- `ruff format --check .`: PASS, 164 files already formatted
- authoritative CI mypy scope
  `uv run mypy apps/api/src packages/python/*/src`: PASS, 49 source files
- `pytest packages/python/curios_runtime/tests/test_work_repository.py -q`:
  47 passed
- `pytest packages/python/curios_runtime/tests/test_postgres_work_repository_integration.py -q`:
  1 passed against LOCAL_DOCKER PostgreSQL with isolated schema, preserved
  volume, and clean `stop`
- persistence/policy regressions:
  `pytest packages/python/curios_persistence/tests/test_persistence_boundary.py packages/python/curios_policy/tests -q`:
  39 passed
- contracts/core regressions:
  `pytest tests/contract tests/schema packages/python/curios_contracts/tests packages/python/curios_core/tests -q`:
  138 passed
- architecture/security:
  `pytest tests/architecture tests/security -q`: 50 passed
- API integration plus BOOT acceptance:
  `pytest tests/integration/test_api_integration.py tests/acceptance -q`:
  12 passed, 2 known dependency warnings
- PostgreSQL persistence integration:
  `pytest packages/python/curios_persistence/tests/test_postgres_persistence_integration.py -q`:
  1 passed serially
- PostgreSQL provider integration:
  `pytest tests/integration/test_postgres_provider_integration.py -q`:
  1 passed serially
- full pytest suite: `pytest -q`: 327 passed, 2 known dependency warnings
- frontend regression: `pnpm install --frozen-lockfile`, `pnpm check`,
  `pnpm --dir apps/web test`, `pnpm --dir apps/web typecheck`, and
  `pnpm --dir apps/web build` passed; web tests reported 1 file / 2 tests and
  production build transformed 18 modules
- `git diff --check`: PASS

Docker/PostgreSQL-dependent verification was run serially after the corrective
patch to avoid competing local PostgreSQL lifecycle commands. The named volume
was preserved; `docker compose down -v` was not used.

## Lifecycle

TASK-M0-005 is `IMPLEMENTED, TESTED` only.

Independent validation is required before `VALIDATED, FROZEN` or any downstream
readiness transition. TASK-M0-004 remains unchanged. TASK-M0-006 through
TASK-M0-014 remain `BLOCKED`.
