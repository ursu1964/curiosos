---
id: TASK-M1-014-VALIDATION-EVIDENCE
title: TASK-M1-014 Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-014
milestone_id: M1
date: 2026-09-27
---

# TASK-M1-014 Validation Evidence

## Scope

Published baseline:
`99da3572d4164f1560049f3f98df97eb8ee65d12`

Implementation:
`d1bc17e2ccadec396778e719908139b55ced85fa`

Correction 1:
`82d38291d7d1d789986b44e5e3aba45841b48dfc`

Validation reconstructed TASK-M1-014 from the frozen M1 task pack, M1
implementation DAG, M1 status ledger, TASK-M1-001 frontend topology guardrails,
TASK-M1-013 API contract, existing web API-boundary architecture, TASK-M1-015
boundary, and architecture/security constraints.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | TASK-M1-013 is validated, frozen, integrated, published, and remote-CI-verified in the published baseline. |
| UI surface | PASS | The console exposes the required M1 objective input, `Decompose Intent`, `Run DAG Once`, `Complete Verification`, and panels for intent, Work DAG, runner outcomes, verification, and M1 events. |
| API boundary | PASS | App/UI can call only `decomposeM1Intent`, `runM1DagOnce`, and `completeM1Verification`; no arbitrary URL, path, method, header, or generic request capability is exposed to App. |
| M1-001 frontend authority | PASS | App imports no direct network primitives and contains no `fetch`, `globalThis`, `window`, `XMLHttpRequest`, `WebSocket`, `EventSource`, or `sendBeacon` authority. |
| Decomposition flow | PASS | The UI submits the draft objective to the frozen M1 API boundary and renders supported or unsupported decomposition responses without browser-side decomposition/template logic. |
| DAG run flow | PASS | The UI constructs a run-once request from accepted decomposition truth, delegates to the API boundary, and renders `EXECUTED`, `WAITING`, `BLOCKED`, `TERMINAL`, `DEFERRED`, `NO_ROUTE`, and `ROUTE_NOT_EXECUTABLE` as domain outcomes. |
| Verification flow | PASS | The UI builds verification input from accepted decomposition plus recorded runner output and renders `APPROVED`, `REJECTED`, and `DEFERRED` without browser-side evidence binding or decision logic. |
| Draft/canonical separation | PASS | Mutable objective input is draft-only. Accepted canonical panels render from `m1State.decomposition`, `m1State.runnerResult`, and `m1State.verificationResult`, not from mutable draft text. |
| Cross-flow consistency | PASS | Editing draft B after accepting intent A leaves canonical A visible. Accepting B replaces A and clears old runner/verification state. Failed replacement leaves A visible with bounded error. |
| Async and double-submit | PASS | M1 actions are single-flight through `m1BusyAction`; controls are disabled while a request is in flight, and generation/intent refs prevent stale responses from overwriting current truth. |
| Error/domain rendering | PASS | Transport/API failures render bounded code/message fields. Domain outcomes such as unsupported decomposition, `NO_ROUTE`, `ROUTE_NOT_EXECUTABLE`, `DEFERRED`, and `REJECTED` are not treated as generic UI errors. |
| Safe error rendering | PASS | The UI does not render raw response objects, stack traces, arbitrary nested detail, provider/DB diagnostics, or secret-shaped attacker strings from bounded error fixtures. |
| Client state | PASS | State remains in-memory React state only. No localStorage, sessionStorage, IndexedDB, service worker state, durable cache, global canonical store, automatic retry, or browser persistence was added. |
| Accessibility | PASS | The M1 objective input has a label, controls have button semantics and disabled states, and status/error regions use semantic live roles. |
| M1-015 boundary | PASS | M1-014 adds focused frontend/component tests only. It does not add a cross-system integration suite, browser/backend integration harness, CI changes, or M1-015 evidence. |

## Original Defect Re-Validation

The previous validation defect was reproduced before Correction 1: after
accepted decomposition A, editing the objective draft to B caused the Intent
panel to display IntentId A with objective B.

Correction 1 was independently revalidated:

- IntentId and objective in the Intent panel now come from the same accepted
  `decomposition.intent` object;
- editing draft B without submitting does not alter canonical A;
- successful accepted decomposition B replaces canonical A;
- failed decomposition B preserves canonical A and shows a bounded error;
- draft text does not leak into run-once or verification request bodies;
- runner, verification, and M1 event panels are sourced from accepted
  runner/verification responses.

## State And Provenance Audit

