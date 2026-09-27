---
id: TASK-M1-013-EVIDENCE
title: TASK-M1-013 M1 API Cognitive Loop Endpoints Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-013
milestone_id: M1
date: 2026-09-27
---

# TASK-M1-013 Implementation Evidence

## Objective

Expose bounded M1 cognitive-loop recorded truth through the existing FastAPI
outer boundary. FastAPI remains an adapter: HTTP input is parsed into canonical
Curios records, delegated to frozen M1 boundaries, and serialized back as
canonical JSON-compatible output.

## Prerequisites

The authoritative M1 DAG requires TASK-M1-011 and TASK-M1-012 before
TASK-M1-013. Both were validated, frozen, integrated, published, and
remote-CI-verified before this task started. The ledger row was stale
`BLOCKED`; this implementation reconciles it to `IMPLEMENTED, TESTED`.

## Endpoint Inventory

TASK-M1-013 adds exactly these application-owned routes:

- `POST /m1/intents/decompose`;
- `POST /m1/dag/run-once`;
- `POST /m1/verification/complete`.

Existing M0 health/provider/work routes are unchanged.

## Request And Response Contracts

`POST /m1/intents/decompose` accepts a simple objective plus optional canonical
`IntentId`, timestamps, context references, source reference, and `WorkDagId`.
It constructs a canonical `Intent`, delegates to the frozen deterministic
decomposer, derives a bounded `WorkDag` when work proposals exist, and returns
the canonical intent, decomposition proposal, and DAG.

`POST /m1/dag/run-once` accepts a canonical `M1DagRunnerRequest` transport
shape: DAG, work items, routing decisions, active agent instances, capability
resolutions keyed by `WorkId`, executor event/evidence IDs keyed by `WorkId`,
producer, occurrence time, observability context, and `max_concurrency`. It
delegates to `BoundedM1DagRunner(DeterministicM1Executor())` and returns the
canonical runner result.

`POST /m1/verification/complete` accepts a canonical `M1VerificationLoopRequest`
transport shape: work, recorded runner node result, verification attempts,
iteration bound, verification/event IDs, verifier/producer refs, timestamp, and
observability context. It delegates to `BoundedM1VerificationLoop` and returns
the canonical verification result.

Responses use `to_json_compatible()` or frozen canonical serializers. No
FastAPI, Pydantic, repository, provider-native, or persistence objects cross the
HTTP response boundary.

## Boundaries

M1-011 remains owner of DAG readiness, deterministic READY-node ordering,
concurrency, route/work compatibility, capability and active-agent gates, and
M1 executor invocation. M1-013 only exposes that boundary through HTTP.

M1-012 remains owner of recorded-execution gating, evidence subject binding,
duplicate evidence rejection, max iteration bounds, first-terminal attempt
semantics, completion decisions, `VerificationReference`, and
`verification.completed` event creation. M1-013 only exposes that boundary
through HTTP.

M1-014 remains owner of the web cognitive-loop console. This task adds no React,
CSS, frontend polling, presentation state, UI business logic, or web behavior.

## Error And Status Mapping

Malformed transport or non-canonical JSON maps to HTTP 400 with
`M1_API_MALFORMED_REQUEST` and fixed bounded text.

Bounded M1 runner errors preserve canonical runner `code`, `message`,
`retryable`, and `operation` fields:

- invalid runner request or concurrency: HTTP 400;
- missing agent, routing decision, or executor identity: HTTP 409.

Bounded M1 verification errors preserve canonical verification `code`,
`message`, `retryable`, and `operation` fields:

- invalid iteration bound/request/evidence: HTTP 400;
- execution not completed, evidence subject mismatch, or missing terminal
  evidence: HTTP 409.

Domain outcomes such as `NO_ROUTE`, `ROUTE_NOT_EXECUTABLE`, `DEFERRED`, or
`REJECTED` remain successful HTTP responses when they are valid canonical M1
results rather than malformed requests.

## Authority Inventory

