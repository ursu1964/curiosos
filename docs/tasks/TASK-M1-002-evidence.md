---
id: TASK-M1-002-EVIDENCE
title: TASK-M1-002 Cognitive Intent and Problem Contracts Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-002
milestone_id: M1
date: 2026-09-25
---

# TASK-M1-002 Evidence

## Objective

Add the minimal canonical cognitive records required for M1:
`Intent`, `Problem`, `Assumption`, `Decision`, and `Plan`.

TASK-M1-002 does not implement deterministic decomposition, work DAG runtime or
persistence, capability resolution, agent persistence, executor seams,
model/profile discovery, routing records, verification loops, API routes, web
UI, integration tests, acceptance tests, CI, or M2+ behavior.

## Starting Baseline

`2debf19e5dfd5411e57fa8699ba659a9520b0fc6`

TASK-M1-001 is `VALIDATED, FROZEN`, satisfying the TASK-M1-002 prerequisite.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Add minimal cognitive records | PASS | `Intent`, `Problem`, `Assumption`, `Decision`, and `Plan` are defined in `curios_contracts.cognitive`. |
| Deterministic serialization | PASS | Each record has explicit `to_json_compatible` and `from_json_compatible` methods; contract/schema tests round-trip JSON-compatible payloads with stable snake_case fields. |
| Use `ObjectReference` | PASS | Cognitive IDs are supported by `ObjectReference`; cross-record and work links use `ObjectReference` only. |
| Do not duplicate `WorkItem` | PASS | `Plan` exposes `work_refs` and intentionally omits `work_id`, `state`, `dependencies`, `required_capabilities`, inputs, outputs, policy, authority, principal, and evidence requirement fields. |
| Preserve frozen contracts | PASS | Existing work, execution, capability, agent, security, event, evidence, and result contracts remain unchanged except for adding cognitive ID/reference support. |
| Preserve architecture/security guards | PASS | M1-001 guard inventories were updated as an explicit TASK-M1-002 authority transition while runtime/API/web/integration/acceptance/deferred M1 surfaces remain blocked. |
| No TypeScript contract expansion | PASS | TypeScript contracts were not required by TASK-M1-002 because no web/API TypeScript consumer exists yet. |
| No dependency changes | PASS | No manifest or lockfile changes were made. |

## Files Changed

- `docs/contracts/TASK-M1-002-cognitive-contracts.md`
- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-002-evidence.md`
- `packages/python/curios_contracts/src/curios_contracts/__init__.py`
- `packages/python/curios_contracts/src/curios_contracts/cognitive.py`
- `packages/python/curios_contracts/src/curios_contracts/identifiers.py`
- `packages/python/curios_contracts/src/curios_contracts/references.py`
- `packages/python/curios_contracts/tests/test_task_m1_002_cognitive_contracts.py`
- `tests/contract/test_cross_contract_boundaries.py`
- `tests/schema/test_contract_serialization.py`
- `tests/security/test_security_baseline.py`

## Contract Shape

TASK-M1-002 adds:

- `IntentId`, `ProblemId`, `AssumptionId`, `DecisionId`, and `PlanId`;
- `ReferenceKind.INTENT`, `PROBLEM`, `ASSUMPTION`, `DECISION`, and `PLAN`;
- immutable canonical records for `Intent`, `Problem`, `Assumption`,
  `Decision`, and `Plan`;
- package-level exports for the new records and typed IDs.

The record fields are bounded text, typed IDs, UTC timestamps, and
`ObjectReference` links. There is no persistence, runtime execution, route,
view, scheduler, prompt, model, or provider behavior.

## Verification

| Check | Result |
| --- | --- |
| TASK-M1-002 focused contract/schema tests | PASS: 23 passed. |
| Identifier/reference regression tests | PASS: 14 passed. |
| Security tests | PASS: 357 passed, 2 known dependency warnings. |
| Architecture tests | PASS: 33 passed. |
| Dependency lock check | PASS: `uv lock --check` resolved 47 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 44 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 212 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python type checking | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 54 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Frontend tests/build | PASS: web tests passed 6 tests; typecheck and build passed. |
| API/core/provider/unit suites | PASS: 54 passed, 2 known dependency warnings. |
| Persistence/policy/runtime non-integration suites | PASS: 128 passed, 4 deselected. |
| Docker-backed API integration | PASS: 6 passed, 2 known dependency warnings. |
| Docker-backed Postgres provider integration | PASS: 1 passed. |
| Docker-backed persistence/runtime integration | PASS: 4 passed when run serially. |
| M0 vertical slice integration | PASS: 2 passed, 2 known dependency warnings. |
| Acceptance tests | PASS: 8 passed, 2 known dependency warnings. |
| Full pytest suite | PASS: 730 passed, 2 known dependency warnings. |

## Lifecycle State

TASK-M1-002 is `IMPLEMENTED, TESTED`.

It is not `VALIDATED` or `FROZEN`; independent validation must make that
decision. TASK-M1-003 and TASK-M1-004 remain `BLOCKED` until TASK-M1-002 is
validated, frozen, and integrated.
