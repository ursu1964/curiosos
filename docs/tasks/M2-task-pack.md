---
id: M2-TASK-PACK
title: M2 Atomic Task Pack
lifecycle: FROZEN
artifact_type: task_pack
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Atomic Task Pack

## Common Rules

- M2 tasks must preserve all frozen BOOT, M0, and M1 boundaries.
- M2 tasks use `TASK-M2-*`; do not create new M1 tasks.
- Each task may authorize only its explicit new surface.
- No task may mark itself `VALIDATED` or `FROZEN`; independent validation is
  required.
- M2 implements only the bounded DataLab Analysis Vertical Slice.
- M2 does not treat `1.txt` or unreconciled P1-P6 material as direct
  implementation authority.
- M2 does not implement chat, LLM generation, embeddings, cloud models,
  generalized tools, subprocess execution, autonomous agents, memory, full
  projects, release, deployment, or tags.
- Every modifying task must update task evidence and the M2 ledger according
  to Build Pack conventions.
- Implementation tasks must not reinterpret POST-M1 frozen planning decisions:
  raw `text/csv` transport, filename rejection rules, ephemeral staging,
  `ArtifactReference(kind=dataset)`, canonical contract ownership, work type
  `dataset_profile`, capability `dataset_profiling`, fixed DataLab endpoints,
  and no-live-model/no-subprocess authority are fixed.

## Frozen Work And Capability Topology

| Token | Kind | Owner | Semantics |
| --- | --- | --- | --- |
| `dataset_profile` | WorkItem work type | DataLab decomposition/runtime | The only executable DataLab WorkItem type in M2. It profiles one accepted dataset through the deterministic in-process profiler. |
| `dataset_profiling` | Capability token | DataLab capability integration | Capability required to execute `dataset_profile` work. |

Dataset intake is API/preprocessing authority, not DAG work. M1 verification
remains a verification-loop operation, not a new DataLab WorkItem type.

## Frozen API Inventory

| Method | Path | Owner task |
| --- | --- | --- |
| `POST` | `/m2/datalab/datasets` | TASK-M2-010 |
| `POST` | `/m2/datalab/analyses` | TASK-M2-010 |
| `POST` | `/m2/datalab/runs/{run_id}/run-once` | TASK-M2-010 |
| `GET` | `/m2/datalab/runs/{run_id}` | TASK-M2-010 |
| `POST` | `/m2/datalab/runs/{run_id}/verification/complete` | TASK-M2-010 |

No generic file/action/tool/chat/model endpoint is authorized.

## Task Inventory

