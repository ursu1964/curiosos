---
id: PG-M0-02A-INTEGRATION-EVIDENCE
title: PG-M0-02A Persistence and Policy Foundation Integration Evidence
lifecycle: TESTED
artifact_type: integration_evidence
authority: integration
milestone_id: M0
tasks:
  - TASK-M0-002
  - TASK-M0-003
date: 2026-09-22
---

# PG-M0-02A Integration Evidence

PG-M0-02A integrated independently validated and frozen task histories:

- TASK-M0-002: `b8dd41271cc956ebb4c6d6afe2dd3e47e78a4eb4`
- TASK-M0-003: `4eee5b2d5e975809a9bc372b01f36c46a418d30d`

Starting main baseline:

`8635860a2e637abe6a4049bb4702fbf486163c62`

## Integration

| Subject | Result |
| --- | --- |
| TASK-M0-002 merge | Merged with preserved task ancestry. |
| TASK-M0-003 merge | Merged with preserved task ancestry after expected shared conflict resolution. |
| Status reconciliation | TASK-M0-001, TASK-M0-002, and TASK-M0-003 are `VALIDATED, FROZEN`. |
| Downstream status | TASK-M0-004 and TASK-M0-005 are `READY`; TASK-M0-006 through TASK-M0-014 remain `BLOCKED`. |
| Later work | TASK-M0-004 and later implementation was not started. |

## Conflict Resolutions

Root `pyproject.toml` was reconciled to include both authorized M0 Python
workspace packages:

- `packages/python/curios_persistence`
- `packages/python/curios_policy`

`uv.lock` was regenerated with `uv lock` from the reconciled manifests rather
than hand-merging conflict fragments.

`tests/security/test_security_baseline.py` was reconciled to authorize exactly
the current M0 implementation package roots:

- `packages/python/curios_persistence`
- `packages/python/curios_policy`

The security topology keeps planned-but-not-yet-authorized M0 runtime package
roots deferred. `packages/python/curios_runtime`, broad `runtime/**`,
`services/**`, top-level `providers/**`, arbitrary application roots,
additional integration/acceptance tests, and M1+ package roots remain blocked.
Secret scanning covers both new M0 packages.

`docs/program/status-ledger/M0-status-ledger.md` was reconciled to preserve
both task lifecycle states and to apply the M0-WAVE-03 readiness transition
after integrated verification passed.

## Architecture And Scope

- `curios_contracts` does not depend on `curios_persistence` or `curios_policy`.
- `curios_core` does not depend on `curios_persistence` or `curios_policy`.
- Persistence and policy remain outer M0 implementation packages.
- Persistence does not call the policy evaluator, encode policy semantics, or
  implement event/evidence repository behavior.
- Policy does not depend on persistence, load policy from PostgreSQL, mutate
  persistence, or implement runtime service behavior.
- No provider/framework/native type became canonical.
- No TASK-M0-004 or TASK-M0-005 implementation was introduced.

## Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed: 10 TOML files parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed; built and installed `curios-persistence` and `curios-policy`. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 158 files already formatted. |
| mypy strict baseline | Passed: no issues found in 47 source files. |
| Persistence unit tests | Passed: 19 tests. |
| Policy tests | Passed: 20 tests. |
| `curios_contracts` and `curios_core` tests | Passed: 123 tests. |
| Architecture and security tests | Passed: 51 tests. |
| Provider package tests | Passed: 29 tests. |
| API, contract, schema, and API integration tests | Passed: 30 tests, 2 known dependency warnings. |
| BOOT acceptance tests | Passed: 6 tests, 2 known dependency warnings. |
| PostgreSQL integrations | Passed: 2 tests; service stopped cleanly and the persistent named volume remained present. |
| Full pytest suite | Passed: 280 tests, 2 known dependency warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed: typecheck, ESLint, and Prettier. |
| Web tests | Passed: 1 test file, 2 tests. |
| Web typecheck | Passed. |
| Web production build | Passed. |
| `git diff --check` | Passed. |

The warnings are the existing FastAPI/Starlette `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings previously
classified as non-blocking dependency warnings.

## Downstream Readiness

The frozen M0 DAG defines M0-WAVE-03 as TASK-M0-004 and TASK-M0-005 after
TASK-M0-002 is validated, frozen, and integrated.

- TASK-M0-004 prerequisites: TASK-M0-001 and TASK-M0-002 validated, frozen,
  and integrated.
- TASK-M0-005 prerequisites: TASK-M0-002 validated, frozen, and integrated.

PG-M0-02A also integrated TASK-M0-003, preserving the policy foundation needed
later by TASK-M0-006. TASK-M0-003 is not a direct hard prerequisite for
TASK-M0-004 or TASK-M0-005 in the frozen task pack.

TASK-M0-004 and TASK-M0-005 are therefore ready for explicit downstream task
authorization. They were not started during this integration.

## Final Status

PG-M0-02A integration is `TESTED`.
