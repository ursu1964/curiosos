---
id: TASK-M2-002-EVIDENCE
title: TASK-M2-002 DataLab Dataset and Analysis Contracts Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M2-002
milestone_id: M2
date: 2026-09-28
---

# TASK-M2-002 Evidence

## Objective

Implement the minimal frozen canonical DataLab dataset and analysis contracts in
`curios_contracts`:

- `DataLabAnalysisRequest`
- `DatasetProfile`
- `DataLabFinding`
- `DataLabAnalysisResult`

TASK-M2-002 does not implement CSV intake, dataset staging, SHA-256
calculation, profiler execution, DataLab run records, persistence,
schema/migration, API routes, web UI, model/provider execution, scheduler
behavior, or TASK-M2-003+ work.

## Starting Baseline

`1780e16f68d2e4440a2974539cd16384f4c42681`

M1 is `FROZEN / CLOSED / PUBLISHED / REMOTE-CI-VERIFIED`.

M2 planning is `VALIDATED / FROZEN / PUBLISHED / REMOTE-CI-VERIFIED`.

TASK-M2-001 is `INTEGRATED / VALIDATED / FROZEN / PUBLISHED /
REMOTE-CI-VERIFIED`.

TASK-M2-002 is DAG-derived `READY / AUTHORIZED`.

## Contract Inventory

Implemented in `packages/python/curios_contracts/src/curios_contracts/datalab.py`:

- `DataLabAnalysisRequest`
- `DatasetProfile`
- `DataLabFinding`
- `DataLabAnalysisResult`

Supporting value objects and enums are contract-internal shape components:

- `DatasetColumnProfile`
- `DatasetProfileWarning`
- `DataLabAnalysisKind`
- `DatasetPrimitiveType`
- `DataLabFindingCategory`
- `DataLabFindingSeverity`

Typed identifiers added to `curios_contracts.identifiers`:

- `DataLabAnalysisId`
- `DataLabRunId`
- `DataLabResultId`

No `DatasetReference` contract was introduced.

## Reused Frozen Primitives

The DataLab contracts reuse:

- `ArtifactReference(kind=dataset)` for dataset identity and locator metadata.
- `IntegrityDescriptor(algorithm=sha256)` for dataset integrity.
- `ObjectReference` for work and principal references.
- `EvidenceReference` / `EvidenceId` for evidence bindings.
- `VerificationReference` for optional verification binding.
- `CorrelationId`, `TraceId`, and `UtcTimestamp` for observability and time.

## Invariants

Dataset artifacts must be:

- `kind=dataset`
- `media_type=text/csv`
- bound to lowercase 64-character SHA-256 integrity
- producer/provenance-bearing
- provider-neutral references, not filesystem authority

`DataLabAnalysisRequest` enforces:

- `analysis_kind=PROFILE_DATASET`
- bounded non-empty objective
- max 10 deterministic constraints
- dataset artifact/hash consistency

`DatasetProfile` enforces:

- dataset artifact/hash consistency
- non-negative row/column counts
- max 100 columns
- column count matching the ordered column profile collection
- per-column missing/non-missing count consistency
- deterministic column and warning ordering

`DataLabFinding` enforces:

- frozen category/severity vocabulary
- bounded summary
- max 5 evidence references
- unique evidence IDs
- dataset artifact/hash binding
- deterministic finding ordering key

`DataLabAnalysisResult` enforces:

- result/run/analysis/work identity fields
- work reference kind is `work`
- dataset/profile/finding artifact and hash consistency
- max 50 findings
- max 100 warnings
- max 20 result-level evidence references
- duplicate finding and evidence rejection
- deterministic finding, warning, and evidence ordering

## Serialization

Every DataLab contract implements repository-standard JSON-compatible
serialization and reconstruction:

`record -> JSON-compatible object -> reconstruction -> equivalent record`

The implementation uses frozen dataclasses and repository contract primitives.
It does not use Pydantic, FastAPI, SQLAlchemy, provider SDK records, or
framework-native models.

