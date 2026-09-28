---
id: TASK-M2-006-VALIDATION-EVIDENCE
title: TASK-M2-006 Independent Validation Evidence
task_id: TASK-M2-006
authority: independent_validation
lifecycle: VALIDATED_FROZEN
---

# TASK-M2-006 Validation Evidence

Published baseline: `aea54d98f87b4ee5a0b0237242b5e3305e42f889`

Implementation: `5d17aa8df92a5070fdf2289cfc8c46f6cd0098cb`

Correction 1: `4d734035432df1a7a839622be7fec4a2bf843a91`

## Acceptance Mapping

TASK-M2-006 defines the Curios-owned deterministic DataLab profiler seam in
`curios_runtime.datalab_profiler`. Validation compared the implementation to
the frozen M2 task pack, contract delta, architecture/security delta, milestone
definition, vertical slices, acceptance matrix, traceability, DAG, and
implementation evidence.

Validated scope:

- `DataLabProfilerRequest`
- `DataLabProfilerStagedInput`
- `DataLabProfilerResourceBounds`
- `DeterministicDataLabProfiler`
- `DataLabProfilerOutcome`
- bounded profiler error/status/event constants

Confirmed absent:

- M2-007 orchestration
- DataLab decomposition
- persistence, schema, or migration
- capability/agent integration
- API or web UI
- provider/model execution
- network, subprocess, shell, plugin, or dynamic-code authority

## Validation History

Initial implementation `5d17aa8` implemented the profiler seam and deterministic
profiling behavior.

Independent validation attempt 1 failed staged-input authority: an arbitrary
object with `handle_id` and `read_authorized_bytes()` was accepted, its callback
executed, and a completed profile was emitted.

Correction 1 `4d73403` replaced duck-typed staged authority with exact
repository-owned `DataLabProfilerStagedInput`.

Final revalidation passed after Correction 1.

## Staged Authority

Original defect reproduction now produces:

- accepted request: false
- callback invoked: false
- profile emitted: false
- result emitted: false
- evidence emitted: false
- event emitted: false

`DataLabProfilerStagedInput` is a nominal repository-owned frozen dataclass. It
stores bytes directly, has an opaque bounded `handle_id`, and does not accept a
callback, path, URL, file object, protocol implementation, or generic reader.

Exact runtime type validation rejects:

- arbitrary duck-typed objects
- callback-backed objects
- callables and lambdas
- `Path`
- filesystem path strings
- `file://`, `http://`, and `https://` strings
- open file objects and `BytesIO`
- objects exposing `read`, `read_bytes`, or `open`
- structurally compatible protocol-like objects
- subclass impersonation

For executable fixtures, invocation count remained zero. Controlled wrappers
representing path reads, `open`, network reads, and subprocess output were
rejected before execution.

Public construction of `DataLabProfilerStagedInput` with direct bytes is
accepted as the frozen profiler seam for already-authorized bytes. Possession of
the handle string alone does not recover bytes; the profiler never interprets
the handle as a path, locator, URL, or filesystem authority. Oversized bytes are
rejected by the profiler resource gate before CSV parsing.

## M2-003 Boundary

M2-003 remains the owner of dataset intake, staging, staged reads, cleanup, and
raw-byte lifetime. TASK-M2-006 does not invoke M2-003 intake, acquire staged
locators, resolve locators, trigger cleanup, or claim restart persistence.

Future M2-007 can bridge:

M2-003 bounded staged bytes -> M2-007 authorized bridge ->
`DataLabProfilerStagedInput` -> TASK-M2-006 profiler.

No arbitrary path, callback, file, URL, network, or duplicate staging authority
is needed.

## Integrity Gate

Validation confirmed:

- successful profiling only when staged bytes SHA-256, request
  `expected_sha256`, and dataset `ArtifactReference` integrity all match;
- staged-byte mismatch produces bounded failure with no successful profile;
- artifact/request integrity mismatch rejects request construction;
- wrong integrity algorithm rejects request construction;
- invalid staged authority fails before byte hashing or parsing.

## Profiling Semantics

