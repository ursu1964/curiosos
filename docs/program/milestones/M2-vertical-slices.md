---
id: MILESTONE-M2-VERTICAL-SLICES
title: M2 Vertical Slice Specification
lifecycle: FROZEN
artifact_type: vertical_slice_specification
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Vertical Slice Specification

## VS-M2-001 Dataset Intake

Objective: accept a bounded CSV upload as a governed dataset artifact/reference.

| Field | Requirement |
| --- | --- |
| Input | Raw `text/csv` upload body, required `X-Curios-Dataset-Filename`, UTF-8, <= 1 MiB, header row, <= 10,000 data rows, <= 100 columns, <= 16 KiB per cell. |
| Output | Canonical dataset `ArtifactReference(kind=dataset)` with SHA-256 integrity, media type, NFC-normalized safe display filename, size, row/column summary, generated staged locator, and producer/provenance reference. |
| Identities/references | `ArtifactReference(kind=dataset)`, producer `ObjectReference`, optional Work/Trace references when intake happens inside a run. |
| Boundaries crossed | Web/API raw upload boundary, dataset intake service, artifact/evidence contract boundary, safe-error boundary. |
| Persistence | Dataset metadata/reference and integrity are durable. Raw bytes are ephemeral staged input and are deleted/invalidated at owning run terminal state. |
| Positive acceptance | Valid CSV produces a dataset reference with stable integrity and bounded metadata. |
| Negative acceptance | Oversize body, missing/unsupported media, non-UTF-8, malformed CSV, duplicate header, empty dataset, unsafe filename, client-supplied path/locator, and secret-shaped metadata fail boundedly. |
| Deterministic requirement | Same bytes and metadata produce the same SHA-256 integrity value and equivalent metadata. |
| Authority requirement | Only staged/authorized upload bytes may be read; no network fetch or arbitrary path read. |
| Evidence requirement | Intake evidence references the accepted dataset artifact and records integrity plus validation summary. |

## VS-M2-002 Analysis Intent To DAG

Objective: convert a DataLab objective and dataset reference into a deterministic bounded analysis Work DAG.

| Field | Requirement |
| --- | --- |
| Input | DataLab analysis request containing objective and one accepted dataset artifact reference. |
| Output | `DataLabAnalysisRequest`, deterministic plan, bounded Work DAG, and exactly one executable WorkItem of type `dataset_profile`. Dataset intake and verification are not DAG work types in M2. |
| Identities/references | Intent/problem/plan references where reused, `DataLabAnalysisRequest`, Work IDs, DAG ID, dataset artifact reference. |
| Boundaries crossed | M1 cognitive contracts, DataLab decomposition, Work DAG records, API observation if applicable. |
| Persistence | Analysis request, runtime-owned DataLab run record, and DAG/work identity are durable. |
| Positive acceptance | `PROFILE_DATASET` objective produces the same one-node DAG shape under equivalent canonical inputs. |
| Negative acceptance | Missing dataset, unsupported objective family, invalid dataset reference, unavailable raw staged bytes, or excessive requested scope fails boundedly without work execution. |
| Deterministic requirement | Work IDs may be caller/fresh generated, but semantic DAG shape and work ordering are stable. |
| Authority requirement | Decomposition does not read dataset bytes and does not invoke tools or models. |
| Evidence requirement | Planning evidence records the selected deterministic DataLab decomposition pattern. |

## VS-M2-003 Capability / Agent Assignment

Objective: resolve `dataset_profiling` requirements to an eligible DataLab agent definition and disposable agent instance.

| Field | Requirement |
| --- | --- |
| Input | WorkItem type `dataset_profile` requiring capability `dataset_profiling`, known capabilities, and DataLab agent definitions. |
| Output | Capability resolution, agent definition reference, agent instance bound to DataLab work, lifecycle event truth. |
| Identities/references | `Capability`, `CapabilityRequirement`, `CapabilityResolution`, `AgentDefinition`, `AgentInstance`, Work reference. |
| Boundaries crossed | Capability resolver, agent repository, lifecycle repository, events/evidence. |
| Persistence | Agent definition, agent instance, and lifecycle event truth persist through the existing M1 agent repositories. |
| Positive acceptance | Exactly one eligible DataLab profiling agent is selected deterministically. |
| Negative acceptance | Missing capability, ambiguous capability, multiple eligible agents, inactive/mismatched agent, and wrong work binding fail boundedly. |
| Deterministic requirement | Equivalent inputs produce the same resolution status and references. |
| Authority requirement | Agent assignment grants no filesystem, network, model, or arbitrary tool authority. |
| Evidence requirement | Assignment/lifecycle evidence links the agent instance to the same WorkItem and dataset analysis run. |

