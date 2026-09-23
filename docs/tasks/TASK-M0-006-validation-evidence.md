---
id: TASK-M0-006-VALIDATION-EVIDENCE
title: TASK-M0-006 Independent Revalidation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-006
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-006 Independent Revalidation Evidence

## Decision

TASK-M0-006 REVALIDATION: PASS

Validated candidate:

`728bb380b5bcb99af911008236b3e7272423266a`

Implementation commit:

`af1df707714f7054700d4256015c542dd8710ce3`

Corrective commit:

`728bb380b5bcb99af911008236b3e7272423266a`

## Correction Diff Audit

The correction diff from `af1df707714f7054700d4256015c542dd8710ce3` to
`728bb380b5bcb99af911008236b3e7272423266a` changes only:

- `packages/python/curios_runtime/src/curios_runtime/single_step_runtime.py`;
- `packages/python/curios_runtime/tests/test_single_step_runtime_service.py`;
- `docs/tasks/TASK-M0-006-evidence.md`.

No frozen TASK-M0-003 policy implementation, TASK-M0-004 event/evidence store,
TASK-M0-005 work repository/transition graph, canonical contract, persistence
schema, migration, provider executor, API, web surface, scheduler, router,
agent runtime, or retry framework changed.

## Consistency Invariant

Frozen M0 authority requires a single-step runtime that evaluates policy before
governed effects, records runtime truth through the frozen repository and
event/evidence boundaries, and does not claim distributed atomicity.

The accepted invariant is:

- before executor invocation, failures must not claim a governed executor
  effect occurred;
- after executor invocation, supported ordinary failures must not silently
  strand persisted work/execution truth as indefinite success-in-progress;
- after executor invocation, the runtime must preserve the most truthful bounded
  state legally representable by the frozen work/execution transition graphs;
- evidence must not be fabricated;
- events record persisted truth and do not override already persisted terminal
  work/execution state;
- lower-layer and executor-native failures remain behind bounded
  TASK-M0-006-owned result/error surfaces.

## Flow Review

Revalidation accepted the corrected flow:

1. read work through `M0WorkRepository`;
2. evaluate `MinimalM0PolicyEvaluator`;
3. append `policy.evaluated`;
4. block non-authorizing policy before work/execution start;
5. transition startable work through repository-owned `READY`/`RUNNING`;
6. create and start execution through `M0WorkRepository`;
7. append `execution.started`;
8. invoke the fakeable `SingleStepExecutor` exactly once;
9. record executor evidence through `EventEvidenceRuntimeStore`;
10. terminalize execution/work through legal repository transitions;
11. append terminal event where possible;
12. return a bounded result or raise a bounded runtime error.

## Failure Matrix

| Case | Work | Execution | Events | Evidence | Executor calls | Result/error | Coherent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Missing work | none | none | none | none | 0 | `NOT_FOUND` | YES |
| Invalid work state `RUNNING`/`WAITING`/terminal | unchanged | none | `policy.evaluated` | none | 0 | `ILLEGAL_STATE` | YES |
| Policy evaluator failure | `CREATED` | none | none | none | 0 | `POLICY_FAILURE` | YES |
| `UNKNOWN` policy | `CREATED` | none | `policy.evaluated` | none | 0 | `BLOCKED` result | YES |
| `DENY` policy | `CREATED` | none | `policy.evaluated` | none | 0 | `BLOCKED` result | YES |
| Policy event store failure | `CREATED` | none | none | none | 0 | `RUNTIME_STORE_FAILURE` | YES |
| Work transition failure | `CREATED` | none | `policy.evaluated` | none | 0 | bounded repository error | YES |
| Execution creation failure | `RUNNING` | none | `policy.evaluated` | none | 0 | bounded repository error | YES |
| Execution start transition failure | `RUNNING` | `CREATED` | `policy.evaluated` | none | 0 | bounded repository error | YES |
| `execution.started` event failure | `RUNNING` | `RUNNING` | `policy.evaluated` | none | 0 | `RUNTIME_STORE_FAILURE` | YES |
| Executor raises | `FAILED` | `FAILED` | policy, started, failed | none | 1 | `EXECUTOR_FAILURE` | YES |
| Executor returns failure | `FAILED` | `FAILED` | policy, started, failed | none | 1 | `FAILED` result | YES |
| Evidence append failure after success | `FAILED` | `SUCCEEDED` | policy, started, failed | none | 1 | `RUNTIME_STORE_FAILURE` with `executor_effect=succeeded` | YES |
| Success execution terminal transition failure | `FAILED` | `FAILED` | policy, started, failed | none | 1 | bounded repository error | YES |
| Success work terminal transition failure | `FAILED` | `SUCCEEDED` | policy, started, failed | none | 1 | bounded repository error | YES |
| Completion event failure | `COMPLETED` | `SUCCEEDED` | policy, started | none | 1 | `COMPLETED` result with `recording_errors` | YES |
| Failure execution transition failure | `FAILED` | `RUNNING` | policy, started | none | 1 | `EXECUTOR_FAILURE` with cleanup detail | YES |
| Failure work transition failure | `RUNNING` | `FAILED` | policy, started | none | 1 | `EXECUTOR_FAILURE` with cleanup detail | YES |
| Failure event failure | `FAILED` | `FAILED` | policy, started | none | 1 | `FAILED` result with `recording_errors` | YES |

