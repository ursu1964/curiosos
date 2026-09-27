---
id: M2-CONTRACT-DELTA
title: M2 Contract Delta
lifecycle: FROZEN
artifact_type: contract_delta
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Contract Delta

## Frozen Reuse Decisions

| Existing contract | M2 decision |
| --- | --- |
| `ArtifactReference` | Reuse for datasets. `kind=dataset`, `media_type=text/csv`, `integrity=sha256`, provider-neutral locator, and producer/provenance semantics exactly fit M2 dataset references. |
| `EvidenceReference` | Reuse for intake, profiling, and verification evidence. |
| `VerificationReference` / verification records | Reuse for verification-gated findings. |
| `WorkItem` | Reuse as the canonical unit of DataLab work. |
| `Result` | Reuse for profiler and DataLab runtime outcomes. |
| `Capability` / `CapabilityRequirement` | Reuse for `dataset_profiling`. |
| `AgentDefinition` / `AgentInstance` | Reuse for DataLab profiling agent assignment. |
| `ObjectReference` | Reuse for dataset/run/result/work/agent/evidence/verification references. |

No `DatasetReference` contract is introduced in M2. A dataset is represented
canonically as `ArtifactReference(kind=dataset)`. The `locator` is an opaque
Curios-generated staged locator or historical provider-neutral reference. It
is not a client path, filesystem path, URI, object-store key, or permission
grant.

## Frozen Contract Ownership

| Contract | Owner | Rationale |
| --- | --- | --- |
| `DataLabAnalysisRequest` | `curios_contracts` | Cross-package canonical request passed through API, decomposition, persistence, runner, and web read models. |
| `DatasetProfile` | `curios_contracts` | Canonical profiler output consumed by result, verification, API, web, and acceptance. |
| `DataLabFinding` | `curios_contracts` | Canonical finding value displayed and verified across package boundaries. |
| `DataLabAnalysisResult` | `curios_contracts` | Canonical result envelope for profile, findings, evidence, and verification references. |
| `DataLabRunState` | `curios_runtime` | DataLab aggregate lifecycle vocabulary for one bounded run; not a persistence-owned semantic. |
| `DataLabRunRecord` | `curios_runtime` | Runtime/domain aggregate record for one DataLab run; API read models and repositories consume this runtime record while persistence stores only durable representations. |

`curios_persistence` owns only persistence record kinds, storage tables,
schema migrations, transaction primitives, payload hash/version mechanics, and
bounded persistence errors. It does not define DataLab lifecycle semantics.

## Frozen Contract Shapes

### DataLabAnalysisRequest

- Purpose: recorded analytical objective over one accepted dataset artifact.
- Identity: `DataLabAnalysisId`.
- State: inert submitted/requested fact, not execution state.
- Serialization: deterministic JSON-compatible object.
- Required fields: `analysis_id`, `dataset_ref`,
  `dataset_integrity_sha256`, `objective`, `analysis_kind`,
  `created_at`, and `correlation_id`.
- Optional fields: `principal_ref`, `trace_id`, and bounded
  `constraints`.
- Enum values: `analysis_kind=PROFILE_DATASET` only.
- Collection limits: maximum 10 constraint entries; keys and values each
  maximum 128 Unicode scalar values.
- Deterministic ordering: constraint entries serialize sorted by key.
- Invariants: exactly one primary `ArtifactReference(kind=dataset)`,
  `media_type=text/csv`, SHA-256 integrity matches `dataset_integrity_sha256`,
  objective is non-empty and at most 1,000 Unicode scalar values, and
  unsupported analysis kind fails boundedly.

### DatasetProfile

- Purpose: deterministic structural summary of accepted CSV bytes.
- Identity: embedded value inside `DataLabAnalysisResult`; no separate global
  identifier.
- State: immutable result value.
- Serialization: deterministic JSON-compatible object.
- Required fields: `dataset_ref`, `dataset_integrity_sha256`, `row_count`,
  `column_count`, ordered `columns`, and ordered `warnings`.
- Column profile fields: `name`, `index`, `inferred_type`,
  `missing_count`, `non_missing_count`, `distinct_count`.
- Optional numeric fields: `minimum`, `maximum`, `mean` only for columns
  inferred as `INTEGER` or `DECIMAL`.
- Enum values: `inferred_type=STRING|INTEGER|DECIMAL|BOOLEAN|EMPTY|MIXED`.
- Collection limits: maximum 100 column profiles and 100 warnings.
- Deterministic ordering: columns sort by CSV column index; warnings sort by
  stable warning code then column index.
- Invariants: counts are non-negative, `missing_count + non_missing_count`
  equals `row_count` for each column, and all values bind to the same dataset
  reference and SHA-256.

### DataLabFinding

- Purpose: bounded analytical finding/warning derived from profiling.
- Identity: stable `finding_key` unique within a
  `DataLabAnalysisResult`.
- State: immutable result value.
- Serialization: deterministic JSON-compatible object.
- Required fields: `finding_key`, `category`, `severity`, `summary`,
  `dataset_ref`, `dataset_integrity_sha256`, and `provenance_path`.
