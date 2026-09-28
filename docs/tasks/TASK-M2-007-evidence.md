---
id: TASK-M2-007-EVIDENCE
title: TASK-M2-007 In-Process Dataset Profiler Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
task_id: TASK-M2-007
date: 2026-09-29
---

# TASK-M2-007 Evidence

## Baseline And Prerequisites

- Baseline: `3a32e86c3980c7227d0930a701dc5b72180de85c`.
- Branch: `task/m2-007-in-process-dataset-profiler`.
- Worktree: `/home/user/projects/curiosos-wt-m2-007`.
- TASK-M2-003 is `INTEGRATED / VALIDATED / FROZEN / PUBLISHED /
  REMOTE-CI-VERIFIED`.
- TASK-M2-006 is `INTEGRATED / VALIDATED / FROZEN / PUBLISHED /
  REMOTE-CI-VERIFIED`.
- TASK-M2-007 is DAG-derived `READY / AUTHORIZED` from direct prerequisites
  TASK-M2-003 and TASK-M2-006.

## Implemented Bridge

Owner: `curios_runtime.datalab_dataset_profiler`.

Implemented:

- `DATALAB_DATASET_PROFILE_WORK_TYPE`
- `DataLabDatasetProfilerRequest`
- `DataLabDatasetProfilerOutcome`
- `DataLabDatasetProfilerStatus`
- `DataLabDatasetProfilerCleanupStatus`
- `DataLabDatasetProfilerErrorCode`
- `DataLabDatasetProfilerError`
- `InProcessDataLabDatasetProfiler`

The bridge accepts a real M2-003 `DataLabDatasetIntakeResult`, a canonical
`WorkItem` whose `work_type` is exactly `dataset_profile`, DataLab analysis/run
identity, deterministic evidence/event IDs, observability context, and M2-006
resource/constraint inputs.

## M2-003 Staged-Read Use

The bridge reads bytes only through `LocalDataLabDatasetStagingStore` using the
opaque staged locator already present on the M2-003 `ArtifactReference`.

It does not:

- accept arbitrary bytes as request input
- accept `Path`, string, URL, file, `BytesIO`, callback, or generic reader
- interpret client filename metadata
- reconstruct filesystem paths from caller data
- create a second staging repository
- fetch remote data

## M2-006 Authority Conversion

After the M2-003 store returns already-authorized staged bytes, the bridge
constructs the explicit M2-006 `DataLabProfilerStagedInput` with a bounded,
opaque handle derived from the dataset content integrity. The profiler still
uses its own exact-type authority check and SHA-256 integrity gate.

Rejected non-M2-003 authority inputs fail before callback or byte access.

## Integrity And Provenance

The bridge preserves both integrity boundaries:

- M2-003 SHA-256 is computed over exact uploaded bytes, including any BOM.
- M2-007 verifies staged bytes still hash to the recorded
  `dataset_integrity_sha256` before invoking M2-006.
- M2-006 verifies its authorized staged bytes match the profiler request SHA
  and dataset artifact integrity.

The bridge does not silently rebind or replace dataset integrity. A staged-byte
mismatch fails boundedly before profiler invocation.

## Work Identity

The bridge requires canonical `WorkItem` input and rejects work types other
than `dataset_profile` before staged bytes are read.

The M2-006 profiler request derives `work_ref` from the supplied canonical
`WorkItem.work_id`, preserving the work subject for `Result`,
`EvidenceReference`, and `EventEnvelope`.

## Profiler Invocation

One authorized bridge request invokes `DeterministicDataLabProfiler.profile`
at most once. There is no retry, recursion, polling, scheduler, generic DAG
runner invocation, capability resolution, agent assignment, verification loop,
or run-state transition.

## Profile, Result, Evidence, And Events

The bridge propagates M2-006 output without reconstructing duplicate records:

- `DatasetProfile`
- `DataLabFinding`
- `DataLabAnalysisResult`
- canonical `Result`
- `EvidenceReference`
- `EventEnvelope`

No bridge-specific evidence or event is introduced.

## Cleanup And Replay

By default, the bridge calls `LocalDataLabDatasetStagingStore.cleanup_staged_bytes`
after a staged read and bounded profiler execution path. Cleanup uses only the
M2-003 bounded cleanup seam and never interprets the locator as an arbitrary
path.

Cleanup behavior:

- successful profile: staged bytes are cleaned;
- profiler bounded failure after read: cleanup is attempted;
- staged-byte integrity mismatch after read: cleanup is attempted;
- already-cleaned or foreign staging handle: read fails boundedly and cleanup
  is not attempted;
