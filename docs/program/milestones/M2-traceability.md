---
id: M2-TRACEABILITY
title: M2 Traceability to Frozen M1 and Historical Input
lifecycle: FROZEN
artifact_type: traceability_record
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Traceability to Frozen M1 and Historical Input

## Traceability Limits

`1.txt` remains historical design input. M2 accepts only the requirements
reconciled into this planning package. Raw `1.txt` text does not directly
authorize implementation.

Detailed P1-P6 artifacts are not tracked as frozen repository authority. M2
therefore preserves the M1 rule that historical P1-P6 material must be
reconciled into approved Build Pack artifacts before it can govern tasks.

## Frozen M1 Reuse

| Frozen M1 capability | M2 use |
| --- | --- |
| Intent/problem/plan records | Represent the DataLab analytical objective and deterministic plan where appropriate. |
| Work DAG | DataLab analysis is expressed as bounded work nodes and dependencies. |
| Capability resolver | `dataset_profiling` is resolved through frozen capability semantics. |
| Agent definitions/instances | DataLab profiling uses disposable agent instances, not autonomous agents. |
| Executor seam | M2 extends with a bounded profiler seam while preserving M1 executor authority boundaries. |
| Routing records | DataLab records deterministic route decisions; no live model route execution. |
| Verification loop | Findings require evidence-bound verification. |
| API/web recorded truth | DataLab API/web must display persisted truth and preserve frontend authority restrictions. |
| CI/acceptance/verification/freeze lifecycle | M2 follows M1 lifecycle precedent. |

## Accepted Historical Requirements From `1.txt`

| Historical concept | Accepted M2 interpretation |
| --- | --- |
| "M2 - DataLab analysis vertical slice" | M2 is DataLab Analysis Vertical Slice. |
| "DataLab will be the first serious application/vertical slice" | DataLab is the first post-M1 practical user outcome. |
| Interface supports datasets/files | M2 supports bounded local CSV/tabular upload only. |
| Capability example `dataset_profiling` | M2 defines/uses `dataset_profiling` capability. |
| Prefer deterministic code/tools before models | M2 uses deterministic in-process profiling and defers LLM generation. |
| Agents are definitions plus execution instances | M2 uses disposable DataLab profiling agent instances. |
| Work DAG, evidence, verification, governance | M2 runs the DataLab slice through DAG, evidence, verification, and bounded authority. |
| UI must not fake thinking | DataLab workspace must display recorded runtime truth only. |

## Rejected Or Deferred Historical Requirements

| Historical concept | M2 decision |
| --- | --- |
| General chat | Deferred. |
| Multilingual/multimodal interface | Deferred. |
| Images/screenshots/documents/source repositories | Deferred. |
| Real LLM generation/chat/embeddings/cloud models | Deferred. |
| General tools/MCP/subprocess execution | Deferred. |
| Memory/knowledge graph runtime | Deferred. |
| Application intelligence | Deferred. |
| Infrastructure intelligence | Deferred. |
| Learning/self-improvement | Deferred. |
| Multi-project enterprise operation | Deferred. |
| Rich live graph/general Library/Docs | Deferred. |

## Conflicts Recorded

Historical material imagines broad capabilities earlier than the frozen M1
architecture permits. M2 resolves this by authorizing only bounded DataLab
surfaces and keeping all broader target-experience features deferred until
future reconciled milestones.

## Executable Planning Traceability Matrix

