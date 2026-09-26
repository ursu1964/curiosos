---
id: TASK-M1-010-EVIDENCE
title: TASK-M1-010 Routing Decision Records Evidence
lifecycle: IMPLEMENTED
artifact_type: implementation_evidence
authority: implementation
task_id: TASK-M1-010
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-010 Implementation Evidence

## Objective

TASK-M1-010 adds deterministic, persistable routing decision records over
already available M1 executor candidates and M1-009 local model/profile
candidates.

It does not execute work, invoke an executor, call a provider/model, discover
models, mutate WorkItem or WorkDag state, transition agents, create execution
records, schedule work, expose API/UI behavior, or implement TASK-M1-011.

## Starting Baseline

`d75700510a11e19e63bbb832d32804372dbd5225`

TASK-M1-001 through TASK-M1-009 are integrated, validated, frozen, published,
and remotely CI-verified at this baseline.

## Prerequisite Proof And Ledger Reconciliation

The authoritative M1 DAG requires:

- TASK-M1-008;
- TASK-M1-009.

Both prerequisites are validated/frozen/integrated/published/remote-CI-verified.
No additional M1-010 entry gate exists in the task specification or DAG.

The M1 status ledger still recorded TASK-M1-010 as `BLOCKED` after M1-009
publication. That row was stale reporting state. This implementation reconciles
the row as part of TASK-M1-010 normal lifecycle evidence and records
TASK-M1-010 as `IMPLEMENTED, TESTED`.

## M1-009 / M1-010 Boundary

M1-009 owns:

- local Ollama model/profile discovery;
- `LocalModelProfile`;
- provider-local availability/status;
- bounded discovery failures.

M1-010 consumes profile records as already supplied candidates. It does not move
discovery into runtime and does not modify M1-009 to recommend a preferred
model.

## M1-010 / M1-011 Boundary

M1-010 owns:

- inert route candidate records;
- deterministic route decision creation;
- selected-route and no-route outcomes;
- bounded structured rationale;
- bounded resource constraints;
- routing decision persistence and reconstruction.

M1-011 owns the later bounded DAG runner. This task leaves absent:

- scheduler/runner loops;
- work claiming;
- WorkItem, WorkDag, AgentInstance, or ExecutionRecord mutation;
- executor invocation;
- provider/model invocation;
- retry/cancellation orchestration.

## Implementation Architecture

The implementation adds `curios_runtime.routing_decision_repository` with:

- `RoutingCandidate`;
- `RouteCandidateKind`;
- `RoutingDecisionRequest`;
- `RoutingDecisionRecord`;
- `RoutingDecisionStatus`;
- `RoutingDecisionRationale`;
- `RoutingRationaleCode`;
- `RoutingDecisionError` and `RoutingDecisionErrorCode`;
- `StoredRoutingDecision`;
- `M1RoutingDecisionRepository`;
- `select_m1_route`.

The routing decision surface uses canonical `DecisionId`, `WorkItem`,
`WorkId`, `ObjectReference`, `ObservabilityContext`, `UtcTimestamp`, and
`SchemaVersion`. Model-profile candidates copy only provider reference, model
name, and status from M1-009 profile records; they do not copy arbitrary model
metadata, provider errors, client objects, prompts, credentials, or generated
content.

Persistence is implemented as a new primitive record kind and table:

- `PersistenceRecordKind.ROUTING_DECISION`;
- `curios_m1_routing_decision_records`;
- Alembic migration `0005_m1_routing_decision_records`.

`curios_persistence.record_to_canonical()` deliberately rejects routing
decision records because reconstruction belongs to the M1 runtime repository,
matching the established M1 Work DAG pattern.

## Routing Semantics

`select_m1_route()` is deterministic and in-memory:

- candidates are sorted by stable candidate key;
- exactly one valid non-`NO_MODEL` candidate produces `SELECTED`;
- zero valid candidates produces `NO_ROUTE` with `NO_VALID_ROUTE`;
- multiple valid candidates produces `NO_ROUTE` with `AMBIGUOUS_ROUTE`;
- `NO_MODEL` is a recordable candidate/outcome marker, not an executable
  candidate;
