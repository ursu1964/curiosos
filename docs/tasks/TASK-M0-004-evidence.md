---
id: TASK-M0-004-EVIDENCE
title: TASK-M0-004 Event and Evidence Runtime Store Evidence
lifecycle: FROZEN
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-004
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-004 Event and Evidence Runtime Store Evidence

## Objective

Implement only the M0 runtime event/evidence writer boundary backed by the
frozen TASK-M0-002 persistence foundation.

## Implemented Surface

- `packages/python/curios_runtime/**`
- runtime event/evidence store tests
- narrow persistence primitive extension for append-order listing and payload
  hash verification
- narrow topology/security/architecture updates authorizing only
  `packages/python/curios_runtime/**` for TASK-M0-004
- M0 status ledger transition to `IMPLEMENTED, TESTED`

## Store API And Ownership

Public runtime API:

- `EventEvidenceRuntimeStore.append_event`
- `EventEvidenceRuntimeStore.get_event`
- `EventEvidenceRuntimeStore.require_event`
- `EventEvidenceRuntimeStore.list_events`
- `EventEvidenceRuntimeStore.append_evidence`
- `EventEvidenceRuntimeStore.get_evidence`
- `EventEvidenceRuntimeStore.require_evidence`
- `EventEvidenceRuntimeStore.list_evidence`
- `EventEvidenceRuntimeStore.append_verification`
- `EventEvidenceRuntimeStore.get_verification`
- `EventEvidenceRuntimeStore.require_verification`
- `EventEvidenceRuntimeStore.list_verifications`
- `RuntimeStoreError`
- `RuntimeStoreErrorCode`

The runtime store returns canonical `EventEnvelope`, `EvidenceReference`, and
`VerificationReference` values. It does not expose SQLAlchemy, PostgreSQL,
database rows, persistence records, or persistence-native exceptions.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Persist canonical event/evidence facts | PASS | Runtime store appends canonical events, evidence references, and verification references through `curios_persistence.canonical_to_record`. |
| Preserve identity and references | PASS | Tests prove event IDs, producer/subject references, observability correlation/causation fields, evidence IDs, artifact/evidence references, and verification references round trip. |
| Preserve deterministic payloads | PASS | Event payload and canonical `to_json()` output round trip unchanged. |
| Respect persistence hash behavior | PASS | Persistence reads and lists verify stored `payload_sha256`; PostgreSQL integration mutates a stored payload and runtime read fails as `CORRUPT_RECORD`. |
| Bounded deterministic read behavior | PASS | `list_*` methods require limits between 1 and 1000 and use persistence append order backed by persistence-owned append ordinals. |
| Missing records fail safely | PASS | `get_*` returns `None`; `require_*` raises Curios-owned `NOT_FOUND`. |
| Duplicate identity fails safely | PASS | Persistence conflicts translate to `RuntimeStoreErrorCode.CONFLICT` with no native exception cause/context. |
| Persistence-native exceptions stay behind boundary | PASS | Runtime errors expose bounded Curios-owned codes/details only. |
| Avoid downstream scope | PASS | No work repository, state transition engine, runtime service, scheduler, broker, API route, executor, knowledge, memory, or policy evaluation was introduced. |

## Corrective Ordering Record

Independent validation failed candidate
`125ff564e3e63e53b00d79a4f2e20f48d2e59fbf` because
`PersistenceTransaction.list_records()` ordered by `created_at ASC,
canonical_id ASC`. That order was deterministic, but it was not authoritative
append order: two records appended in one transaction as `z_second_by_sort` then
`a_first_by_sort` were listed as `a_first_by_sort`, `z_second_by_sort`.

The correction keeps append ordering as a persistence-owned primitive rather
than canonical Curios semantics:

- each M0 primitive persistence table now has an internal `append_ordinal`
  `BIGINT GENERATED ALWAYS AS IDENTITY` column;
- `PersistenceRecord` and canonical contracts do not expose the ordinal;
- `list_records()` orders by `append_ordinal ASC` after filtering by
  `PersistenceRecordKind`;
- limits remain bounded from 1 through 1000;
- payload hash verification remains active for reads and lists;
- no pagination, query framework, event bus, scheduler, work repository, or
  runtime orchestration behavior was introduced.

Adversarial PostgreSQL coverage proves:

- same-transaction inserts `z_second_by_sort`, `a_first_by_sort` list in that
  insertion order;
- cross-transaction inserts retain successful append order even when lexical
  IDs disagree;
- rolled-back and duplicate failed inserts do not become visible and do not
  alter observable list ordering;
- restart/reconstruction returns the same append ordering;
- a schema at frozen `0001_m0_runtime_records` with existing rows upgrades to
  the append-ordinal head migration and preserves visible row order.

## Dependencies

Added `curios-runtime` workspace package dependencies:

- `curios-contracts`
- `curios-persistence`

No brokers, queues, async infrastructure, external event systems, scheduler,
API/web dependencies, provider SDKs, or policy dependencies were added.

## Verification

Local implementation verification:

| Check | Result |
| --- | --- |
| TOML parse | PASS: all repository TOML files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS: local PostgreSQL compose config parsed. |
| Ruff check | PASS: `uv run ruff check .`. |
| Ruff format check | PASS: 165 files already formatted. |
| mypy source gate | PASS: no issues found in 50 source files. |
| TASK-M0-004 runtime unit tests | PASS: 9 passed. |
| persistence/policy regressions | PASS: 41 passed. |
| contracts/core regressions | PASS: 123 passed. |
| architecture/security | PASS: 51 passed. |
| PostgreSQL integration | PASS: runtime and persistence integration tests, 3 passed. |
| API integration | PASS: 7 passed, 2 known dependency warnings. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| full pytest | PASS: 291 passed, 2 known dependency warnings. |
| frontend regression | PASS: `pnpm install --frozen-lockfile`, `pnpm check`, web test 1 file / 2 tests, web typecheck, web build with 18 modules transformed. |
| `git diff --check` | PASS. |

The PostgreSQL integration used isolated generated schemas, stopped the local
PostgreSQL service cleanly, and preserved the
`curios-local-docker_postgres_data` named volume.

## Independent Revalidation

Independent revalidation of corrected candidate
`002f04b19e964ed42ab3d6bd8fd1720010337163` accepted the append-order
correction and runtime-store boundary.

Validation evidence:

- `docs/tasks/TASK-M0-004-validation-evidence.md`

## Lifecycle

TASK-M0-004 is `VALIDATED, FROZEN`.

TASK-M0-005 remains `READY`. TASK-M0-006 through TASK-M0-014 remain `BLOCKED`.
Frozen M0-004 and M0-005 must integrate before downstream readiness changes.