- Optional fields: `evidence_refs`.
- Enum values: `category=SCHEMA|COMPLETENESS|TYPE_MIX|DISTRIBUTION|QUALITY`;
  `severity=INFO|WARNING|ERROR`.
- Collection limits: maximum 5 evidence references per finding and maximum
  500 Unicode scalar values for `summary`.
- Deterministic ordering: sort by severity rank `ERROR`, `WARNING`, `INFO`,
  then category, then finding key.
- Invariants: no raw unbounded cell dumps, no secret-shaped values, and every
  finding binds to the same dataset hash as the enclosing result.

### DataLabAnalysisResult

- Purpose: profile plus findings plus evidence/provenance after execution.
- Identity: `DataLabResultId`.
- State: immutable result value; aggregate lifecycle lives in
  `DataLabRunRecord`.
- Serialization: deterministic JSON-compatible object.
- Required fields: `result_id`, `run_id`, `analysis_id`, `work_ref`,
  `dataset_ref`, `dataset_integrity_sha256`, `profile`, ordered `findings`,
  ordered `warnings`, ordered `evidence_refs`, and `created_at`.
- Optional fields: `verification_ref`.
- Collection limits: maximum 50 findings, 100 warnings, and 20 result-level
  evidence references.
- Deterministic ordering: findings, warnings, and evidence references use
  their frozen ordering rules.
- Invariants: approved/verified result must be evidence-bound to the same
  dataset/run/work identity.

### DataLabRunRecord

- Purpose: durable recorded truth for one DataLab run identity.
- Identity: `DataLabRunId`.
- State: `DataLabRunState`, separate from `WorkItemState`.
- Serialization: deterministic JSON-compatible runtime record payload.
- Required fields: `run_id`, `analysis_ref`, `request_snapshot`,
  `dataset_ref`, `dataset_integrity_sha256`, `work_dag_ref`, `state`,
  `created_at`, and `updated_at`.
- Optional fields: `active_work_ref`, `agent_instance_ref`,
  `routing_decision_ref`, `result_ref`, `verification_ref`,
  `failure_code`, and bounded `failure_summary`.
- Enum values: `state=CREATED|READY|RUNNING|AWAITING_VERIFICATION|COMPLETED|FAILED`.
- Collection limits: no embedded raw dataset bytes; embedded request/result
  snapshots obey their own limits.
- Deterministic ordering: record reconstruction returns references and
  snapshots in canonical serialization order.
- Invariants: no raw dataset bytes in the persistence payload by default;
  references must preserve same-run identity; terminal states are
  `COMPLETED` and `FAILED`.

Legal transitions:

- `CREATED -> READY`
- `READY -> RUNNING`
- `READY -> FAILED`
- `RUNNING -> AWAITING_VERIFICATION`
- `RUNNING -> FAILED`
- `AWAITING_VERIFICATION -> COMPLETED`
- `AWAITING_VERIFICATION -> FAILED`

Same-state replay with the same recorded evidence is idempotent. DataLab uses
the M1 verification attempt vocabulary without synonyms:

- `PASSED -> APPROVED -> COMPLETED`;
- `FAILED -> REJECTED -> FAILED`;
- `INCONCLUSIVE -> DEFERRED -> AWAITING_VERIFICATION`;
- `NOT_EVALUATED -> DEFERRED -> AWAITING_VERIFICATION`;
- zero attempts -> `DEFERRED -> AWAITING_VERIFICATION`.

The first terminal `PASSED` or `FAILED` attempt determines terminal state and
cannot be overridden. While the run remains `AWAITING_VERIFICATION`, a caller
may submit another explicit bounded verification request; no automatic retry
loop is authorized.

## Persistence Record Kinds

M2 persistence planning freezes these new record kinds:

- `datalab_analysis_request`
- `datalab_run`
- `datalab_analysis_result`

`DatasetProfile` and `DataLabFinding` are embedded in
`datalab_analysis_result`. Dataset artifact metadata/reference uses the
existing artifact/reference persistence boundary. Evidence, verification, and
events reuse existing stores and are referenced from DataLab records rather
than duplicated.

The persisted representation must reconstruct
`curios_runtime.DataLabRunRecord` exactly or fail boundedly with a corrupt or
conflicting record error. `curios_persistence` may store the JSON-compatible
payload and verify payload hashes, but `curios_runtime` owns validation,
lifecycle transitions, and canonical reconstruction semantics.

## Safe Validation Errors

All M2 contracts fail invalid shapes through bounded contract errors. Contract
errors must not expose raw dataset cells, raw upload body, provider/native
parser exceptions, filesystem paths, stack traces, secrets, or framework
diagnostics.

## Explicit Non-Contracts

M2 must not create:

- `DatasetReference`;
- a duplicate `WorkItem`;
- a duplicate `Result`;
- a duplicate evidence or verification reference;
- a duplicate capability or agent model;
- a model generation contract;
- a generic tool contract;
- a project/session platform contract.

## Contract Acceptance

TASK-M2-002 passes only if contract tests prove deterministic serialization,
bounded validation, reference integrity, no duplication of BOOT/M1 primitives,
and no hidden provider/framework authority.