| Capability | M1-013 result |
| --- | --- |
| WorkItem read | AUTHORIZED as supplied canonical HTTP input and serialized output |
| WorkItem mutation | ABSENT |
| WorkDag read | AUTHORIZED as supplied canonical HTTP input and derived intent DAG output |
| WorkDag mutation | ABSENT |
| route read/recompute | AUTHORIZED only as supplied routing decision input; recomputation ABSENT |
| capability resolution | AUTHORIZED only as supplied canonical runner input |
| agent read/transition | agent read AUTHORIZED as supplied input; transition ABSENT |
| runner invocation | AUTHORIZED through `BoundedM1DagRunner` |
| executor direct invocation | ABSENT; runner owns executor invocation |
| verification invocation | AUTHORIZED through `BoundedM1VerificationLoop` |
| ExecutionRecord mutation | ABSENT |
| persistence / DB | ABSENT |
| event/evidence read/create | AUTHORIZED only through canonical runner/verification results; persistence ABSENT |
| provider/model invocation | ABSENT |
| outbound network | ABSENT |
| policy evaluation/grant | ABSENT |
| retry/cancel | ABSENT |
| API | AUTHORIZED for the three exact M1 endpoints |
| UI | ABSENT |
| prompt/memory | ABSENT |

## Cross-Domain And Safe-Error Evidence

Tests cover:

- happy path per endpoint;
- malformed canonical input;
- selected route compatible with work -> executor-owned event/evidence surface;
- selected route incompatible with work -> `ROUTE_NOT_EXECUTABLE` and no
  executor event/evidence;
- `NO_ROUTE` remains a domain result;
- verification approval over recorded runner output and bound evidence;
- duplicate evidence rejection;
- wrong-work evidence rejection;
- secret-shaped upstream evidence text not leaking in HTTP error JSON;
- OpenAPI contains only the intended M1 paths and no model-generation or web
  console path.

## Dependencies And Schema

`apps/api` now declares workspace-local dependencies on `curios-capability`,
`curios-cognitive`, and `curios-dag` because the API adapter parses and
delegates to those frozen M1 contracts. No third-party dependency, database
schema, migration, or new package is introduced. `uv.lock` records only these
workspace-local dependency edges for `curios-api`.

## Verification

Implementation verification:

- `uv lock --check`: PASS;
- `uv sync --locked --all-groups --all-packages`: PASS;
- `pnpm install --frozen-lockfile`: PASS;
- Docker Compose config: PASS;
- `ruff format --check .`: PASS, 272 files already formatted;
- `ruff check .`: PASS;
- `mypy apps/api/src packages/python/*/src`: PASS, 70 source files;
- `pnpm check`: PASS;
- apps/web tests: PASS, 1 file / 6 tests;
- apps/web typecheck: PASS;
- apps/web production build: PASS;
- contract/schema/architecture tests: PASS, `52 passed`;
- API tests including M1-013 endpoints: PASS, `23 passed`;
- package/provider/runtime/persistence non-Docker suites: PASS, `107 passed`;
- security baseline: PASS, `353 passed`;
- API and M0 vertical-slice integration: PASS, `8 passed`;
- acceptance: PASS, `8 passed`;
- full pytest: PASS, `996 passed`;
- Docker-backed PostgreSQL provider/persistence/event-evidence/work DAG/work
  repository/agent repository/agent lifecycle/routing repository integrations:
  PASS serially, `9 passed`.

Known warnings: existing FastAPI/Starlette TestClient deprecation warnings and
the known `VIRTUAL_ENV` mismatch notice from the surrounding shell environment.

Docker/PostgreSQL note: one broad package run initially failed in
`test_postgres_agent_lifecycle_repository_integration.py` with PostgreSQL
connection refused while the compose service was not running after prior
service lifecycle activity. Container state was inspected, PostgreSQL was
started and waited to healthy, the failed slice passed in isolation, and all
Docker-backed slices then passed serially. The final full pytest pass was
green.

## File Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `apps/api/pyproject.toml` | REQUIRED | Workspace-local dependencies needed by the API adapter. |
| `apps/api/src/curios_api/service.py` | REQUIRED | Exact M1 endpoint implementation and canonical parsing/error mapping. |
| `apps/api/tests/test_fastapi_service_composition.py` | JUSTIFIED SUPPORT | Dependency boundary assertion updated for required workspace-local dependencies. |
| `apps/api/tests/test_m1_cognitive_loop_endpoints.py` | REQUIRED | Focused M1-013 API contract and adversarial coverage. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Reconciles stale M1-013 row to implementation lifecycle. |
| `docs/tasks/TASK-M1-013-evidence.md` | REQUIRED | Implementation evidence. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Authorizes only exact M1-013 API route/test surface. |
| `uv.lock` | REQUIRED | Records workspace-local dependency edges for `curios-api`. |

## Lifecycle

TASK-M1-013 is `IMPLEMENTED, TESTED`.

TASK-M1-013 remains awaiting independent validation/freeze. TASK-M1-014 remains
blocked until TASK-M1-013 is validated, frozen, integrated, published, and
remote-CI-verified according to the M1 DAG.
