---
id: TASK-BOOT-016-EVIDENCE
title: TASK-BOOT-016 Security Baseline Tests Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-016
---

# TASK-BOOT-016 Security Baseline Tests Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Main branch verified at `75f01fc1ce8526d5f20475e8c4e7d00bf30d23e9`; TASK-BOOT-016 implementation began after PG-07A readiness passed. |
| 2 | IMPLEMENTED | Repository-level security baseline tests and security documentation were added for TASK-BOOT-016 scope. |
| 3 | TESTED | Required deterministic checks were run after implementation; see check evidence below. |

## Implementation Summary

- Security tests: `tests/security/test_security_baseline.py`.
- Security baseline documentation: `docs/security/TASK-BOOT-016-security-baseline.md`.
- Status evidence: this document and the TASK-BOOT-016 row in `docs/program/status-ledger/BOOT-000-task-ledger.md`.

No canonical contract, core, provider, API, frontend, database, Docker, CI, or
runtime implementation files were modified.

## Security Baseline Categories

- Frozen security vocabulary checks.
- `UNKNOWN` policy outcome preservation and non-authorization.
- Secret/credential leakage and prohibited-field checks.
- Security contract source import checks for provider/framework/runtime
  independence.
- Local configuration example checks for `CURIOS_` prefix discipline.
- Core authority-boundary checks.
- PG-08 provider/runtime absence checks.

## Check Evidence

| Check | Result |
| --- | --- |
| TASK-BOOT-016 security tests | Passed: `uv run pytest tests/security -q` reported 9 passed. |
| Root and package TOML parse | Passed: root and all Python package `pyproject.toml` files parsed with `tomllib`. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .` reported 91 files already formatted. |
| mypy strict baseline | Passed: `uv run mypy packages/python` reported no issues in 45 source files. |
| Package-local contract tests | Passed: `uv run pytest packages/python/curios_contracts/tests -q` reported 114 passed. |
| Package-local core tests | Passed: `uv run pytest packages/python/curios_core/tests -q` reported 9 passed. |
| Repository contract tests | Passed: `uv run pytest tests/contract -q` reported 10 passed. |
| Repository schema tests | Passed: `uv run pytest tests/schema -q` reported 5 passed. |
| Repository architecture tests | Passed: `uv run pytest tests/architecture -q` reported 11 passed. |
| Full pytest suite | Passed: `uv run pytest -q` reported 158 passed. |
| Diff whitespace | Passed: `git diff --check`. |
| Scope review | Passed: changes are limited to `tests/security/**`, `docs/security/**`, TASK-BOOT-016 evidence, and the TASK-BOOT-016 status-ledger row. No contract/core implementation, provider, API, frontend, Docker, CI, dependency, or TASK-BOOT-018+ implementation files were modified. |

## Final Status

`TASK-BOOT-016` is `TESTED`. This task does not self-declare `VALIDATED` or
`FROZEN`.
