---
id: TASK-M2-003-EVIDENCE
title: TASK-M2-003 Bounded Dataset Intake Boundary Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M2-003
milestone_id: M2
date: 2026-09-28
---

# TASK-M2-003 Evidence

## Objective

Implement the frozen bounded DataLab dataset-intake boundary:

```text
bounded CSV bytes plus filename metadata
 -> validated staged dataset
 -> ArtifactReference(kind=dataset) with SHA-256 integrity and provenance
```

TASK-M2-003 does not implement profiler execution, DataLab decomposition,
DataLab run records, persistence records, database schema, API routes, web UI,
capability or agent integration, provider/model execution, or TASK-M2-004+
work.

## Starting Baseline

`7753f220f0da6949e4e8be42ae8f1831d7e4b62b`

TASK-M2-001 is `INTEGRATED / VALIDATED / FROZEN / PUBLISHED /
REMOTE-CI-VERIFIED`.

TASK-M2-002 is `INTEGRATED / VALIDATED / FROZEN / PUBLISHED /
REMOTE-CI-VERIFIED`.

TASK-M2-003 is DAG-derived `READY / AUTHORIZED`.

## Intake Seam

Implemented in
`packages/python/curios_runtime/src/curios_runtime/datalab_dataset_intake.py`:

- `LocalDataLabDatasetStagingStore`
- `DataLabDatasetIntakeResult`
- `DataLabDatasetIntakeError`
- `DataLabDatasetIntakeErrorCode`
- `normalize_datalab_dataset_filename`

The public runtime export surface was updated through
`packages/python/curios_runtime/src/curios_runtime/__init__.py`.

## Frozen Bounds

Implemented exact TASK-M2-003 bounds:

| Bound | Result |
| --- | --- |
| Media | `text/csv` only. |
| Encoding | UTF-8 with optional BOM stripped before parsing. |
| Delimiter | Comma only; no dialect detection. |
| Upload size | Maximum 1 MiB. |
| Data rows | Maximum 10,000, excluding header. |
| Columns | Maximum 100. |
| Cell size | Maximum 16 KiB after UTF-8 decoding. |
| Header | Required. |
| Empty dataset | Rejected when no header or no data row exists. |
| Duplicate columns | Rejected by exact header-cell equality. |

No analytical type inference or `DatasetProfile` production exists in this
task.

## Filename Rule

`X-Curios-Dataset-Filename` semantics are implemented as filename metadata:

