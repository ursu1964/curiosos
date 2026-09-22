---
id: M0-TASK-PACK
title: M0 Atomic Task Pack
lifecycle: SPECIFIED
artifact_type: task_pack
authority: program_planning
milestone_id: M0
date: 2026-09-22
---

# M0 Atomic Task Pack

## Common Rules

- M0 tasks must preserve all frozen BOOT boundaries.
- M0 tasks use `TASK-M0-*`; do not create `TASK-BOOT-029`.
- Each task may authorize only its explicit new surface.
- No task may mark itself `VALIDATED` or `FROZEN`; independent verification is required.
- M0 does not implement M1+ deferred scope.
- Every modifying task must update task evidence and the M0 ledger according to Build Pack conventions.

## Task Inventory

| Task | Title | Objective | Prerequisites | Primary Authorized Surfaces | Verification |
| --- | --- | --- | --- | --- | --- |
| TASK-M0-001 | M0 Topology and Guardrail Transition | Authorize exact M0 package/test/doc surfaces and update architecture/security checks without broadening topology. | BOOT-000, M0-000A | `docs/**`, `tests/security/**`, `tests/architecture/**`, root workspace metadata only if required for explicit M0 package placeholders | security, architecture, diff |
| TASK-M0-002 | PostgreSQL Runtime Persistence Foundation | Add M0 persistence package and Alembic migration for work, execution, event, evidence, artifact, policy decision, and verification records. | TASK-M0-001 | `packages/python/curios_persistence/**`, migration surface explicitly authorized by TASK-M0-001, package metadata, tests | unit, integration PostgreSQL, migration check, security |
| TASK-M0-003 | Minimal Policy Evaluator | Implement deterministic fail-safe policy evaluator for M0 effects and provider-inventory work. | TASK-M0-001 | `packages/python/curios_policy/**`, tests, docs | unit, contract, security |
| TASK-M0-004 | Event and Evidence Runtime Store | Implement runtime event/evidence writer interfaces backed by canonical contracts and M0 persistence. | TASK-M0-001, TASK-M0-002 | `packages/python/curios_runtime/**` event/evidence modules or `packages/python/curios_persistence/**` if owned there, tests | unit, integration, architecture |
| TASK-M0-005 | Work Repository and State Transitions | Implement persisted WorkItem/ExecutionRecord repositories and allowed lifecycle transitions. | TASK-M0-002 | `packages/python/curios_runtime/**`, `packages/python/curios_persistence/**`, tests | unit, integration, contract |
| TASK-M0-006 | Single-Step Work Runtime Service | Implement one-at-a-time local work execution service that evaluates policy, records state/events/evidence, and never schedules DAGs. | TASK-M0-003, TASK-M0-004, TASK-M0-005 | `packages/python/curios_runtime/**`, tests | unit, integration, security |
| TASK-M0-007 | Provider Inventory Executor | Add the only M0 executor capability: collect provider descriptors through existing provider catalogs and produce canonical result/evidence. | TASK-M0-006 | `packages/python/curios_runtime/**`, provider integration tests | unit, integration, acceptance-prep |
| TASK-M0-008 | M0 API Work Endpoints | Add FastAPI routes for work creation, status, execution, events, evidence, and provider-inventory work only. | TASK-M0-007 | `apps/api/**`, tests, docs | API tests, integration, architecture, security |
| TASK-M0-009 | M0 Web Work Console | Evolve web bootstrap into minimal work console consuming only M0 API routes. | TASK-M0-007 | `apps/web/**`, TypeScript package usage where needed, tests | Vitest, typecheck, build, security |
| TASK-M0-010 | M0 Integration Test Foundation | Add end-to-end deterministic integration tests for VS-M0-001 through VS-M0-003. | TASK-M0-008, TASK-M0-009 | `tests/integration/**`, `tests/fixtures/**`, docs | integration, PostgreSQL, no live Ollama |
| TASK-M0-011 | M0 CI Quality Gate Update | Extend CI to run M0 runtime, persistence, API, web, integration, and security gates. | TASK-M0-010 | `.github/workflows/quality-gates.yml`, `tests/security/**`, evidence | workflow static, local reproduction |
| TASK-M0-012 | M0 Acceptance Suite | Add M0 acceptance tests proving all vertical slices and runtime truth. | TASK-M0-011 | `tests/acceptance/**`, docs | acceptance, full deterministic suite |
| TASK-M0-013 | M0 Independent Verification Record | Independently verify the complete M0 baseline and record evidence. | TASK-M0-012 | `docs/tasks/**`, `docs/program/status-ledger/**` | independent verification |
| TASK-M0-014 | M0 Final Freeze | Record final M0 freeze/status-ledger closure. | TASK-M0-013 | `docs/program/milestones/**`, `docs/program/status-ledger/**`, `docs/tasks/**` | final closure checks |

## Detailed Task Constraints

### TASK-M0-001

Prohibited scope: production runtime behavior, database schemas, API endpoints,
web product UI, policy engines, persistence implementation.

Acceptance: M0 security topology rejects arbitrary `services/**`,
`providers/**`, unrelated `apps/**`, arbitrary `.github/**`, and unapproved
runtime packages while allowing only the M0 surfaces explicitly needed by later
tasks.

### TASK-M0-002

Prohibited scope: domain objects becoming ORM models, provider-native database
types crossing canonical boundaries, application repositories outside M0
persistence, multi-tenant or production IAM persistence.

Acceptance: migrations are reversible where safe, PostgreSQL integration is
isolated, and persisted records map to canonical IDs and JSON-compatible
contract payloads.

### TASK-M0-003

Prohibited scope: full policy language, RBAC/ABAC, approval workflow, secret
resolver, credential handling, production IAM.

Acceptance: unsupported, unknown, or unevaluable governed effects do not
authorize execution.

### TASK-M0-006

Prohibited scope: DAG scheduler, async job queue, multi-agent orchestration,
model router, arbitrary tool execution, external writes, destructive effects.

Acceptance: one work item can transition through created/ready/running/
completed or failed/blocked states with persisted evidence.

### TASK-M0-008

Prohibited scope: new canonical HTTP semantics, FastAPI leaking inward,
unbounded API surface, frontend behavior, direct database access from route
handlers when a service/repository boundary exists.

Acceptance: HTTP translates canonical `Result`/`ContractError` at the outer
boundary and never redefines Curios contracts.

### TASK-M0-009

Prohibited scope: duplicated canonical models, direct Python/backend imports,
provider-native objects, product workflows beyond M0 work console.

Acceptance: web tests/build are deterministic and require no live backend.
