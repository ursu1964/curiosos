---
id: TASK-M1-011-EVIDENCE
title: TASK-M1-011 Bounded DAG Runner Evidence
lifecycle: IMPLEMENTED
artifact_type: implementation_evidence
authority: implementation
task_id: TASK-M1-011
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-011 Implementation Evidence

## Objective

TASK-M1-011 adds a bounded dependency-aware local DAG runner that consumes
frozen M1 Work DAG readiness, routing decisions, active agent instances, and
the deterministic M1 executor seam.

It does not implement a production scheduler, daemon, retry engine, external
queue, provider/model invocation, API/UI route, or milestone closure.

## Starting Baseline

`c0d119a494b3660f83dc195ed171137170c37583`

TASK-M1-001 through TASK-M1-010 are integrated, validated, frozen, published,
and remotely CI-verified at this baseline.

## Prerequisite Proof And Ledger Reconciliation

The authoritative M1 DAG requires:

- TASK-M1-004;
- TASK-M1-007;
- TASK-M1-008;
- TASK-M1-010.

All four prerequisites were validated/frozen/integrated/published and remote
CI-verified before this task began. No additional M1-011 entry gate exists in
the task pack, implementation DAG, or M1 milestone artifacts.

The M1 status ledger still recorded TASK-M1-011 as `BLOCKED` after TASK-M1-010
publication. That row was stale reporting state. This implementation reconciles
the row as part of normal TASK-M1-011 evidence and records TASK-M1-011 as
`IMPLEMENTED, TESTED`.

## Implementation Architecture

The implementation adds `curios_runtime.m1_bounded_dag_runner` with:

- `M1DagRunnerRequest`;
- `M1DagRunnerResult`;
- `M1DagRunnerNodeResult`;
- `M1DagRunnerStatus`;
- `M1DagRunnerNodeStatus`;
- `M1DagRunnerReasonCode`;
- `M1DagRunnerError` and `M1DagRunnerErrorCode`;
- `BoundedM1DagRunner`.

The runner derives readiness with `derive_work_dag_state()`, selects READY
nodes in canonical DAG node order, limits the selected batch by
`max_concurrency`, validates routing/agent/executor identity before execution,
and invokes only the injected `M1Executor` for selected deterministic executor
routes.

The runner returns canonical executor `EventEnvelope` and `EvidenceReference`
values emitted by the executor seam. It does not persist events/evidence,
mutate WorkItem or WorkDag records, transition AgentInstance records, create
ExecutionRecord records, or complete DAG nodes.

## Routing / Execution Boundary

M1-010 routing decisions remain inert inputs. M1-011 may consume a supplied
`RoutingDecisionRecord` and invoke the deterministic executor only when the
decision selected a `DETERMINISTIC_EXECUTOR` candidate for the same ready work
and the selected candidate still supports the actual `WorkItem.work_type`.

`NO_ROUTE` and selected model-profile routes are bounded blocked node outcomes.
They do not trigger model/profile discovery, provider instantiation, model
generation, cloud lookup, fallback routing, or arbitrary callable execution.

## State And Restart Semantics

The runner does not own persisted WorkItem, WorkDag, AgentInstance, or
ExecutionRecord mutation. State transition truth remains recorded in the
canonical repositories owned by earlier or later tasks.

Restart/recovery is represented by recomputing from recorded canonical inputs:
the runner has no cache. A downstream node waits while dependencies are not
complete, becomes ready when recorded WorkItem truth says its dependencies are
complete, and becomes blocked when an upstream dependency is recorded FAILED or
CANCELLED.

TASK-M1-012 remains responsible for verification-gated work/DAG completion.
Executor self-report alone does not complete a DAG node.

## Authority Inventory

