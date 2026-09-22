---
id: TASK-BOOT-016-EVIDENCE
title: TASK-BOOT-016 Security Baseline Tests Evidence
lifecycle: VALIDATED
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
| 4 | CORRECTED | PG-07B validation found false-negative weaknesses in repository secret scanning, semantic secret-field detection, core security-runtime boundary checks, and PG-08 surface detection. TASK-BOOT-016 tests were strengthened without adding runtime implementation. |
| 5 | VALIDATED | Independent PG-07B revalidation accepted the corrected TASK-BOOT-016 baseline. |
| 6 | FROZEN | The BOOT task ledger records TASK-BOOT-016 as `VALIDATED, FROZEN`; PG-07B is closed. |

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
- Tracked source/config/documentation secret-literal checks with approved
  placeholder handling.
- Security contract source import checks for provider/framework/runtime
  independence.
- Local configuration example checks for `CURIOS_` prefix discipline.
- Core authority-boundary checks using source topology and public API limits.
- PG-08 provider/runtime absence checks using current-stage tracked topology
  and workspace/package ownership boundaries.

## Corrective Validation Findings Addressed

| Finding | Corrective Mechanism |
| --- | --- |
| Representative fixtures did not prove repository secret-leakage protection. | Added tracked-file scanning across current authoritative source, configuration, and documentation surfaces, with deterministic placeholder handling for local examples. |
| Secret-value field detection used a narrow denylist. | Added semantic field-token detection with explicit allowlist only for frozen `SecretReference` metadata/reference fields, plus adversarial synthetic dataclass cases. |
| Core security-runtime boundary used only a few name substrings. | Added exact current-stage `curios_core` source topology and public export checks, preserving only the frozen `CoreContext`, `CoreServices`, and provider catalog port surface. |
| PG-08 absence used bypassable fixed paths. | Added tracked top-level/package/workspace boundary checks against the authorized current-stage topology. |

## Check Evidence

| Check | Result |
| --- | --- |
| TASK-BOOT-016 security tests | Passed: `uv run pytest tests/security -q` reported 20 passed. |
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
| Full pytest suite | Passed: `uv run pytest -q` reported 169 passed. |
| Diff whitespace | Passed: `git diff --check`. |
| Scope review | Passed: changes are limited to `tests/security/**`, `docs/security/**`, TASK-BOOT-016 evidence, and the TASK-BOOT-016 status-ledger row. No contract/core implementation, provider, API, frontend, Docker, CI, dependency, or TASK-BOOT-018+ implementation files were modified. |

## Independent Revalidation

Independent PG-07B revalidation was performed against corrective commit
`93f7c6ffabeaca4b7ce24ff4e18746e11e672eb6`.

| Revalidation Area | Result |
| --- | --- |
| Acceptance matrix | Passed: all mandatory TASK-BOOT-016 criteria were satisfied. |
| Prior failure A: secret leakage | Passed: tracked current-stage source, configuration, and documentation surfaces are scanned deterministically; approved placeholders are distinguished from secret-shaped values. |
| Prior failure B: secret-value fields | Passed: semantic secret/credential/token field detection rejects representative variants while preserving frozen `SecretReference` metadata/reference fields. |
| Prior failure C: core security-runtime boundary | Passed: `curios_core` source topology, public exports, `CoreContext`, `CoreServices`, and dependency direction remain bounded and do not implement policy, authority, or secret-resolution engines. |
| Prior failure D: PG-08 absence | Passed: current-stage tracked top-level paths, package roots, and workspace members match the authorized topology; provider/runtime surfaces remain absent. |
| Mechanical verification | Passed: TOML validation, `uv lock --check`, locked sync, Ruff, Ruff format check, mypy, targeted tests, full pytest, and `git diff --check`. |
| Scope review | Passed: no contract/core production changes, provider runtime, API/frontend, CI, dependency, or TASK-BOOT-018+ implementation was introduced. |

## Final Status

`TASK-BOOT-016` is `VALIDATED, FROZEN` after independent PG-07B revalidation.