| Task | Title | Objective | Prerequisites | Primary Authorized Surfaces |
| --- | --- | --- | --- | --- |
| TASK-M2-001 | M2 Topology and Guardrail Transition | Authorize exact M2 DataLab package/test/doc surfaces without broadening M1. | M2 readiness validation | docs, architecture/security tests, repository metadata documenting allowed M2 roots |
| TASK-M2-002 | DataLab Dataset and Analysis Contracts | Add minimal DataLab request/profile/finding/result contracts while reusing BOOT/M1 primitives. | TASK-M2-001 | `packages/python/curios_contracts/**`, contract/schema tests, docs |
| TASK-M2-003 | Bounded Dataset Intake Boundary | Implement safe bounded CSV upload/intake, validation, metadata, integrity, and artifact reference creation. | TASK-M2-002 | DataLab intake package/module, API-adjacent helpers only if owned, tests, docs |
| TASK-M2-004 | Deterministic DataLab Decomposition | Decompose supported DataLab objectives into bounded analysis Work DAG proposals. | TASK-M2-002 | DataLab cognitive/decomposition package/module, tests, docs |
| TASK-M2-005 | DataLab Persistence Records | Persist DataLab run/result/evidence metadata without raw dataset persistence by default. | TASK-M2-002 | runtime repository, persistence storage modules, one DataLab migration, tests, docs |
| TASK-M2-006 | Deterministic Profiler Seam | Add Curios-owned in-process profiler request/outcome seam with explicit resource bounds. | TASK-M2-002 | DataLab profiler/runtime module, tests, docs |
| TASK-M2-007 | In-Process Dataset Profiler | Implement deterministic CSV profiler over authorized dataset bytes only. | TASK-M2-003, TASK-M2-006 | DataLab profiler implementation, tests, docs |
| TASK-M2-008 | DataLab Capability and Agent Integration | Register/use `dataset_profiling` capability and DataLab agent assignment over frozen contracts. | TASK-M2-002 | capability/runtime integration modules, tests, docs |
| TASK-M2-009 | DataLab Runner and Verification Binding | Bind DataLab decomposition, persistence, profiler, agent, runner, evidence, and verification. | TASK-M2-004, TASK-M2-005, TASK-M2-007, TASK-M2-008 | runtime integration module, tests, docs |
| TASK-M2-010 | DataLab API Endpoints | Expose bounded DataLab intake/run/read endpoints through FastAPI. | TASK-M2-009 | `apps/api/**`, API tests, docs |
| TASK-M2-011 | Focused DataLab Web Workspace | Add DataLab workspace over explicit web API-boundary functions. | TASK-M2-010 | `apps/web/**`, web tests, docs |
| TASK-M2-012 | M2 Vertical-Slice Integration Tests | Prove VS-M2-001 through VS-M2-006 across frozen boundaries. | TASK-M2-010, TASK-M2-011 | exact `tests/integration/**` files, docs |
| TASK-M2-013 | M2 CI Quality Gate Update | Extend quality gates for M2 package, persistence, integration, acceptance, security, and no-live-model checks. | TASK-M2-012 | `.github/workflows/quality-gates.yml`, security evidence |
| TASK-M2-014 | M2 Acceptance Suite | Add milestone-level acceptance tests for the DataLab vertical slice. | TASK-M2-013 | exact `tests/acceptance/**` files, docs |
| TASK-M2-015 | Independent M2 Verification Record | Independently verify complete M2 baseline. | TASK-M2-014 | docs/tasks, status ledger |
| TASK-M2-016 | Final M2 Freeze | Record final M2 freeze/status closure. | TASK-M2-015 | docs/program/milestones, docs/program/status-ledger, docs/tasks |

## Detailed Task Constraints

### TASK-M2-001

Objective: transition M2 topology, architecture, and security guardrails for
the exact DataLab planning scope.

Prohibited scope: product implementation, contracts, runtime behavior,
persistence schema, API routes, web UI, CI changes, model execution, tool
execution.

Acceptance: future M2 surfaces are represented as planned ownership only, and
M3+ or out-of-scope M2 surfaces remain blocked.

### TASK-M2-002

Objective: add minimum DataLab contracts without duplicating existing
canonical primitives.

Must reuse: `ArtifactReference`, `EvidenceReference`, `VerificationReference`,
`WorkItem`, `Result`, `Capability`, and `AgentInstance`.

Prohibited scope: file parsing, API behavior, persistence implementation,
profiler execution, UI behavior, model generation.

Acceptance: contracts serialize deterministically, reject invalid shapes, and
preserve dataset artifact identity/provenance.

### TASK-M2-003

Objective: implement bounded CSV intake for authorized upload bytes.

Required constraints: `text/csv`, UTF-8, comma delimiter, <= 1 MiB,
<= 10,000 data rows, <= 100 columns, <= 16 KiB per cell, header required,
duplicate columns rejected, empty datasets rejected, unsafe filenames bounded,
SHA-256 integrity recorded.

