---
id: TASK-M0-004-VALIDATION-EVIDENCE
title: TASK-M0-004 Independent Revalidation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-004
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-004 Independent Revalidation Evidence

## Decision

TASK-M0-004 REVALIDATION: PASS

Validated candidate:

`002f04b19e964ed42ab3d6bd8fd1720010337163`

Previous validation result:

`TASK-M0-004 VALIDATION: FAIL`

The prior blocking defect was that `PersistenceTransaction.list_records()`
ordered records by `created_at` and `canonical_id` instead of successful
persistence append order. The corrected candidate resolves that defect.

## Append-Order Revalidation

Live PostgreSQL adversarial checks verified:

- same-transaction inserts `z_second_by_sort`, then `a_first_by_sort` list as
  `z_second_by_sort`, `a_first_by_sort`;
- cross-transaction inserts preserve successful append order even when lexical
  IDs disagree;
- rolled-back records remain absent;
- failed duplicate inserts remain absent and do not disturb the ordering of
  successful records;
- store reconstruction preserves the same list order.

The successful observed order after all append tests was:

`z_second_by_sort`, `a_first_by_sort`, `m_third_across_transactions`,
`c_fourth_after_failed_insert`

## Ordinal Audit

Validation confirmed:

- every M0 primitive persistence table has `append_ordinal BIGINT GENERATED
  ALWAYS AS IDENTITY`;
- the ordinal is database-generated and persistence-owned;
- the ordinal is generic across work, execution, event, evidence, artifact,
  policy decision, and verification primitive tables;
- `list_records()` orders by `append_ordinal ASC`;
- canonical IDs, timestamps, and arbitrary database order are not used for
  list ordering;
- `PersistenceRecord`, canonical contracts, and runtime-store public APIs do
  not expose append ordinals;
- no gapless ordinal assumption is present.

The ordinal remains an implementation detail and is not canonical Curios
semantics.

## Migration Audit

Revision `0002_m0_append_order_ordinals` is package-owned under
`curios_persistence/migrations`.

Validation confirmed:

- upgrade from frozen `0001_m0_runtime_records` succeeds with existing rows;
- existing rows remain visible after upgrade;
- all seven primitive tables receive `append_ordinal`;
- downgrade `-1` removes `append_ordinal` from all seven primitive tables;
- downgrade `base` still removes the M0 record tables;
- no event/evidence-specific semantics leaked into the persistence schema.

## Compatibility

Frozen TASK-M0-002 compatibility remains intact:

- insert/read/count behavior;
- transaction commit and rollback;
- duplicate conflict isolation;
- payload SHA-256 verification;
- restart persistence;
- package-owned PostgreSQL migrations.

TASK-M0-002 does not require reopening.

## Runtime Store Acceptance

Runtime-store validation confirmed:

- `EventEnvelope` round-trip;
- `EvidenceReference` round-trip;
- `VerificationReference` round-trip;
- duplicate handling through bounded `RuntimeStoreErrorCode.CONFLICT`;
- missing handling through `None` reads and bounded `NOT_FOUND` errors;
- corrupt payload/hash mismatch handling as `CORRUPT_RECORD`;
- canonical reference, correlation, causation, and payload preservation;
- no SQLAlchemy, PostgreSQL, persistence record, or database-native leakage.

## Scope And Topology

Validation found no:

- TASK-M0-005 work repository or state transition implementation;
- TASK-M0-006 orchestration;
- scheduler or DAG engine;
- executor;
- broker or event bus;
- policy evaluation;
- API or web behavior;
- M1+ behavior.

TASK-M0-004 authorization remains limited to the runtime event/evidence store
and the narrow persistence-owned append-order primitive needed by the store.
TASK-M0-005 remains unimplemented on this branch. TASK-M0-006 and later remain
blocked.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS: 11 TOML files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS: local PostgreSQL compose config parsed. |
| Ruff check | PASS. |
| Ruff format check | PASS: 165 files already formatted. |
| mypy source gate | PASS: no issues found in 50 source files. |
| Broad mypy probe including tests | NON-BLOCKING: existing strict-test typing issues outside TASK-M0-004 were observed. |
| TASK-M0-004 runtime-store tests | PASS: 10 passed. |
| persistence/policy regressions | PASS: 41 passed. |
| contracts/core regressions | PASS: 138 passed. |
| architecture/security | PASS: 51 passed. |
| PostgreSQL integrations | PASS: 4 passed. |
| API integration | PASS: 6 passed, 2 known dependency warnings. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| full pytest suite | PASS: 291 passed, 2 known dependency warnings. |
| `pnpm install --frozen-lockfile` | PASS. |
| `pnpm check` | PASS. |
| web tests | PASS: 1 test file, 2 tests. |
| web typecheck | PASS. |
| web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings.

## Lifecycle Transition

TASK-M0-004 is `VALIDATED, FROZEN`.

TASK-M0-005 remains `READY`. TASK-M0-006 through TASK-M0-014 remain `BLOCKED`.
Do not make TASK-M0-006 ready until frozen M0-004 and M0-005 integrate.
