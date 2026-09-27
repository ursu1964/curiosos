---
id: TASK-M2-001-VALIDATION-EVIDENCE
title: TASK-M2-001 Independent Validation Evidence
lifecycle: FROZEN
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M2-001
milestone_id: M2
date: 2026-09-27
---

# TASK-M2-001 Validation Evidence

## Scope

This record freezes independent validation for
`TASK-M2-001 - M2 Topology and Guardrail Transition`.

Published M2 planning baseline:
`935935d64d30c266e270faad03122c97a15fdbc5`.

Implementation:
`b3a755a6365d33aac8cee7ad5445228e72578dd2`.

Correction 1:
`de292a64887fe0c6dc52fbe65f234a1db13d843e`.

Correction 2:
`d1dbfef5d6043092b42dcb632dc70bf8b664a7d4`.

No TASK-M2-002 implementation, product code, schema, migration, dependency,
CI workflow, merge, push, tag, release, or deployment occurred during
validation.

## Validation History

| Event | Result |
| --- | --- |
| Initial implementation validation | Failed because authorized future M2 surfaces were encoded as permanent absence rules. |
| Correction 1 | Converted absence checks into ownership and authority invariants. |
| Re-validation after Correction 1 | Failed because DataLab API adapter guards did not reject filesystem, persistence, or profiler/runtime implementation bypasses. |
| Correction 2 | Added bounded API-adapter authority guards while preserving explicit runtime-seam and composition-root compatibility. |
| Final validation | Passed against frozen TASK-M2-001 and M2 planning authority. |

## Acceptance Mapping

| Requirement | Result | Evidence |
| --- | --- | --- |
| Future M2 surface compatibility | PASS | Valid synthetic fixtures for future DataLab contracts, runtime records, persistence storage representation, exact work/capability identifiers, exact API endpoints, and exact web boundary functions passed. |
| Wrong-owner and duplicate rejection | PASS | Synthetic fixtures rejected DataLab canonical contracts outside `curios_contracts`, `DataLabRunState` and `DataLabRunRecord` in `curios_persistence`, duplicate `DatasetReference`, alternate work identifiers, and alternate capability identifiers. |
| API adapter authority | PASS | Valid DataLab API adapter delegation to a public runtime/application seam passed; synthetic direct profiler, persistence, filesystem, staging/tempfile, client-filename path, model/provider, and network authority failed guards. |
| Composition root compatibility | PASS | Composition-root dependency wiring for repository/runtime services remains allowed while DataLab endpoint/adapter bypass authority is rejected. |
| Frontend authority | PASS | Exact future DataLab `apiBoundary` functions passed; generic request escape hatches and direct App/network authority remain rejected by existing frontend guards. |
| Execution authority | PASS | Synthetic DataLab/runtime/profiler surfaces with subprocess, shell, command execution, dynamic import/code, network, provider/model, cloud, and arbitrary filesystem authority failed guards. Ordinary deterministic in-process computation passed. |
| Permanent versus temporal model | PASS | Permanent guards enforce ownership, package direction, exact API/web inventories, no duplicate abstractions, forbidden authority, and M3+ boundaries. The temporal fact that downstream M2 product surfaces are absent during TASK-M2-001 is proven by diff/scope audit rather than a permanent repository ban. |
| Downstream implementability | PASS | TASK-M2-002 through downstream API/web tasks can introduce their frozen surfaces without weakening TASK-M2-001 ownership or authority guarantees. Later tasks may add more specific guards as semantics become concrete. |
| M1 non-regression | PASS | M1 package direction, canonical abstraction uniqueness, persistence direction, provider/model boundaries, executor/routing/verification ownership, API composition, App network prohibition, generic frontend request prohibition, secret scanner, and workflow self-protection remain active. |
| M3+ boundary | PASS | Synthetic M3+ package/surface expansion remains rejected; no M3+ authority is reserved inside M2. |
| No premature product | PASS | Cumulative TASK-M2-001 diff contains no DataLab contracts, runtime records, dataset intake, staging, profiler, persistence, migration, API route, web boundary implementation, or UI. |
| Dependency/schema/CI hygiene | PASS | No dependency, lockfile, schema, migration, infrastructure, or CI workflow changes. |

## Probe Summary

Independent scratch probes produced these results:

- valid future owners: PASS.
- invalid wrong owners: PASS.
- duplicate `DatasetReference`: PASS.
- exact `dataset_profile` and `dataset_profiling` tokens: PASS.
- alternate work/capability identifiers: PASS.
- exact future API inventory: PASS.
- extra M2 API endpoint: PASS, rejected.
- exact future web boundary inventory: PASS.
- generic web request escape hatch: PASS, rejected.
- valid DataLab API adapter plus composition root: PASS.
- invalid DataLab API authority bypass: PASS, rejected.
- deterministic in-process computation: PASS.
- forbidden runtime authority: PASS, rejected.

## Verification

Final verification before this evidence record:

- `uv lock --check`: PASS.
- `uv sync --locked --all-groups --all-packages`: PASS.
- `pnpm install --frozen-lockfile`: PASS.
- Docker Compose config: PASS.
- `ruff format --check .`: PASS, 302 files already formatted.
- `ruff check .`: PASS.
- `mypy apps/api/src packages/python/*/src`: PASS, 70 source files.
- `pnpm check`: PASS.
- `pnpm --dir apps/web test`: PASS, 26 tests.
- `pnpm --dir apps/web typecheck`: PASS.
- `pnpm --dir apps/web build`: PASS.
- `uv run pytest tests/contract tests/schema -q`: PASS, 16 tests.
- `uv run pytest tests/architecture -q`: PASS, 45 tests.
- `uv run pytest tests/security -q`: PASS, 382 tests, 2 existing
  FastAPI/Starlette deprecation warnings.
- M1 package/API gate: PASS, 618 tests, 9 intentional deselections,
  2 existing FastAPI/Starlette deprecation warnings.
- M1 PostgreSQL gate: PASS, 4 tests.
- VS-M1 integration: PASS, 6 tests, 2 existing FastAPI/Starlette
  deprecation warnings.
- M1 acceptance: PASS, 14 tests, 2 existing FastAPI/Starlette deprecation
  warnings.
- Full pytest: PASS, 1206 tests, 2 existing FastAPI/Starlette deprecation
  warnings.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS.

Docker/PostgreSQL note: the local PostgreSQL service was started for the
serial DB-backed gates; no transient DB failure occurred during final
validation.

## Post-Record Requirement

After adding this evidence and freezing the ledger, rerun affected checks:

- `ruff format --check .`
- `ruff check .`
- focused TASK-M2-001 architecture/security guards.
- `uv run pytest tests/architecture -q`
- `uv run pytest tests/security -q`
- `git diff --check`
- `git diff --cached --check`

## 1.txt Guard

Historical input `1.txt` remains outside this worktree, untracked in the
primary repository, and untouched.

Expected SHA-256:

`d3db09d30c2b8ee24cad0339c140f7256eac3ea89f1bc9eafa9e86c55bb38b88`

## Downstream Status

TASK-M2-001 is `VALIDATED / FROZEN` on the task branch after this record.

TASK-M2-002 is DAG-blocked until TASK-M2-001 is integrated, published, and
remote-CI-verified according to the frozen lifecycle. TASK-M2-002 has not
started.
