---
id: TASK-M0-006-EVIDENCE
title: TASK-M0-006 Single-Step Work Runtime Service Evidence
lifecycle: VALIDATED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-006
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-006 Evidence

## Objective

Implement the minimal single-step M0 work runtime service that coordinates
already frozen policy, work repository, and event/evidence store boundaries.

## Starting Baseline

`6d512af4fdfe4366630f6cf88e8c71381ac539ed`

## Implemented Surface

- `packages/python/curios_runtime/src/curios_runtime/single_step_runtime.py`
- `packages/python/curios_runtime/tests/test_single_step_runtime_service.py`
- package export and dependency metadata for `curios-runtime`
- narrow security/architecture guardrail updates authorizing only the
  TASK-M0-006 runtime-service module
- M0 ledger transition to `IMPLEMENTED, TESTED`, followed by independent
  revalidation to `VALIDATED, FROZEN`

No production contract, persistence schema, policy rule, work transition graph,
provider implementation, API route, web surface, scheduler, queue, retry engine,
agent runtime, model router, or TASK-M0-007 executor implementation was added.

## Runtime Service API

TASK-M0-006 adds Curios-owned runtime-service types:

- `SingleStepRuntimeService`
- `SingleStepRuntimeRequest`
- `SingleStepRuntimeResult`
- `SingleStepRuntimeStatus`
- `SingleStepRuntimeError`
- `SingleStepRuntimeErrorCode`
- `SingleStepExecutionRequest`
- `SingleStepExecutionOutcome`
- `SingleStepExecutor`

`SingleStepExecutor` is a fakeable seam. TASK-M0-006 does not provide a
provider-inventory executor; TASK-M0-007 owns that concrete capability.

## Single-Step Flow

The service coordinates one work item:

1. read the target `WorkItem` through `M0WorkRepository`;
2. evaluate frozen minimal policy using `MinimalM0PolicyEvaluator`;
3. record a canonical `policy.evaluated` event;
4. block safely when policy returns `DENY` or `UNKNOWN`;
5. transition authorized `CREATED`/`READY` work through repository-owned
   `READY`/`RUNNING` states;
6. create and start one `ExecutionRecord` through the repository boundary;
7. call the fakeable executor seam;
8. record executor evidence references through `EventEvidenceRuntimeStore`;
9. transition successful execution/work to `SUCCEEDED`/`COMPLETED`, or
   executor failure to `FAILED`;
10. record canonical execution/evidence events.

The service does not manipulate persistence rows directly and does not duplicate
policy or state-transition tables.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Coordinates one work item only | PASS | Unit tests exercise one deterministic `WorkItem` by ID. |
| Uses frozen policy evaluator | PASS | Service constructs `M0PolicyEvaluationRequest` and consumes `PolicyDecision` without rewriting outcomes. |
| `UNKNOWN`/denial fail closed | PASS | Tests prove no executor invocation and no work transition when policy is non-authorizing. |
| Uses frozen work repository | PASS | Work and execution transitions occur only through `M0WorkRepository`. |
| Uses frozen event/evidence store | PASS | Events and executor evidence are appended through `EventEvidenceRuntimeStore`. |
| Executor remains a seam | PASS | Tests use deterministic fakes; no provider inventory collection or live provider call exists. |
| Bounded failure semantics | PASS | Missing work, illegal state, repository/store failures, executor exceptions, and executor failure results are covered. |
| Lower-layer exceptions do not leak | PASS | Runtime errors are TASK-M0-006-owned and suppress lower exception cause/context. |
| Topology remains exact | PASS | Security tests authorize `single_step_runtime.py` while continuing to reject scheduler/executor/router/agent modules. |
| Architecture remains inward | PASS | Contracts/core do not depend on runtime; runtime consumes only authorized workspace packages. |
| Downstream scope blocked | PASS | TASK-M0-007 through TASK-M0-014 remain blocked in the M0 ledger. |

## Failure and Partial-Failure Semantics

Independent TASK-M0-006 validation failed after finding post-executor partial
failures that could leave persisted truth contradictory or indefinitely
`RUNNING`. Confirmed failures included evidence append failure after executor
success, execution success persisted before work completion failed, terminal
event append failure masking coherent terminal state, and cleanup operations
masking executor failures.

The corrected M0 consistency invariant is:

- before executor invocation, failures must not claim a governed effect
  occurred;
- after executor invocation, the runtime must persist the most truthful bounded
  terminal state legal under the frozen work/execution transition graphs;
- terminal events and evidence events are records of persisted truth, not the
  authority over already persisted terminal state;
- lower repository/store/native executor exceptions never cross the runtime
  boundary unwrapped.

The deterministic partial-failure protocol is:

| Case | Corrected behavior |
| --- | --- |
| Pre-executor failure | Fail fast with bounded runtime error; executor is not called; no execution/effect truth is fabricated. |
| Executor raises | Mark work `FAILED`, then execution `FAILED` where legal; record `execution.failed` where possible; raise `EXECUTOR_FAILURE` without native exception leakage. |
| Executor returns failure | Mark work `FAILED`, then execution `FAILED` where legal; record `execution.failed` where possible; return failed runtime result when finalization succeeds. |
| Success evidence append/event failure | Preserve executor-effect truth by terminalizing execution as `SUCCEEDED` where possible; mark work `FAILED`; raise bounded runtime-store error with `executor_effect=succeeded`. |
| Success execution terminal transition failure | Do not retry success during cleanup; mark execution `FAILED` and work `FAILED` where legal; raise bounded repository error. |
| Success work terminal transition failure | Preserve already persisted execution `SUCCEEDED`; mark work `FAILED` where legal; raise bounded repository error rather than returning `COMPLETED`. |
| Terminal event failure | Do not revert terminal state; return terminal result with `recording_errors` containing the bounded event-store failure and omit the missing event from returned events. |
| Cleanup operation failure | Preserve whatever persisted truth succeeded, attach bounded cleanup details to the runtime error, and never leak `RepositoryError`, `RuntimeStoreError`, or executor-native exceptions. |