The profiler emits the real M2-002 `DatasetProfile`,
`DataLabFinding`, `DataLabAnalysisResult`, `Result`, `EvidenceReference`, and
`EventEnvelope` contracts.

Validated behavior:

- row and column counts
- source column order
- UTF-8 BOM handling
- primitive inference for `INTEGER`, `DECIMAL`, `BOOLEAN`, `STRING`, `EMPTY`,
  and `MIXED`
- locale-independent numeric parsing
- booleans `true/false/yes/no/1/0`
- non-finite values as strings
- missing values from empty cells after trimming
- `missing_count + non_missing_count == row_count`
- warnings for empty, high-missingness, and mixed columns
- deterministic findings derived only from frozen warning categories
- bounded malformed CSV and resource-limit failures

## Result, Evidence, And Events

`DataLabAnalysisResult` and canonical `Result` preserve dataset, integrity,
profile, finding, work, run, analysis, result, and evidence consistency.

Evidence is bounded, inspection-kind, work-subject bound, and references the
dataset artifact ID without raw bytes, paths, or locators.

Events are limited to profiler started/completed/failed/timeout semantics,
carry bounded payloads, preserve subject/correlation context, and do not claim
verification completion, persistence, run-state transition, DAG mutation, or
cleanup.

## Resource Bounds

Validated resource limits:

- profiler timeout: maximum 5 seconds
- max upload bytes: 1 MiB
- max rows: 10,000
- max columns: 100
- max cell bytes: 16 KiB
- max warnings: 100
- max findings: 50
- max event payload: 16 KiB

The implementation has no retry loop, polling loop, scheduler, recursion, or
background execution framework.

## Determinism

Repeated equivalent requests with identical staged bytes and caller-supplied
IDs/timestamps produced identical JSON-compatible outcomes. Alternate staged
handle metadata did not affect output.

## Safe Errors

Validation used credential-shaped cell data, path-like values, URL-like values,
malformed authority objects, malformed integrity, and mixed values.

Public errors do not expose authority object reprs, callback names, CSV data,
filename values, paths, URLs, locators, provider/framework diagnostics,
tracebacks, or raw bytes.

## Non-Regression

- M2-001 architecture/security guards passed without weakening.
- M2-002 contract/reference regressions passed.
- M2-003 intake/staging regressions passed.
- No duplicate profile, finding, result, reference, staging, or byte-provider
  abstraction was introduced.

## Dependency / Schema

Dependency delta: none.

Lockfile delta: none.

Database schema or migration delta: none.

API/web delta: none.

Persistence/provider/model/CI delta: none.

## Verification

Pre-record verification:

- `uv lock --check`: passed.
- `uv sync --locked --all-groups --all-packages`: passed.
- `pnpm install --frozen-lockfile`: passed.
- Docker Compose config: passed.
- Ruff format: 317 files already formatted.
- Ruff check: passed.
- mypy: 73 source files passed.
- `pnpm check`: passed.
- Web tests: 26 passed.
- Web typecheck/build: passed.
- Contract/schema: 16 passed.
- Architecture: 47 passed.
- Security: 382 passed, 2 existing deprecation warnings.
- M2-006 implementation and validation regressions: 48 passed.
- Runtime package tests: 336 passed.
- M2-003 regressions: 36 passed.
- M2-002 regressions: 24 passed.
- M1 package/API slice excluding externally managed PostgreSQL persistence
  file: 815 passed, 2 existing deprecation warnings.
- PostgreSQL persistence integration: 2 passed.
- PostgreSQL provider integration: 1 passed.
- VS-M1 integration: 6 passed, 2 existing deprecation warnings.
- Acceptance: 14 passed, 2 existing deprecation warnings.
- Full pytest: 1328 passed, 2 existing deprecation warnings.

Docker/transient result: PostgreSQL was started and reached healthy state
before DB-backed slices. No recovery was required.

## Lifecycle

TASK-M2-006 is `VALIDATED / FROZEN` on the task branch.

TASK-M2-007 remains blocked until TASK-M2-006 completes its required
integration, publication, and exact-SHA remote-CI lifecycle.
