---
id: TASK-M2-002-VALIDATION-EVIDENCE
title: TASK-M2-002 DataLab Dataset and Analysis Contracts Validation Evidence
lifecycle: FROZEN
artifact_type: task_validation_evidence
task_id: TASK-M2-002
milestone_id: M2
date: 2026-09-28
---

# TASK-M2-002 Validation Evidence

## Scope

This evidence validates TASK-M2-002 after Correction 1.

- Published baseline: `1780e16f68d2e4440a2974539cd16384f4c42681`
- Implementation: `f8a9ad6c76715fe410bcab89e3a1d2451294cc7e`
- Correction 1: `db7187ecfddcffc174ab44cf0c3ac822b80e6291`

TASK-M2-002 remains limited to canonical `curios_contracts` records and
reference integration. It does not implement DataLab runtime records, CSV
intake, staging, profiling, persistence, database schema, API, web UI, or
provider/model execution.

## Initial Validation Failure

The first independent validation failed because the new canonical typed IDs
could not be converted into the existing generic object-reference mechanism:

- `ObjectReference.from_id(DataLabAnalysisId.generate())`
- `ObjectReference.from_id(DataLabRunId.generate())`
- `ObjectReference.from_id(DataLabResultId.generate())`

The failure was classified as a TASK-M2-002 contract completeness defect.

## Correction 1 Result

Correction 1 integrates the DataLab typed IDs into the existing
`ObjectReference` mechanism:

| Typed ID | ReferenceKind | Serialized kind |
| --- | --- | --- |
| `DataLabAnalysisId` | `ReferenceKind.DATALAB_ANALYSIS` | `datalab_analysis` |
| `DataLabRunId` | `ReferenceKind.DATALAB_RUN` | `datalab_run` |
| `DataLabResultId` | `ReferenceKind.DATALAB_RESULT` | `datalab_result` |

The inverse path preserves typed identity:

```text
typed ID
 -> ObjectReference.from_id(...)
 -> to_json_compatible()
 -> ObjectReference.from_json_compatible(...)
 -> same kind and typed ID class
```

Wrong-kind combinations among analysis, run, result, and existing M1/BOOT
kinds are rejected boundedly.

No `DatasetReference`, `DataLabReference`, `DataLabAnalysisReference`,
`DataLabRunReference`, or `DataLabResultReference` abstraction exists.
`ObjectReference` remains the single generic kind/ref-id abstraction.

## Contract Inventory

Validated headline contracts:

- `DataLabAnalysisRequest`
- `DatasetProfile`
- `DataLabFinding`
- `DataLabAnalysisResult`

Validated supporting types authorized by frozen contract shape or derived
necessity:

- `DataLabAnalysisId`
- `DataLabRunId`
- `DataLabResultId`
- `DataLabAnalysisKind`
- `DatasetColumnProfile`
- `DatasetPrimitiveType`
- `DatasetProfileWarning`
- `DataLabFindingCategory`
- `DataLabFindingSeverity`

No unauthorized public DataLab contract expansion was found.

## Reference And Integrity Audit

DataLab contracts reuse `ArtifactReference(kind=dataset)` and
`IntegrityDescriptor` for dataset identity and integrity. Validation confirmed:

- dataset references require `kind=dataset`;
- dataset references require `media_type=text/csv`;
- dataset references require SHA-256 integrity;
- digest format is canonical lowercase SHA-256 hex;
- producer/provenance reference is required;
- locator remains provider-neutral metadata, not filesystem authority;
- no duplicate dataset/hash source of truth is introduced.

Cross-record mismatches are rejected for request/profile/result dataset
identity, profile/result integrity, and finding/result dataset bindings.

## Contract Results

`DataLabAnalysisRequest` validation covers identity, dataset binding, analysis
kind `PROFILE_DATASET`, bounded objective, bounded constraints, optional
principal/trace context, deterministic constraint ordering, serialization, and
malformed reconstruction.

`DatasetProfile` validation covers dataset binding, row and column counts,
ordered column profiles, warning ordering, maximum 100 columns, maximum 100
warnings, duplicate column rejection, nonnegative counts, and
`missing_count + non_missing_count == row_count`.

`DatasetColumnProfile` validation covers name/index identity, primitive type,
missing/non-missing/distinct counts, numeric metric constraints, finite numeric
values, duplicate name/index rejection at profile level, and malformed enum
rejection.

`DataLabFinding` validation covers finding key identity, exact category and
severity vocabularies, bounded summary, dataset/hash binding, bounded
provenance path, maximum five evidence references, duplicate evidence-ID
rejection, deterministic ordering, and bounded reconstruction failures.

