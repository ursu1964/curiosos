---
id: TASK-M1-014-EVIDENCE
title: TASK-M1-014 M1 Web Cognitive Loop Console Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-014
milestone_id: M1
date: 2026-09-27
---

# TASK-M1-014 Implementation Evidence

## Objective

Extend the existing web console to present M1 cognitive-loop truth through the
frozen M1 API adapter. The browser remains a bounded presentation/control layer:
it constructs exact M1 API requests, delegates decomposition, DAG running, and
verification to the server, and renders canonical domain outcomes without
inventing runtime truth.

## Prerequisites

TASK-M1-014 depends directly on TASK-M1-013. TASK-M1-013 was validated, frozen,
integrated, published, and remote-CI-verified before implementation began at
baseline `99da3572d4164f1560049f3f98df97eb8ee65d12`. The ledger row for
TASK-M1-014 was stale `BLOCKED`; this implementation reconciles it to
`IMPLEMENTED, TESTED`.

## UI Surface

The console adds a structured M1 Cognitive Loop section with:

- intent objective input;
- `Decompose Intent`;
- `Run DAG Once`;
- `Complete Verification`;
- panels for intent, work DAG, runner outcomes, verification outcome, and M1
  events.

The existing M0 provider-inventory console remains present and unchanged.

## API Boundary Extensions

`apps/web/src/apiBoundary.ts` adds only explicit capability-shaped functions:

- `decomposeM1Intent` -> `POST /m1/intents/decompose`;
- `runM1DagOnce` -> `POST /m1/dag/run-once`;
- `completeM1Verification` -> `POST /m1/verification/complete`.

The API boundary does not expose a generic request function, arbitrary path,
arbitrary method, provider/model call, or direct runtime hook to App/UI.

## Domain Rendering

The web console preserves HTTP/domain distinctions from TASK-M1-013:

- unsupported decomposition is rendered as an M1 domain outcome;
- runner outcomes such as `NO_ROUTE`, `ROUTE_NOT_EXECUTABLE`, `WAITING`,
  `BLOCKED`, `TERMINAL`, and `DEFERRED` are rendered as canonical runner
  truth, not generic transport failures;
- verification `APPROVED`, `REJECTED`, and `DEFERRED` are rendered from the
  bounded verification response.

Bounded API failures are rendered through the canonical error code/status and
bounded message only. The UI does not render raw response objects, stack traces,
provider/DB errors, or arbitrary exception details.

## Client State

Client state is minimal and in memory only. No `localStorage`, `sessionStorage`,
`IndexedDB`, service worker state, hidden cache, automatic retry, or durable
browser persistence was added.

M1 actions are single-flight: while one M1 request is pending, M1 controls are
disabled so repeated clicks cannot issue duplicate decomposition, runner, or
verification requests. Selecting a new intent clears prior runner and
verification truth.

## Authority Inventory

| Capability | M1-014 result |
| --- | --- |
| decomposition request | AUTHORIZED through `decomposeM1Intent` |
| run-once request | AUTHORIZED through `runM1DagOnce` |
| verification request | AUTHORIZED through `completeM1Verification` |
| arbitrary HTTP request | ABSENT |
| arbitrary path/method | ABSENT |
| direct fetch in App/UI | ABSENT |
| provider/model invocation | ABSENT |
| executor invocation | ABSENT |
| persistence / browser durable state | ABSENT |
| WorkItem/DAG/Agent mutation | ABSENT in browser |
| routing recomputation | ABSENT |
| policy grant | ABSENT |
| automatic retry/cancel | ABSENT |
| API error rendering | AUTHORIZED bounded fields only |
| domain-result rendering | AUTHORIZED canonical status/reason fields |

## Boundary Evidence

M1-013 remains owner of HTTP transport, canonical parsing, and bounded API error
mapping. M1-014 consumes only the frozen M1 endpoint surface.

M1-011 remains owner of DAG readiness, ordering, concurrency, route/work
compatibility, capability and agent gates, and executor invocation. The UI
constructs a canonical run-once request from decomposition output and displays
the returned runner result.

M1-012 remains owner of recorded-execution gating, evidence subject binding,
duplicate evidence handling, loop bounds, first-terminal semantics, completion
decisions, verification reference creation, and verification events. The UI
submits a bounded verification request only from recorded runner output and
displays the returned verification result.

M1-015 remains owner of M1 vertical-slice integration tests. TASK-M1-014 adds
focused web tests with fake API responses and no live backend/model dependency.

## Security And Guardrail Evidence

The TASK-M1-001 frontend authority invariant is preserved:

- App/UI contains no direct `fetch`, `globalThis.fetch`, `window.fetch`,
  `XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon`, or
  equivalent network primitive;
- `apiBoundary.ts` still contains exactly one private `fetch` call;
- security guards authorize only the three exact M1 web API capabilities;
- no broad web, provider/model, persistence, runtime, direct executor, or UI
  exemption was added.

## Verification

Implementation verification:

- `uv lock --check`: PASS;
- `uv sync --locked --all-groups --all-packages`: PASS;
- `pnpm install --frozen-lockfile`: PASS;
- Docker Compose config with `infrastructure/local/docker/compose.yaml`: PASS;
- `ruff format --check .`: PASS, 276 files already formatted;
- `ruff check .`: PASS;
- `mypy apps/api/src packages/python/*/src`: PASS;
- `pnpm check`: PASS;
- apps/web tests: PASS, 1 file / 15 tests;
- apps/web typecheck: PASS;
- apps/web production build: PASS;
- contract/schema/architecture tests: PASS, `52 passed`;
- M1/API/runtime package regressions: PASS, `506 passed`;
- all package tests: PASS, `551 passed`;
- complete API suite: PASS, `183 passed`;
- security baseline: PASS, `353 passed`;
- full pytest: PASS, `1156 passed`;
- Docker-backed serial slices: PASS, 21 tests across API integration,
  PostgreSQL provider, provider integration, persistence, event/evidence, work
  repository, Work DAG repository, agent repository, agent lifecycle repository,
  routing repository, and M0 vertical slice;
- acceptance: PASS, `8 passed`;
- `git diff --check`: PASS;
- `git diff --cached --check`: PASS.

Known warnings: the existing FastAPI/Starlette TestClient deprecation warnings
and the known `VIRTUAL_ENV` mismatch notice from the surrounding shell
environment.

## File Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `apps/web/src/apiBoundary.ts` | REQUIRED | Adds exact M1 API-boundary functions and canonical payload types. |
| `apps/web/src/App.tsx` | REQUIRED | Adds the bounded M1 cognitive-loop console. |
| `apps/web/src/App.css` | JUSTIFIED SUPPORT | Styles the new structured M1 controls without adding UI framework/dependency. |
| `apps/web/src/App.test.tsx` | REQUIRED | Focused M1-014 web authority, rendering, double-submit, safe-error, and delegation coverage. |
| `tests/security/test_security_baseline.py` | REQUIRED | Updates exact frontend authority inventory for TASK-M1-014. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Reconciles stale TASK-M1-014 status to implemented/tested. |
| `docs/tasks/TASK-M1-014-evidence.md` | REQUIRED | Records implementation evidence and authority boundaries. |