## VS-M2-004 Deterministic Profiling Execution

Objective: execute the authorized in-process DataLab profiler and record structured findings.

| Field | Requirement |
| --- | --- |
| Input | READY `dataset_profile` work, accepted dataset reference, authorized staged-input handle, active DataLab agent instance, selected deterministic executor route, profiler bounds. |
| Output | Dataset profile, findings, result, event, evidence references, and bounded runner node outcome. |
| Identities/references | DataLab run ID, Work ID, AgentInstance ID, dataset artifact reference, evidence IDs, routing decision reference. |
| Boundaries crossed | Work DAG readiness, runner, routing, deterministic profiler seam, evidence/event recording. |
| Persistence | Runtime-owned DataLab run plus result, profile, findings, event, and evidence truth persist through the M2 repository/storage boundary and existing event/evidence stores. |
| Positive acceptance | Valid dataset profile includes row/column counts, ordered column profiles, inferred primitive types, missing/non-missing counts, bounded distinct counts, numeric min/max/mean for numeric columns, warnings, findings, and provenance. |
| Negative acceptance | Dataset unavailable, integrity mismatch, parser error, resource limit, timeout, unsupported column shape, route/work incompatibility, and tool failure fail boundedly. |
| Deterministic requirement | Same dataset bytes and bounds produce equivalent profile/result semantics. |
| Authority requirement | In-process profiler only; no subprocess, shell, network, external database, arbitrary filesystem, or model invocation. |
| Evidence requirement | Profiler evidence references the dataset artifact and generated result artifact/record. |

## VS-M2-005 Verification-Gated Findings

Objective: require verification evidence before DataLab findings are accepted as completed truth.

| Field | Requirement |
| --- | --- |
| Input | Recorded successful profiling execution, same-work result, same-dataset evidence, verification attempts. |
| Output | Verification reference, completion decision, verification event, and DataLab run transition to `COMPLETED`, `FAILED`, or retained `AWAITING_VERIFICATION`. |
| Identities/references | Work ID, DataLab run ID, DataLab result ID, EvidenceReference, VerificationReference. |
| Boundaries crossed | Verification loop, evidence binding, result/run repository, event store. |
| Persistence | Verification reference plus DataLab run/result verification state persist through existing verification persistence and M2 run/result records. |
| Positive acceptance | `PASSED` verification attempts map to M1 `APPROVED` and are tied to successful profiling execution and same dataset artifact. |
| Negative acceptance | Wrong evidence subject, duplicate evidence, missing execution, failed execution, integrity mismatch, `FAILED`, `INCONCLUSIVE`, `NOT_EVALUATED`, zero attempts, and stale evidence cannot mark findings approved. |
| Deterministic requirement | Equivalent verification attempts produce equivalent completion decisions. |
| Authority requirement | Verification does not rerun tools, mutate raw dataset bytes, or invoke models. |
| Evidence requirement | Verification evidence binds to the same DataLab run, WorkItem, dataset artifact, and result. |

## VS-M2-006 Recorded-Truth API / Web

Objective: present DataLab recorded truth through bounded API/web surfaces.

| Field | Requirement |
| --- | --- |
| Input | DataLab run identity and persisted recorded truth. |
| Output | API and web display of dataset metadata, run state, DAG/work state, profiling findings, evidence, verification decision, and bounded errors through fixed DataLab endpoints and explicit web boundary functions. |
| Identities/references | DataLab run ID, dataset artifact reference, Work/DAG/Agent/Route/Evidence/Verification references. |
| Boundaries crossed | FastAPI DataLab endpoints, web API-boundary capabilities, DataLab repositories/read models. |
| Persistence | Web displays persisted/reconstructed truth, not fabricated frontend state. |
| Positive acceptance | Focused DataLab workspace displays the current accepted run/result/provenance state for the active request generation. |
| Negative acceptance | Malformed upload, unsupported media, unsafe errors, stale run/result state, late stale responses, generation-mismatched responses, and frontend direct-network authority are rejected. |
| Deterministic requirement | Equivalent persisted truth renders equivalent semantic UI state. |
| Authority requirement | App has no direct network authority outside explicit DataLab API-boundary functions. |
| Evidence requirement | UI exposes evidence/provenance references associated with the displayed result. |