- NFC normalization.
- Maximum 128 Unicode scalar values.
- Reject empty names, `.`, `..`, `/`, `\`, absolute-looking names,
  drive-qualified names, NUL, ASCII/C0/C1 controls, and visibly
  credential-like key/value text.
- The normalized filename is returned as metadata only.
- The normalized filename is never used as the staged filesystem path or
  locator.

## Integrity And ArtifactReference

The implementation computes SHA-256 over the exact accepted upload bytes,
including any UTF-8 BOM. The parser receives BOM-stripped UTF-8 text, but
integrity remains tied to the supplied byte representation.

Accepted intake returns `ArtifactReference(kind=dataset)` with:

- `media_type=text/csv`
- `IntegrityDescriptor(algorithm=sha256)`
- generated opaque staged locator
- caller-supplied producer/provenance reference

No `DatasetReference` or duplicate hash abstraction was introduced.

## Staging And Cleanup

`LocalDataLabDatasetStagingStore` stages bytes only under a server-selected
root and a filename derived from the generated `ArtifactId`. The staged locator
uses the opaque `curios-datalab-staged:` prefix and is not derived from client
metadata.

The staging seam supports:

- staged read by generated locator;
- idempotent cleanup;
- bounded failure for missing or malformed locators;
- no deletion outside the staging root;
- replay truth that metadata can survive cleanup while raw bytes do not.

After cleanup, staged-byte reads fail with `DATALAB_DATASET_UNAVAILABLE`.
Re-analysis therefore requires a new upload.

## Safe Errors

Bounded domain error codes implemented:

- `DATALAB_UNSUPPORTED_MEDIA`
- `DATALAB_INVALID_FILENAME`
- `DATALAB_EMPTY_DATASET`
- `DATALAB_UPLOAD_TOO_LARGE`
- `DATALAB_INVALID_ENCODING`
- `DATALAB_MALFORMED_CSV`
- `DATALAB_DUPLICATE_COLUMNS`
- `DATALAB_TOO_MANY_COLUMNS`
- `DATALAB_TOO_MANY_ROWS`
- `DATALAB_CELL_TOO_LARGE`
- `DATALAB_INTEGRITY_FAILURE`
- `DATALAB_STAGING_FAILURE`
- `DATALAB_DATASET_UNAVAILABLE`

Errors use fixed bounded messages. Tests cover that raw CSV values, unsafe
filenames, parser diagnostics, and staged paths are not echoed.

## Authority Inventory

Authorized authority:

- bounded supplied byte intake;
- UTF-8 decoding;
- standard-library CSV structural parsing;
- SHA-256 calculation;
- bounded local staging under a server-owned root;
- staged read and cleanup by generated locator;
- `ArtifactReference` construction.

Absent authority:

- network or remote URL retrieval;
- provider/model invocation;
- subprocess, shell, dynamic code, plugin loading;
- arbitrary client filesystem path authority;
- database writes, persistence schema, migration;
- DataLab run lifecycle, scheduler, retry loop;
- API route or web UI behavior.

## Guard Compatibility

M2-001 guard compatibility was preserved:

- DataLab runtime files have no forbidden execution/model/network imports or
  calls.
- Client filename metadata is structurally rejected as filesystem authority in
  the new architecture guard.
- The API adapter guard remains unchanged.
- `DatasetReference` remains absent.
- M3+ package roots remain rejected.

M2-002 contract compatibility was preserved by producing canonical
`ArtifactReference(kind=dataset)` with `text/csv`, SHA-256 integrity, and
producer/provenance.

## Adversarial Results

Focused TASK-M2-003 tests cover:

- minimal valid CSV;
- UTF-8 and UTF-8 BOM;
- exact upload, row, column, and cell bounds;
- invalid UTF-8;
- malformed quotes;
- embedded newline shape mismatch;
- empty body and header-only CSV;
- duplicate columns;
- unsafe filename metadata including traversal, absolute path, drive-qualified
  path, separators, NUL/control characters, over-length names, and
  credential-like metadata;
- CSV containing credential-like values without error leakage;
- generated staged read;
- idempotent cleanup;
- invalid locator cleanup without outside-file deletion.

## Verification

Verification results:

- `uv lock --check`: PASS.
- `uv sync --locked --all-groups --all-packages`: PASS.
- `pnpm install --frozen-lockfile`: PASS.
- Docker Compose config: PASS.
- Ruff format: PASS, 311 files already formatted.
- Ruff check: PASS.
- mypy: PASS, 72 source files.
- `pnpm check`: PASS.
- Web tests: PASS, 26 tests.
- Web typecheck/build: PASS.
- Contract/schema: PASS, 16 tests.
- Architecture: PASS, 47 tests.
- Security: PASS, 382 tests, 2 warnings.
- TASK-M2-003 focused runtime tests: PASS, 28 tests.
- Runtime package tests excluding integration: PASS, 272 passed, 8 intentional
  deselections.
- M2-002 contract/reference regressions: PASS, 24 tests.
- M1 package/API gate: PASS, 682 passed, 9 intentional deselections,
  2 warnings.
- M1 PostgreSQL gate: PASS, 4 tests.
- M1 vertical slice: PASS, 6 tests, 2 warnings.
- Acceptance: initial run hit a PostgreSQL lifecycle transient while the
  database was shutting down; after service recovery, PASS, 14 tests,
  2 warnings.
- Full pytest: PASS, 1272 tests, 2 warnings.
- Diff whitespace checks: PASS.

The warnings are the existing FastAPI/Starlette TestClient deprecation
warnings.

## Dependency And Schema Result

No third-party dependency, workspace dependency, lockfile, database schema,
migration, API, web, provider/model, or CI workflow change was introduced.

## Downstream Status

TASK-M2-007 depends on TASK-M2-003 and TASK-M2-006. After this implementation:

- TASK-M2-003 side: implemented/tested locally, awaiting independent
  validation/freeze and integration lifecycle.
- TASK-M2-006 side: not implemented in this task.

TASK-M2-007 remains blocked. TASK-M2-004, TASK-M2-005, TASK-M2-006, and
TASK-M2-008 were not started.
