---
id: MILESTONE-M2-DEFINITION
title: M2 Milestone Definition
lifecycle: FROZEN
artifact_type: milestone_definition
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Milestone Definition

## Authority Classification

| Source | Classification | M2 Use |
| --- | --- | --- |
| M1 final freeze record and status ledger | FROZEN AUTHORITY | Establishes the closed M1 cognitive-loop baseline and the post-M1 deferred-scope boundary. |
| BOOT, M0, and M1 contracts | FROZEN AUTHORITY | Provide canonical work, agent, capability, artifact, evidence, verification, policy, event, DAG, routing, API, and web boundary semantics. |
| POST-M1-001 reconstruction | PLANNING INPUT | Reconstructed DataLab as the best-supported first useful post-M1 vertical slice. |
| Human POST-M1-002 decisions | PLANNING INPUT ACCEPTED FOR M2 | Select DataLab, bounded CSV upload, deterministic in-process profiling, no LLM generation, focused UI, and durable DataLab run identity. |
| `1.txt` | HISTORICAL DESIGN INPUT | Supplies target-product direction only; accepted M2 requirements are reconciled here before they can govern tasks. |

## Milestone

Identifier: `M2`

Name: DataLab Analysis Vertical Slice

Objective:

A user uploads a bounded local CSV/tabular dataset and supplies an analytical
objective. CuriosOS records a governed dataset artifact/reference, creates a
deterministic bounded analysis plan and Work DAG, resolves the
`dataset_profiling` capability, executes an authorized deterministic
in-process profiler, records structured findings, evidence, and provenance,
verifies the result, persists the required recorded truth, and presents that
truth through a bounded DataLab API/web workspace.

## Scope Reduction From Historical Input

Historical material describes broad chat, multimodal input, model routing,
agents, tools, memory, application intelligence, infrastructure intelligence,
and self-improvement. M2 narrows that into the first practical user-visible
application slice:

- bounded CSV/tabular upload, not arbitrary file intake;
- deterministic profiling, not live LLM analysis;
- one in-process profiler seam, not a general tool/subprocess framework;
- durable DataLab run identity, not full project/session management;
- focused DataLab workspace, not general chat, Library, rich live graph, or
  application workspace.

## In Scope

- M2 planning authority, status ledger, and evidence conventions.
- Bounded CSV/tabular upload as an authorized dataset artifact.
- Dataset metadata/reference, integrity hash, and provenance.
- Canonical DataLab analysis request, profile, finding, result, and run-record
  semantics.
- Deterministic DataLab decomposition into a bounded Work DAG.
- Reuse of frozen M1 Work DAG, capability resolver, agent records, routing,
  runner, verification, events, and evidence where valid.
- `dataset_profiling` capability and deterministic agent assignment.
- A bounded deterministic in-process profiler seam and profiler implementation.
- No-network tool execution.
- DataLab run/result/evidence persistence.
- Verification-gated findings.
- DataLab API and focused DataLab web workspace.
- VS-M2-001 through VS-M2-006 integration, CI, acceptance, independent
  verification, and final M2 freeze.

## Explicitly Out Of Scope

- General conversational assistant.
- Real LLM generation, chat, embeddings, prompt orchestration, cloud models,
  or live model quality gates.
- Arbitrary filesystem access.
- Arbitrary subprocess or general tool execution.
- Remote dataset fetching.
- Autonomous agents.
- Production scheduler or distributed DAG runtime.
- Knowledge or memory runtime.
- Full project/session management.
- Rich live graph, general Library, Docs rendering, or application workspace.
- Application intelligence.
- Infrastructure intelligence.
- Learning, self-improvement, or reusable pattern induction.
- Multi-project enterprise operation.
- Release, deployment, or tag creation.

## Dataset Constraints

M2 freezes these dataset-intake limits for planning. Implementation tasks may
make a stricter choice but must not broaden them without an explicit planning
revision.

