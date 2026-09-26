---
id: TASK-M1-007-EVIDENCE
title: TASK-M1-007 Agent Lifecycle Repository and Events Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-007
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-007 Evidence

## Objective

Record persisted canonical `AgentInstance` lifecycle transitions and canonical
events without implementing scheduling, execution, provider/model invocation,
policy grants, agent memory, API routes, or UI behavior.

TASK-M1-007 reuses the frozen M1-006 `AgentInstance` persistence boundary and
the frozen event/evidence contracts. It does not duplicate `WorkItem`,
`WorkDag`, `ExecutionRecord`, capability-resolution, or provider abstractions.

## Starting Baseline

`e176780a94401533fdfb89c52429febe5c07c319`

TASK-M1-001 through TASK-M1-006 are integrated, validated, frozen, published,
and remotely CI-verified at this baseline. The integrated M1 DAG records
TASK-M1-007 as `READY` because TASK-M1-005 and TASK-M1-006 are both
validated/frozen and integrated.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Canonical agent persistence reuse | PASS | `M1AgentLifecycleRepository` reads and replaces canonical `AgentInstance` records through the existing `PersistenceStore` boundary and does not introduce a shadow agent record. |
| Legal lifecycle transitions | PASS | `AGENT_INSTANCE_TRANSITIONS` covers the frozen `CREATED`, `READY`, `ACTIVE`, `WAITING`, `COMPLETED`, `FAILED`, and `CANCELLED` vocabulary. Unit tests cover valid forward transitions, repeated same-state idempotency, and illegal backward/terminal transitions. |
| Bounded failure semantics | PASS | Missing instances, stale expected state/version, corrupt persisted records, illegal transitions, and persistence failures raise bounded `AgentLifecycleError` values with stable codes and no provider-native exception leakage. |
| Persisted state mutation | PASS | `transition_instance` updates only the canonical `AgentInstance.state`, `started_at`, and `ended_at` lifecycle fields. It preserves `agent_definition_id`, `work_id`, `execution_id`, authority, principal, and observability references. |
| Canonical lifecycle events | PASS | Successful changed transitions emit canonical `EventEnvelope` records with event type `agent.lifecycle.transitioned`, agent-instance subject/producer references, canonical observability context, bounded payload, and TASK-M1-007 metadata. |
| Atomic state/event behavior | PASS | State replacement and event insertion occur in one persistence transaction. Regression tests prove event conflicts, replacement failures, and event insert failures roll back state changes. |
| Idempotency | PASS | Repeating a request for the current state returns `changed=False`, preserves the existing version, and emits no duplicate event. |
| Reconstructability | PASS | PostgreSQL integration creates an agent definition/instance, records READY and ACTIVE lifecycle events, recreates the persistence store, and reconstructs the persisted instance and events. |
| Work and execution boundaries | PASS | `work_id` and optional `execution_id` remain logical references carried by `AgentInstance` and `ObservabilityContext`; TASK-M1-007 does not mutate `WorkItem`, `WorkDag`, or `ExecutionRecord`. |
| Authority boundary | PASS | The implementation has no scheduler, executor, retry/cancel execution, provider/model invocation, network, API, UI, prompt, memory, policy-grant, or DAG-mutation behavior. |
| Architecture/security guards | PASS | Security inventory authorizes only `agent_lifecycle_repository.py`, its public declarations, focused tests, ledger, and evidence for TASK-M1-007. Existing M1-001 through M1-006 guard restrictions remain in force. |
| Dependency scope | PASS | No `pyproject.toml`, `uv.lock`, package manifest, pnpm lockfile, or migration/schema change was required. |

## Files Changed

- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-007-evidence.md`
- `packages/python/curios_runtime/src/curios_runtime/__init__.py`
- `packages/python/curios_runtime/src/curios_runtime/agent_lifecycle_repository.py`
- `packages/python/curios_runtime/tests/test_agent_lifecycle_repository.py`
- `packages/python/curios_runtime/tests/test_postgres_agent_lifecycle_repository_integration.py`
- `tests/security/test_security_baseline.py`

## Lifecycle Semantics

TASK-M1-007 implements these authorized transitions:

| Source | Targets |
| --- | --- |
| `CREATED` | `READY`, `CANCELLED` |
| `READY` | `ACTIVE`, `CANCELLED` |
| `ACTIVE` | `WAITING`, `COMPLETED`, `FAILED`, `CANCELLED` |
| `WAITING` | `ACTIVE`, `FAILED`, `CANCELLED` |
| `COMPLETED` | none |
| `FAILED` | none |
| `CANCELLED` | none |

The repository treats same-state requests as idempotent observations, not as
new transitions. Entering `ACTIVE` sets `started_at` if absent. Entering a
terminal state sets `ended_at` if absent.

## Authority Inventory

TASK-M1-007 introduces these authorized capabilities:

- persisted canonical `AgentInstance` lifecycle transition;
- canonical lifecycle `EventEnvelope` creation;
- atomic persistence of state replacement and event insertion;
- bounded lifecycle repository errors for conflict, corrupt records, illegal
  transitions, not found, and persistence failures;
- PostgreSQL integration over the existing M1-006 agent tables and existing
  event/evidence persistence table.

TASK-M1-007 leaves these absent:

- capability matching or agent selection;
- policy evaluation or grants;
- provider/model selection or invocation;
- network access;
- WorkItem mutation, WorkDag mutation, or derived DAG readiness;
- ExecutionRecord creation or mutation;
- scheduling, execution, retry, or cancellation;
- prompt construction, memory access, API behavior, or UI behavior;
- new migration, table, workspace package, or third-party dependency.

## Verification

| Check | Result |
| --- | --- |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 241 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python typing | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 64 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| M1 regression, contract, schema, architecture, and security tests | PASS: combined slice passed 646 tests with 2 known FastAPI/Starlette deprecation warnings. |
| M1-007 focused unit tests | PASS: included in the combined regression slice; `test_agent_lifecycle_repository.py` passed 16 tests in focused verification. |
| Docker-backed integrations | PASS: serial slices passed API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, Work DAG repository 1, M1-006 agent repository 1, M1-007 agent lifecycle repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: `uv run pytest -q tests/acceptance` passed 8 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Full pytest suite | PASS: `uv run pytest -q` passed 838 tests with 2 known FastAPI/Starlette deprecation warnings. |

One serial Docker command initially failed before running the Work DAG slice
because the command used the wrong local test path for that existing file. The
correct owner path, `packages/python/curios_dag/tests/test_postgres_work_dag_repository_integration.py`,
passed on rerun. This was a command/path error, not a product or infrastructure
failure.

## Lifecycle State

TASK-M1-007 is `IMPLEMENTED, TESTED`.

Independent validation/freeze is still required before TASK-M1-007 can become
an integrated prerequisite for TASK-M1-008.
