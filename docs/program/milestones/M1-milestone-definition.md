---
id: MILESTONE-M1-DEFINITION
title: M1 Milestone Definition
lifecycle: PLANNED
artifact_type: milestone_definition
authority: program_planning
milestone_id: M1
date: 2026-09-23
---

# M1 Milestone Definition

## Authority Classification

| Source | Classification | M1 Use |
| --- | --- | --- |
| BOOT-000 final freeze record and supporting artifacts | FROZEN AUTHORITY | Establishes canonical contracts, core/provider/API/web boundaries, architecture/security guardrail patterns, CI conventions, and Build Pack lifecycle. |
| M0 final freeze record and supporting artifacts | FROZEN AUTHORITY | Establishes governed local work execution, persistence, policy, runtime, provider inventory, API/web observation, integration, CI, acceptance, and verification foundations. |
| TASK-M0-001 through TASK-M0-014 evidence | FROZEN AUTHORITY | Supplies the frozen implementation and validation state that M1 must extend without semantic drift. |
| Canonical BOOT contracts | FROZEN AUTHORITY | Define `WorkItem`, `ExecutionRecord`, `Capability`, `CapabilityRequirement`, `AgentDefinition`, `AgentInstance`, `EventEnvelope`, `EvidenceReference`, `VerificationRecord`, `PolicyDecision`, and `ObjectReference`. |
| `1.txt` and unreconciled P1-P6 references | HISTORICAL DESIGN INPUT | Provide target-architecture direction only. They do not directly authorize implementation. |
| M1 reconstruction report | DERIVED PROPOSAL INPUT | Starting proposal refined here into a reviewable executable-program package. |

## Milestone

Identifier: `M1`

Name: First Cognitive Loop

Purpose: extend the frozen M0 governed local work runtime into the smallest
coherent cognitive loop: a simple intent is represented, decomposed into a
bounded work DAG, matched to capabilities and disposable agent instances,
executed through bounded executor/routing decisions, verified with evidence,
and shown through API/web surfaces as recorded truth.

## Scope Reduction From Historical Input

The historical M1 sketch includes broad cognitive graph, model router, agent
execution, event stream, and live UI ideas. M1 narrows that to the smallest
testable milestone:

- deterministic/template intent decomposition, not model-backed planning;
- bounded local DAG runner, not production scheduler;
- disposable agent assignment, not autonomous agents;
- model/profile discovery and routing decision records, not model generation;
- recorded-truth API/web observation, not generalized cognitive dashboard.

## Capability Delivered

M1 delivers one local cognitive loop:

1. A user/test submits a simple intent.
2. Curios records canonical intent/problem/plan facts.
3. A deterministic template decomposes the intent into a bounded work DAG.
4. Capability requirements are resolved to frozen capability/agent records.
5. Disposable agent instances are assigned to DAG work nodes.
6. A bounded runner executes ready independent nodes up to a fixed concurrency
   limit through a frozen executor seam.
7. The router records whether each node used deterministic execution, existing
   M0 executor behavior, or a non-invoked model/profile candidate.
8. Verification gates completion and records evidence.
9. API/web surfaces display the persisted DAG, agent, routing, execution,
   event, evidence, and verification truth.

## Entry Criteria

- BOOT-000 is `VALIDATED, FROZEN` and integrated.
- M0 is `VALIDATED, FROZEN` and integrated at baseline
  `1e71e27f4589ec09f98c0319511d67f5d93642e8`.
- M1 planning artifacts are committed.
- Independent M1 readiness validation passes.
- No M1 implementation starts before exact task-owned surfaces are authorized.

## Exit Criteria

M1 exits only when all are true:

- Every approved `TASK-M1-*` task is `VALIDATED, FROZEN`.
- The M1 acceptance suite proves VS-M1-001 through VS-M1-006.
- M1 CI gates include M1 package, integration, acceptance, architecture,
  security, API, web, and deterministic no-live-model checks.
- Independent M1 verification records lifecycle, architecture, security,
  DAG/runtime truth, acceptance, dependency, and repository hygiene evidence.
- The M1 final freeze record identifies the final M1 baseline.
- No unresolved M1 blocker remains.

## In Scope

- M1 planning authority and status ledger.
- Narrow evolution of BOOT/M0 architecture and security topology for explicit
  M1 surfaces only.
- Canonical cognitive intent/problem/plan record contracts where required.
- Persistence of cognitive records, DAG records, agent assignment records,
  routing decision records, and verification bindings using M0 persistence
  primitives where valid.
- Deterministic template intent decomposition.
- Minimal DAG model and bounded local DAG runner.
- Deterministic capability matching.
- Disposable agent definition/instance assignment over frozen contracts.
- Executor seam for deterministic work and M0 provider-inventory reuse.
- Ollama/model discovery or profile records only; no model generation.
- API endpoints for M1 intent/DAG/agent/routing/verification observation.
- Web console extension for recorded M1 loop truth.
- M1 integration, CI, acceptance, independent verification, and freeze records.

## Explicitly Out Of Scope

- Autonomous agents.
- Production-scale scheduler.
- Unbounded or distributed DAG runtime.
- Generalized tool execution.
- Model generation, prompt orchestration, or cloud model execution.
- Full model-router optimization.
- Knowledge or memory runtime.
- DataLab.
- Learning or self-improvement.
- Production IAM, RBAC/ABAC, or full policy language.
- Secret resolver.
- External brokers.
- Cloud infrastructure.
- Live LLM quality gates.
- Multi-project execution.

## Frozen BOOT and M0 Assumptions

- Curios contracts remain canonical.
- `WorkItem` remains the canonical unit of work.
- `ExecutionRecord` remains one attempt to execute work.
- `AgentDefinition` and `AgentInstance` already exist as canonical contracts;
  M1 persists and uses them, it does not redefine them.
