---
id: TASK-M0-002-EVIDENCE
title: TASK-M0-002 PostgreSQL Runtime Persistence Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-002
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-002 Evidence

## Objective

Implement the M0 PostgreSQL runtime persistence foundation only.

TASK-M0-002 establishes the package-local persistence boundary required by
later M0 event/evidence and work-state tasks. It does not implement event store
semantics, work repositories, state transitions, runtime services, schedulers,
policy evaluation, API routes, or web behavior.

## Starting Baseline

`8635860a2e637abe6a4049bb4702fbf486163c62`

This matched `main` before TASK-M0-002 implementation began.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Add authorized M0 persistence package | PASS | Added `packages/python/curios_persistence/**` and root workspace membership only for TASK-M0-002. |
| Keep PostgreSQL/SQLAlchemy implementation-local | PASS | Public API exports persistence value objects/config/store helpers only; engines, connections, tables, and drivers remain internal. |
| Keep canonical contracts authoritative | PASS | Persistence stores canonical IDs and JSON-compatible payloads; no ORM models were added to `curios_contracts` or `curios_core`. |
| Own M0 schema/migration surface | PASS | Added in-package Alembic environment and `0001_m0_runtime_records` migration for work, execution, event, evidence, artifact, policy decision, and verification record tables. |
| Provide transaction boundary | PASS | `PersistenceStore.transaction()` commits on success and rolls back on exceptions. |
| Provide deterministic failure translation | PASS | SQLAlchemy integrity/connectivity/schema failures translate to `PersistenceError` codes without public `__cause__`/`__context__` native exception leakage. |
| Preserve restart persistence | PASS | LOCAL_DOCKER integration rereads a persisted work record after store disposal and recreation. |
| Preserve isolated PostgreSQL state | PASS | Integration uses a generated PostgreSQL schema and drops it after verification; the existing named volume is preserved. |
| Avoid downstream TASK-M0-004/005 behavior | PASS | No event/evidence repository, work repository, state transition enforcement, runtime service, scheduler, or API behavior was added. |

## Corrective Validation Finding

Independent TASK-M0-002 validation at
`3559b2342bd9cacc6d89911dda7f376bdcde1c09` failed because public persistence
operations translated SQLAlchemy/PostgreSQL exceptions into bounded
`PersistenceError` values using native Python exception chaining. That left
provider/database-native exceptions reachable through `PersistenceError.__cause__`
at the Curios persistence boundary.

The corrective implementation removes native chaining from every audited
public persistence translation site while preserving bounded Curios-owned
diagnostics:

- `PersistenceStore.transaction()` -> operation `transaction`
- `PersistenceStore.check_readiness()` -> operation `readiness`
- `PersistenceTransaction.insert_record()` -> operation `insert_<kind>`
- `PersistenceTransaction.read_record()` -> operation `read_<kind>`
- `PersistenceTransaction.count_records()` -> operation `count_<kind>`
- `apply_schema_migrations()` -> operation `schema_migration`

Translated public errors retain `code`, `retryable`, `operation`, and safe
`cause_type` metadata. They do not expose the native exception object, raw SQL,
connection URL, credentials, database-native traceback/detail, or arbitrary
provider payload through the public error representation.

TASK-M0-002 remains `IMPLEMENTED, TESTED` pending independent revalidation.

## Files Changed