## Safe Errors

Validation errors are bounded `TypeError` or `ValueError` messages. They do not
include raw dataset contents, filesystem paths, provider objects, traceback
details, framework diagnostics, or secret-shaped values.

Secret-shaped text is rejected from bounded human text fields that could carry
user-provided prose.

## Guard Compatibility

TASK-M2-001 guardrails accept the now-real authorized future surfaces:

- `DataLabAnalysisRequest` in `curios_contracts`
- `DatasetProfile` in `curios_contracts`
- `DataLabFinding` in `curios_contracts`
- `DataLabAnalysisResult` in `curios_contracts`

The guards still reject:

- `DatasetReference`
- DataLab run records under persistence ownership
- forbidden DataLab filesystem/network/model/execution authority
- unauthorized API/web/M3+ surfaces

## Authority Inventory

TASK-M2-002 adds pure contracts only.

No authority was added for:

- filesystem access
- network access
- subprocess or shell execution
- dynamic import or code execution
- provider/model execution
- database or persistence behavior
- scheduling, retry, or cancellation behavior
- API routes
- web/UI behavior

## Adversarial Coverage

Focused contract tests cover:

- positive construction
- JSON-compatible round-trip reconstruction
- deterministic ordering from reversed input
- wrong artifact kind
- missing dataset integrity
- hash mismatch
- request/profile/result dataset mismatch
- duplicate finding identity
- duplicate evidence identity
- objective and collection bounds
- malformed JSON-compatible payloads
- safe error behavior for secret-shaped prose
- framework/provider neutrality

## Verification

Final verification was performed after implementation:

- `uv lock --check`: PASS.
- `uv sync --locked --all-groups --all-packages`: PASS.
- `pnpm install --frozen-lockfile`: PASS.
- Docker Compose config: PASS.
- `ruff format --check .`: PASS, 306 files already formatted.
- `ruff check .`: PASS.
- `mypy apps/api/src packages/python/*/src`: PASS, 71 source files.
- `pnpm check`: PASS.
- `pnpm --dir apps/web test`: PASS, 26 tests.
- `pnpm --dir apps/web typecheck`: PASS.
- `pnpm --dir apps/web build`: PASS.
- `uv run pytest tests/contract tests/schema -q`: PASS, 16 tests.
- `uv run pytest tests/architecture -q`: PASS, 45 tests.
- `uv run pytest tests/security -q`: PASS, 382 tests, 2 existing
  FastAPI/Starlette deprecation warnings.
- TASK-M2-002 focused contract tests: PASS, 8 tests.
- `uv run pytest packages/python/curios_contracts/tests -q`: PASS, 129 tests.
- M1 package/API gate: PASS, 626 tests, 9 intentional deselections, 2 existing
  FastAPI/Starlette deprecation warnings.
- M1 PostgreSQL gate: PASS, 4 tests.
- VS-M1 integration: PASS, 6 tests, 2 existing FastAPI/Starlette deprecation
  warnings.
- Acceptance gate: initial attempt hit a local PostgreSQL lifecycle transient
  (`database system is shutting down`). After restarting the local compose
  PostgreSQL service and waiting for `pg_isready`, the serial rerun passed with
  14 tests and 2 existing FastAPI/Starlette deprecation warnings.
- Full pytest: PASS, 1214 tests, 2 existing FastAPI/Starlette deprecation
  warnings.

## Dependency / Schema Result

No dependency, lockfile, database schema, migration, API, web, infrastructure,
or CI workflow changes were introduced.

## 1.txt Guard

`1.txt` remains untracked and untouched.

Expected SHA-256:

`d3db09d30c2b8ee24cad0339c140f7256eac3ea89f1bc9eafa9e86c55bb38b88`

## Downstream Status

TASK-M2-002 is `IMPLEMENTED / TESTED` locally after implementation
verification.

TASK-M2-003 and later remain blocked until TASK-M2-002 independent
validation/freeze and integration/publication lifecycle gates pass.
