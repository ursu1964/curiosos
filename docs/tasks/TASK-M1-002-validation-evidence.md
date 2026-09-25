---
id: TASK-M1-002-VALIDATION-EVIDENCE
title: TASK-M1-002 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-002
milestone_id: M1
date: 2026-09-25
---

# TASK-M1-002 Independent Validation Evidence

## Decision

TASK-M1-002 VALIDATION: PASS

Validated implementation:

`1c46cfc8e229cb2d62058ef03fc3964f2ff8c27e`

Validated upstream baseline:

`2debf19e5dfd5411e57fa8699ba659a9520b0fc6`

## Reconstructed Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite authority | PASS | TASK-M1-001 is validated/frozen at `2debf19e5dfd5411e57fa8699ba659a9520b0fc6`; M1-002 was READY and owned only cognitive contract surfaces. |
| Scope | PASS | The implementation diff is limited to canonical contract code, ID/reference support, contract/schema/security tests, docs, evidence, and ledger updates. |
| Required records | PASS | `Intent`, `Problem`, `Assumption`, `Decision`, and `Plan` are the only new production classes in `curios_contracts.cognitive`. |
| Typed identifiers | PASS | `IntentId`, `ProblemId`, `AssumptionId`, `DecisionId`, and `PlanId` are concrete `CuriosId` types with stable prefixes `int`, `prb`, `asm`, `dcn`, and `pln`. |
| Reference semantics | PASS | New IDs map to `ReferenceKind.INTENT`, `PROBLEM`, `ASSUMPTION`, `DECISION`, and `PLAN`; cross-record links use `ObjectReference`. |
| Single generic reference abstraction | PASS | Repository AST inventory found exactly one generic `ObjectReference` class, in `curios_contracts.references`; no competing `Reference` or `GenericReference` class was introduced. |
| Serialization | PASS | Each cognitive record has explicit `to_json_compatible` and `from_json_compatible`; round trips preserve equality and stable JSON-compatible payloads. |
| Construction invariants | PASS | Malformed IDs, cross-kind `ObjectReference` pairs, and wrong record reference kinds reject during construction or deserialization. |
| Immutable defaults | PASS | Records are frozen dataclasses with tuple defaults; adversarial mutable caller-provided lists normalize to tuples and do not retain caller mutability. |
| Work boundary | PASS | `Plan` references work with `work_refs: tuple[ObjectReference, ...]` constrained to kind `work` and does not duplicate `WorkItem` identity, state, dependencies, capabilities, inputs, outputs, policy, authority, principal, or evidence requirement fields. |
| No runtime authority | PASS | No persistence, database, ORM, repository, runtime, provider, executor, scheduler, graph runtime, decomposition, prompt, memory, API, or frontend implementation was added. |
| Architecture/security guards | PASS | M1 surface and canonical authority inventories were transitioned narrowly for TASK-M1-002 and continue to block deferred M1 and M2+ surfaces. |
| Dependencies | PASS | No Python, frontend, manifest, or lockfile dependency changes were made. |

## Contract Review

### Intent

`Intent` is the submitted user/system intent record. It owns `intent_id`,
`objective`, `submitted_at`, optional `source_ref`, and `context_refs`.
Validation enforces `IntentId`, bounded objective text, UTC timestamp
normalization, and `ObjectReference` context/source references. It has no work
state, execution state, prompt, model message, planner, persistence, API, or UI
authority.

### Problem

`Problem` is a bounded problem statement derived from an intent. It owns
`problem_id`, `intent_ref`, `objective`, `statement`, `created_at`, and
`context_refs`. Validation enforces `ProblemId`, `intent_ref` kind `intent`,
bounded text, UTC timestamp normalization, and `ObjectReference` context
references. It does not decompose work or duplicate `WorkItem`.

### Assumption

`Assumption` is a bounded cognitive fact linked to a canonical subject. It owns
`assumption_id`, `subject_ref`, `statement`, `created_at`, and `basis_refs`.
Validation enforces `AssumptionId`, `ObjectReference` subject/basis references,
bounded statement text, and UTC timestamp normalization. It has no policy,
runtime, or persistence authority.

### Decision

`Decision` is a bounded cognitive decision fact. It owns `decision_id`,
`subject_ref`, `question`, `selected_option`, `rationale`, `decided_at`, and
`input_refs`. Validation enforces `DecisionId`, `ObjectReference` subject/input
references, bounded text fields, and UTC timestamp normalization. It is not
`PolicyDecision` and does not authorize effects.

