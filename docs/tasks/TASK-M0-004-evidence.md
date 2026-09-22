---
id: TASK-M0-004-EVIDENCE
title: TASK-M0-004 Event and Evidence Runtime Store Evidence
lifecycle: TESTED
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
- narrow persistence primitive extension for deterministic listing and payload
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
| Bounded deterministic read behavior | PASS | `list_*` methods require limits between 1 and 1000 and use persistence append order. |
| Missing records fail safely | PASS | `get_*` returns `None`; `require_*` raises Curios-owned `NOT_FOUND`. |
| Duplicate identity fails safely | PASS | Persistence conflicts translate to `RuntimeStoreErrorCode.CONFLICT` with no native exception cause/context. |
| Persistence-native exceptions stay behind boundary | PASS | Runtime errors expose bounded Curios-owned codes/details only. |
| Avoid downstream scope | PASS | No work repository, state transition engine, runtime service, scheduler, broker, API route, executor, knowledge, memory, or policy evaluation was introduced. |

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
| Ruff format check | PASS: 164 files already formatted. |
| mypy source gate | PASS: no issues found in 49 source files. |
| TASK-M0-004 runtime tests | PASS: 10 passed. |
| persistence/policy regressions | PASS: 40 passed. |
| contracts/core regressions | PASS: 123 passed. |
| architecture/security/acceptance | PASS: 57 passed, 2 known dependency warnings. |
| PostgreSQL integration | PASS: runtime and persistence integration tests, 2 passed. |
| full pytest | PASS: 290 passed, 2 known dependency warnings. |
| frontend regression | PASS: `pnpm install --frozen-lockfile`, `pnpm check`, web test 2 passed, web typecheck, web build. |
| `git diff --check` | PASS. |

The PostgreSQL integration used isolated generated schemas, stopped the local
PostgreSQL service cleanly, and preserved the
`curios-local-docker_postgres_data` named volume.

## Lifecycle

TASK-M0-004 is `IMPLEMENTED, TESTED` only. Independent validation is still
required before `VALIDATED, FROZEN`.

TASK-M0-005 remains `READY`. TASK-M0-006 through TASK-M0-014 remain `BLOCKED`.
