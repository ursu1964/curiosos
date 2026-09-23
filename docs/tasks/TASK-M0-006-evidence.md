---
id: TASK-M0-006-EVIDENCE
title: TASK-M0-006 Single-Step Work Runtime Service Evidence
lifecycle: TESTED
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
- M0 ledger transition to `IMPLEMENTED, TESTED`

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

- Missing work raises `SingleStepRuntimeError(NOT_FOUND)`.
- Non-authorizing policy returns `SingleStepRuntimeResult(BLOCKED)` and does not
  invoke the executor.
- Unsupported work states raise `SingleStepRuntimeError(ILLEGAL_STATE)`.
- Repository errors translate to bounded runtime-service errors.
- Runtime-store failures translate to bounded runtime-service errors.
- Executor exceptions mark work/execution failed where possible and raise
  `SingleStepRuntimeError(EXECUTOR_FAILURE)` without native exception leakage.
- Executor `Result.failure(...)` marks work/execution failed and returns a
  bounded failed runtime result.

TASK-M0-006 does not claim distributed transactions across repository and
event/evidence boundaries.

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

- TOML validation: `passed`
- `uv lock --check`: `passed`
- `uv sync --locked --all-groups --all-packages`: `passed`
- Docker Compose config: `passed`
- Ruff check: `passed`
- Ruff format check: `passed`
- mypy source scope: `52 source files`, `passed`
- policy tests: `20 passed`
- runtime unit tests including TASK-M0-006: `64 passed`
- contracts/core tests: `123 passed`
- provider/API package tests: `38 passed`
- contract/schema/architecture/security/acceptance tests: `77 passed`,
  `2` known dependency warnings
- PostgreSQL-backed persistence/provider/runtime integration tests: `24 passed`
- full pytest: `352 passed`, `2` known dependency warnings
- frontend frozen install/check/test/typecheck/build: `passed`; web test
  `2 passed`
- `git diff --check`: `passed`
- `pytest packages/python/curios_runtime/tests/test_single_step_runtime_service.py packages/python/curios_runtime/tests/test_event_evidence_store.py tests/security tests/architecture -q`:
  `73 passed`

The known warnings are the pre-existing Starlette/TestClient `httpx` warning
and anyio `BlockingPortal` alias deprecation warning.

## Lifecycle

TASK-M0-006 is `IMPLEMENTED, TESTED`.

It is not `VALIDATED` or `FROZEN`. Independent validation must decide whether
TASK-M0-006 can freeze and whether TASK-M0-007 may become ready.
