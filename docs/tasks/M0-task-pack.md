---
id: M0-TASK-PACK
title: M0 Atomic Task Pack
lifecycle: FROZEN
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
| TASK-M0-009 | M0 Web Work Console | Evolve web bootstrap into minimal work console consuming only M0 API routes. | TASK-M0-008 | `apps/web/**`, TypeScript package usage where needed, tests | Vitest, typecheck, build, security |
| TASK-M0-010 | M0 Integration Test Foundation | Add end-to-end deterministic integration tests for VS-M0-001 through VS-M0-003. | TASK-M0-008, TASK-M0-009 | `tests/integration/**`, `tests/fixtures/**`, docs | integration, PostgreSQL, no live Ollama |
| TASK-M0-011 | M0 CI Quality Gate Update | Extend CI to run M0 runtime, persistence, API, web, integration, and security gates. | TASK-M0-010 | `.github/workflows/quality-gates.yml`, `tests/security/**`, evidence | workflow static, local reproduction |
| TASK-M0-012 | M0 Acceptance Suite | Add M0 acceptance tests proving all vertical slices and runtime truth. | TASK-M0-011 | `tests/acceptance/**`, docs | acceptance, full deterministic suite |
| TASK-M0-013 | M0 Independent Verification Record | Independently verify the complete M0 baseline and record evidence. | TASK-M0-012 | `docs/tasks/**`, `docs/program/status-ledger/**` | independent verification |
| TASK-M0-014 | M0 Final Freeze | Record final M0 freeze/status-ledger closure. | TASK-M0-013 | `docs/program/milestones/**`, `docs/program/status-ledger/**`, `docs/tasks/**` | final closure checks |

## Detailed Task Constraints

### TASK-M0-001

Objective: authorize exact M0 package, test, and documentation surfaces before
runtime implementation begins.

Prerequisites: BOOT-000 frozen baseline, accepted M0 planning authority.

Authorized surfaces: `docs/**`, `tests/security/**`, `tests/architecture/**`,
and root workspace metadata only when required to name explicit M0 surfaces.

Responsibilities: narrow security topology evolution, architecture-boundary
guards for M0 packages, and task/status evidence.

Prohibited scope: production runtime behavior, database schemas, API endpoints,
web product UI, policy engines, persistence implementation.

Required boundaries: frozen BOOT topology, `curios_contracts` independence,
`curios_core` inward dependency direction, provider/API/web outer boundaries.

Acceptance: M0 security topology rejects arbitrary `services/**`,
`providers/**`, unrelated `apps/**`, arbitrary `.github/**`, and unapproved
runtime packages while allowing only the M0 surfaces explicitly needed by later
tasks.

Verification: security tests, architecture tests, identifier/topology review,
and `git diff --check`.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: none beyond readiness validation.

Gate membership: PG-M0-01.

Downstream consumers: TASK-M0-002 and TASK-M0-003.

### TASK-M0-002

Objective: add the M0 PostgreSQL persistence package and migrations for runtime
records required by the vertical slice.

Prerequisites: TASK-M0-001 validated, frozen, and integrated.

Authorized surfaces: `packages/python/curios_persistence/**`, the explicitly
authorized migration surface, package metadata, persistence tests, evidence.

Responsibilities: schema/migration ownership, repository-local mapping between
canonical IDs/payloads and PostgreSQL records, isolated integration checks.

Prohibited scope: domain objects becoming ORM models, provider-native database
types crossing canonical boundaries, application repositories outside M0
persistence, multi-tenant or production IAM persistence.

Required boundaries: canonical Curios contracts remain semantic authority;
PostgreSQL and SQLAlchemy remain implementation details.

Acceptance: migrations are reversible where safe, PostgreSQL integration is
isolated, and persisted records map to canonical IDs and JSON-compatible
contract payloads.

Verification: unit tests, PostgreSQL integration, migration validation,
architecture/security checks, lock/workspace validation.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: integrates with TASK-M0-003 at M0-PG-02A-INTEGRATION.

Gate membership: PG-M0-02A.

Downstream consumers: TASK-M0-004 and TASK-M0-005.

### TASK-M0-003

Objective: implement the minimal deterministic M0 policy evaluator needed for
provider-inventory work and fail-safe governed effects.

Prerequisites: TASK-M0-001 validated, frozen, and integrated.

