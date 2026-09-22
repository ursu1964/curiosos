---
id: TASK-M0-002-VALIDATION-EVIDENCE
title: TASK-M0-002 Independent Revalidation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-002
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-002 Independent Revalidation Evidence

## Decision

TASK-M0-002 REVALIDATION: PASS

Validated candidate:

`f4f3accd4541eed9e3bb6fd2a508c606d7cb9b81`

Implementation baseline:

`8635860a2e637abe6a4049bb4702fbf486163c62`

Previous validation result:

`TASK-M0-002 VALIDATION: FAIL`

The prior blocking defect was native SQLAlchemy/PostgreSQL exception leakage
through public `PersistenceError.__cause__` chaining. The corrected candidate
fully resolves that defect.

## Previous Defect Revalidation

Public persistence exception translation paths were audited adversarially:

- `PersistenceStore.transaction()` -> operation `transaction`;
- `PersistenceStore.check_readiness()` -> operation `readiness`;
- `PersistenceTransaction.insert_record()` -> operation `insert_<kind>`;
- `PersistenceTransaction.read_record()` -> operation `read_<kind>`;
- `PersistenceTransaction.count_records()` -> operation `count_<kind>`;
- `apply_schema_migrations()` -> operation `schema_migration`.

Representative `IntegrityError`, `OperationalError`, `ProgrammingError`, and
generic `SQLAlchemyError` failures produce public `PersistenceError` instances
with:

- `__cause__ is None`;
- `__context__ is None`;
- no intended public native exception object access;
- no raw SQL, connection URL, credential, provider-native detail, or
  provider-native traceback in the public message, JSON summary, repr, or
  formatted traceback.

Bounded Curios-owned metadata remains:

- `code`;
- `retryable`;
- `operation`;
- `cause_type`.

No uncorrected public translation path was found that exposes SQLAlchemy,
psycopg, PostgreSQL, or Alembic native exception details through the Curios
persistence API.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Scope remains persistence-only | PASS | Changes are limited to `curios_persistence`, package metadata, persistence tests, topology/security docs/tests, and evidence/ledger files. |
| Authorized public surface is exact | PASS | `curios_persistence.__all__` exposes only config, store, record, kind, error, conversion, and migration primitives. |
| Schema primitives are authorized | PASS | Tables store canonical ID, payload, payload hash, and timestamps only. |
| No M0-004 event/evidence semantics | PASS | No event/evidence repository, writer, store semantics, API route, or runtime service was added. |
| No M0-005 work repository/state machine semantics | PASS | No work repository, lifecycle transition enforcement, or state machine behavior was added. |
| Alembic surface is authorized and package-owned | PASS | Migration environment and revision live under `curios_persistence/migrations`. |
| Canonical translation remains deterministic | PASS | Canonical objects map to `PersistenceRecord` by fixed kind, canonical ID, and JSON-compatible payload. |
| Identity/hash behavior remains correct | PASS | `payload_sha256` is computed from canonical sorted JSON with stable separators. |
| Transaction commit/rollback remains correct | PASS | Live PostgreSQL integration verifies commit visibility and rollback on user exception. |
| Duplicate conflict translation remains correct | PASS | Duplicate insert maps to `PersistenceErrorCode.CONFLICT` with safe cause type `IntegrityError`. |
| Restart persistence remains correct | PASS | Live integration rereads a persisted work record after store disposal and recreation. |
| SQLAlchemy/PostgreSQL objects remain internal | PASS | Public package exports no engine, connection, metadata, table, driver, or Alembic objects. |
| Contracts/core remain dependency-clean | PASS | `curios_contracts` and `curios_core` have no SQLAlchemy, Alembic, psycopg, or `curios_persistence` dependency/import. |

## Schema Classification

Each created table remains an authorized primitive persistence table, not a
downstream semantic implementation:

| Table | Classification |
| --- | --- |
| `curios_m0_work_records` | AUTHORIZED PRIMITIVE |
| `curios_m0_execution_records` | AUTHORIZED PRIMITIVE |
| `curios_m0_event_records` | AUTHORIZED PRIMITIVE |
| `curios_m0_evidence_records` | AUTHORIZED PRIMITIVE |
| `curios_m0_artifact_records` | AUTHORIZED PRIMITIVE |
| `curios_m0_policy_decision_records` | AUTHORIZED PRIMITIVE |
| `curios_m0_verification_records` | AUTHORIZED PRIMITIVE |

## Dependency And Guardrail Audit

Required and architecturally valid dependencies:

- `curios-contracts`: required for canonical contract conversion.
- `sqlalchemy`: required for PostgreSQL Core schema, engine, transactions, and
  deterministic exception categories.
- `psycopg[binary]`: required PostgreSQL driver for SQLAlchemy local Docker
  integration.
- `alembic`: required for package-owned reversible migration execution.

No unused TASK-M0-002 dependency was found.

Guardrails remain intact:

- TASK-M0-002 authorizes exactly `packages/python/curios_persistence/**`.
- `curios_policy` remains unauthorized and absent.
- `curios_runtime` remains unauthorized and absent.
- Representative M1+ package roots and broad runtime/service/provider roots
  remain blocked by topology tests.
- BOOT topology, security, core authority, provider/API/web, exact `.github`,
  and acceptance protections remain active.

## PostgreSQL Verification

The required LOCAL_DOCKER PostgreSQL integration passed against
`postgres:18`.

Verified behavior:

- Docker Compose config is valid;
- health/readiness succeeds after migrations;
- generated schema isolates test state;
- package-owned Alembic migration applies;
- migration downgrade removes record tables;
- transaction commit and rollback behavior is correct;
- duplicate conflict translation is deterministic;
- persisted work record survives store disposal/recreation;
- service is stopped cleanly after the test;
- named volume `curios-local-docker_postgres_data` is preserved;
- `docker compose down -v` was not used.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS: 9 TOML files parsed. |
| `uv lock --check` | PASS: resolved 44 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 41 packages. |
| Docker Compose config | PASS: `docker compose ... config --quiet`. |
| Ruff | PASS: all checks passed. |
| Ruff format | PASS: 151 files already formatted. |
| mypy | PASS: no issues found in 45 source files. |
| Persistence unit tests | PASS: 19 passed. |
| PostgreSQL integration | PASS: 1 passed. |
| Contracts/core | PASS: 123 passed. |
| Provider/API regressions | PASS: 45 passed, 2 known dependency warnings. |
| Contract/schema | PASS: 15 passed. |
| Architecture | PASS: 14 passed. |
| Security | PASS: 37 passed. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| Full pytest | PASS: 260 passed, 2 known dependency warnings. |
| Frontend frozen install | PASS: `pnpm install --frozen-lockfile`. |
| Frontend repository check | PASS: typecheck, ESLint, and Prettier. |
| Web tests | PASS: 1 test file, 2 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings previously classified as
non-blocking dependency warnings.

## Lifecycle Transition

TASK-M0-002 is `VALIDATED, FROZEN`.

TASK-M0-003 remains `READY`.

TASK-M0-004 through TASK-M0-014 remain `BLOCKED`. Do not make TASK-M0-004 ready
until PG-M0-02 integration with TASK-M0-003 is complete.
