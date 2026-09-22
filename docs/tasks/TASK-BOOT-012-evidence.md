---
id: TASK-BOOT-012-EVIDENCE
title: TASK-BOOT-012 Event and Observability Contracts Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-012
---

# TASK-BOOT-012 Event and Observability Contracts Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-012-events-observability` at required base `ffbf8c5828eba954e06d24742ad168d9dfa38ab1`; event and observability contract implementation began. |
| 2 | IMPLEMENTED | Python contract modules, package exports, tests, and authoritative contract documentation were added for TASK-BOOT-012 scope. |
| 3 | TESTED | Deterministic checks were run after implementation; see check evidence below. |
| 4 | IMPLEMENTED | Reconciliation brought authoritative main `7f343d5550e28ea046fa9c3f710e3ec3a3623aa3` into the branch with a merge commit and replaced the duplicate generic reference contract with TASK-BOOT-010 `ObjectReference`. |
| 5 | TESTED | Combined TASK-BOOT-009, TASK-BOOT-010, and TASK-BOOT-012 contract checks were run after reconciliation; see check evidence below. |

## Implementation Summary

- Contract documentation: `docs/contracts/TASK-BOOT-012-events-observability-contracts.md`.
- Python contracts: `events.py`, `observability.py`, the frozen TASK-BOOT-010 `ObjectReference` contract in `references.py`, and the `CorrelationId` primitive extension in `identifiers.py`.
- Package exports: `packages/python/curios_contracts/src/curios_contracts/__init__.py`.
- Tests: event, observability, serialization, identifier, and architecture tests under `packages/python/curios_contracts/tests`.

## Semantic Policies

- Correlation representation: `CorrelationId` is a typed Curios ID with prefix `cor`; it is distinct from `TraceId`.
- Authoritative dependency: TASK-BOOT-010 is FROZEN and defines `ObjectReference(kind, ref_id)` as the single canonical generic Curios reference contract.
- Causation representation: no independent `CausationId` namespace was added; causation is represented as `causation_ref`, an `ObjectReference` to the immediate cause, commonly a prior event's `event_id`.
- Producer and subject reference strategy: `ObjectReference(kind, ref_id)` is the provider-neutral strategy for producer, subject, principal, and causation references.
- Event type policy: stable lower-case dotted strings, independent from `schema_version`, with no class-name contract semantics.
- Payload policy: payload and metadata must be JSON-compatible and must not contain secrets, exception objects, provider-native responses, or executable content semantics.

## Runtime Event Vocabulary

```text
work.created
execution.started
execution.completed
execution.failed
provider.invoked
policy.evaluated
approval.requested
approval.resolved
evidence.produced
verification.completed
```

## Check Evidence

| Check | Result |
| --- | --- |
| Path, branch, and base verification | Passed: `/home/user/projects/curiosos-wt-012`, branch `task/boot-012-events-observability`, base `ffbf8c5828eba954e06d24742ad168d9dfa38ab1`. |
| Pre-change status | Passed: no pre-existing local file modifications were reported before implementation. |
| Root and package TOML parse | Passed: `pyproject.toml` and all Python package `pyproject.toml` files parsed with `tomllib`. |
| `uv lock --check` | Passed: lockfile resolved without update. |
| `uv sync --frozen` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .` after applying formatter. |
| mypy strict baseline | Passed: `uv run --package curios-contracts mypy packages/python`. |
| TASK-009 + TASK-010 + TASK-012 tests | Passed: `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` reported 75 passed. |
| Serialized representation inspection | Passed: `EventEnvelope` serialized to snake_case JSON with explicit schema version, UTC `occurred_at`, `ObjectReference` producer, `ObjectReference` subject, `ObjectReference` principal, `ObjectReference` causation, trace ID, correlation ID, and work ID; round-trip returned producer kind `provider`, subject kind `work`, and causation kind `event`. |
| Architecture/import scan | Passed: exactly one `ObjectReference` implementation; no obsolete generic reference class; no OpenTelemetry, broker, provider SDK, WorkItem, AgentDefinition, AgentInstance, Capability, security, or policy implementation dependency found in `curios_contracts` source. |
| Obsolete reference search | Passed: no obsolete standalone generic reference implementation, import, or legacy field-name usage remained in source, tests, or TASK-BOOT-012 docs. |
| Diff whitespace | Passed: `git diff --check`. |
| Scope review | Passed: reconciliation changes are limited to merging frozen TASK-BOOT-010 mainline contracts, TASK-BOOT-012 Python contracts/tests, TASK-BOOT-012 documentation/status evidence, and architecture tests needed for the combined contract suite; no TypeScript packages, README, historical source, provider adapters, broker, persistence, API, or UI files were modified. |

## Shared-Contract Conflict Review

The shared-reference conflict was discovered during reconciliation with current
main. TASK-BOOT-012's duplicate pre-reconciliation generic reference contract
was removed. TASK-BOOT-012 now uses frozen TASK-BOOT-010
`ObjectReference(kind, ref_id)` for event producer, subject, principal, and
causation references.