`DataLabAnalysisResult` validation covers result/run/analysis typed identity,
work reference kind, dataset/hash/profile/finding consistency, maximum 50
findings, maximum 100 warnings, maximum 20 result evidence references,
optional verification reference representation, deterministic ordering, and
serialization round trip.

TASK-M2-002 only represents evidence and verification references. It does not
perform verification, completion decisions, run-state transitions, persistence,
or retry behavior.

## Determinism And Safety

Validation confirmed:

- deterministic JSON-compatible serialization and reconstruction for every
  new public contract/value object;
- canonical sorting for constraints, columns, warnings, findings, and evidence
  references where frozen ordering requires it;
- immutable canonical records are protected from caller collection mutation;
- malformed JSON-compatible payloads fail boundedly;
- public validation errors do not expose raw dataset values, filesystem paths,
  provider diagnostics, framework internals, arbitrary object reprs, or
  sensitive-looking input values.

The DataLab contract module remains framework/provider neutral. It does not
import or depend on Pydantic, FastAPI, Starlette, SQLAlchemy, provider SDKs,
network clients, filesystem execution, subprocess, shell, dynamic code, or
database implementation.

## M2-001 Guard Compatibility

The now-real canonical DataLab contracts in `curios_contracts` pass the
TASK-M2-001 ownership and authority guards without weakening those guards.
The guards still reject wrong contract owners, `DatasetReference`,
persistence-owned run semantics, API filesystem/persistence/profiler bypass,
model/network authority, generic frontend escape hatches, and M3+ expansion.

## Validation Regressions

The validation regression file
`packages/python/curios_contracts/tests/test_task_m2_002_validation_regressions.py`
preserves:

- original DataLab ID to `ObjectReference` reproduction;
- inverse DataLab reference reconstruction;
- wrong-kind DataLab reference rejection;
- wrong dataset kind/media/integrity cases;
- cross-record dataset and integrity mismatches;
- duplicate columns, findings, and evidence IDs;
- over-bound constraints;
- deterministic ordering;
- mutable input aliasing protection;
- malformed JSON-compatible reconstruction;
- safe bounded error behavior.

## Verification

Pre-record validation results:

- `uv lock --check`: PASS.
- `uv sync --locked --all-groups --all-packages`: PASS.
- `pnpm install --frozen-lockfile`: PASS.
- Docker Compose config: PASS.
- `ruff format --check .`: PASS, 307 files.
- `ruff check .`: PASS.
- `mypy apps/api/src packages/python/*/src`: PASS, 71 source files.
- `pnpm check`: PASS.
- Web tests: PASS, 26 tests.
- Web typecheck: PASS.
- Web build: PASS.
- Contract/schema: PASS, 16 tests.
- Architecture: PASS, 45 tests.
- Security: PASS, 382 tests, 2 existing FastAPI/Starlette warnings.
- Focused TASK-M2-002 reference/contract/validation regressions: PASS, 40 tests.
- `packages/python/curios_contracts/tests`: PASS, 157 tests.
- Package-local Python tests: PASS, 402 tests, 2 existing FastAPI/Starlette warnings.
- M0 runtime/persistence/policy package slice: PASS, 287 tests, 10 deselections.
- M1 package/API slice: PASS, 654 tests, 9 intentional deselections, 2 existing warnings.
- API integration: PASS, 6 tests, 2 existing warnings.
- PostgreSQL provider integration: PASS, 1 test.
- M0 PostgreSQL integration: PASS, 4 tests.
- M1 PostgreSQL integration: PASS, 4 tests.
- VS-M1 integration: PASS, 6 tests, 2 existing warnings.
- Acceptance: initial PostgreSQL lifecycle overlap failed during parallel local
  execution; after service recovery and serial rerun, PASS, 14 tests, 2 existing
  warnings.
- Full pytest: PASS, 1242 tests, 2 existing warnings.

Docker transient handling: local parallel execution caused PostgreSQL fast
shutdown during M0 vertical and acceptance slices. Service logs showed fast
shutdown/startup events. PostgreSQL was restarted, readiness was confirmed
with `pg_isready`, and the affected slices passed on serial rerun.

## Dependency And Schema Result

- Third-party dependency delta: none.
- Workspace dependency delta: none.
- `uv.lock`: unchanged.
- `pnpm-lock.yaml`: unchanged.
- Database schema delta: none.
- Migration delta: none.
- API/web implementation delta: none.

## Lifecycle Result

TASK-M2-002 is validated and frozen by this evidence. Downstream tasks remain
blocked until TASK-M2-002 completes the integration, publication, and exact-SHA
remote-CI lifecycle required by the frozen M2 DAG.
