---
id: TASK-M2-007-VALIDATION-EVIDENCE
title: TASK-M2-007 Independent Re-Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
task_id: TASK-M2-007
date: 2026-09-29
---

# TASK-M2-007 Independent Re-Validation Evidence

## Scope

Published baseline:
`3a32e86c3980c7227d0930a701dc5b72180de85c`

Implementation:
`9a4f02e060d5deb9b826cdd50c55a425fce6bce2`

Correction 1:
`1f0f5827e8253c9c73f373e60a28d11a8e3c7f9a`

The cumulative chain was validated as:

`3a32e86 -> 9a4f02e -> 1f0f582`

The reviewed scope remains the M2-003 to M2-006 in-process dataset profiler
bridge, plus the minimum canonical M2-003 staged-locator helper required by
Correction 1. No M2-004 decomposition, M2-005 persistence/schema/migration,
M2-008 capability/agent integration, M2-009 convergence, API, web, provider,
model, dependency, lockfile, or CI workflow work was introduced.

## Acceptance Mapping

TASK-M2-007 owns only the frozen bridge:

M2-003 `DataLabDatasetIntakeResult` and bounded staging store
to authorized staged read, to M2-006 `DataLabProfilerStagedInput`, to
`DeterministicDataLabProfiler`, to canonical profile/result/evidence/events,
with bounded cleanup according to the task semantics.

The validation compared the implementation against:

- `docs/tasks/M2-task-pack.md`
- `docs/contracts/M2-contract-delta.md`
- `docs/architecture/M2-architecture-security-delta.md`
- `docs/program/milestones/M2-milestone-definition.md`
- `docs/program/milestones/M2-vertical-slices.md`
- `docs/program/milestones/M2-acceptance-matrix.md`
- `docs/program/milestones/M2-traceability.md`
- `docs/program/milestones/M2-implementation-dag.md`
- `docs/program/status-ledger/M2-status-ledger.md`
- TASK-M2-001, TASK-M2-002, TASK-M2-003, and TASK-M2-006 evidence and
  validation records

## Original Failure And Correction 1

Independent validation attempt 1 failed because M2-007 accepted a hybrid
intake result:

- artifact identity B
- staged locator A
- integrity SHA(A)
- staged bytes A

The bridge emitted successful output attributed to artifact B. The root cause
was that the bridge validated staged-byte SHA integrity but did not bind the
M2-003 generated staged locator to the same `ArtifactId` carried by the
`ArtifactReference`.

Correction 1 introduced `datalab_staged_locator_for_artifact_id()` as the
canonical M2-003 locator helper and requires, before any effect:

`intake_result.artifact_ref.locator == canonical locator for artifact_id`

Mismatch is a bounded `INVALID_REQUEST` failure.

## Artifact / Locator Invariant

The corrected implementation enforces:

- A artifact + A locator + SHA(A): valid.
- B artifact + A locator + SHA(A): rejected.
- A artifact + B locator + SHA(B): rejected.
- A artifact + A locator + wrong SHA: passes identity validation, then fails
  the SHA second-defense gate.
- Forged lookalike locators: rejected.

There is no identity rebinding. The bridge never changes the artifact ID,
locator, SHA, or output provenance to make a mismatch valid.

## Pre-Effect Ordering

The original B/A exploit was revalidated with counters around staged read,
SHA calculation, `DataLabProfilerStagedInput` construction, profiler
invocation, and cleanup.

For artifact/locator mismatch:

- staged read count: `0`
- staged-byte hash count: `0`
- profiler staged-input construction count: `0`
- profiler invocation count: `0`
- cleanup count: `0`
- profile/result/evidence/events: absent

Invalid hybrid requests do not clean up the victim dataset. Dataset A remains
readable after rejected B/A hybrid execution.

## Locator Helper

`datalab_staged_locator_for_artifact_id()` is deterministic, bounded,
repository-owned, filename-independent, and produces the exact canonical
M2-003 locator grammar used by dataset intake:

`curios-datalab-staged:<ArtifactId>`

The helper does not create filesystem, URL, or path authority and does not
introduce a second locator format or staging system.

## Store Ownership

An intake result produced by store A does not resolve through unrelated store B.
The foreign-store case fails boundedly as dataset unavailable, with no fallback,
arbitrary lookup, filesystem lookup, or network lookup.

## SHA Second Defense And Byte Identity

After artifact/locator identity passes, the SHA gate remains active:

`SHA(staged bytes) == ArtifactReference.integrity == dataset_integrity_sha256`

The bytes read from M2-003 are passed exactly into M2-006 sealed profiler
authority. Validation covered BOM and CRLF bytes with no decoding,
re-encoding, newline normalization, BOM stripping, truncation, or CSV rewrite
before profiler integrity verification.

## M2-006 Sealed Authority

M2-007 constructs the real M2-006 `DataLabProfilerStagedInput` only after an
authorized M2-003 read. It does not accept caller-supplied profiler authority,
duck-typed staged input, callback-backed input, `Path`, URL, file object,
`BytesIO`, protocol impostor, or subclass impersonation.

The M2-006 Correction 1 callback-not-invoked property remains covered by the
M2-006 regression suite and by M2-007 bridge tests.

## Work Identity And Invocation Count

The bridge requires the exact work type `dataset_profile`. Near misses and
unrelated work types fail before staged read or profiler invocation.

Valid execution invokes the profiler exactly once. Invalid pre-profiler cases
invoke it zero times. There is no retry, polling, scheduler, route selection,
capability assignment, agent loop, or generic DAG runner behavior.

## Output Propagation And Provenance

Canonical M2-006 output is propagated without duplicate models or semantic
reconstruction:

