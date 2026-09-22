---
id: PG-M0-02B-INTEGRATION-EVIDENCE
title: PG-M0-02B M0 Wave-03 Runtime Store and Work Repository Integration Evidence
lifecycle: TESTED
artifact_type: integration_evidence
authority: integration
milestone_id: M0
tasks:
  - TASK-M0-004
  - TASK-M0-005
date: 2026-09-23
---

# PG-M0-02B Integration Evidence

PG-M0-02B integrated independently validated and frozen task histories:

- TASK-M0-004: `b5b2856f58e6564316ea7f8c7e804e1261385dbd`
- TASK-M0-005: `2e963d53ffd8ea7b31d9a1d36719269357ee9467`

Starting main baseline:

`eb835ec39cde3eb57eceda6fb5045c9cbb124bfd`

## Integration

| Subject | Result |
| --- | --- |
| TASK-M0-004 merge | Merged with preserved task ancestry. |
| TASK-M0-005 merge | Merged with preserved task ancestry after expected shared conflict resolution. |
| Status reconciliation | TASK-M0-001 through TASK-M0-005 are `VALIDATED, FROZEN`. |
| Downstream status | TASK-M0-006 is `READY`; TASK-M0-007 through TASK-M0-014 remain `BLOCKED`. |
| Later work | TASK-M0-006 and later implementation was not started. |

## Conflict Resolutions

`packages/python/curios_runtime/src/curios_runtime/__init__.py` was reconciled
to export both frozen runtime boundaries:

- TASK-M0-004: `EventEvidenceRuntimeStore`, `RuntimeStoreError`,
  `RuntimeStoreErrorCode`;
- TASK-M0-005: `M0WorkRepository`, `RepositoryError`,
  `RepositoryErrorCode`, `StoredWorkItem`, `StoredExecutionRecord`,
  transition vocabularies, and pure transition helpers.

No runtime coordinator, facade, scheduler, executor, policy orchestration,
retry engine, or TASK-M0-006 service behavior was introduced.

`packages/python/curios_persistence/src/curios_persistence/boundary.py` was
reconciled to preserve both persistence extensions:

- TASK-M0-004 `list_records()` with append-order listing and payload-hash
  verification;
- TASK-M0-005 `replace_record()` with optimistic payload-hash replacement.

The corrected TASK-M0-002 public persistence error boundary remains intact:
translated public persistence errors do not expose native database exceptions
through intentional public chaining.

`tests/security/test_security_baseline.py` was reconciled to authorize the
current `packages/python/curios_runtime` package root for the frozen
TASK-M0-004/TASK-M0-005 capabilities only. TASK-M0-006 and TASK-M0-007 remain
absent from the authorized package-root registry, and broader runtime,
services, providers, app, integration-test, API, web, and M1+ surfaces remain
blocked.

## Alembic And Schema

Alembic inspection found exactly one head:

`0002_m0_append_order_ordinals`

Lineage:

`0001_m0_runtime_records -> 0002_m0_append_order_ordinals`

The integrated migration set is:

- `0001_m0_runtime_records.py`
- `0002_m0_append_order_ordinals.py`

All seven primitive record tables include the internal `append_ordinal`
column. The ordinal remains persistence-internal and is not canonical Curios
identity or semantics. `replace_record()` uses the existing `payload_sha256`
version token and requires no schema branch beyond the integrated lineage.

## Architecture And Separation

- `curios_contracts` and `curios_core` do not depend on `curios_runtime`,
  `curios_persistence`, or `curios_policy`.
- `curios_runtime` depends only on authorized frozen lower boundaries:
  `curios_contracts` and `curios_persistence`.
- `curios_runtime` does not depend on `curios_policy`.
- `curios_persistence` remains implementation-owned and does not encode
  runtime-store, repository, or policy semantics.
- `curios_policy` remains independent and is not coupled to persistence or
  runtime.
- The work repository does not emit events, evaluate policy, orchestrate
  execution, or call an executor.
- The event/evidence runtime store does not mutate work state, evaluate
  policy, orchestrate execution, or call an executor.

## Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed: 11 TOML files parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed; built and installed `curios-runtime`. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 171 files already formatted. |
| mypy strict baseline | Passed: no issues found in 51 source files. |
| Persistence unit tests | Passed: 19 tests. |
| Policy tests | Passed: 20 tests. |
| Runtime-store and work-repository unit tests | Passed: 56 tests. |
| `curios_contracts` and `curios_core` tests | Passed: 123 tests. |
| Provider package tests | Passed: 29 tests. |
| API, contract, schema, and API integration tests | Passed: 30 tests, 2 known dependency warnings. |
| Architecture and security tests | Passed: 51 tests. |
| BOOT acceptance tests | Passed: 6 tests, 2 known dependency warnings. |
| PostgreSQL integrations | Passed: 5 tests serially; service stopped cleanly and the persistent named volume remained present. |
| Full pytest suite | Passed: 339 tests, 2 known dependency warnings. |
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

The frozen M0 DAG defines TASK-M0-006 as consuming:

- TASK-M0-003 minimal policy evaluator;
- TASK-M0-004 event/evidence runtime store;
- TASK-M0-005 work repository and state transitions.

After PG-M0-02B integration, all three prerequisites are validated, frozen, and
integrated. TASK-M0-006 is therefore ready for explicit downstream task
authorization.

TASK-M0-007 through TASK-M0-014 remain blocked. TASK-M0-006 was not started
during this integration.

## Final Status

PG-M0-02B integration is `TESTED`.
