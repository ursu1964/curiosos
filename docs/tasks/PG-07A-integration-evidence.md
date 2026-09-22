---
id: PG-07A-INTEGRATION-EVIDENCE
title: PG-07A Integration Evidence
lifecycle: IMPLEMENTED
artifact_type: evidence
authority: authoritative
tasks:
  - TASK-BOOT-014
  - TASK-BOOT-015
  - TASK-BOOT-017
---

# PG-07A Integration Evidence

PG-07A integrated independently validated commits:

- TASK-BOOT-014: `20b27f31c17b09708885e7447ef2bde2ab93a865`
- TASK-BOOT-015: `12bb41da9695ef35ca69e99d24a132972a348edb`
- TASK-BOOT-017: `56428d8fcdd8b67ab822691e96c0a9a44bf39642`

## Integration

| Subject | Result |
| --- | --- |
| Pre-integration baseline | `main` was at `ad9901090f57a76249989fa882b8774d14f79875`. |
| TASK-BOOT-017 merge | Merged without conflicts. |
| TASK-BOOT-014 merge | Conflict only in `docs/program/status-ledger/BOOT-000-task-ledger.md`; resolved by preserving TASK-BOOT-014 and TASK-BOOT-017 status rows. |
| TASK-BOOT-015 merge | Conflict only in `docs/program/status-ledger/BOOT-000-task-ledger.md`; resolved by preserving TASK-BOOT-014, TASK-BOOT-015, and TASK-BOOT-017 status rows. |
| Status reconciliation | TASK-BOOT-014, TASK-BOOT-015, and TASK-BOOT-017 recorded as `VALIDATED, FROZEN`. |
| TASK-BOOT-016 status | Not started; remains frozen planning state only. |
| Later task status | TASK-BOOT-018+ not advanced. |
| Outstanding verification | `BOOT-VERIFY-PG-READINESS-001` remains open. |

## Core Semantic Review

`CoreContext` is composed from the frozen `ObservabilityContext` contract and an
optional frozen `Authority` contract from TASK-BOOT-013.

The integrated core foundation does not evaluate policy, grant authority, mutate
authority, embed secret values, or import provider implementations. Optional
`Authority` represents bounded context supplied to core behavior.

`ProviderCatalog` is a Curios-owned core port exposing canonical
`ProviderDescriptor` contracts through `Result`. It does not import provider
implementations, select or rank providers, implement capability routing, grant
provider authority, or contain Ollama/PostgreSQL/FastAPI-specific semantics.

`CoreServices` remains a minimal service boundary and does not implement a
scheduler, DAG engine, capability resolver, model router, agent execution,
policy engine, event bus, persistence, or provider behavior.

## Deterministic Checks

| Check | Result |
| --- | --- |
| TOML validation | Passed for root and Python package `pyproject.toml` files. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed: 87 files already formatted. |
| `uv run mypy packages/python` | Passed: no issues found in 45 source files. |
| `uv run pytest packages/python/curios_contracts/tests -q` | Passed: 114 tests passed. |
| `uv run pytest packages/python/curios_core/tests -q` | Passed: 9 tests passed. |
| `uv run pytest tests/contract -q` | Passed: 10 tests passed. |
| `uv run pytest tests/schema -q` | Passed: 5 tests passed. |
| `uv run pytest tests/architecture -q` | Passed: 11 tests passed. |
| `uv run pytest -q` | Passed: 149 tests passed. |
| Core semantic review | Passed. |
| Manual architecture/import scan | Passed. |
| Source-only secret scan | Passed. |
| Conflict-marker scan | Passed. |
| `git diff --check` | Passed. |