Authorized surfaces: `packages/python/curios_policy/**`, tests, evidence, and
documentation for M0 policy behavior.

Responsibilities: map M0 effect requests to canonical `PolicyDecision`
outcomes without becoming a full policy language.

Prohibited scope: full policy language, RBAC/ABAC, approval workflow, secret
resolver, credential handling, production IAM.

Required boundaries: `PolicyDecision.UNKNOWN` remains distinct from `DENY` and
non-authorizing for governed effects; approvals remain policy/control outcomes,
not effects.

Acceptance: unsupported, unknown, or unevaluable governed effects do not
authorize execution.

Verification: unit tests, contract round-trip checks, security tests, and
architecture checks.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: integrates with TASK-M0-002 at M0-PG-02A-INTEGRATION.

Gate membership: PG-M0-02A.

Downstream consumers: TASK-M0-006.

### TASK-M0-004

Objective: implement the M0 runtime event/evidence writer boundary backed by
the persistence foundation.

Prerequisites: TASK-M0-001 and TASK-M0-002 validated, frozen, and integrated.

Authorized surfaces: `packages/python/curios_runtime/**` event/evidence modules
or `packages/python/curios_persistence/**` only if TASK-M0-002 establishes
that ownership, tests, evidence.

Responsibilities: persist canonical event/evidence facts, preserve
correlation/provenance fields, and avoid fake verification or fabricated
runtime truth.

Prohibited scope: event bus, external broker, telemetry semantic authority,
verification engine, policy engine, scheduler, agent runtime.

Required boundaries: `EventEnvelope`, `ObservabilityContext`,
`EvidenceReference`, `VerificationRecord`, and `ObjectReference` remain
canonical; persistence shape is not canonical semantics.

Acceptance: runtime events and evidence can be recorded and reread through the
M0 persistence boundary without provider/framework-native leakage.

Verification: unit tests, persistence integration tests, architecture checks,
serialization checks, and `git diff --check`.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: integrates with TASK-M0-005 at M0-PG-02B-INTEGRATION.

Gate membership: PG-M0-02B.

Downstream consumers: TASK-M0-006 and TASK-M0-010.

### TASK-M0-005

Objective: implement persisted `WorkItem` and `ExecutionRecord` repository
behavior and allowed M0 state transitions.

Prerequisites: TASK-M0-002 validated, frozen, and integrated.

Authorized surfaces: `packages/python/curios_runtime/**`,
`packages/python/curios_persistence/**`, tests, evidence.

Responsibilities: create/retrieve/update work and execution records, enforce
allowed M0 transitions, and preserve canonical runtime state vocabularies.

Prohibited scope: scheduler, queue, DAG execution, arbitrary execution engine,
agent runtime, model routing, application-level repository architecture beyond
M0 work/execution records.

Required boundaries: `WorkItem` is distinct from `ExecutionRecord`;
`EngineeringLifecycle` remains separate from runtime state machines.

Acceptance: persisted work and execution records move only through allowed M0
states and can be recovered after runtime objects are disposed.

Verification: unit tests, PostgreSQL integration tests, contract/state
transition checks, architecture checks.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: integrates with TASK-M0-004 at M0-PG-02B-INTEGRATION.

Gate membership: PG-M0-02B.

Downstream consumers: TASK-M0-006 and TASK-M0-010.

### TASK-M0-006

Objective: implement a single-step local runtime service that coordinates
policy, work state, event/evidence recording, and bounded executor invocation.

Prerequisites: TASK-M0-003, TASK-M0-004, and TASK-M0-005 validated, frozen, and
integrated.

Authorized surfaces: `packages/python/curios_runtime/**`, runtime tests,
evidence.

Responsibilities: run one work item at a time, evaluate policy before governed
effects, record transitions/events/evidence, and expose deterministic service
results.

Prohibited scope: DAG scheduler, async job queue, multi-agent orchestration,
model router, arbitrary tool execution, external writes, destructive effects.

Required boundaries: `CoreContext` may carry supplied authority but does not
grant it; policy decisions are consumed, not silently rewritten.

Acceptance: one work item can transition through created/ready/running/
completed or failed/blocked states with persisted evidence.

Verification: unit tests, integration tests, security tests, state-transition
checks, architecture checks.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: M0-RUNTIME-INTEGRATION.