| Constraint | M2 Decision |
| --- | --- |
| Accepted media | `text/csv` only. Upload must be treated as tabular CSV with a header row. |
| Encoding | UTF-8 only, with optional UTF-8 BOM stripped before parsing. |
| Delimiter | Comma only for M2. No dialect auto-detection authority. |
| Maximum bytes | 1 MiB per uploaded dataset. |
| Maximum rows | 10,000 data rows, excluding the header row. |
| Maximum columns | 100 columns. |
| Maximum field size | 16 KiB per cell. |
| Malformed CSV | Bounded failure before analysis; no partial findings may be accepted. |
| Duplicate columns | Bounded failure; column identity must remain unambiguous. |
| Empty dataset | Bounded failure when there is no header or no data row. |
| Client filename | Required `X-Curios-Dataset-Filename` display metadata. Unicode is normalized to NFC before validation. Empty names, names longer than 128 Unicode scalar values, `/`, `\`, `.`, `..`, absolute paths, drive-qualified paths, NUL, and ASCII/C0/C1 control characters are rejected. Invalid names fail boundedly; they are not silently rewritten. |
| Server staged locator | Generated only by CuriosOS. The client never supplies it. It is opaque, provider-neutral, confined to the authorized staging boundary, and cannot contain client path authority. |
| Integrity | SHA-256 is required for every accepted dataset artifact reference. |
| Raw data persistence | Raw dataset bytes are not persisted in the Curios persistence store by default. |
| Cleanup/lifetime | Uploaded bytes are ephemeral staged input. Staging exists only from successful intake through completion, failure, or cancellation of the owning bounded DataLab run. Raw bytes are deleted or invalidated when the run reaches a terminal state. Cleanup failure is recorded boundedly and grants no persistent file authority. |

## Dataset Lifetime Semantics

M2 freezes this semantic model independently of the concrete storage
mechanism:

- raw uploaded bytes are ephemeral staged input, not durable Curios truth;
- durable truth is dataset artifact identity, media type, byte size, SHA-256,
  accepted filename metadata, creation timestamp, provenance, DataLab run,
  result, evidence, and verification records;
- staging begins only after bounded intake accepts the upload;
- staging ends when the owning DataLab run reaches a terminal state;
- a process restart before terminal completion makes the staged bytes
  unavailable unless the authorized staging provider can prove the exact bytes
  still exist and match the recorded SHA-256;
- a run whose required raw input is unavailable cannot be replayed
  automatically and must enter a bounded `DATASET_UNAVAILABLE` failure or
  deferred outcome;
- after cleanup, the persisted `ArtifactReference(kind=dataset)` remains
  historical recorded truth and must not imply raw bytes are still retrievable;
- re-analysis after cleanup requires a new upload and a new dataset artifact
  reference.

## Frozen M2 Resource Bounds

| Bound | M2 Decision |
| --- | --- |
| Objective length | Maximum 1,000 Unicode scalar values after trimming. |
| Profiler timeout | Maximum 5 seconds of in-process profiler execution per run. Timeout produces a bounded profiler timeout result. |
| Profiler memory model | The profiler may materialize the full accepted input because input is bounded to 1 MiB. M2 does not claim an OS-level memory cap. |
| Findings | Maximum 50 findings per result. |
| Warnings | Maximum 100 warnings across profile and result. |
| Evidence references | Maximum 20 evidence references per DataLab result and maximum 5 per finding. |
| Finding/message text | Maximum 500 Unicode scalar values per finding summary/message. |
| Profile columns | Maximum 100 column profiles, matching dataset column bound. |
| Event payload | Maximum 16 KiB canonical DataLab event payload; larger diagnostic detail is omitted or summarized safely. |
| API upload body | Maximum 1 MiB raw `text/csv` body. |
| API response body | Maximum 256 KiB canonical DataLab response content for M2 read endpoints. |

## Frozen M2 API Shape

M2 uses raw CSV upload, not multipart and not JSON base64.

| Operation | Method and path | Content-Type | Request | Success response | Primary status | Authority |
| --- | --- | --- | --- | --- | --- | --- |
| Dataset intake | `POST /m2/datalab/datasets` | `text/csv` | Raw CSV body plus required `X-Curios-Dataset-Filename`. | Dataset artifact metadata/reference and integrity. | `201 Created` | Reads only request body bytes and writes dataset metadata/reference. |
| Create analysis | `POST /m2/datalab/analyses` | `application/json` object | Dataset artifact reference, SHA-256, and bounded objective. | DataLab run record in `READY` or bounded failure. | `201 Created` | Creates request/run/DAG records; no dataset byte read and no tool/model execution. |
| Run once | `POST /m2/datalab/runs/{run_id}/run-once` | `application/json` object | Empty object or bounded run-once options object. | Updated run/result state. | `200 OK` | Executes at most one READY `dataset_profile` work item through bounded profiler seam. |
| Read run | `GET /m2/datalab/runs/{run_id}` | none | Path run ID only. | Recorded run truth, profile, findings, evidence, verification state, and bounded errors. | `200 OK` | Reads persisted DataLab truth only. |
| Complete verification | `POST /m2/datalab/runs/{run_id}/verification/complete` | `application/json` object | Verification evidence references and desired completion attempt. | Updated verification/run decision. | `200 OK` | Applies M1 verification semantics; does not rerun tools or mutate dataset bytes. |

Unsupported or missing `Content-Type` is rejected before domain processing.
Malformed, oversize, or unsafe upload/request data maps to bounded Curios
errors without raw body/header echo or native framework/parser diagnostics.
Not found, conflict, stale run, unavailable dataset, hash mismatch, and unsafe
error cases use bounded M2 error codes and never expose raw internal detail.

Failure semantics are frozen by the M2 architecture/security delta:

- upload media/header/body failures use bounded `DATALAB_*` transport error
  codes and do not invoke DataLab domain logic;
- JSON endpoints use M1-013-style `application/json` object-only transport
  handling with bounded 400 errors before domain invocation;
- not-found states use bounded 404 errors;
- stale/conflicting run, dataset, and verification states use bounded 409
  errors;
- persistence, staging, integrity, and unexpected internal failures use
  bounded 500 errors;
- valid DataLab outcomes such as `NO_ROUTE`, `ROUTE_NOT_EXECUTABLE`,
  `AWAITING_VERIFICATION`, verification `DEFERRED`, and verification
  `REJECTED` remain domain responses rather than generic HTTP failures.

## Frozen DataLab Execution Semantics

Work types:

- `dataset_profile`: the only executable DataLab WorkItem type in M2.

Capabilities:

- `dataset_profiling`: required by `dataset_profile` work and resolved to one
  active DataLab profiling agent definition/instance.

Routing:

- route candidate kind: deterministic in-process executor;
- supported work types: `dataset_profile`;
- no-route and route/work incompatibility produce bounded failures;
- provider/model discovery may exist from M1 but no provider/model invocation,
  generation, chat, embeddings, or cloud call is allowed.

Verification:

- M2 reuses the M1 verification loop;
- evidence subject binds to the same `dataset_profile` work, DataLab run,
  dataset SHA-256, and DataLab result;
- duplicate, stale, wrong-work, wrong-run, or wrong-dataset evidence is
  rejected;
- verification attempt `PASSED` maps to M1 `APPROVED` and completes the run;
- verification attempt `FAILED` maps to M1 `REJECTED` and fails the run;
- verification attempt `INCONCLUSIVE`, `NOT_EVALUATED`, or zero attempts map
  to M1 `DEFERRED` and leave the run awaiting verification;
- the first terminal `PASSED` or `FAILED` attempt determines the terminal
  decision and cannot be overridden by later attempts;
- while still `AWAITING_VERIFICATION`, a caller may explicitly submit another
  bounded verification request; M2 has no automatic retry loop.

## User-Visible Capability Delivered

1. The user supplies a CSV dataset and analytical objective.
2. Curios records a dataset artifact reference with integrity and provenance.
3. Curios records a DataLab analysis request and deterministic analysis plan.
4. Curios creates a bounded Work DAG using frozen M1 DAG semantics.
5. Curios resolves `dataset_profiling` to an eligible DataLab agent definition
   and disposable agent instance.
6. Curios runs a deterministic in-process profiler with no network and no
   subprocess authority.
7. Curios records a structured profile, findings, events, evidence, and result.
8. Curios verifies the findings before presenting completion.
9. DataLab API/web surfaces display recorded truth, not fabricated analysis.

## Entry Criteria

M2 planning may be reviewed only when all are true:

- M1 is closed, published, and remote-CI-verified at
  `139274bc146db743e79411fbef04992dd6920839`.
- M2 planning artifacts are present and internally consistent.
- `1.txt` remains historical input only and is not modified.
- No M2 product implementation has started.

## Exit Criteria

M2 exits only when all are true:

- Every approved `TASK-M2-*` task is validated and frozen.
- VS-M2-001 through VS-M2-006 pass integration and acceptance.
- M2 CI gates include DataLab contracts, package/runtime, persistence, API,
  web, vertical-slice integration, acceptance, architecture, security, and
  no-live-model checks.
- Independent M2 verification records lifecycle, architecture, security,
  contract, dataset, tool, persistence, API/web, CI, acceptance, dependency,
  and repository-hygiene evidence.
- The M2 final freeze record identifies the final M2 baseline.
- No unresolved M2 blocker remains.

## Readiness Status

The corrected M2 planning package passed independent readiness validation and
is frozen as executable M2 planning authority. The readiness record authorizes
only `TASK-M2-001` as the first implementation unit. No later M2 task is ready
until its DAG prerequisites are validated, frozen, and integrated.