- `required_route_kind` and `required_provider_ref` constraints may filter
  candidates;
- `local_only` must remain `true` when present.

The implementation intentionally does not choose a first candidate from an
ambiguous set and does not rank, score, benchmark, or infer model quality.

## Constraint And Rationale Semantics

Resource constraints are bounded JSON-compatible mappings with an allowlisted
key set:

- `local_only`;
- `required_route_kind`;
- `required_provider_ref`.

Unknown constraints, non-local routing, unsupported route kinds, unsafe text,
and sensitive-shaped keys or values fail boundedly.

Rationale is structured as bounded reason codes plus sanitized details. It does
not contain raw provider errors, prompts, generated text, secret-shaped values,
environment values, or hidden chain-of-thought.

## No-Route Semantics

No route is a first-class bounded outcome, not an exception leak and not a
fallback execution attempt. Empty candidate sets, no-model-only requests,
unsupported executor work types, unavailable model profiles, or ambiguous
candidate sets produce reconstructable `NO_ROUTE` records.

## Authority Inventory

| Capability | M1-010 result |
| --- | --- |
| model-profile read | AUTHORIZED as already provided candidate input |
| routing decision creation | AUTHORIZED |
| route persistence | AUTHORIZED through `M1RoutingDecisionRepository` |
| WorkItem read | AUTHORIZED only for work ID/type reference validation |
| WorkItem mutation | ABSENT |
| WorkDag read | ABSENT |
| WorkDag mutation | ABSENT |
| capability resolution | ABSENT |
| agent read/mutation | ABSENT |
| executor invocation | ABSENT |
| ExecutionRecord creation/mutation | ABSENT |
| Result creation | ABSENT |
| event/evidence emission | ABSENT |
| DB access | AUTHORIZED only via canonical persistence boundary |
| scheduling | ABSENT |
| provider selection | ABSENT beyond recording a candidate provider reference |
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
| Prerequisites | PASS | DAG prerequisites TASK-M1-008 and TASK-M1-009 are satisfied; ledger stale row reconciled in this task. |
| Persist routing decisions | PASS | `M1RoutingDecisionRepository` creates, reads, lists, and reconstructs records using `PersistenceStore`. |
| Candidate list and selected route | PASS | `RoutingDecisionRecord` stores bounded candidates and exactly one selected route only when unambiguous. |
| No-model/no-route route | PASS | `NO_ROUTE` records are produced for empty, no-model-only, unsupported, invalid, and ambiguous candidate sets. |
| Rationale | PASS | `RoutingDecisionRationale` uses bounded reason codes and sanitized details. |
| Resource constraints | PASS | Allowlisted constraints filter deterministically and reject unsupported/unsafe values. |
| Determinism | PASS | Candidate order is normalized by key; permutation tests produce identical decisions. |
| Persistence/schema | PASS | New record kind, schema table, migration 0005, downgrade -1, and re-upgrade are covered. |
| Safe-error/no-secret | PASS | Sensitive-shaped text in constraints is rejected without exposing raw supplied values. |
| M1-011 boundary | PASS | No runner, scheduler, work claiming, executor invocation, lifecycle mutation, retry, cancellation, provider/model invocation, API, or UI behavior is added. |

## Failure And Adversarial Coverage

Focused tests cover:

- single deterministic executor route;
- M1-009 model profile candidate projection without metadata duplication;
- reversed candidate order;
- multiple valid candidates;
- route-kind/provider constraints;
- empty candidate set;
- no-model-only candidate set;
- unsupported executor work type;
- candidate/work mismatch;
- duplicate candidate identity;
- unsupported and sensitive-shaped constraints;
- serialization/reconstruction;
- duplicate persisted decision;
- corrupt persisted payload;
- wrong persistence record kind;
- persistence backend failure;
- absence of execution/scheduling/provider/model/prompt/memory authority in
  decision payloads.

## Dependency And Schema Changes

No new package or third-party dependency is introduced.

Schema changes are limited to:

