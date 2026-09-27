---
id: POST-M1-003-VALIDATION-EVIDENCE
title: POST-M1-003 M2 Planning Validation Evidence
lifecycle: VALIDATED
artifact_type: readiness_validation_evidence
authority: program_planning
task_id: M2-READINESS
milestone_id: M2
date: 2026-09-27
---

# POST-M1-003 Validation Evidence

## Decision

M2 PLANNING VALIDATION: PASS

Validated baseline:

`139274bc146db743e79411fbef04992dd6920839`

M1 state:

`FROZEN / CLOSED / PUBLISHED / REMOTE-CI-VERIFIED`

## Authority Reviewed

- Frozen M1 final freeze record and status ledger.
- Frozen BOOT, M0, and M1 contracts and architecture boundaries.
- M2 planning package produced by POST-M1-002.
- POST-M1-002 Correction 1 planning updates.
- POST-M1-002 Correction 2 planning updates.
- Historical `1.txt` only as read-only traceability input.

## Validation History

| Validation step | Result |
| --- | --- |
| POST-M1-003 attempt 1 | FAILED: broad planning ambiguity. |
| POST-M1-002 Correction 1 | COMPLETE: froze dataset, contract, topology, profiler, persistence, API, web, traceability, and readiness semantics. |
| POST-M1-003 attempt 2 | FAILED: four remaining blockers. |
| POST-M1-002 Correction 2 | COMPLETE: corrected run-record ownership, API failure/status semantics, verification mapping, and web stale-response provenance. |
| POST-M1-003 final re-validation | PASSED. |

Historical failed validation attempts remain part of the planning record and
are not erased.

## Validated Objective

M2 is the DataLab Analysis Vertical Slice:

```text
bounded local CSV/tabular input
  -> governed dataset artifact/reference
  -> deterministic analysis decomposition
  -> M1 Work DAG
  -> dataset_profiling capability
  -> active bounded agent
  -> deterministic in-process profiler
  -> profile/findings/evidence
  -> M1 verification
  -> durable DataLab recorded truth
  -> bounded API/web presentation
```

No live model, chat, embeddings, cloud model, arbitrary tool execution,
subprocess, shell, plugin execution, network dataset fetch, scheduler,
autonomous agent loop, release, deployment, or tag authority is introduced.

## Freeze Findings

| Area | Result |
| --- | --- |
| Filename/path semantics | PASS: `X-Curios-Dataset-Filename` is metadata only, NFC-normalized, capped at 128 Unicode scalar values, and unsafe names are rejected. |
| Dataset lifetime | PASS: raw bytes are ephemeral staged input; durable truth stores metadata/reference/integrity; re-analysis after cleanup requires a new upload. |
| ArtifactReference reuse | PASS: `ArtifactReference(kind=dataset)` is reused; no `DatasetReference` is introduced. |
| Contract ownership | PASS: DataLab request/profile/finding/result are owned by `curios_contracts`; run state/record are owned by `curios_runtime`; persistence owns storage mechanics only. |
| Work and capability topology | PASS: `dataset_profile` and `dataset_profiling` are the only M2 work type and capability. |
| Agent semantics | PASS: M1 `AgentDefinition` and `AgentInstance` are reused; no autonomous loop or new agent state machine is authorized. |
| Tool/profiler seam | PASS: deterministic in-process profiler only, with bounded request/outcome, timeout, events, evidence, and safe errors. |
| Profiler semantics | PASS: row/column counts, deterministic primitive type inference, missing/non-missing counts, distinct counts, numeric min/max/mean for numeric columns, bounded warnings/findings. |
| Resource bounds | PASS: 1 MiB upload, 10,000 rows, 100 columns, 16 KiB cells, 1,000-character objectives, 5-second profiler timeout, 50 findings, 100 warnings, 20 result evidence refs, 5 finding evidence refs, 16 KiB event payload, 256 KiB M2 read response. |
| Persistence/run state | PASS: durable records and reconstruction semantics are specified; run states are `CREATED`, `READY`, `RUNNING`, `AWAITING_VERIFICATION`, `COMPLETED`, and `FAILED`. |
| Verification mapping | PASS: M1 verification vocabulary and completion decisions are reused exactly; first terminal attempt wins; deferred re-verification is explicit caller/API action only. |
| API inventory | PASS: exactly five DataLab endpoints are frozen, including raw `text/csv` upload and M1-013-style JSON transport handling. |
| Web provenance | PASS: dataset, analysis, run, and verification generations prevent stale overwrites and hybrid canonical truth. |
| Vertical slices | PASS: VS-M2-001 through VS-M2-006 each define positive/negative, deterministic, persistence, safe-error, authority, evidence, and PASS/FAIL criteria. |
| Task DAG | PASS: `M2-000A` and `M2-READINESS` are non-task planning nodes; TASK-M2-001 through TASK-M2-016 are the exact 16 M2 tasks; the graph is acyclic. |
| Traceability | PASS: each authoritative requirement maps to contract, component, task owner, VS slice, integration owner, acceptance, evidence, and CI owner. |
| Security authority | PASS: new authority is limited to bounded upload intake, filename metadata, ephemeral staging/read, profiler execution, result/evidence creation, persistence, API, and frontend boundary functions. |
| M1 non-regression | PASS: M2 extends frozen M1 boundaries without redefining M1 contracts, routing, runner, verification, persistence ownership, capability resolution, agent lifecycle, or frontend authority. |

## Protected Paths

Validation confirmed no M2 planning change under:

- `apps/`
- `packages/`
- `tests/`
- `.github/`
- `infrastructure/`
- manifests or lockfiles
- schemas or migrations

## Historical Input Guard

`1.txt` remains untracked historical input only.

Expected SHA-256:

`d3db09d30c2b8ee24cad0339c140f7256eac3ea89f1bc9eafa9e86c55bb38b88`

It is not staged, committed, moved, deleted, or promoted into direct
implementation authority.

## Mechanical Checks

- `git diff --check`: PASS.
- `git diff --cached --check`: PASS.
- M2 planning ambiguity search: PASS for implementation-critical terms.
- Protected-path review: PASS.

No product, test, CI, schema, migration, provider/model, dependency, release,
deployment, tag, or TASK-M2-001 implementation work was performed.

## Lifecycle Transition

- M2 planning: `VALIDATED, FROZEN`.
- M2-000A: `VALIDATED, FROZEN`.
- M2-READINESS: `VALIDATED, FROZEN`.
- TASK-M2-001: `READY`.
- TASK-M2-002 through TASK-M2-016: `BLOCKED`.

## First Executable Unit

`TASK-M2-001 - M2 Topology and Guardrail Transition`

TASK-M2-001 must branch from a baseline containing the M2 planning freeze.
No TASK-M2-002 or later implementation may start until its frozen DAG
prerequisites are implemented, tested, independently validated, frozen, and
integrated.
