---
id: TASK-M1-008-VALIDATION-EVIDENCE
title: TASK-M1-008 Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-008
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-008 Validation Evidence

## Scope

Validated implementation:
`40749c811d70db4b1859bf8315ab570f6e98612c`

Published baseline:
`cba5cbf0ceb34bb8e45cbf1e140a9026b54456a8`

TASK-M1-008 adds the Curios-owned executor seam and deterministic executors for
bounded M1 tasks. Validation reconstructed the contract from the frozen M1 task
pack, implementation DAG, M1 status ledger, M1-003 decomposition, M1-004 work
DAG readiness, M1-005 capability resolution, M1-007 lifecycle/events, canonical
`Result`, `EventEnvelope`, and `EvidenceReference` contracts, plus architecture
and security constraints.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | M1-003, M1-004, M1-005, and M1-007 are validated/frozen and integrated in the published baseline. |
| Authorized ownership | PASS | M1-008 authorizes M1 runtime modules, tests, and evidence. `curios_runtime.executor_seam` is the correct owner; contracts/core remain uncontaminated. |
| Fixed work-type boundary | PASS | The supported work types exactly match the frozen M1-003 decomposition outputs: `collect_recorded_context`, `compose_recorded_summary`, `verify_recorded_summary`, `inspect_current_state`, `apply_bounded_change`, and `verify_bounded_change`. Near-miss valid tokens fail boundedly. |
| Request contract | PASS | `ExecutorRequest` requires canonical `WorkItem`, `WorkDagNodeReadiness`, `CapabilityResolution`, optional `AgentInstance`, canonical producer reference, caller-supplied event/evidence IDs, timestamp, and observability context. Cross-domain mismatches are rejected. |
| Readiness gate | PASS | Only `WorkDagNodeReadiness.READY` can complete; `WAITING`, `BLOCKED`, and `TERMINAL` return bounded failure without evidence. |
| Capability gate | PASS | Only `MATCHED`/`EXACT_MATCH` capability resolutions with matching work requirements pass. Both missing reasons and both ambiguous reasons fail boundedly; ambiguity never selects an agent and missing never falls back. |
| Agent gate | PASS | Only an `ACTIVE` `AgentInstance` bound to the requested work and selected agent definition passes. All other lifecycle states fail boundedly. |
| Result semantics | PASS | Successful outcomes use canonical `Result.success`; failures use canonical `Result.failure` with bounded `ContractError` and no native exception leakage. |
| Event semantics | PASS | Outcomes return canonical `EventEnvelope` with event type `executor.deterministic.completed`, canonical subject/producer references, bounded payload, and observability context. It does not claim persisted lifecycle, WorkItem, ExecutionRecord, provider, or scheduler side effects. |
| Evidence semantics | PASS | Successful outcomes include one canonical in-memory `EvidenceReference` related to the `WorkItem`; failures include no evidence. No durable evidence persistence is implied. |
| Determinism/idempotency | PASS | Repeated identical requests produce identical semantic outputs because IDs, timestamps, and observability context are caller-supplied. No global/cache mutation is present. |
| Side-effect authority | PASS | Source and behavior expose no persistence, database, network, provider/model invocation, prompt/memory, WorkItem/DAG mutation, agent transition, ExecutionRecord mutation, scheduling, retry, cancellation, API, UI, or policy grant/evaluation authority. |
| Dependency scope | PASS | `curios_runtime` gains only local workspace dependencies on `curios-capability` and `curios-dag`; lockfile drift is limited to those local relationships and introduces no third-party dependency changes. |
| Guard changes | PASS | Security changes are additive and bounded to `executor_seam.py`, exact public declarations, M1-008 evidence, and runtime test coverage. Existing M1-001 through M1-007 restrictions remain active. |