- `Capability` and `CapabilityRequirement` remain canonical provider-neutral
  capability contracts.
- `EventEnvelope`, `EvidenceReference`, `VerificationRecord`, and
  `ObjectReference` remain canonical.
- M0 runtime/repository/store boundaries remain authoritative for work,
  execution, events, evidence, policy decisions, and verification records.
- `PolicyDecision.UNKNOWN` remains non-authorizing.
- API and web remain outer interfaces.

## Concept Classification

| Concept | Classification | M1 Decision |
| --- | --- | --- |
| Intent | Canonical contract | New minimal Curios-owned record for submitted user/system intent. |
| Objective | Canonical contract | Represented as a bounded objective field on intent/problem records, not a full objective-management system. |
| Problem | Canonical contract | New minimal problem statement record derived from intent. |
| Assumption | Canonical contract | New bounded cognitive record linked by `ObjectReference`. |
| Decision | Canonical contract | New bounded cognitive record for planning/runtime decisions. |
| Plan | Canonical contract | New bounded plan record containing references to generated work/DAG records. |
| Cognitive graph node/edge | Runtime/persistence record | M1 persists graph links among canonical cognitive records; graph storage is not a full knowledge graph. |
| Work DAG | Runtime/persistence record | DAG nodes reference existing `WorkItem` records; DAG edges do not replace `WorkItem.dependencies`. |
| Capability | Existing canonical contract | Reuse frozen `Capability`; no duplicate vocabulary. |
| Capability matching result | Runtime/persistence record | Records deterministic match/ambiguity/failure. |
| AgentDefinition | Existing canonical contract | Reuse frozen `AgentDefinition`. |
| AgentInstance | Existing canonical contract | Reuse frozen `AgentInstance`; not a duplicate `ExecutionRecord`. |
| Agent lifecycle | Existing canonical vocabulary plus runtime record | Use frozen `AgentInstanceState`; M1 records transitions and events. |
| Executor seam | Implementation-local protocol | Curios-owned runtime interface; no framework/provider authority. |
| Routing decision | Runtime/persistence record | Records selected execution route and rationale; not optimizer authority. |
| Model profile | Implementation-local/provider record | Discovery/profile metadata only; no generation contract. |
| Verification result | Existing canonical contract | Reuse `VerificationRecord`, `EvidenceReference`, and `EventEnvelope`. |

## M0 Reuse Map

| M1 Need | Frozen Reuse |
| --- | --- |
| Work identity and state | `WorkItem`, `WorkId`, `M0WorkRepository`. |
| Execution attempt | `ExecutionRecord`, `ExecutionId`, `SingleStepRuntimeService` where applicable. |
| Events | `EventEnvelope`, `EventEvidenceRuntimeStore`. |
| Evidence | `EvidenceReference`, existing evidence store behavior. |
| Verification | `VerificationRecord`, evidence references, runtime store. |
| Policy safety | `PolicyDecision`, `EffectClassification`, minimal M0 policy evaluator semantics. |
| Provider inventory work | `ProviderInventoryExecutor`. |
| Provider descriptors | `ProviderDescriptor`, `ProviderCatalog`, `CoreServices`. |
| Persistence | `curios_persistence` primitives and migrations extended only by explicit M1 persistence tasks. |
| API/web boundary | Frozen FastAPI/web outer-boundary pattern from M0. |

## Vertical Slices

| Slice | User-Observable Objective | Boundaries Exercised | Acceptance |
| --- | --- | --- | --- |
| VS-M1-001 Intent to DAG | A simple intent becomes a persisted cognitive problem/plan and bounded work DAG. | Intent/problem contracts, deterministic decomposition, DAG records, API observation. | Persisted records reconstruct the same intent, problem, plan, nodes, and dependency edges. |
| VS-M1-002 Capability to Agent Assignment | A DAG node's capability need is matched to a disposable agent instance. | `CapabilityRequirement`, capability resolver, `AgentDefinition`, `AgentInstance`, lifecycle records. | Known capability matches deterministically; missing/ambiguous capability fails boundedly. |
| VS-M1-003 Bounded Parallel Execution | Independent DAG nodes run concurrently while dependent nodes wait. | DAG readiness, agent lifecycle, executor seam, routing decisions, runtime events. | Fixed concurrency is respected and state transitions remain recorded truth. |
| VS-M1-004 Routing Decision Record | Each executed node records why it used deterministic execution, existing M0 behavior, or a non-invoked model/profile candidate. | Executor seam, model/profile discovery, routing decision records. | Route decisions are persisted and reconstructable without live generation. |
| VS-M1-005 Verification-Gated Completion | Completion requires verification evidence. | Verification records, evidence references, events, work/DAG terminal state. | Executor self-report alone cannot complete a DAG node. |
| VS-M1-006 Recorded-Truth Presentation | API/web display cognitive loop truth from persisted records. | API/web outer boundaries, cognitive/DAG/agent/routing/verification stores. | Displayed state is scoped, current, and not fabricated by frontend or API. |

## Acceptance Criteria

- A simple intent can be submitted and represented as canonical cognitive
  records.
- Deterministic decomposition creates a bounded acyclic work DAG.
- Capability matching either selects an eligible agent definition or records a
  bounded ambiguity/failure.
- Disposable agent instances are bound to work and execution truth without
  replacing `ExecutionRecord`.
- Independent DAG nodes execute in bounded parallel order; dependent nodes wait.
- Routing decisions are recorded without invoking a live model.
- Verification evidence gates completion.
- API/web surfaces display persisted recorded truth.
- M1 architecture/security topology blocks deferred M2+ and M1+ surfaces.
