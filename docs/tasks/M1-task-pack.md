---
id: M1-TASK-PACK
title: M1 Atomic Task Pack
lifecycle: FROZEN
artifact_type: task_pack
authority: program_planning
milestone_id: M1
date: 2026-09-23
---

# M1 Atomic Task Pack

## Common Rules

- M1 tasks must preserve all frozen BOOT and M0 boundaries.
- M1 tasks use `TASK-M1-*`; do not create `TASK-M0-020`.
- Each task may authorize only its explicit new surface.
- No task may mark itself `VALIDATED` or `FROZEN`; independent validation is
  required.
- M1 does not implement M2+ deferred scope.
- M1 does not treat `1.txt` or unreconciled P1-P6 material as direct task
  authority.
- Every modifying task must update task evidence and the M1 ledger according to
  Build Pack conventions.

## Task Inventory

| Task | Title | Objective | Prerequisites | Primary Authorized Surfaces |
| --- | --- | --- | --- | --- |
| TASK-M1-001 | M1 Topology and Guardrail Transition | Authorize exact M1 package/test/doc surfaces without broadening BOOT/M0 topology. | M1 readiness validation | docs, security tests, architecture tests, metadata only if required |
| TASK-M1-002 | Cognitive Intent and Problem Contracts | Add minimal canonical intent/problem/assumption/decision/plan contracts. | TASK-M1-001 | `packages/python/curios_contracts/**`, TypeScript contracts if required, tests, docs |
| TASK-M1-003 | Deterministic Intent Decomposition | Implement bounded template/rule decomposition from simple intent to plan/work suggestions. | TASK-M1-002 | M1 cognitive package/module, tests, docs |
| TASK-M1-004 | Work DAG Records and State | Persist bounded DAG nodes/edges over `WorkItem` references with acyclicity/readiness semantics. | TASK-M1-002 | M1 runtime/persistence modules, migrations if required, tests |
| TASK-M1-005 | Capability Resolver Foundation | Deterministically match frozen `CapabilityRequirement` values to known capabilities/agent definitions. | TASK-M1-001 | M1 capability resolver module, tests |
| TASK-M1-006 | Agent Definition and Instance Persistence | Persist and retrieve canonical `AgentDefinition` and `AgentInstance` records for M1 assignment. | TASK-M1-001 | M1 runtime/persistence modules, migrations if required, tests |
| TASK-M1-007 | Agent Lifecycle Repository and Events | Record agent lifecycle transitions and canonical events without duplicating execution records. | TASK-M1-005, TASK-M1-006 | M1 runtime modules, event/evidence integration tests |
| TASK-M1-008 | Executor Seam and Deterministic Executors | Add Curios-owned executor seam and deterministic executors for bounded M1 tasks. | TASK-M1-003, TASK-M1-004, TASK-M1-005, TASK-M1-007 | M1 runtime modules, tests |
| TASK-M1-009 | Model/Profile Discovery Records | Add profile/discovery records for local model candidates without generation. | TASK-M1-001 | provider/profile module, tests |
| TASK-M1-010 | Routing Decision Records | Persist route decisions over executor/model-profile candidates without full router optimization. | TASK-M1-008, TASK-M1-009 | M1 runtime/persistence modules, tests |
| TASK-M1-011 | Bounded DAG Runner | Execute ready DAG nodes with a fixed concurrency limit and dependency-aware state transitions. | TASK-M1-004, TASK-M1-007, TASK-M1-008, TASK-M1-010 | M1 runtime modules, tests |
| TASK-M1-012 | Verification Loop and Evidence Binding | Require verification evidence before DAG node/work completion. | TASK-M1-011 | M1 runtime verification modules, tests |
| TASK-M1-013 | M1 API Cognitive Loop Endpoints | Expose intent, DAG, agent, routing, verification, and recorded-truth observation through FastAPI. | TASK-M1-011, TASK-M1-012 | `apps/api/**`, tests, docs |
| TASK-M1-014 | M1 Web Cognitive Loop Console | Extend web console to show recorded M1 cognitive loop truth. | TASK-M1-013 | `apps/web/**`, tests, docs |
| TASK-M1-015 | M1 Integration Tests | Add cross-boundary integration tests for VS-M1-001 through VS-M1-006. | TASK-M1-013, TASK-M1-014 | exact `tests/integration/**` files, docs |
| TASK-M1-016 | M1 CI Quality Gate Update | Extend quality gates for M1 deterministic package/integration/acceptance checks. | TASK-M1-015 | `.github/workflows/quality-gates.yml`, security topology, evidence |
| TASK-M1-017 | M1 Acceptance Suite | Add milestone-level acceptance tests for the first cognitive loop. | TASK-M1-016 | exact `tests/acceptance/**` files, docs |
| TASK-M1-018 | M1 Independent Verification Record | Independently verify complete M1 baseline. | TASK-M1-017 | docs/tasks, status ledger |
| TASK-M1-019 | M1 Final Freeze | Record final M1 freeze/status closure. | TASK-M1-018 | docs/program/milestones, docs/program/status-ledger, docs/tasks |