Gate membership: PG-M0-03.

Downstream consumers: TASK-M0-007.

### TASK-M0-007

Objective: add the sole M0 executor capability: provider inventory collection
through existing Curios provider catalogs.

Prerequisites: TASK-M0-006 validated, frozen, and integrated; frozen BOOT
provider foundations remain available.

Authorized surfaces: `packages/python/curios_runtime/**`, provider-inventory
tests, evidence.

Responsibilities: invoke authorized provider catalog ports, collect canonical
`ProviderDescriptor` values, produce canonical `Result`/evidence, and remain
deterministic.

Prohibited scope: model generation, model routing, arbitrary provider calls,
external writes, live Ollama requirement, agent/tool execution, provider
selection/ranking.

Required boundaries: `ProviderDescriptor` and `ProviderCatalog` remain Curios
contracts/ports; provider-native payloads stay provider-local.

Acceptance: provider inventory work returns canonical descriptors and evidence
without requiring network, GPU, downloaded model, or arbitrary provider
execution.

Verification: unit tests, provider integration tests with deterministic/fake
boundaries, architecture/security checks.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: M0-RUNTIME-INTEGRATION.

Gate membership: PG-M0-04.

Downstream consumers: TASK-M0-008.

### TASK-M0-008

Objective: add FastAPI routes for M0 work creation, status, execution, events,
evidence, and provider-inventory work only.

Prerequisites: TASK-M0-007 validated, frozen, and integrated.

Authorized surfaces: `apps/api/**`, API tests, docs/evidence.

Responsibilities: compose the runtime service at the HTTP boundary, translate
canonical results/errors to HTTP, and define the concrete M0 API route contract
that the web console consumes.

Prohibited scope: new canonical HTTP semantics, FastAPI leaking inward,
unbounded API surface, frontend behavior, direct database access from route
handlers when a service/repository boundary exists.

Required boundaries: FastAPI remains outer composition; canonical Curios
contracts remain semantic authority.

Acceptance: HTTP translates canonical `Result`/`ContractError` at the outer
boundary and never redefines Curios contracts.

Verification: API tests, integration tests, architecture/security checks,
deterministic failure-translation tests.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: M0-API-INTEGRATION.

Gate membership: PG-M0-05A.

Downstream consumers: TASK-M0-009 and TASK-M0-010.

### TASK-M0-009

Objective: evolve the web bootstrap into a minimal M0 work console consuming
only the routes established by TASK-M0-008.

Prerequisites: TASK-M0-008 validated, frozen, and integrated.

Authorized surfaces: `apps/web/**`, TypeScript contract usage where required,
web tests, docs/evidence.

Responsibilities: display submitted work, execution state, provider inventory
results, events, and evidence using the API boundary.

Prohibited scope: duplicated canonical models, direct Python/backend imports,
provider-native objects, product workflows beyond M0 work console.

Required boundaries: the frontend is an outer interface and does not become
backend/domain/security authority.

Acceptance: web tests/build are deterministic and require no live backend.

Verification: Vitest, typecheck, production build, security topology, API-route
reference review.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: M0-WEB-INTEGRATION.

Gate membership: PG-M0-05B.

Downstream consumers: TASK-M0-010 and TASK-M0-012.

### TASK-M0-010

Objective: add deterministic integration tests proving VS-M0-001 through
VS-M0-003 across persistence, policy, runtime, provider inventory, and API.

Prerequisites: TASK-M0-008 and TASK-M0-009 validated, frozen, and integrated.

Authorized surfaces: `tests/integration/**`, `tests/fixtures/**`, docs/evidence.

Responsibilities: exercise integrated M0 behavior without live Ollama or
external network; include PostgreSQL only through authorized local integration.

Prohibited scope: product functionality, new runtime code, CI workflow changes,
acceptance-suite ownership, browser E2E unless separately authorized.

Required boundaries: tests verify behavior without becoming semantic authority.

Acceptance: integration tests fail if provider-inventory work, policy
denial/unknown safety, or runtime-truth persistence is broken.

Verification: integration suite, PostgreSQL integration, no-live-Ollama review,
full deterministic backend checks.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: M0-ACCEPTANCE preparation.

Gate membership: PG-M0-06.

Downstream consumers: TASK-M0-011 and TASK-M0-012.

### TASK-M0-011