| State | Classification | Source |
| --- | --- | --- |
| `m1State.intentObjective` | DRAFT | Editable input only. |
| `m1State.decomposition` | CANONICAL ACCEPTED TRUTH | Successful `decomposeM1Intent` response. |
| `m1State.runnerResult` | CANONICAL ACCEPTED TRUTH | Successful `runM1DagOnce` response for current accepted intent. |
| `m1State.verificationResult` | CANONICAL ACCEPTED TRUTH | Successful `completeM1Verification` response for current accepted intent. |
| `m1BusyAction` | TRANSIENT REQUEST STATE | Single-flight UI disablement and progress labels. |
| `m1RequestGeneration` | TRANSIENT REQUEST STATE | Stale response rejection. |
| `activeM1IntentId` | TRANSIENT REQUEST STATE | Current accepted intent guard for run/verify responses. |
| `m1State.lastFailure` | ERROR STATE | Bounded API failure detail. |
| Rendered status messages | DERIVED PRESENTATION | Derived from canonical responses or bounded failures. |

The Intent, Work DAG, runner, verification, and event/evidence panels each use
one accepted canonical source. No displayed canonical object combines mutable
draft text with stale or newer response data.

## Validator Regressions

Independent validation coverage was added in `apps/web/src/App.test.tsx`.

It covers:

- original A -> draft B defect;
- successful canonical B replacement;
- failed B replacement;
- accepted unsupported B replacement and downstream invalidation;
- runner domain outcomes for waiting, no route, terminal, and deferred states;
- run-once and verification double-submit prevention;
- cross-action single-flight behavior;
- DAG and verification request provenance with draft text changed;
- safe bounded error rendering;
- basic M1 accessibility controls and status regions.

## Authority And Guard Review

TASK-M1-014 authorizes only the bounded web console and exact frontend
API-boundary capabilities over TASK-M1-013. It adds no backend/API
implementation, persistence, DB write, provider/model invocation, outbound
network outside `apiBoundary.ts`, executor invocation, route recomputation,
WorkItem/WorkDag/Agent/ExecutionRecord mutation, policy grant, prompt, memory,
or M1-015 integration-test authority.

Security inventory changes are narrowly additive for this validation evidence
file. No broad web, network, provider/model, persistence, runtime,
direct-executor, arbitrary-callback, or generic API exemption was added.

## Delta Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `apps/web/src/apiBoundary.ts` | REQUIRED | Exact M1 API-boundary capabilities introduced by implementation. |
| `apps/web/src/App.tsx` | REQUIRED | Bounded M1 console and Correction 1 canonical Intent rendering. |
| `apps/web/src/App.css` | JUSTIFIED SUPPORT | Presentation for the M1 console without new dependencies. |
| `apps/web/src/App.test.tsx` | REQUIRED | Implementation, Correction 1, and independent validation regressions. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Advances TASK-M1-014 to validated/frozen after independent re-validation. |
| `docs/tasks/TASK-M1-014-evidence.md` | REQUIRED | Implementation and Correction 1 evidence under validation. |
| `docs/tasks/TASK-M1-014-validation-evidence.md` | REQUIRED | Independent validation/freeze record. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Exact validation evidence authorization in the security inventory. |

No changed file was classified as questionable or out of scope.

## Verification

Post-record verification was run after validation records changed:

- `uv lock --check`: PASS;
- `uv sync --locked --all-groups --all-packages`: PASS;
- `pnpm install --frozen-lockfile`: PASS;
- Docker Compose config with `infrastructure/local/docker/compose.yaml`: PASS;
- `ruff format --check .`: PASS;
- `ruff check .`: PASS;
- `mypy apps/api/src packages/python/*/src`: PASS;
- `pnpm check`: PASS;
- apps/web tests: PASS, 1 file / 26 tests;
- apps/web typecheck: PASS;
- apps/web production build: PASS;
- contract/schema/architecture tests: PASS, 52 passed;
- security baseline: PASS, 353 passed;
- M1-013 API suite: PASS, 183 passed;
- M1-011/M1-012/M1-013 focused regressions: PASS, 155 passed;
- package/provider/runtime/persistence suites: PASS, 551 passed;
- Docker-backed serial slices: PASS, 23 tests;
- acceptance: PASS, 8 passed;
- full pytest: PASS, 1156 passed;
- `git diff --check`: PASS;
- `git diff --cached --check`: PASS.

Known warnings: inherited FastAPI/Starlette `TestClient` deprecation warnings
and the known surrounding-shell `VIRTUAL_ENV` mismatch notice from `uv`.

No skipped or deselected tests were counted as passed.

## Decision

TASK-M1-014 is `VALIDATED, FROZEN`.

TASK-M1-015 remains blocked until TASK-M1-014 is integrated into the main M1
baseline according to the authoritative M1 DAG.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-015 implementation, or M1 closure was performed during
validation.
