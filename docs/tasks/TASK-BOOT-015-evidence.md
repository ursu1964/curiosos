---
id: TASK-BOOT-015-EVIDENCE
title: TASK-BOOT-015 Architecture Conformance Checks Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-015
---

# TASK-BOOT-015 Architecture Conformance Checks Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-015-architecture-checks` at required base `ad9901090f57a76249989fa882b8774d14f79875`; TASK-BOOT-015 implementation began. |
| 2 | IMPLEMENTED | Repository-level architecture conformance tests and architecture documentation were added for TASK-BOOT-015 scope. |
| 3 | TESTED | Deterministic architecture and baseline checks were run after implementation; see check evidence below. |

## Implementation Summary

- Architecture tests: `tests/architecture/test_architecture_conformance.py`.
- Architecture documentation: `docs/architecture/TASK-BOOT-015-architecture-conformance.md`.
- Failure mapping: architecture conformance violations report `ARCHITECTURE_FAILURE`.
- Dependencies added: none.

## Check Evidence

| Check | Result |
| --- | --- |
| Path, branch, and base verification | Passed: `/home/user/projects/curiosos-wt-015`, branch `task/boot-015-architecture-checks`, base `ad9901090f57a76249989fa882b8774d14f79875`. |
| Architecture test suite | Passed: `uv run pytest tests/architecture -q` reported 11 passed. |
| Existing contract tests | Passed: `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` reported 114 passed. |
| Ruff check | Passed after formatting: `uv run ruff check .`. |
| Ruff format check | Passed after formatting: `uv run ruff format --check .`. |
| mypy | Passed: `uv run --package curios-contracts mypy packages/python` reported success for 40 source files. |
| Diff whitespace | Passed: `git diff --check`. |
| Scope review | Passed: changes are limited to `tests/architecture/**`, TASK-BOOT-015 docs/evidence/status under `docs/**`, and the status ledger entry for TASK-BOOT-015. No TASK-BOOT-014, TASK-BOOT-016, TASK-BOOT-017, product functionality, provider, API, database, Docker, Ollama, or frontend implementation was added. |

## Implemented Rule Coverage

- `curios_contracts` cannot import or declare package dependencies on forbidden
  provider/framework/runtime/tooling dependencies, including `curios_core`.
- Package metadata checks normalize Python distribution names so dotted import
  rules such as `google.genai` and `opentelemetry.exporter` also cover
  `google-genai` and `opentelemetry-exporter-*` dependencies.
- `curios_core` cannot import or declare package dependencies on provider,
  framework, telemetry implementation, Docker, or repository tooling concerns.
- Provider implementation imports from contracts/core are blocked even while
  provider directories are absent.
- Canonical contracts are checked against SQLAlchemy ORM base/decorator/mapping
  contamination.
- Canonical contracts are checked against FastAPI authority contamination.
- Canonical annotations are checked against provider-native imported or
  qualified types.
- `ObjectReference` is checked as the only generic `kind/ref_id` reference
  abstraction.
- Frontend direction is checked through repository workspace configuration and
  source paths only.
- Canonical domain packages are checked against repository tooling and
  infrastructure imports.

## Example Failure Quality

The architecture suite includes a deterministic failure-message formatting
check. The tested example renders:

```text
ARCHITECTURE_FAILURE: curios_contracts must not depend on provider/framework/runtime packages; file=packages/python/curios_contracts/src/curios_contracts/example.py:12; dependency=fastapi; detail=imports 'fastapi'
```

## False-Positive and False-Negative Assessment

- False positives are limited by using AST imports, package metadata, class
  structure, decorators, bases, and annotations instead of broad source grep.
- Provider implementation detection uses explicit import-root/path conventions;
  future providers should keep clear provider naming or live under
  `providers/**`.
- The frontend rule deliberately avoids brittle source-text claims about
  semantic authorship. It verifies structural direction, not whether TypeScript
  source happens to copy domain vocabulary.
- Annotation checks detect provider-native types only when linked to forbidden
  imports or forbidden qualified names. A purely local type with provider-like
  naming is outside the deterministic signal used here.

## Final Status

`TASK-BOOT-015` is `TESTED`. This task does not self-declare `VALIDATED` or
`FROZEN`.