The pre-executor `RUNNING` states are accepted as bounded startup failure
truth because the governed executor effect has not occurred. The correction
does not introduce generalized recovery or retry semantics.

## Previous Blocking Defects

The previous validation blockers are resolved:

- evidence persistence failure after executor success no longer leaves both
  records `RUNNING`;
- success terminal transition failures no longer silently split success truth
  into `execution=SUCCEEDED` and `work=RUNNING`;
- terminal event failures no longer override coherent terminal states;
- executor failure cleanup failures remain bounded and preserve persisted truth;
- the expanded tests cover persisted truth across the post-executor failure
  matrix.

## Recording Errors Review

`recording_errors` lives on `SingleStepRuntimeResult` as
`tuple[SingleStepRuntimeError, ...]`.

It is a TASK-M0-006 service-result field used only when terminal work/execution
truth has already been persisted but terminal event recording failed. The values
are bounded Curios-owned runtime errors with stable code, message, operation,
retryable flag, and bounded detail. They do not contain native exception
objects, SQLAlchemy/psycopg objects, `RepositoryError`, `RuntimeStoreError`,
`PersistenceError`, raw provider payloads, SQL, credentials, or tracebacks.

Revalidation accepts this as necessary bounded recording status for truthful M0
finalization. It is not a generalized warning framework and does not introduce
new canonical state vocabulary.

## State Graph Integrity

Revalidation confirmed no new work states, execution states, transition tables,
or terminal rollback transitions. Runtime transitions continue to go through
`M0WorkRepository`.

The correction uses only legal frozen states:

- Work: `CREATED`, `READY`, `RUNNING`, `WAITING`, `COMPLETED`, `FAILED`,
  `CANCELLED`;
- Execution: `CREATED`, `RUNNING`, `WAITING`, `SUCCEEDED`, `FAILED`,
  `CANCELLED`.

## Error Boundary

Representative paths were inspected for bounded error behavior. Public runtime
errors suppress native causes/contexts with `raise ... from None`. No
`RepositoryError`, `RuntimeStoreError`, `PersistenceError`, SQLAlchemy/psycopg
exception, executor-native exception object, raw persisted payload, SQL, URL,
credential, or provider-native detail crosses the TASK-M0-006 boundary.

## Separation And Topology

Revalidation confirmed:

- policy semantics remain in `curios_policy`;
- state-transition semantics remain in `M0WorkRepository`;
- event/evidence persistence semantics remain in `EventEvidenceRuntimeStore`;
- `SingleStepExecutor` remains a fakeable seam;
- no provider-inventory executor or TASK-M0-007 behavior appears;
- exact runtime source-file topology remains enforced by security tests;
- representative scheduler, DAG, retry, provider executor, model router, and
  agent runtime modules remain blocked.

No external dependency was added by the correction.

## Test Quality

The expanded TASK-M0-006 tests inspect persisted work state, execution state,
events, evidence, executor call count, and bounded result/error shape. The
failure injection store operates at the actual persistence insert/replace seams
used by the frozen repository and runtime store. Tests do not merely assert
error codes; they expose intermediate and final runtime truth.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS: 11 `pyproject.toml` files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS. |
| Ruff | PASS. |
| Ruff format | PASS: 175 files already formatted. |
| Authoritative mypy | PASS: `uv run mypy apps/api/src packages/python/*/src`; 52 source files. |
| TASK-M0-006 tests | PASS: 25 passed. |
| Policy tests | PASS: 20 passed. |
| Persistence tests | PASS: 21 passed. |
| Event/evidence and work repository tests | PASS: 56 passed. |
| Contracts/core tests | PASS: 123 passed. |
| Provider/API package tests | PASS: 38 passed. |
| Contract/schema tests | PASS: 15 passed. |
| Architecture/security tests | PASS: 56 passed. |
| API integration | PASS: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration | PASS: 1 passed serially. |
| PostgreSQL runtime event/evidence integration | PASS: 1 passed serially. |
| PostgreSQL runtime work repository integration | PASS: 1 passed serially. |
| PostgreSQL persistence integration | PASS: 2 passed serially. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| Full pytest | PASS: 369 passed, 2 known dependency warnings. |
| `pnpm install --frozen-lockfile` | PASS. |
| `pnpm check` | PASS. |
| Web tests | PASS: 1 test file, 2 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings.

PostgreSQL-dependent checks were run serially. The named PostgreSQL volume was
preserved; `docker compose down -v` was not used.

## Lifecycle And Downstream Readiness

TASK-M0-006 is `VALIDATED, FROZEN`.

The frozen DAG requires TASK-M0-006 to be validated, frozen, and integrated
before TASK-M0-007 can become ready. Therefore TASK-M0-007 remains `BLOCKED` on
this task branch. After this validation/freeze commit is integrated into
`main`, TASK-M0-007 may become `READY`; it is not implemented by this
validation.