| Capability | M1-011 result |
| --- | --- |
| WorkItem read | AUTHORIZED as supplied canonical work input |
| WorkItem mutation | ABSENT |
| WorkDag read | AUTHORIZED as supplied canonical DAG input |
| WorkDag mutation | ABSENT |
| route decision read | AUTHORIZED as supplied routing decision input |
| route decision creation | ABSENT |
| agent read | AUTHORIZED as supplied AgentInstance input |
| agent lifecycle transition | ABSENT |
| executor invocation | AUTHORIZED only through injected `M1Executor` for deterministic executor routes |
| ExecutionRecord creation/mutation | ABSENT |
| Result creation | ABSENT except executor-owned result returned through `ExecutorOutcome` |
| event emission | AUTHORIZED only as executor-owned events returned in runner outcome |
| evidence creation | AUTHORIZED only as executor-owned evidence references returned in runner outcome |
| persistence/DB | ABSENT |
| scheduling | ABSENT beyond one bounded local runner pass |
| work claiming | ABSENT |
| provider invocation | ABSENT |
| model invocation | ABSENT |
| network | ABSENT |
| policy evaluation/grant | ABSENT |
| retry/cancellation | ABSENT |
| API/UI | ABSENT |
| prompt/memory | ABSENT |

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | TASK-M1-004, TASK-M1-007, TASK-M1-008, and TASK-M1-010 are satisfied; stale ledger row reconciled in this task. |
| Fixed maximum concurrency | PASS | READY nodes beyond `max_concurrency` return `DEFERRED` without executor invocation. |
| Readiness | PASS | Runner uses `derive_work_dag_state()` and executes only READY nodes. |
| Deterministic tie breaking | PASS | DAG node states are canonicalized by work ID; tests cover reversed inputs. |
| State transitions | PASS | Runner reports node outcomes without mutating canonical persisted state; recorded truth remains repository-owned. |
| Failure/cancellation propagation | PASS | FAILED/CANCELLED upstream WorkItems block downstream nodes through DAG readiness. |
| Events/evidence | PASS | Executor-owned canonical events/evidence refs are surfaced for executed nodes only. |
| Restart | PASS | A new runner object recomputes from supplied recorded WorkItem truth with no cache. |
| No provider/model authority | PASS | Model-profile routes remain blocked; no provider/model/network imports or calls exist. |
| Route/work compatibility | PASS | Selected deterministic executor routes must support the actual `WorkItem.work_type` before executor invocation. |
| Downstream boundary | PASS | Verification-gated completion, API/web presentation, and milestone closure remain absent. |

## Failure And Adversarial Coverage

Focused tests cover:

- no ready executable work;
- one ready node;
- multiple independent ready nodes;
- fixed concurrency deferral;
- dependent node waiting;
- FAILED/CANCELLED upstream dependency propagation;
- restart/reconstruction from updated recorded WorkItem truth;
- selected deterministic executor route;
- selected deterministic executor route whose supported work types include the
  actual `WorkItem.work_type`;
- selected deterministic executor route whose supported work types exclude the
  actual `WorkItem.work_type`;
- mixed READY nodes where a compatible route executes and an incompatible route
  is bounded without executor invocation;
- concurrency-budget behavior when an incompatible selected route is among the
  first READY nodes;
- `NO_ROUTE`;
- selected model-profile route without model invocation;
- missing routing decision;
- missing active agent;
- duplicate active agents;
- missing executor event/evidence IDs;
- executor failure outcome;
- no WorkItem/AgentInstance mutation;
- absence of persistence, provider/model, scheduler, daemon, network, API/UI,
  prompt, and memory authority.

## Dependency And Schema Changes

No package, third-party dependency, lockfile, pnpm manifest, schema, or
migration change is introduced.

## Correction 1

Independent validation found that a selected deterministic executor route was
treated as executable solely because its kind was `DETERMINISTIC_EXECUTOR`.
The runner did not verify that the route's `supported_work_types` included the
actual routed `WorkItem.work_type`, so an incompatible selected route could
reach `M1Executor`.

Correction 1 tightens the selected-route gate in
`BoundedM1DagRunner._run_ready_node()`:

- compatible selected deterministic route -> exactly one executor invocation
  for that READY node;
- incompatible selected deterministic route -> bounded
  `ROUTE_NOT_EXECUTABLE` node outcome;
- incompatible route -> no executor invocation, no executor event, and no
  executor evidence reference;
- no route recomputation, provider/model invocation, persistence, WorkItem
  mutation, WorkDag mutation, AgentInstance transition, ExecutionRecord
  mutation, retry, cancellation, or TASK-M1-012 behavior is introduced.

The validator regression file
`packages/python/curios_runtime/tests/test_task_m1_011_validation_regressions.py`
is preserved and expanded to cover compatible routes, incompatible routes,
mixed DAG outcomes, deterministic ordering, executor invocation counts, and
concurrency-budget behavior.

## Verification

Focused verification before evidence update:

- `uv sync --locked --all-groups --all-packages`: PASS;
- `ruff format`: PASS;
- `ruff check` on M1-011 implementation/test/security files: PASS;
- `pytest packages/python/curios_runtime/tests/test_task_m1_011_bounded_dag_runner.py -q`:
  PASS, 14 passed;
- `pytest tests/security/test_security_baseline.py tests/architecture/test_architecture_conformance.py -q`:
  PASS, 390 passed, 2 warnings.

Complete repository verification is recorded in the implementation result for
this task.

## Downstream

TASK-M1-011 remains awaiting independent validation/freeze. TASK-M1-012 and
TASK-M1-013 must not start until TASK-M1-011 is validated, frozen, integrated,
and published according to the authoritative DAG.