## Delta Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_runtime/src/curios_runtime/executor_seam.py` | REQUIRED | Owns the authorized M1 executor seam and deterministic executor behavior. |
| `packages/python/curios_runtime/src/curios_runtime/__init__.py` | JUSTIFIED SUPPORT | Exports the authorized seam symbols from the runtime package. |
| `packages/python/curios_runtime/pyproject.toml` | REQUIRED | Adds local workspace dependencies on frozen capability and DAG packages consumed by the request contract. |
| `uv.lock` | JUSTIFIED SUPPORT | Records only local workspace dependency relationships; no third-party drift. |
| `packages/python/curios_runtime/tests/test_task_m1_008_executor_seam.py` | REQUIRED | Focused implementation coverage for M1-008 behavior. |
| `packages/python/curios_runtime/tests/test_task_m1_008_validation_regressions.py` | REQUIRED VALIDATION SUPPORT | Adds independent boundary/adversarial coverage for exact work types, readiness, capability, agent lifecycle, cross-domain mismatches, determinism, and side-effect absence. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Adds bounded authorization for the exact M1-008 runtime/evidence surfaces without broad runtime exemptions. |
| `docs/tasks/TASK-M1-008-evidence.md` | REQUIRED | Implementation evidence and stale-readiness reconciliation. |
| `docs/tasks/TASK-M1-008-validation-evidence.md` | REQUIRED | Independent validation/freeze evidence. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Advances TASK-M1-008 from `IMPLEMENTED, TESTED` to `VALIDATED, FROZEN`. |

## Adversarial Coverage

Validator regressions cover:

- every frozen supported work type derived from M1-003 decomposition;
- near-miss and unrelated valid work-type tokens;
- every M1-004 readiness value;
- both M1-005 missing reasons and both ambiguous reasons;
- capability resolution order/shape mismatch;
- every M1-007 `AgentInstanceState`;
- agent/work mismatch;
- capability-selected agent definition mismatch;
- terminal DAG readiness with an active agent;
- ambiguous capability with an apparently usable active agent;
- repeated identical request serialization stability;
- input immutability/no hidden mutation;
- static absence of persistence, provider, network, callback, and import authority.

## Authority Audit

M1-008 may read caller-supplied canonical work, derived DAG readiness,
capability-resolution records, and selected agent-instance facts. It may return
an inert deterministic result, event envelope, and evidence reference.

M1-008 does not persist or mutate any record and does not schedule, claim,
retry, cancel, route, invoke providers, call models, access the network,
evaluate/grant policy, create prompts, access memory, expose API/UI behavior, or
implement M1-009, M1-010, or M1-011.

## Verification

Pre-validation-record verification:

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS |
| `uv sync --locked --all-groups --all-packages` | PASS |
| `pnpm install --frozen-lockfile` | PASS |
| Docker Compose config | PASS |
| `ruff format --check .` | PASS: 248 files formatted. |
| `ruff check .` | PASS |
| `mypy apps/api/src packages/python/*/src` | PASS: 65 source files. |
| `pnpm check` | PASS |
| Web tests | PASS: 6 tests. |
| Web typecheck | PASS |
| Web build | PASS |
| Contract/schema tests | PASS: 16 tests. |
| Architecture tests | PASS: 36 tests. |
| Security tests | PASS: 355 tests with 2 known FastAPI/Starlette deprecation warnings. |
| M1-001 through M1-008 regression slice | PASS: 240 tests. |
| Package/API/provider/runtime/persistence non-integration slice | PASS: 376 tests, 9 deselected. |
| Docker-backed serial integrations | PASS: API 6, PostgreSQL provider 1, persistence 2, event/evidence 1, work repository 1, Work DAG repository 1, agent repository 1, agent lifecycle repository 1, M0 vertical slice 2. |
| Acceptance tests | PASS: 8 tests. |
| Full pytest | PASS: 880 tests with 2 known FastAPI/Starlette deprecation warnings. |
| `git diff --check` and `git diff --cached --check` | PASS |

Known warnings:

- `uv` reported the inherited `VIRTUAL_ENV=/home/user/projects/curiosos/.venv`
  does not match the task worktree `.venv`; `uv` ignored it.
- FastAPI/Starlette `TestClient` deprecation warnings remain known.

No Docker/PostgreSQL transient failure occurred during this validation run.

## Decision

TASK-M1-008 is `VALIDATED, FROZEN`.

TASK-M1-010 remains blocked until TASK-M1-008 and TASK-M1-009 are both
validated/frozen and integrated. TASK-M1-011 remains blocked on TASK-M1-008,
TASK-M1-010, and its other documented prerequisites. TASK-M1-009 remains
independently ready and was not started.
