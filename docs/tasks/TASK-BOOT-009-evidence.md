---
id: TASK-BOOT-009-EVIDENCE
title: TASK-BOOT-009 Primitive Contracts Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-009
---

# TASK-BOOT-009 Primitive Contracts Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-009-primitive-contracts` at required base `01b8bcc2310b2e63771358b80d1b24a6fcbe69fa`; primitive implementation began. |
| 2 | IMPLEMENTED | Primitive Python modules, package exports, tests, and contract documentation added for TASK-BOOT-009 scope. |
| 3 | TESTED | Deterministic checks were run after implementation; see check evidence below. |

## Implementation Summary

- Contract documentation: `docs/contracts/TASK-BOOT-009-primitive-contracts.md`.
- Python primitives: `identifiers.py`, `temporal.py`, `schema_version.py`, `lifecycle.py`, and `serialization.py`.
- Package exports: `packages/python/curios_contracts/src/curios_contracts/__init__.py`.
- Tests: package-local tests under `packages/python/curios_contracts/tests`.

## Semantic Policies

- ID implementation: internal standard-library ULID-style value using a 48-bit millisecond timestamp and 80 bits from `secrets.randbits`; no dependency or library-specific object appears in serialized contracts.
- Timestamp policy: reject naive input; normalize timezone-aware non-UTC input to UTC; serialize with RFC3339 `Z`.
- Duration policy: non-negative integer milliseconds.
- Schema-version policy: canonical `major.minor.patch` string with non-negative integer components and no package-version coupling.
- Lifecycle policy: engineering/build lifecycle only; runtime lifecycle states are deferred.

## Check Evidence

| Check | Result |
| --- | --- |
| Path, branch, and base verification | Passed: `/home/user/projects/curiosos-wt-009`, branch `task/boot-009-primitive-contracts`, base `01b8bcc2310b2e63771358b80d1b24a6fcbe69fa`. |
| Pre-change clean status | Passed: `git status --short` returned clean before implementation. |
| Root and package TOML parse | Passed. |
| `uv lock --check` | Passed. |
| `uv sync --frozen` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .`. |
| mypy strict baseline | Passed: `uv run --package curios-contracts mypy packages/python`. |
| Primitive contract tests | Passed: `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` reported 30 passed. |
| Serialized representation inspection | Passed: IDs, timestamps, schema versions, lifecycle values, and explicit null fields produced JSON-compatible primitives. |
| Architecture/import scan | Passed: no forbidden imports from `curios_contracts` source or tests. |
| Diff whitespace | Passed: `git diff --check` and `git diff --cached --check`. |
| Scope review | Passed: staged changes are limited to `packages/python/curios_contracts/**`, `docs/contracts/TASK-BOOT-009-primitive-contracts.md`, `docs/tasks/TASK-BOOT-009-evidence.md`, and `docs/program/status-ledger/BOOT-000-task-ledger.md`. |