### Plan

`Plan` is a bounded cognitive plan record. It owns `plan_id`, `problem_ref`,
`objective`, `created_at`, `assumption_refs`, `decision_refs`, and `work_refs`.
Validation enforces `PlanId`, `problem_ref` kind `problem`, assumption refs kind
`assumption`, decision refs kind `decision`, work refs kind `work`, bounded
objective text, and UTC timestamp normalization.

`Plan.work_refs` is a reference list, not a second work model. `Plan` has no
`work_id`, `state`, `dependencies`, `required_capabilities`, `inputs`,
`expected_outputs`, `policy_constraint_refs`, `authority_ref`, `principal_ref`,
or `evidence_requirement_refs`.

## Adversarial Validation

The validator ran additional probes outside the implementation's happy-path
tests:

- malformed or cross-prefix cognitive IDs reject;
- `ObjectReference(kind=work, ref_id=ProblemId(...))` rejects;
- cognitive IDs round-trip through the existing `ObjectReference`;
- `Problem.intent_ref`, `Plan.problem_ref`, `Plan.assumption_refs`,
  `Plan.decision_refs`, and `Plan.work_refs` reject wrong kinds;
- caller-provided mutable lists normalize to immutable tuples;
- all five records serialize, deserialize, and reserialize to the same
  JSON-compatible payloads;
- `Plan` remains disjoint from `WorkItem` fields except the shared bounded
  metadata fields `objective` and `created_at`;
- AST import/declaration inventory for `cognitive.py` contains exactly the
  five required records and only contract-layer imports.

No additional production correction or regression test was required.

## Mechanical Verification

| Check | Result |
| --- | --- |
| `git status --short --branch` | PASS: clean before validation evidence edits. |
| `uv lock --check` | PASS: 47 packages resolved. |
| `uv sync --locked --all-groups --all-packages` | PASS: 44 packages checked. |
| `pnpm install --frozen-lockfile` | PASS. |
| Docker Compose config | PASS: canonical local compose file parsed. |
| `uv run ruff format --check .` | PASS: 213 files already formatted after validation evidence was added. |
| `uv run ruff check .` | PASS. |
| `uv run mypy apps/api/src packages/python/*/src` | PASS: no issues in 54 source files. |
| `pnpm check` | PASS: TypeScript build mode, ESLint, and Prettier. |
| Web tests | PASS: 1 file, 6 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| M1-002 focused tests | PASS: 7 passed. |
| Contract/schema/architecture suite | PASS: 56 passed. |
| Security suite | PASS: 357 passed, 2 known dependency warnings. |
| API integration tests | PASS: 6 passed, 2 known dependency warnings. |
| Docker-backed PostgreSQL provider integration | PASS: 1 passed. |
| Docker-backed persistence/runtime integration | PASS: 4 passed when run serially. |
| M0 vertical-slice integration tests | PASS: 2 passed, 2 known dependency warnings. |
| BOOT/M0 acceptance tests | PASS: 8 passed, 2 known dependency warnings. |
| API/core/provider/unit suites | PASS: 54 passed, 2 known dependency warnings. |
| Persistence/policy/runtime non-integration suites | PASS: 128 passed, 4 deselected. |
| Full pytest suite | PASS: 730 passed, 2 known dependency warnings. |
| `git diff --check` | PASS. |

Known warnings are the existing Starlette/FastAPI `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings.

## Lifecycle Transition

TASK-M1-002 is `VALIDATED, FROZEN`.

According to the frozen M1 DAG, TASK-M1-003 and TASK-M1-004 become eligible
after this validation/freeze commit is integrated into the main M1 baseline.
Existing TASK-M1-005, TASK-M1-006, and TASK-M1-009 READY status is unchanged.
TASK-M1-007 through TASK-M1-019 remain blocked by their documented
prerequisites.

No TASK-M1-003, TASK-M1-005, TASK-M1-006, TASK-M1-009, later M1 work, merge,
push, deploy, rebase, reset, cherry-pick, or main-branch integration was
performed.

## Files Modified For Validation

- `docs/contracts/TASK-M1-002-cognitive-contracts.md`
- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-002-evidence.md`
- `docs/tasks/TASK-M1-002-validation-evidence.md`
- `tests/security/test_security_baseline.py`
