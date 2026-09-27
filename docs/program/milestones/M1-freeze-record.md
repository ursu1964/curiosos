---
id: M1-FREEZE-RECORD
title: M1 Final Freeze Record
lifecycle: FROZEN
artifact_type: freeze_record
authority: authoritative
milestone_id: M1
date: 2026-09-27
---

# M1 Final Freeze Record

## Decision

M1 CLOSURE: PASS

M1 is approved for final `VALIDATED, FROZEN` status after TASK-M1-019 is
committed and integrated into `main`.

## Baselines

| Baseline | Meaning |
| --- | --- |
| `f9f138f0048737a1c91a14f21c3d711e03a6db57` | Independently verified and published M1 input baseline containing integrated TASK-M1-018 independent verification. |
| TASK-M1-019 closure commit | Final authoritative M1 baseline after this freeze record, TASK-M1-019 evidence, and the M1 ledger closure are committed and integrated into `main`. |

The final closure commit SHA is intentionally not asserted inside this
uncommitted artifact. Repository history establishes it once TASK-M1-019 is
committed and integrated.

## BOOT and M0 Relationship

M1 extends the frozen BOOT-000 and M0 foundations. It does not replace BOOT or
M0 authority and does not redefine their canonical semantics.

BOOT-000 remains the authority for canonical contracts, `ObjectReference`,
`Result`, `ContractError`, core/provider/API/web direction, and baseline
security/architecture guardrail patterns.

M0 remains the authority for governed local work execution, persistence,
policy, runtime event/evidence/work truth, provider inventory, M0 API/web
observation, integration, CI, acceptance, independent verification, and final
freeze conventions.

## Closure Criteria

| Criterion | Result |
| --- | --- |
| M1-000A and TASK-M1-001 through TASK-M1-018 are `VALIDATED, FROZEN`. | PASS |
| TASK-M1-018 is integrated, published, and remote-CI-verified at `f9f138f0048737a1c91a14f21c3d711e03a6db57`. | PASS |
| TASK-M1-019 records final freeze/status closure. | PASS |
| M1 DAG waves and program gates through M1-VERIFY are closed. | PASS |
| VS-M1-001 through VS-M1-006 integration proof passed. | PASS |
| VS-M1-001 through VS-M1-006 acceptance proof passed. | PASS |
| Exact-SHA Quality Gates run `36337078696` passed on the verified input baseline. | PASS |
| Final architecture boundary remains intact. | PASS |
| Final security and authority topology remains exact. | PASS |
| Final dependency and migration state remains unchanged by closure. | PASS |
| No live model, cloud provider, credential, release, tag, or deployment is required for M1 closure. | PASS |
| No required M1 work remains only on an unmerged branch. | PASS |
| No unresolved M1 blocker remains. | PASS |
| No M2 executable task is authorized by this freeze. | PASS |

## Frozen M1 Scope

M1 freezes the first cognitive loop:

- cognitive intent/problem/assumption/decision/plan records;
- deterministic/template intent decomposition;
- bounded Work DAG records and derived readiness/terminal views;
- deterministic capability matching;
- canonical agent definition/instance persistence;
- agent lifecycle repository and canonical lifecycle events;
- executor seam and deterministic executors;
- provider-local model/profile discovery records without generation;
- deterministic routing decision records;
- bounded DAG runner;
- bounded verification loop and evidence binding;
- FastAPI M1 cognitive-loop endpoints;
- web cognitive-loop console over explicit API-boundary capabilities;
- VS-M1-001 through VS-M1-006 integration tests;
- Quality Gates M1 package/API, PostgreSQL, VS integration, acceptance,
  architecture, security, frontend, and full-pytest gates;
- M1 acceptance suite;
- independent M1 verification record;
- final M1 freeze/status closure.

## Deferred Scope

The following remain outside M1 and are not authorized by this freeze:

- autonomous agents;
- production-scale scheduler;
- unbounded or distributed DAG runtime;
- generalized tool execution;
- model generation, prompt orchestration, chat, embeddings, or cloud model
  execution;
