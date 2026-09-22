---
id: MILESTONE-M0-DEFINITION
title: M0 Milestone Definition
lifecycle: SPECIFIED
artifact_type: milestone_definition
authority: program_planning
milestone_id: M0
date: 2026-09-22
---

# M0 Milestone Definition

## Authority Classification

| Source | Classification | M0 Use |
| --- | --- | --- |
| BOOT-000 final freeze record | FROZEN AUTHORITY | Establishes BOOT completion, deferred scope, and that no post-BOOT task was authorized before M0 planning. |
| BOOT-000 architecture baseline | FROZEN AUTHORITY | Preserves Curios-owned semantics, provider/framework independence, `LOCAL_DOCKER`, and policy `UNKNOWN` safety. |
| BOOT-000 decision baseline | FROZEN AUTHORITY | Supplies frozen stack, topology, environment, contracts, test, security, observability, CI, and task-control decisions. |
| BOOT-000 task pack and implementation DAG | FROZEN AUTHORITY | Defines the Build Pack task/gate model reused for M0. |
| TASK-BOOT-009 through TASK-BOOT-013 contracts | FROZEN AUTHORITY | Provide M0 canonical contract vocabulary and runtime state semantics. |
| TASK-BOOT-014 through TASK-BOOT-016 tests | FROZEN AUTHORITY | Provide contract, architecture, and security gate patterns that M0 must evolve narrowly. |
| TASK-BOOT-017 through TASK-BOOT-024 foundations | FROZEN AUTHORITY | Provide core, provider, API, and web foundations reused unchanged where possible. |
| TASK-BOOT-025 and TASK-BOOT-026 gates | FROZEN AUTHORITY | Provide CI and BOOT acceptance patterns for M0 quality gates. |
| TASK-BOOT-027 independent verification | FROZEN AUTHORITY | Establishes that the BOOT baseline is fit as the starting point for M0 planning. |
| Historical P1-P6 and Phase 0 references | HISTORICAL DESIGN INPUT | Mentioned as authority sources but not tracked as executable artifacts; cannot be promoted directly into M0 tasks without reconciliation. |
| M0 vertical slices and task inventory in this artifact set | DERIVED PROPOSAL | A concrete executable program derived from frozen BOOT boundaries. Becomes M0 planning authority only after review/approval. |
| Full cognitive graph runtime, multi-agent orchestration, DataLab, self-improvement, production IAM, cloud infrastructure, external brokers, live LLM quality gates | NOT AUTHORIZED / DEFERRED | Explicitly excluded from BOOT and not included in M0. |

## Milestone

Identifier: `M0`

Name: Governed Local Work Execution Slice

Purpose: turn the frozen BOOT foundations into the smallest meaningful CuriosOS
runtime capability: a local, deterministic, evidence-backed work execution
path that preserves Curios-owned contracts, policy safety, persistence,
observability, API/web boundaries, and runtime truth.

## Capability Delivered

M0 delivers a single local vertical slice:

1. A user or test submits a bounded work request through the FastAPI boundary.
2. CuriosOS creates a canonical `WorkItem` and policy/effect context.
3. A minimal policy evaluator makes a fail-safe decision for the requested
   effect.
4. A single-step local runtime executes only an authorized provider-inventory
   capability.
5. Runtime events, execution state, evidence, and result references are
   persisted in PostgreSQL through provider-local persistence.
6. API and web surfaces show recorded runtime truth rather than fabricated
   status.
7. CI and acceptance gates prove the slice deterministically without live
   Ollama, GPU, external network, or post-BOOT orchestration features.

## Entry Criteria

- BOOT-000 is `VALIDATED, FROZEN`, integrated into `main`, and synchronized
  with `origin/main`.
- `BOOT-VERIFY-PG-READINESS-001` is verified.
- TASK-BOOT-001 through TASK-BOOT-028 are `VALIDATED, FROZEN`.
- M0 planning artifacts are reviewed and accepted.
- No M0 implementation task starts before its allowed surfaces are explicitly
  authorized by the M0 task pack.