Objective: extend the CI quality gates so M0 runtime, persistence, API, web,
integration, architecture, security, and acceptance checks run in CI.

Prerequisites: TASK-M0-010 validated, frozen, and integrated.

Authorized surfaces: `.github/workflows/quality-gates.yml`, relevant
security-topology tests for the exact CI change, docs/evidence.

Responsibilities: preserve TASK-BOOT-025 CI semantics while adding M0 checks
and keeping hosted execution deterministic.

Prohibited scope: deployment, release automation, publishing, broad `.github/**`
authorization, live Ollama/GPU/model dependency, post-M0 gates.

Required boundaries: GitHub Actions remains implementation of Curios quality
gates, not domain semantic authority.

Acceptance: CI invokes M0 checks, preserves least privilege and pinned actions,
and fails on M0 verification failures.

Verification: workflow static validation, local reproduction of represented
checks, security topology tests, diff hygiene.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: M0-ACCEPTANCE preparation.

Gate membership: PG-M0-07.

Downstream consumers: TASK-M0-012.

### TASK-M0-012

Objective: add M0 acceptance tests proving VS-M0-001 through VS-M0-004 and the
complete governed local work execution slice.

Prerequisites: TASK-M0-011 validated, frozen, and integrated.

Authorized surfaces: `tests/acceptance/**`, docs/evidence, narrowly required
test fixtures.

Responsibilities: prove cross-boundary behavior: API submission, runtime
execution, persistence recovery, policy failure, evidence, and web/API
observability.

Prohibited scope: new production behavior, broad E2E/browser framework,
post-M0 scenarios, live external provider requirements.

Required boundaries: acceptance tests observe runtime truth and do not invent
new canonical semantics.

Acceptance: every M0 vertical slice has objective PASS/FAIL evidence and the
ordinary suite remains deterministic.

Verification: acceptance suite, full backend/frontend checks, PostgreSQL
integration with persistent volume preserved.

Lifecycle result: `IMPLEMENTED, TESTED` only; independent validation is required
before `VALIDATED, FROZEN`.

Integration dependencies: M0-ACCEPTANCE.

Gate membership: PG-M0-08.

Downstream consumers: TASK-M0-013.

### TASK-M0-013

Objective: independently verify the complete M0 baseline and record the M0
verification evidence.

Prerequisites: TASK-M0-012 validated, frozen, and integrated.

Authorized surfaces: `docs/tasks/**`, `docs/program/status-ledger/**`, and
verification records only.

Responsibilities: audit lifecycle, history, architecture, security, vertical
slices, CI/acceptance, and mechanical verification results.

Prohibited scope: production/test implementation changes, corrective fixes,
post-M0 planning, final freeze declaration.

Required boundaries: implementation success is not sufficient for validation;
verification remains independent evidence.

Acceptance: independent verification finds no unresolved M0 blocker and records
the exact verified baseline.

Verification: complete authoritative M0 verification suite and repository
hygiene checks.

Lifecycle result: verification record may be marked `VALIDATED, FROZEN` only
when the independent verification itself passes under Build Pack conventions.

Integration dependencies: M0-VERIFY.

Gate membership: PG-M0-09.

Downstream consumers: TASK-M0-014.

### TASK-M0-014

Objective: perform final M0 closure, status-ledger update, and freeze record.

Prerequisites: TASK-M0-013 validated, frozen, and integrated.

Authorized surfaces: `docs/program/milestones/**`,
`docs/program/status-ledger/**`, `docs/tasks/**`.

Responsibilities: close the milestone, record final baseline semantics, and
identify the next program state without starting it.

Prohibited scope: production/test implementation changes, additional M0 feature
work, M1 implementation, branch/worktree cleanup unless explicitly required.

Required boundaries: final closure relies on independent verification rather
than self-attestation.

Acceptance: every M0 task/gate is lifecycle-consistent, evidence agrees with
history, and no unresolved M0 blocker remains.

Verification: ledger/evidence consistency, relevant architecture/security
checks if documentation affects topology, `git diff --check`.

Lifecycle result: M0 may be recorded as `VALIDATED, FROZEN` only if TASK-M0-014
closure criteria pass.

Integration dependencies: M0-FREEZE.

Gate membership: PG-M0-10.

Downstream consumers: next milestone/readiness program, if later authorized.