## Detailed Task Constraints

### TASK-M1-001

Objective: transition security and architecture guardrails from frozen M0 to
planned M1 without authorizing implementation surfaces prematurely.

Prerequisites: independent M1 readiness validation.

Authorized surfaces: M1 docs, security tests, architecture tests, and metadata
only when needed to name explicit planned surfaces.

Responsibilities: planned-vs-authorized topology, exact future task ownership,
M1+ blocking, evidence.

Prohibited scope: production packages, runtime behavior, contracts, persistence,
API routes, web features, CI workflow.

Acceptance: arbitrary cognitive/runtime/agent/model/API/web/test surfaces remain
blocked until their owning task authorizes them.

Verification: security, architecture, topology adversarial tests, diff check.

Lifecycle: `IMPLEMENTED, TESTED`; independent validation required.

Downstream consumers: TASK-M1-002, TASK-M1-005, TASK-M1-006, TASK-M1-009.

### TASK-M1-002

Objective: add the minimal canonical cognitive records required for M1.

Prerequisites: TASK-M1-001 validated, frozen, and integrated.

Authorized surfaces: canonical contracts, TypeScript contracts only if needed,
contract/schema tests, docs, evidence.

Responsibilities: `Intent`, `Problem`, `Assumption`, `Decision`, and `Plan`
records; serialization; object references.

Prohibited scope: knowledge graph runtime, memory system, model prompts,
workflow engine, UI behavior.

Acceptance: records serialize deterministically, reference existing canonical
objects with `ObjectReference`, and do not duplicate `WorkItem`.

Verification: contract tests, schema tests, architecture/security.

Downstream consumers: TASK-M1-003 and TASK-M1-004.

### TASK-M1-003

Objective: implement deterministic/template decomposition from a simple intent
to a bounded plan/work-DAG proposal.

Prerequisites: TASK-M1-002 validated, frozen, and integrated.

Authorized surfaces: M1 cognitive implementation module, tests, evidence.

Responsibilities: fixed supported intent categories, bounded decomposition
results, unsupported-intent failure.

Prohibited scope: model-backed planning, autonomous decomposition, prompt
engineering, learning, DataLab-specific analysis.

Acceptance: same input produces same decomposition; unsupported intent is
bounded and non-executing.

Verification: unit tests, contract round trips, security.

Downstream consumers: TASK-M1-008.

### TASK-M1-004

Objective: persist bounded DAG nodes/edges over `WorkItem` references and
derive readiness/terminal dependency state.

Prerequisites: TASK-M1-002 validated, frozen, and integrated.

Authorized surfaces: M1 runtime/persistence modules, migrations if required,
tests, evidence.

Responsibilities: DAG identity, acyclicity, dependency edges, readiness,
terminal behavior, failure/cancellation propagation, reconstruction.

Prohibited scope: production scheduler, distributed execution, retries,
external queues, arbitrary graph database.

Acceptance: DAGs are acyclic, reconstructable, and reference work without
duplicating work state.

Verification: unit, PostgreSQL integration if persistence is added,
architecture/security.

Downstream consumers: TASK-M1-008 and TASK-M1-011.

### TASK-M1-005

Objective: implement deterministic capability matching.

Prerequisites: TASK-M1-001 validated, frozen, and integrated.

Authorized surfaces: M1 capability resolver module, tests, evidence.

Responsibilities: requirements, offered capabilities, exact matching,
ambiguity/failure records.

Prohibited scope: marketplace, ontology, learning-based ranking, provider
selection, policy grants.

Acceptance: known requirement matches eligible capability; ambiguous/missing
matches fail boundedly.

Verification: unit, contract, architecture/security.