- `DatasetProfile`
- `DataLabFinding`
- `DataLabAnalysisResult`
- canonical `Result`
- `EvidenceReference`
- `EventEnvelope`

Output from dataset A remains bound to A's artifact identity, integrity, work
identity, evidence subject, and event subject. Interleaved A/B runs preserve
provenance and do not mix identities.

## Cleanup, Replay, And Failure Atomicity

Invalid artifact/locator identity fails before cleanup so a forged intake
result cannot delete another dataset's staged bytes.

Valid cleanup still uses the M2-003 bounded cleanup seam. Cleanup isolation was
validated with staged datasets A and B. Cleaning A does not remove or expose B.

After valid terminal cleanup, replay against the same staging handle fails
boundedly. There is no hidden cache, raw-byte restoration, filesystem fallback,
network fallback, or automatic re-upload.

For failures before profiler invocation, no successful execution output is
emitted. For bounded profiler failure after staged read, only the frozen failure
outcome is returned.

## Evidence And Events

The bridge preserves profiler evidence and events and does not invent
additional M2-009 evidence or events. Evidence and events remain bounded,
deterministically ordered, bound to the correct work/dataset subject, and free
of raw CSV, filename, path, locator, persistence, routing, capability,
verification, or DAG mutation claims.

## Safe Errors

Validation used secret-shaped CSV content, secret-shaped filenames,
path-like/URL-like locators, malformed artifact identity, wrong SHA, and wrong
work type probes. Public errors remain fixed and bounded and do not expose raw
cells, filename, locator, path, URL, SHA payloads beyond canonical error codes,
callback/object repr, traceback, or provider/framework diagnostics.

## Authority Audit

Authorized:

- M2-003 staged read and cleanup
- canonical locator validation
- M2-006 staged input construction
- M2-006 profiler invocation
- canonical output propagation

Absent:

- arbitrary filesystem authority
- arbitrary callback or generic file authority
- network or remote fetch
- subprocess or shell
- dynamic import/plugin execution
- provider/model/cloud SDK
- DB writes or persistence implementation
- API/UI
- scheduler/autonomous loop
- M2-009 convergence behavior

## Non-Regression

- M2-001 architecture/security guards pass without weakening.
- M2-002 contract/reference regressions pass with no duplicate canonical
  abstraction.
- M2-003 intake/staging/cleanup/SHA regressions pass, including the canonical
  locator helper matching existing intake generation.
- M2-006 profiler regressions pass, including sealed authority,
  callback-not-invoked, integrity gate, deterministic profiling, and safe
  errors.

## Validation Regressions

Added:

`packages/python/curios_runtime/tests/test_task_m2_007_validation_regressions.py`

The validator regressions preserve:

- original B/A hybrid exploit
- zero pre-effect counters
- canonical locator helper
- locator lookalikes
- foreign store
- SHA second defense
- byte identity
- work identity
- invocation count
- sealed-authority non-bypass
- output provenance
- invalid-hybrid cleanup non-effect
- valid cleanup isolation
- replay
- failure atomicity
- safe errors
- no M2-009 authority

Focused validation result: 14 passed.

## Dependency / Schema Result

Dependency delta: none.
Lockfile delta: none.
DB schema: unchanged.
Migration: none.
Persistence implementation: none.
API/web: none.
Provider/model: none.
CI: unchanged.

## Verification

Complete verification before validation record:

- `uv lock --check`: passed.
- `uv sync --locked --all-groups --all-packages`: passed.
- `pnpm install --frozen-lockfile`: passed.
- Docker Compose config: passed.
- Ruff format: 323 files already formatted after validation regression
  formatting.
- Ruff check: passed.
- mypy: 74 source files passed.
- `pnpm check`: passed.
- Web tests: 26 passed.
- Web typecheck/build: passed.
- Contract/schema: 16 passed.
- Architecture/security combined: 429 passed, 2 existing warnings.
- M2-007 validation regressions: 14 passed.
- Combined M2-007/M2-006/M2-003 focused/regression slice: 110 passed.
- Runtime package tests: 376 passed.
- M2-002 contract/reference regressions: 24 passed.
- Package/API non-DB slice: 864 passed, 16 intentional deselections,
  2 existing warnings.
- PostgreSQL persistence integration: 2 passed.
- Runtime/DAG PostgreSQL integration: 6 passed.
- PostgreSQL provider integration: 1 passed.
- API integration: 6 passed, 2 existing warnings.
- VS-M1 integration: 6 passed, 2 existing warnings.
- Acceptance: 14 passed, 2 existing warnings.
- Full pytest: 1368 passed, 2 existing warnings.

Docker/transient result:

- No PostgreSQL failure occurred during the revalidation verification.
- DB-backed slices were run serially with PostgreSQL health checks because
  lifecycle tests may stop the service as part of normal cleanup.

Post-record verification:

- Focused M2-007 implementation plus validation regressions: 40 passed.
- Runtime package tests: 376 passed.
- M2-006 regressions: 48 passed.
- M2-003 regressions: 36 passed.
- M2-002 contract/reference regressions: 24 passed.
- Architecture: 47 passed.
- Security: 382 passed, 2 existing warnings.
- Ruff format: 323 files already formatted.
- Ruff check: passed.
- `git diff --check`: passed.
- Full pytest: 1368 passed, 2 existing warnings.

## Downstream Status

TASK-M2-007 is validated/frozen by this evidence after Correction 1.

TASK-M2-009 remains blocked until TASK-M2-004, TASK-M2-005, TASK-M2-007, and
TASK-M2-008 satisfy the full frozen lifecycle required by the DAG.