- cleanup failure is reported separately and does not convert a profiler
  success into a profiler failure.

After cleanup, replay against the same staged handle fails boundedly; re-analysis
requires a new upload.

## Safe Errors

Bridge errors use fixed bounded messages and error codes. They do not echo:

- raw CSV rows or cells
- secret-shaped data
- client filename
- filesystem path
- staged locator
- callback/object repr
- traceback
- framework/provider diagnostics

## Authority Inventory

Authorized:

- M2-003 staged read and cleanup
- construction of explicit M2-006 staged input from already-authorized bytes
- one deterministic in-process M2-006 profiler invocation
- canonical profiler output propagation

Absent:

- arbitrary filesystem authority
- arbitrary callback or generic tool execution
- network or remote fetch
- subprocess or shell
- dynamic plugin/import execution
- provider/model/cloud SDK
- database write or persistence implementation
- API/web transport behavior
- capability/agent integration
- DataLab run lifecycle implementation

## Compatibility

- M2-001: architecture/security authority guards remain green with the real
  M2-007 bridge surface.
- M2-002: the bridge uses canonical DataLab contracts and reference mappings
  emitted by M2-006.
- M2-003: intake bounds, filename metadata semantics, staging containment,
  locator semantics, cleanup safety, and SHA behavior are unchanged.
- M2-006: Correction 1 staged-input authority remains intact; M2-007 does not
  create a bypass around `DataLabProfilerStagedInput`.

## Focused Test Coverage

`packages/python/curios_runtime/tests/test_task_m2_007_dataset_profiler.py`
covers:

- valid M2-003 staged dataset to M2-006 profile
- exact SHA preservation and BOM compatibility
- canonical profile/result/evidence/event propagation
- multiple staged datasets and cleanup isolation
- deterministic repeated execution when cleanup is intentionally skipped
- cleanup and replay failure after cleanup
- foreign/cleaned staging handle failure
- staged-byte integrity mismatch
- wrong work type rejection before byte access
- arbitrary bytes/path/file/URL/callback rejection
- duck-typed callback authority not invoked
- safe-error behavior
- outcome invariant checks

## Dependency / Schema Result

No dependency, lockfile, database schema, migration, API, web, provider/model,
or CI workflow changes were introduced.

## Verification

Completed verification:

- `uv lock --check`: passed.
- `uv sync --locked --all-groups --all-packages`: passed.
- `pnpm install --frozen-lockfile`: passed.
- Docker Compose config: passed.
- Ruff format: 321 files already formatted after formatting the new focused
  test file.
- Ruff check: passed.
- mypy: 74 source files passed.
- `pnpm check`: passed.
- Web tests: 26 passed.
- Web typecheck/build: passed.
- Contract/schema: 16 passed.
- Architecture: 47 passed.
- Security: 382 passed, 2 existing deprecation warnings.
- Focused TASK-M2-007 dataset-profiler tests: 15 passed.
- Combined M2-007/M2-006/M2-003 runtime focused/regression slice: 99 passed.
- M2-002 contract/reference regressions: 24 passed.
- Runtime package tests: 351 passed.
- Package/API non-DB slice: 853 passed, 16 intentional deselections,
  2 existing deprecation warnings.
- PostgreSQL persistence integration: 2 passed.
- Runtime/DAG PostgreSQL integration: 6 passed.
- PostgreSQL provider integration: 1 passed.
- API integration: 6 passed, 2 existing deprecation warnings.
- VS-M1 integration: final rerun 6 passed, 2 existing deprecation warnings.
- Acceptance: final rerun 14 passed, 2 existing deprecation warnings.
- Full pytest: 1343 passed, 2 existing deprecation warnings.

Docker/transient result:

- PostgreSQL was started from the repository Docker Compose file and reached a
  healthy state before DB-backed slices.
- An initial concurrent run of VS-M1 and acceptance observed PostgreSQL
  connection-refused failures after the container was stopped during DB
  lifecycle cleanup. The failure evidence was preserved.
- The service was inspected, restarted, and verified healthy.
- Affected DB-backed slices were rerun serially and passed cleanly.

## Downstream Status

After this implementation, TASK-M2-007 is implemented/tested locally but still
awaits independent validation/freeze, integration, publication, and exact-SHA
remote-CI verification.

TASK-M2-009 remains blocked until TASK-M2-004, TASK-M2-005, TASK-M2-007, and
TASK-M2-008 satisfy the frozen lifecycle prerequisites.