Downstream consumers: TASK-M1-007 and TASK-M1-008.

### TASK-M1-006

Objective: persist canonical agent definitions and instances for M1 assignment.

Prerequisites: TASK-M1-001 validated, frozen, and integrated.

Authorized surfaces: M1 runtime/persistence modules, migrations if required,
tests, evidence.

Responsibilities: create/read agent definitions and disposable agent instances
using frozen contracts.

Prohibited scope: autonomous agents, prompts, persistent worker processes,
sleep/wake/rebirth, scheduler ownership.

Acceptance: agent instances bind to work and optional execution without
duplicating `ExecutionRecord`.

Verification: unit, persistence integration if required, architecture/security.

Downstream consumers: TASK-M1-007.

### TASK-M1-007

Objective: record agent lifecycle transitions and events.

Prerequisites: TASK-M1-005 and TASK-M1-006 validated, frozen, and integrated.

Authorized surfaces: M1 runtime modules, tests, evidence.

Responsibilities: state transitions for `CREATED`, `READY`, `ACTIVE`,
`WAITING`, `COMPLETED`, `FAILED`, `CANCELLED`; canonical events.

Prohibited scope: execution engine, scheduler, authority grants, agent memory.

Acceptance: transitions are legal, persisted, event-backed, and reconstructable.

Verification: unit, integration, event/evidence checks.

Downstream consumers: TASK-M1-008 and TASK-M1-011.

### TASK-M1-008

Objective: add Curios-owned executor seam and deterministic executors.

Prerequisites: TASK-M1-003, TASK-M1-004, TASK-M1-005, and TASK-M1-007
validated, frozen, and integrated.

Authorized surfaces: M1 runtime modules, tests, evidence.

Responsibilities: executor request/outcome protocol, deterministic supported
executors, bounded failure translation.

Prohibited scope: generic tool framework, model invocation, arbitrary provider
execution, retry framework.

Acceptance: executor outcomes are deterministic and produce canonical
events/evidence without lower-layer leakage.

Verification: unit, integration, architecture/security.

Downstream consumers: TASK-M1-010 and TASK-M1-011.

### TASK-M1-009

Objective: add local model/profile discovery records.

Prerequisites: TASK-M1-001 validated, frozen, and integrated.

Authorized surfaces: provider/profile module, tests, evidence.

Responsibilities: profile shape, unavailable-provider behavior, no-secret
metadata, deterministic fakeable tests.

Prohibited scope: model generation, prompt execution, cloud models, model
quality evaluation, live LLM quality gates.

Acceptance: local model candidates can be represented without invoking them.

Verification: unit tests, no-live-model ordinary tests, security.

Downstream consumers: TASK-M1-010.

### TASK-M1-010

Objective: persist routing decision records.

Prerequisites: TASK-M1-008 and TASK-M1-009 validated, frozen, and integrated.

Authorized surfaces: M1 runtime/persistence modules, tests, evidence.

Responsibilities: route candidate list, selected route, rationale, resource
constraints, no-model route.

Prohibited scope: optimizer, learning router, live model invocation, cloud
provider routing.

Acceptance: decisions are deterministic and reconstructable.

Verification: unit, persistence integration if required, architecture/security.

Downstream consumers: TASK-M1-011.

### TASK-M1-011

Objective: implement bounded dependency-aware local DAG runner.

Prerequisites: TASK-M1-004, TASK-M1-007, TASK-M1-008, and TASK-M1-010
validated, frozen, and integrated.

Authorized surfaces: M1 runtime modules, tests, evidence.

Responsibilities: fixed maximum concurrency, readiness, deterministic tie
breaking, state transitions, failure/cancellation propagation, events.

Prohibited scope: production scheduler, distributed workers, external queues,
retry engine, long-running daemon.

Acceptance: independent nodes run concurrently within bound; dependent nodes
wait; restart reads recorded truth.

Verification: unit, integration, PostgreSQL where applicable.

Downstream consumers: TASK-M1-012 and TASK-M1-013.

### TASK-M1-012

Objective: gate completion on verification evidence.

Prerequisites: TASK-M1-011 validated, frozen, and integrated.

Authorized surfaces: M1 runtime verification modules, tests, evidence.

Responsibilities: separate execution output, verification action, verification
record, evidence, and completion decision.

Prohibited scope: DataLab evaluator, self-improvement, generalized test
generation, live LLM judgment.