## Exit Criteria

M0 exits only when all are true:

- Every `TASK-M0-*` task in the approved M0 task pack is `VALIDATED, FROZEN`.
- The M0 acceptance suite proves the governed local work execution slice.
- M0 CI gates include M0 contract, architecture, security, integration,
  acceptance, API, and web checks.
- Independent M0 verification records lifecycle, architecture, security,
  persistence, runtime truth, and acceptance evidence.
- The M0 final freeze record identifies the final M0 baseline.
- No unresolved M0 blocker remains.

## In Scope

- M0 planning authority and status ledger.
- Narrow evolution of BOOT security/architecture topology for explicit M0
  surfaces only.
- PostgreSQL-backed persistence for M0 work, execution, event, evidence,
  artifact, policy decision, and verification records.
- Alembic migrations required for M0 persistence.
- Minimal Curios-owned runtime service for one work item at a time.
- Minimal deterministic policy evaluator preserving `UNKNOWN` as
  non-authorizing.
- One built-in provider-inventory execution capability.
- API endpoints for work creation, status, execution, events, evidence, and
  runtime truth.
- Web bootstrap evolution into a minimal M0 work console.
- M0 integration, CI, acceptance, independent verification, and freeze records.

## Explicitly Out Of Scope

- General DAG scheduler.
- Multi-agent orchestration runtime.
- Agent autonomy, planning, memory, learning, or self-improvement.
- Model generation, model routing, prompt systems, or live LLM quality gates.
- DataLab and application intelligence.
- Full policy language, production IAM, RBAC/ABAC, approval workflow, or secret
  resolver.
- External event brokers.
- Production observability stack.
- Cloud infrastructure provisioning.
- Arbitrary provider execution beyond the provider-inventory capability.
- New product UI beyond the minimal M0 work console.

## Frozen BOOT Assumptions

- CuriosOS contracts remain canonical.
- Pydantic, FastAPI, SQLAlchemy, PostgreSQL, Ollama, React, Vite, Docker, and
  OpenTelemetry remain provider/framework/tooling implementations.
- Provider/framework code depends inward; `curios_contracts` and `curios_core`
  must not depend outward.
- `ObjectReference(kind, ref_id)` is the only generic object/reference
  abstraction.
- `LOCAL_DOCKER` remains the canonical local environment profile.
- `PolicyDecision.UNKNOWN` remains distinct from `DENY` and never authorizes a
  governed effect.

## Security Constraints

- M0 tasks may authorize only their explicit new surface.
- Secret scanning must cover every new governed source/config/docs surface.
- No task may broadly allow `services/**`, `providers/**`, arbitrary
  `apps/**`, arbitrary `.github/**`, or arbitrary runtime packages.
- M0 persistence must not store secret values.
- Core context may carry supplied authority but must not grant or evaluate it.
- Policy evaluation remains minimal, deterministic, and fail-safe.

## Operational Constraints

- M0 ordinary tests must be deterministic.
- Ordinary CI must not require live Ollama, GPU, downloaded models, or external
  network model calls.
- PostgreSQL integration uses the existing `LOCAL_DOCKER` service and must
  preserve the named volume.
- Persistent database changes require explicit Alembic migrations and rollback
  consideration.
- Generated build artifacts remain uncommitted unless explicitly authorized.

## Acceptance Criteria

- A bounded work request can be submitted through the API and observed through
  API and web surfaces.
- Work, execution, event, evidence, policy, and result facts are persisted and
  recoverable after runtime object disposal.
- A successful provider-inventory execution produces canonical events,
  evidence, and result references.
- A denied or unknown policy decision prevents governed execution and produces
  bounded canonical failure evidence.
- Runtime views show recorded state, not fabricated activity.
- Architecture and security tests continue to block inward dependency and
  topology violations.
- CI and M0 acceptance gates pass deterministically.