- full model-router optimization;
- knowledge or memory runtime;
- DataLab;
- learning or self-improvement;
- production IAM, RBAC/ABAC, or full policy language;
- secret resolver;
- external brokers;
- cloud infrastructure;
- live LLM quality gates;
- multi-project execution;
- any M2 implementation task.

`1.txt` and unreconciled P1-P6 material remain historical design input only.
They do not directly authorize executable work.

## Integration and Acceptance Freeze

M1 closure relies on:

- TASK-M1-015 integration PASS for VS-M1-001 through VS-M1-006;
- TASK-M1-017 acceptance PASS for VS-M1-001 through VS-M1-006;
- TASK-M1-018 independent verification PASS;
- final TASK-M1-019 closure checks.

Latest exact-SHA remote Quality Gates evidence at
`f9f138f0048737a1c91a14f21c3d711e03a6db57`:

- Frontend: success, including 26 web tests, typecheck, and build;
- Python, Backend, Providers, Integration: success;
- Repository Hygiene: success;
- M1 package/API: 618 passed, 9 intentional deselections;
- M1 PostgreSQL: 4 passed;
- VS-M1 integration: 6 passed;
- acceptance: 14 passed, no skips/deselections;
- security: 360 passed;
- architecture: 36 passed;
- full pytest: 1175 passed.

## Historical Transients

M1-017 publication run `36312837839` attempt 1 failed in the Frontend
Corepack/Node/Undici setup before repository frontend execution. Attempt 2
succeeded at the same exact SHA with no repository change. TASK-M1-018
classified this as a resolved CI/toolchain infrastructure transient, not a
product or acceptance defect.

That transient remains part of milestone history and is not an unresolved M1
blocker.

## Architecture Freeze

The frozen M1 architecture preserves this direction:

```text
curios_contracts
  <- curios_core
  <- cognitive / DAG / capability / persistence / runtime / providers
  <- FastAPI API
  <- web interface
```

Framework, provider, database, model/profile, runtime, API, and web
implementation details do not become canonical Curios semantics.

M1 adds bounded cognitive-loop records and runtime seams without changing
BOOT/M0 authority direction.

## Security Freeze

The final M1 security topology authorizes only the frozen current M1 surfaces:

- exact M1 package, API, web, integration, acceptance, workflow, evidence, and
  verification surfaces;
- no direct App network authority;
- explicit web API-boundary capabilities only;
- bounded executor and routing authority;
- no policy bypass;
- no scheduler daemon;
- no live model, cloud provider, credential, release, deployment, or publishing
  authority.

Workflow permissions remain least privilege: `contents: read`.

## API and Frontend Freeze

The frozen M1 API surface is exactly:

- `POST /m1/intents/decompose`
- `POST /m1/dag/run-once`
- `POST /m1/verification/complete`

M1-013 malformed JSON and media-type corrections remain frozen.

M1-014 draft/canonical separation remains frozen: editable draft input cannot
mutate accepted canonical intent truth, and no IntentId A plus Objective B
hybrid may be presented as canonical truth.

## Persistence and Migration Freeze

The final M1 migration head is:

`0005_m1_routing_decision_records`

M1 durable record families remain:

- Work DAG records;
- AgentDefinition and AgentInstance records;
- agent lifecycle events;
- RoutingDecision records;
- existing M0 event/evidence/work persistence.

TASK-M1-019 makes no schema or migration change.

## Dependency Freeze

The final M1 dependency and lockfile state remains unchanged by closure:

- `uv.lock` remains consistent;
- `pnpm-lock.yaml` remains consistent;
- no dependency manifest changes are introduced by TASK-M1-019;
- M1 closes without live model dependencies or external model credentials.

## Release and Deployment Policy

TASK-M1-019 creates no tag, GitHub release, or deployment.

Release and deployment remain outside M1 closure.

## Known Non-Blocking Warnings

Accepted verification surfaces report existing dependency warnings:

- FastAPI/Starlette `TestClient` `httpx` deprecation warning;
- AnyIO `BlockingPortal` alias deprecation warning.

They are recorded technical debt and are not M1 closure blockers.

## Next Program State

NEXT: AUTHORIZATION REQUIRED

M1 final freeze does not authorize M2 execution or any post-M1 implementation
task.