TASK-M0-006 still does not claim distributed transactions, retries, a scheduler,
or generalized recovery machinery across repository and event/evidence
boundaries.

## Corrected Failure Matrix

The adversarial runtime-service tests now assert final persisted work state,
execution state, events, evidence, executor call count, result/error, and
exception boundary behavior for:

| Failure point | Persisted truth/result |
| --- | --- |
| Policy evaluator failure | Work remains `CREATED`; no execution, events, evidence, or executor call; bounded `POLICY_FAILURE`. |
| Policy event store failure | Work remains `CREATED`; no execution/evidence/executor call; bounded `RUNTIME_STORE_FAILURE`. |
| Work start transition failure | Work remains `CREATED`; no execution/evidence/executor call; `policy.evaluated` only; bounded repository error. |
| Execution creation failure | Work is `RUNNING`; no execution/evidence/executor call; `policy.evaluated` only; bounded repository error. |
| Execution start transition failure | Work is `RUNNING`; execution remains `CREATED`; no executor call; bounded repository error. |
| `execution.started` event failure | Work/execution are `RUNNING`; executor is not called; bounded runtime-store error. |
| Executor raises | Work `FAILED`, execution `FAILED`; `execution.failed` recorded where possible; bounded `EXECUTOR_FAILURE`. |
| Executor returns failure | Work `FAILED`, execution `FAILED`; failed runtime result; no native/lower error leakage. |
| Evidence append failure after executor success | Work `FAILED`, execution `SUCCEEDED`; no evidence fabricated; bounded runtime-store error with executor success detail. |
| Success work terminal transition failure | Work `FAILED`, execution `SUCCEEDED`; bounded repository error; no false completed result. |
| Success execution terminal transition failure | Work `FAILED`, execution `FAILED`; bounded repository error; no stranded success truth. |
| Completion event append failure | Work `COMPLETED`, execution `SUCCEEDED`; completed result includes bounded `recording_errors`; no event authority over state. |
| Failure work transition failure | Work remains `RUNNING`, execution `FAILED`; bounded `EXECUTOR_FAILURE` with cleanup detail. |
| Failure execution transition failure | Work `FAILED`, execution remains `RUNNING`; bounded `EXECUTOR_FAILURE` with cleanup detail. |
| Failure event append failure | Work `FAILED`, execution `FAILED`; failed result includes bounded `recording_errors`. |

The success regression remains `work=COMPLETED`, `execution=SUCCEEDED`,
policy/start/evidence/completion events, persisted executor evidence, and
`COMPLETED` result.

The non-authorizing regression remains: `UNKNOWN`/`DENY` records
`policy.evaluated`, returns `BLOCKED`, leaves work unchanged, creates no
execution, and never invokes the executor.

Repeated invocation remains blocked for `RUNNING`, `WAITING`, and terminal work
states; these states do not cause duplicate executor invocation.

## Topology and Scope

The security topology now distinguishes the authorized runtime package root
from its exact current-stage source files. The current authorized runtime source
files are:

- `__init__.py`
- `event_evidence_store.py`
- `work_repository.py`
- `single_step_runtime.py`
- `py.typed`

Representative future surfaces such as scheduler, provider executor, model
router, and agent runtime modules remain rejected by security tests.

## Verification

Implementation verification:

- TOML validation: `11` manifests parsed, `passed`
- `uv lock --check`: `passed`
- `uv sync --locked --all-groups --all-packages`: `passed`
- Docker Compose config: `passed`
- Ruff check: `passed`
- Ruff format check: `175` files already formatted, `passed`
- mypy source scope: `52 source files`, `passed`
- TASK-M0-006 service tests: `25 passed`
- policy tests: `20 passed`
- event/evidence runtime-store unit tests: `9 passed`
- work repository unit tests: `47 passed`
- persistence tests: `21 passed`
- runtime package tests: `83 passed`
- contracts/core tests: `123 passed`
- provider/API package tests: `38 passed`
- contract/schema tests: `15 passed`
- architecture tests: `16 passed`
- security tests: `40 passed`
- API integration tests: `6 passed`, `2` known dependency warnings
- PostgreSQL-backed provider integration test: `1 passed`
- PostgreSQL-backed runtime event/evidence integration test: `1 passed`
- PostgreSQL-backed runtime work repository integration test: `1 passed`
- PostgreSQL-backed persistence integration tests: `2 passed`
- BOOT acceptance tests: `6 passed`, `2` known dependency warnings
- full pytest: `369 passed`, `2` known dependency warnings
- frontend frozen install/check/test/typecheck/build: `passed`; web test
  `2 passed`
- `git diff --check`: `passed`
- focused touched-file Ruff check/format and source mypy checks: `passed`

The known warnings are the pre-existing Starlette/TestClient `httpx` warning
and anyio `BlockingPortal` alias deprecation warning.

## Lifecycle

TASK-M0-006 was implemented and tested by the implementation agent, corrected
after independent validation found post-executor partial-failure consistency
defects, then independently revalidated at candidate
`728bb380b5bcb99af911008236b3e7272423266a`.

TASK-M0-006 is `VALIDATED, FROZEN`.

TASK-M0-007 remains `BLOCKED` until this validation/freeze commit is integrated
into `main`; after integration, the frozen DAG permits TASK-M0-007 to become
`READY`.