- `PersistenceRecordKind.ROUTING_DECISION`;
- `curios_m1_routing_decision_records`;
- Alembic revision `0005_m1_routing_decision_records`.

No pnpm manifest/lockfile change is required.

## Correction 1

Independent validation found that `required_provider_ref` accepted any
canonical `ObjectReference`, including non-provider references such as
`kind=work`, and later interpreted the malformed provider constraint as a
regular no-match filter. Correction 1 tightens
`_normalize_resource_constraints()` so malformed references and structurally
valid wrong-kind references fail request validation as
`RoutingDecisionErrorCode.INVALID_CONSTRAINT` with a fixed bounded message:
`Routing constraints require a canonical provider reference.`

The correction preserves the required distinction:

- malformed or wrong-kind `required_provider_ref` -> `INVALID_CONSTRAINT`;
- valid provider reference with no matching candidate -> deterministic
  `NO_ROUTE` / `NO_VALID_ROUTE`;
- valid provider reference matching exactly one model-profile candidate ->
  deterministic `SELECTED`.

The validator regression file
`packages/python/curios_runtime/tests/test_task_m1_010_validation_regressions.py`
is preserved and expanded to cover matching provider references, no-match
provider references, wrong-kind work/agent-instance/execution references,
malformed reference payloads, and secret-shaped malformed values.

## Verification

Initial focused checks after implementation:

| Check | Result |
| --- | --- |
| Worktree sync | PASS: `uv sync --locked --all-groups --all-packages` installed the task worktree environment. |
| Focused M1-010 routing tests | PASS: `uv run pytest packages/python/curios_runtime/tests/test_task_m1_010_routing_decision_records.py -q` passed 19 tests. |
| Persistence boundary tests | PASS: `uv run pytest packages/python/curios_persistence/tests/test_persistence_boundary.py -q` passed 23 tests. |
| Focused security guard inventory | PASS: selected runtime authority and M1 surface registry tests passed 3 tests. |
| Focused typecheck | PASS: `uv run mypy packages/python/curios_runtime/src packages/python/curios_persistence/src`. |
| Focused lint/format | PASS after formatting two files. |

Full verification after this evidence/ledger update:

| Check | Result |
| --- | --- |
| Lock check | PASS: `uv lock --check` resolved 50 packages. |
| Locked sync | PASS: `uv sync --locked --all-groups --all-packages`. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker Compose config | PASS. |
| Python formatting | PASS: `uv run ruff format --check .` reported 258 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python typing | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 68 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests/typecheck/build | PASS: 6 web tests, typecheck, and production build. |
| Contract/schema/architecture/security | PASS: 407 tests with 2 inherited FastAPI/Starlette warnings. |
| M1-001 through M1-009 plus M1-010 focused regressions | PASS: 296 tests. |
| Package/API/provider suites | PASS: 78 tests with 2 inherited FastAPI/Starlette warnings. |
| Runtime/persistence/policy non-integration suites | PASS: 221 tests with 10 deselected integration tests. |
| Docker-backed integrations | PASS: API 6, PostgreSQL provider 1, persistence 2, event/evidence 1, work repository 1, Work DAG repository 1, agent repository 1, agent lifecycle repository 1, routing decision repository 1, and M0 vertical slice 2. |
| Migration chain | PASS: single Alembic head `0005_m1_routing_decision_records`; `0004_m1_agent_records` -> head, downgrade -1, and re-upgrade succeeded. |
| Acceptance tests | PASS: 8 tests with 2 inherited FastAPI/Starlette warnings. |
| Full pytest | PASS: 925 tests with 2 inherited FastAPI/Starlette warnings. |
| Repository whitespace | PASS: `git diff --check`; staged whitespace check performed before commit. |

Known warning: inherited `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` does
not match this task worktree `.venv`; `uv` ignored it and used the project
environment.

## Lifecycle State

TASK-M1-010 is `IMPLEMENTED, TESTED`.

Independent validation/freeze is still required before TASK-M1-010 can become
an integrated prerequisite for TASK-M1-011.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-011 implementation, or later-task implementation was
performed.