Acceptance: work/DAG completion cannot be recorded without verification result
and evidence.

Verification: unit, integration, security.

Downstream consumers: TASK-M1-013.

### TASK-M1-013

Objective: expose M1 cognitive-loop recorded truth through FastAPI.

Prerequisites: TASK-M1-011 and TASK-M1-012 validated, frozen, and integrated.

Authorized surfaces: exact `apps/api` modules/routes/tests, docs/evidence.

Responsibilities: submit simple intent, observe cognitive records, DAG,
agents, routing decisions, verification, events, and evidence.

Prohibited scope: generalized assistant API, arbitrary work submission,
model-generation endpoint, direct database authority.

Acceptance: API exposes recorded truth and bounded errors without native
leakage.

Verification: API tests, integration, architecture/security.

Downstream consumers: TASK-M1-014 and TASK-M1-015.

### TASK-M1-014

Objective: extend web console to show M1 cognitive loop truth.

Prerequisites: TASK-M1-013 validated, frozen, and integrated.

Authorized surfaces: exact `apps/web` files/tests, docs/evidence.

Responsibilities: submit simple intent and display cognitive/DAG/agent/routing
and verification truth from API.

Prohibited scope: generalized cognitive dashboard, live graph animation,
DataLab UI, model controls, arbitrary agents/tools.

Acceptance: deterministic tests require no live backend/model and stale data
cannot overwrite selected intent truth.

Verification: Vitest, typecheck, build, security.

Downstream consumers: TASK-M1-015.

### TASK-M1-015

Objective: add M1 vertical-slice integration tests.

Prerequisites: TASK-M1-013 and TASK-M1-014 validated, frozen, and integrated.

Authorized surfaces: exact integration test files, docs/evidence.

Responsibilities: prove VS-M1-001 through VS-M1-006 across frozen boundaries.

Prohibited scope: production fixes, CI workflow changes, acceptance ownership,
browser E2E unless explicitly authorized later.

Acceptance: integration tests fail on broken intent-to-DAG, capability/agent,
parallelism, routing, verification, or API/web truth.

Verification: integration, PostgreSQL where required, no live model.

Downstream consumers: TASK-M1-016.

### TASK-M1-016

Objective: update CI quality gates for M1.

Prerequisites: TASK-M1-015 validated, frozen, and integrated.

Authorized surfaces: exact workflow file, security tests, docs/evidence.

Responsibilities: invoke M1 packages/tests/integration/acceptance while
preserving BOOT/M0 gates.

Prohibited scope: deployment, release, publishing, cloud, live model gates.

Acceptance: CI fails on M1 verification failures and remains least privilege.

Verification: workflow static validation, local reproduction, security.

Downstream consumers: TASK-M1-017.

### TASK-M1-017

Objective: add M1 acceptance suite.

Prerequisites: TASK-M1-016 validated, frozen, and integrated.

Authorized surfaces: exact acceptance test files, docs/evidence.

Responsibilities: milestone-level proof for VS-M1-001 through VS-M1-006.

Prohibited scope: product implementation, M2 scenarios, live model requirement.

Acceptance: every M1 vertical slice has objective PASS/FAIL evidence.

Verification: acceptance, full deterministic suite, security/architecture.

Downstream consumers: TASK-M1-018.

### TASK-M1-018

Objective: independently verify complete M1 baseline.

Prerequisites: TASK-M1-017 validated, frozen, and integrated.

Authorized surfaces: verification record and status ledger only.

Responsibilities: lifecycle, history, architecture, security, CI, acceptance,
dependency, hygiene, and mechanical verification.

Prohibited scope: implementation fixes, final freeze, M2 planning.

Acceptance: no unresolved M1 blocker remains.

Verification: full authoritative M1 suite.

Downstream consumers: TASK-M1-019.

### TASK-M1-019

Objective: perform final M1 closure and freeze.

Prerequisites: TASK-M1-018 validated, frozen, and integrated.

Authorized surfaces: M1 freeze record, status ledger, evidence.

Responsibilities: close milestone, record final baseline semantics, identify
next program state without starting it.

Prohibited scope: implementation changes, M2 execution, branch/worktree cleanup
unless explicitly required.

Acceptance: every M1 task/gate is lifecycle-consistent and no blocker remains.

Verification: ledger/evidence consistency, architecture/security if affected,
diff check.