- `packages/python/curios_persistence/**`
- `pyproject.toml`
- `uv.lock`
- `tests/security/test_security_baseline.py`
- `docs/architecture/TASK-M0-001-topology-guardrails.md`
- `docs/security/TASK-M0-001-topology-guardrails.md`
- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-002-evidence.md`

## Persistence Topology

Ownership package: `curios_persistence`.

Public boundary:

- `PersistenceConfig`
- `PersistenceStore`
- `PersistenceRecord`
- `PersistenceRecordKind`
- `PersistenceError`
- `PersistenceErrorCode`
- `canonical_to_record`
- `record_to_canonical`
- `apply_schema_migrations`

Internal implementation details:

- SQLAlchemy `Engine`, `Connection`, `Table`, `MetaData`, and PostgreSQL JSONB.
- Alembic `Config` and migration command execution.
- PostgreSQL driver/native exceptions.

`curios_contracts` and `curios_core` do not import SQLAlchemy, Alembic,
PostgreSQL drivers, or `curios_persistence`.

## Schema And Storage Behavior

The initial migration creates these M0 record tables:

- `curios_m0_work_records`
- `curios_m0_execution_records`
- `curios_m0_event_records`
- `curios_m0_evidence_records`
- `curios_m0_artifact_records`
- `curios_m0_policy_decision_records`
- `curios_m0_verification_records`

Each table stores:

- `canonical_id` as the primary key;
- `payload` as PostgreSQL JSONB containing the canonical JSON-compatible
  contract payload;
- `payload_sha256` for deterministic payload identity checks;
- `created_at` and `updated_at` database timestamps.

The persistence layer maps canonical contract objects to persistence records
and back for `WorkItem`, `ExecutionRecord`, `EventEnvelope`,
`EvidenceReference`, `ArtifactReference`, `PolicyDecision`, and
`VerificationReference`. A `PolicyDecision` must carry a canonical
`decision_id` before persistence.

## Dependencies

Added `curios-persistence` workspace package dependencies:

- `curios-contracts`
- `sqlalchemy`
- `psycopg[binary]`
- `alembic`

No PostgreSQL, SQLAlchemy, Alembic, or driver dependency was added to
`curios_contracts` or `curios_core`.

## Security And Architecture Transition

The M0 topology allowlist now authorizes exactly
`packages/python/curios_persistence/**` for TASK-M0-002. Planned policy and
runtime package roots remain blocked.

Secret scanning now covers `packages/python/curios_persistence/src`. The
package stores public canonical IDs and JSON-compatible payloads only; it does
not introduce secret resolution, IAM, policy evaluation, or embedded secrets.

## PostgreSQL Verification

The LOCAL_DOCKER integration test starts only the frozen PostgreSQL 18 service,
uses a generated schema name for isolation, applies migrations, verifies
transaction commit/rollback, rereads persisted state after store disposal,
validates deterministic duplicate-key failure translation, downgrades the M0
record migration, drops the generated schema, stops PostgreSQL, and confirms
the existing `curios-local-docker_postgres_data` volume still exists.

`docker compose down -v` was not used.

## Verification

Required TASK-M0-002 verification passed:

| Check | Result |
| --- | --- |
| TOML validation | Passed: 9 TOML files parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: 151 files already formatted. |
| mypy strict baseline | Passed: `uv run mypy apps/api/src packages/python/*/src` found no issues in 45 source files. |
| Persistence unit tests | Passed: 19 passed. |
| Persistence LOCAL_DOCKER integration | Passed: 1 passed. |
| Architecture and security tests | Passed: 51 passed. |
| Contract/core tests | Passed: 123 passed. |
| Provider/persistence regression tests | Passed: 48 passed. |
| Contract/schema/API integration tests | Passed: 21 passed, 2 known dependency warnings. |
| PostgreSQL integrations | Passed: 2 passed. |
| BOOT acceptance | Passed: 6 passed, 2 known dependency warnings. |
| Full pytest suite | Passed: 260 passed, 2 known dependency warnings. |
| Frontend frozen install | Passed. |
| Frontend workspace check | Passed: typecheck, ESLint, and Prettier. |
| Web tests | Passed: 1 test file, 2 tests. |
| Web typecheck | Passed. |
| Web production build | Passed. |
| `git diff --check` | Passed. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings previously classified as
non-blocking dependency warnings.

## Lifecycle State

TASK-M0-002 is `IMPLEMENTED, TESTED`.

TASK-M0-003 remains `READY`.

TASK-M0-004 through TASK-M0-014 remain `BLOCKED`.