Filename rule: require `X-Curios-Dataset-Filename`; normalize to NFC, then
reject empty names, names longer than 128 Unicode scalar values, `/`, `\`,
`.`, `..`, absolute paths, drive-qualified paths, NUL, and ASCII/C0/C1
control characters. The client filename is metadata only and never becomes a
locator. CuriosOS generates the staged locator.

Lifetime rule: raw bytes are ephemeral staged input from accepted intake until
the owning run reaches `COMPLETED` or `FAILED`. After cleanup, re-analysis
requires a new upload.

Prohibited scope: arbitrary filesystem access, network fetch, raw dataset
persistence by default, analysis/profiling, model generation.

Acceptance: accepted datasets produce a governed artifact reference; invalid
datasets fail boundedly without leaking raw content or native parser errors.

### TASK-M2-004

Objective: create deterministic DataLab decomposition for supported profiling
objectives.

Supported objective family: `PROFILE_DATASET` only. Equivalent text accepted
by deterministic matching must map to this family without LLM interpretation.
Near-miss or free-form unsupported objectives fail boundedly. The generated
DAG contains exactly one executable WorkItem of type `dataset_profile` with
the dataset artifact reference and SHA-256 propagated into work metadata.

Prohibited scope: model-backed planning, arbitrary analysis planning,
application intelligence, memory, chat, UI behavior.

Acceptance: equivalent canonical inputs produce equivalent plan/work/DAG
semantics; unsupported objectives fail boundedly.

### TASK-M2-005

Objective: persist DataLab run/result/evidence metadata and reconstruct it as
recorded truth.

Durable truth: dataset artifact metadata/reference/integrity,
`DataLabAnalysisRequest`, `DataLabRunRecord`, `DataLabAnalysisResult` with
embedded `DatasetProfile` and findings, existing evidence references, existing
verification references, and existing event records. This task owns any new
DataLab persistence record kind and migration required for those records.

Ownership split: `curios_runtime` owns `DataLabRunState`,
`DataLabRunRecord`, lifecycle semantics, runtime invariants, and DataLab run
repository behavior. `curios_persistence` owns durable record kinds, table
schema, migration, transaction primitives, payload hash/version mechanics, and
bounded storage errors. Persisted run payloads must reconstruct the runtime
record exactly or fail boundedly.

Prohibited scope: raw dataset persistence by default, arbitrary artifact store,
project/session management, schema changes outside explicit DataLab tables.

Acceptance: run/result records are reconstructable, linked to dataset artifact
references, and bounded on corrupt/conflicting records.

### TASK-M2-006

Objective: define a bounded in-process profiler seam.

Owner package/module: DataLab runtime/profiler package introduced by this
task. The seam request contains dataset artifact reference, authorized staged
input handle, expected SHA-256, profiling constraints, run/work identity, and
observability context. The outcome contains `Result`, `DatasetProfile`,
bounded findings/warnings, events, and evidence references.

Prohibited scope: subprocess, shell, plugin runner, arbitrary tools, network,
model invocation, retry framework.

Acceptance: request/outcome types are deterministic, bounded, evidence-ready,
and safe-error preserving.

### TASK-M2-007

Objective: implement the deterministic CSV profiler.

Prohibited scope: pandas/polars/duckdb dependency, external process, network,
model calls, visualization, UI.

Acceptance: profiler reports row/column counts, inferred primitive column
types, null/empty counts, bounded distinct/value summaries, warnings, and
evidence under fixed resource limits.

Profiler semantics: primitive types are `STRING`, `INTEGER`, `DECIMAL`,
`BOOLEAN`, `EMPTY`, and `MIXED`; inference is locale-independent; whitespace
is trimmed for inference; empty cells are missing; booleans are
`true/false/yes/no/1/0`; decimals use `.`; non-finite values are strings;
mixed primitive classes infer `MIXED`. Numeric min/max/mean are emitted only
for `INTEGER` and `DECIMAL` columns.

### TASK-M2-008

Objective: integrate `dataset_profiling` capability with DataLab agent
definition/instance assignment.

The DataLab agent definition is a bounded capability declaration, not
autonomous intelligence. An agent instance must be `ACTIVE` before executable
work and must bind to the `dataset_profile` WorkItem according to frozen M1
lifecycle semantics. M2 reuses M1 agent persistence and adds no new agent
state machine.

Prohibited scope: autonomous agents, sleep/wake/rebirth, scheduler authority,
new permission grants.

Acceptance: exactly one eligible DataLab profiling agent is selected
deterministically; missing/ambiguous/inactive cases fail boundedly.

### TASK-M2-009

Objective: bind DataLab run execution and verification over M1 runner and
verification semantics.

Run states: `CREATED`, `READY`, `RUNNING`, `AWAITING_VERIFICATION`,
`COMPLETED`, and `FAILED`. Terminal states are `COMPLETED` and `FAILED`.
Verification attempt `PASSED` maps to M1 `APPROVED` and completes the run;
`FAILED` maps to M1 `REJECTED` and fails it; `INCONCLUSIVE`,
`NOT_EVALUATED`, and zero attempts map to M1 `DEFERRED` and leave it awaiting
verification. The first terminal `PASSED` or `FAILED` attempt cannot be
overridden. While awaiting verification, an explicit caller/API verification
request may be submitted again; no automatic retry loop is authorized.

Prohibited scope: new scheduler, model route execution, raw dataset mutation,
approval workflow, UI/API ownership.

Acceptance: successful profiling plus same-run evidence can be verified;
wrong or missing evidence cannot approve findings.

### TASK-M2-010

Objective: expose exact DataLab API endpoints.

Prohibited scope: generic file/action/tool endpoints, chat endpoints, model
endpoints, web implementation.

Acceptance: API enforces raw `text/csv` upload for
`POST /m2/datalab/datasets`, `application/json` object requests for analysis,
run-once, and verification completion, exact endpoint-by-endpoint failure
status/error mappings, safe errors, no raw secret/body/header echo,
recorded-truth reads, and exact OpenAPI surface.

### TASK-M2-011

Objective: add a focused DataLab web workspace.

Prohibited scope: general chat, rich live graph, Library, project UI, direct
App network authority.

Acceptance: web can upload/reference dataset, submit objective, run once,
display findings/evidence/provenance, and preserve canonical state.

Explicit frontend boundary functions: `uploadDataLabDataset`,
`createDataLabAnalysis`, `runDataLabAnalysisOnce`, `readDataLabRun`, and
`completeDataLabVerification`. App code remains prohibited from direct network
authority or generic request helpers.

The workspace must use request generations for dataset, analysis, run, and
verification state. Late or generation-mismatched responses cannot overwrite
newer accepted truth, restore invalidated downstream state, clear newer
errors/status, relabel a newer dataset/run, or assemble canonical hybrids.

### TASK-M2-012

Objective: prove VS-M2-001 through VS-M2-006 by integration tests.

Prohibited scope: production fixes, CI changes, acceptance ownership.

Acceptance: integration fails on broken intake, decomposition, capability,
profiler, verification, or API/web truth.

### TASK-M2-013

Objective: update CI quality gates for M2.

Prohibited scope: deployment, release, publishing, live model gates, weakening
BOOT/M0/M1 gates.

Acceptance: CI hard-fails on M2 gate failures and remains least privilege.

### TASK-M2-014

Objective: add M2 acceptance suite.

Prohibited scope: product implementation, M3 scenarios, live model
requirement.

Acceptance: every VS-M2 slice has milestone PASS/FAIL evidence.

### TASK-M2-015

Objective: independently verify complete M2 baseline.

Authorized surfaces: verification record and M2 status ledger only.

Acceptance: no unresolved M2 blocker remains.

### TASK-M2-016

Objective: perform final M2 closure and freeze.

Authorized surfaces: M2 freeze record, status ledger, evidence.

Acceptance: every M2 task/gate is lifecycle-consistent and no blocker remains.
