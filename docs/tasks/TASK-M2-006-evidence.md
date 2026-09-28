---
id: TASK-M2-006-EVIDENCE
title: TASK-M2-006 Implementation Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
task_id: TASK-M2-006
date: 2026-09-28
---

# TASK-M2-006 Implementation Evidence

## Baseline And Prerequisites

- Baseline: `aea54d98f87b4ee5a0b0237242b5e3305e42f889`.
- TASK-M2-001, TASK-M2-002, and TASK-M2-003 are published and remote-CI-verified.
- TASK-M2-006 is DAG-ready from TASK-M2-002. TASK-M2-003 compatibility was audited, but M2-003 is not a direct prerequisite for this task.

## Implemented Seam

Owner: `curios_runtime.datalab_profiler`.

Implemented:

- `DataLabProfilerRequest`
- `DataLabProfilerResourceBounds`
- `DataLabProfilerStagedInput`
- `DeterministicDataLabProfiler`
- `DataLabProfilerOutcome`
- `DataLabProfilerOutcomeStatus`
- `DataLabProfilerErrorCode`

The seam accepts a dataset `ArtifactReference(kind=dataset)`, an authorized staged-input handle, expected SHA-256, DataLab run/work/result identity, evidence/event IDs, observability context, constraints, and explicit resource bounds.

## Authority Inventory

Authorized:

- supplied staged bytes through exact `DataLabProfilerStagedInput`
- UTF-8/BOM decoding
- standard-library CSV parsing
- SHA-256 integrity verification
- deterministic in-process profile computation
- canonical contract construction

Absent:

- filesystem path authority
- client filename authority
- network or remote URL retrieval
- subprocess, shell, plugin loading, dynamic code execution
- provider/model invocation
- database writes
- API or web transport behavior
- retry framework, scheduler, or run lifecycle orchestration

## Integrity Gate

The profiler computes SHA-256 over the exact supplied staged bytes and compares it to both the request `expected_sha256` and the dataset artifact integrity. A mismatch returns a bounded failure and does not produce a `DatasetProfile`.

## Profiling Semantics

Implemented deterministic CSV profile facts:

- `row_count`
- `column_count`
- source-header column order
- per-column `name`, `index`, `inferred_type`, `missing_count`, `non_missing_count`, `distinct_count`
- numeric `minimum`, `maximum`, and `mean` only for `INTEGER` and `DECIMAL`

Frozen primitive type rules:

- empty cells are missing
- whitespace is trimmed for inference only
- boolean values are case-insensitive `true`, `false`, `yes`, `no`, `1`, and `0`
- integers are optional sign plus base-10 digits
- decimals use `.` only
- non-finite values such as `NaN` and `Infinity` are strings
- mixed primitive classes infer `MIXED`

## Findings, Warnings, Evidence, And Events

Produced `DatasetProfileWarning` and `DataLabFinding` values for:

- empty columns
- high missingness
- mixed primitive types

Produced `EvidenceReference` with inspection kind and the dataset artifact reference. Produced `EventEnvelope` records for started/completed and bounded failure/timeout paths. Event payloads are bounded and exclude raw CSV, staged handles, paths, and diagnostic internals.

## Safe Errors

Failures use bounded `ContractError` values with fixed messages. Error paths do not echo:

- raw CSV rows or cells
- secret-shaped CSV values
- staged handles or locators
- filesystem paths
- provider/framework diagnostics
- stack traces or arbitrary exception representations

## Compatibility

- M2-001: authority guards remain applicable to the real profiler seam; no forbidden imports/calls were introduced.
- M2-002: the profiler emits real `DatasetProfile`, `DataLabFinding`, `DataLabAnalysisResult`, `Result`, `EvidenceReference`, and `EventEnvelope` contracts.
- M2-003: the staged input seam is compatible with ephemeral staged bytes and exact-byte SHA-256 semantics, without wiring intake to profiling.

## Focused Test Coverage

`packages/python/curios_runtime/tests/test_task_m2_006_datalab_profiler.py` covers:

- minimal valid dataset
- deterministic repeated profiling
- UTF-8 BOM handling and exact-byte hash
- multiple primitive types
- missing values and mixed types
- profile counts and numeric summaries
- canonical result/profile/evidence/events
- wrong dataset kind
- non-seam staged input rejection
- integrity mismatch
- malformed CSV
- row, column, and cell bounds
- unsupported constraints
- safe-error behavior
- staged handle metadata non-authority

## Dependency / Schema Result

No dependency, lockfile, database schema, migration, API, or web changes were introduced.

## Independent Validation Attempt 1

Result: FAILED.

Failed criterion: staged-input authority.

Exact reproduction:

- an arbitrary duck-typed object exposing `handle_id` and
  `read_authorized_bytes()` was accepted as profiler input;
- the object's callback was invoked;
- the profiler completed and emitted a profile.

Root cause: `_require_staged_input()` trusted behavioral shape rather than an
explicit repository-owned authority type.

## Correction 1

Correction 1 replaces the structural protocol trust boundary with exact
`DataLabProfilerStagedInput` authority. The authority stores bounded bytes
directly and does not accept arbitrary callbacks, paths, files, URLs, generic
readers, or filesystem/network-capable wrappers.

M2-003 compatibility is preserved by ownership:

- M2-003 continues to own staged locator storage/read/cleanup.
- Future M2-007 may read already-authorized staged bytes through M2-003 and
  construct `DataLabProfilerStagedInput`.
- M2-006 still does not resolve locators, open paths, trigger cleanup, or
  orchestrate intake-to-profiler execution.

Correction 1 regression coverage proves:

- the original arbitrary duck-typed callback-backed object is rejected;
- rejected authority methods/callbacks are not invoked;
- strings, filesystem-like strings, URLs, `Path`, file-like objects,
  `BytesIO`, callables, generic objects, and subclass impersonation are
  rejected before byte access;
- valid repository-owned `DataLabProfilerStagedInput` still profiles
  deterministic authorized bytes;
- integrity gate and profiler semantics are unchanged.

## Verification

Completed verification:

- `uv lock --check`: passed.
- `uv sync --locked --all-groups --all-packages`: passed.
- `pnpm install --frozen-lockfile`: passed.
- Docker Compose config: passed.
- Ruff format: 316 files already formatted.
- Ruff check: passed.
- mypy: 73 source files passed.
- `pnpm check`: passed.
- Web tests: 26 passed.
- Web typecheck/build: passed.
- Contract/schema: 16 passed.
- Architecture: 47 passed.
- Security: 382 passed, 2 existing deprecation warnings.
- Focused TASK-M2-006 profiler tests: 25 passed.
- Runtime package tests: 313 passed.
- M2-003 intake regressions: 36 passed.
- M2-002 contract/reference regressions: 24 passed.
- API integration: 6 passed, 2 existing deprecation warnings.
- Acceptance: 14 passed, 2 existing deprecation warnings.
- Package/API slice excluding the externally managed PostgreSQL persistence file: 792 passed, 2 existing deprecation warnings.
- PostgreSQL persistence integration rerun: 2 passed.
- PostgreSQL provider integration: 1 passed.
- VS-M1 integration: 6 passed, 2 existing deprecation warnings.
- Full pytest: 1305 passed, 2 existing deprecation warnings.

Correction 1 transient result: no PostgreSQL lifecycle failure occurred during
the correction verification. PostgreSQL was started and reached healthy state
before DB-backed slices, which then ran cleanly.