| Req ID | Requirement | Source | Contract | Component | TASK-M2 owner | VS-M2 slice | Integration test owner | Acceptance criterion | Evidence | CI gate owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M2-REQ-001 | Bounded raw CSV upload with fixed media, size, row, column, cell, encoding, and delimiter limits. | Human decision, frozen M1 safe boundary lessons, `1.txt` dataset concept. | `ArtifactReference`, intake validation errors. | DataLab intake. | TASK-M2-003, TASK-M2-010 | VS-M2-001 | TASK-M2-012 | Valid upload accepted; invalid media/shape rejected boundedly. | Intake evidence and artifact metadata. | TASK-M2-013 |
| M2-REQ-002 | Client filename is metadata only; invalid filename/path semantics are rejected. | POST-M1-003 defect correction. | `ArtifactReference.locator` remains Curios-generated and provider-neutral. | DataLab intake/API. | TASK-M2-003, TASK-M2-010 | VS-M2-001 | TASK-M2-012 | Unsafe filename/path fails before persistence. | Safe-error/intake evidence. | TASK-M2-013 |
| M2-REQ-003 | Raw bytes are ephemeral staged input; durable truth excludes raw dataset by default. | Human decision, M1 recorded-truth boundary. | `ArtifactReference`, `DataLabRunRecord`. | Staging boundary and persistence. | TASK-M2-003, TASK-M2-005 | VS-M2-001, VS-M2-004 | TASK-M2-012 | Cleanup/unavailable bytes produce bounded `DATASET_UNAVAILABLE`; metadata remains historical. | Run/evidence record. | TASK-M2-013 |
| M2-REQ-004 | Use `ArtifactReference(kind=dataset)`; no `DatasetReference` in M2. | BOOT artifact contract. | `ArtifactReference`, `IntegrityDescriptor`. | Contracts/intake/persistence. | TASK-M2-002, TASK-M2-003 | VS-M2-001 | TASK-M2-012 | Dataset identity, media, SHA-256, provenance preserved without new reference type. | Contract/intake evidence. | TASK-M2-013 |
| M2-REQ-005 | Canonical DataLab request/profile/finding/result contracts. | Human M2 decision. | `DataLabAnalysisRequest`, `DatasetProfile`, `DataLabFinding`, `DataLabAnalysisResult`. | Contracts/runtime/API/web. | TASK-M2-002 | VS-M2-002..006 | TASK-M2-012 | Serialization, invariants, collection limits, ordering, safe validation pass. | Contract evidence. | TASK-M2-013 |
| M2-REQ-006 | Durable DataLab run identity and aggregate state. | Human session decision. | `DataLabRunRecord`, `DataLabRunState`. | Runtime run repository plus persistence storage representation. | TASK-M2-005, TASK-M2-009 | VS-M2-002, VS-M2-005, VS-M2-006 | TASK-M2-012 | Runtime-owned run reconstructs with legal state transitions and no duplicate orchestration semantics. | Runtime/persistence run evidence. | TASK-M2-013 |
| M2-REQ-007 | Deterministic `PROFILE_DATASET` decomposition to one `dataset_profile` WorkItem. | M1 DAG/decomposition reuse. | `DataLabAnalysisRequest`, `WorkItem`. | DataLab decomposition/DAG. | TASK-M2-004 | VS-M2-002 | TASK-M2-012 | Equivalent inputs produce equivalent DAG shape; unsupported objectives fail. | Decomposition evidence. | TASK-M2-013 |
| M2-REQ-008 | Capability `dataset_profiling` resolves to active DataLab agent without autonomy. | M1 capability/agent reuse, `1.txt` capability example. | `CapabilityRequirement`, `AgentDefinition`, `AgentInstance`. | Capability resolver and lifecycle. | TASK-M2-008 | VS-M2-003 | TASK-M2-012 | Exactly one active agent selected; missing/ambiguous/inactive fail boundedly. | Assignment/lifecycle evidence. | TASK-M2-013 |
| M2-REQ-009 | Deterministic in-process profiler seam only. | Human tool decision. | `DatasetProfile`, `DataLabFinding`, `Result`, `EvidenceReference`. | DataLab profiler/runtime. | TASK-M2-006, TASK-M2-007 | VS-M2-004 | TASK-M2-012 | No shell/subprocess/plugin/network/model; timeout/resource failures bounded. | Profiler/event/evidence records. | TASK-M2-013 |
| M2-REQ-010 | Fixed profiler output semantics and bounds. | POST-M1-003 defect correction. | `DatasetProfile`, `DataLabFinding`. | Profiler. | TASK-M2-007 | VS-M2-004 | TASK-M2-012 | Required counts/types/summaries emitted deterministically within bounds. | Profiler evidence. | TASK-M2-013 |
| M2-REQ-011 | M1 routing reused for deterministic executor route. | M1 routing freeze. | RoutingDecision, WorkItem refs. | Routing/runner. | TASK-M2-009 | VS-M2-004 | TASK-M2-012 | Correct route selected; no-route/incompatible route fail boundedly. | Routing evidence. | TASK-M2-013 |
| M2-REQ-012 | Findings require M1 verification-gated completion. | M1 verification freeze. | `EvidenceReference`, `VerificationReference`, `DataLabAnalysisResult`. | Verification/run persistence. | TASK-M2-009 | VS-M2-005 | TASK-M2-012 | APPROVED completes; REJECTED fails; DEFERRED waits; wrong evidence rejected. | Verification evidence. | TASK-M2-013 |
| M2-REQ-013 | DataLab API has exact bounded endpoint inventory. | Human API/web outcome. | DataLab contracts plus bounded errors. | FastAPI DataLab endpoints. | TASK-M2-010 | VS-M2-006 | TASK-M2-012 | Exact OpenAPI/API behavior; no generic action endpoint. | API evidence. | TASK-M2-013 |
| M2-REQ-014 | Focused DataLab web workspace uses explicit boundary functions only. | Human UI decision, M1 frontend authority. | API DTOs/read models. | Web API boundary and workspace. | TASK-M2-011 | VS-M2-006 | TASK-M2-012 | Upload/create/run/read/verify visible; no direct App network authority. | Web/security evidence. | TASK-M2-013 |
| M2-REQ-015 | Web draft state cannot relabel accepted canonical truth. | M1-014 provenance lesson. | DataLab read model state. | Web workspace. | TASK-M2-011 | VS-M2-006 | TASK-M2-012 | Draft edits leave accepted dataset/run/result truth intact; failed replacement preserves prior truth. | Web acceptance evidence. | TASK-M2-013 |
| M2-REQ-016 | No live model, chat, embeddings, cloud, general tools, memory, scheduler, project system, release, deployment, or tags. | Human decisions, M1 freeze. | None new. | Architecture/security/CI. | TASK-M2-001, TASK-M2-013, TASK-M2-015, TASK-M2-016 | All VS-M2 | TASK-M2-012 | Security/architecture/CI guards prove absent authority. | Guard evidence and verification record. | TASK-M2-013 |
| M2-REQ-017 | DataLab run semantics are runtime-owned; persistence owns storage mechanics only. | POST-M1-003 re-validation blocker. | `DataLabRunRecord`, `DataLabRunState`, `PersistenceRecordKind`. | Runtime repository and persistence storage boundary. | TASK-M2-005, TASK-M2-009 | VS-M2-002, VS-M2-005, VS-M2-006 | TASK-M2-012 | Persisted representation reconstructs runtime run record exactly or fails boundedly. | Runtime/persistence evidence. | TASK-M2-013 |
| M2-REQ-018 | M2 API failure/status mapping is exact and bounded. | POST-M1-003 re-validation blocker, M1-013 safe transport precedent. | Bounded DataLab API errors. | FastAPI DataLab endpoints and safe-error mapper. | TASK-M2-010 | VS-M2-001, VS-M2-006 | TASK-M2-012 | Transport, domain, not-found, conflict, and internal failures map to frozen statuses/codes without raw leakage. | API/safe-error evidence. | TASK-M2-013 |
| M2-REQ-019 | DataLab verification attempts map exactly to M1 completion decisions and run states. | POST-M1-003 re-validation blocker, M1 verification freeze. | `VerificationReference`, `DataLabRunRecord`, `DataLabAnalysisResult`. | Verification binding/runtime run repository. | TASK-M2-009 | VS-M2-005 | TASK-M2-012 | `PASSED/FAILED/INCONCLUSIVE/NOT_EVALUATED/zero attempts` produce frozen run outcomes and first-terminal behavior. | Verification/run evidence. | TASK-M2-013 |
| M2-REQ-020 | Web request generations prevent stale responses and canonical hybrids. | POST-M1-003 re-validation blocker, M1-014 provenance lesson. | DataLab API DTO/read model state. | Web API boundary and DataLab workspace state. | TASK-M2-011 | VS-M2-006 | TASK-M2-012 | Late or generation-mismatched responses cannot overwrite newer accepted truth or restore stale downstream state. | Web provenance evidence. | TASK-M2-013 |
