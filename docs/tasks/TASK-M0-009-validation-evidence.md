---
id: TASK-M0-009-VALIDATION-EVIDENCE
title: TASK-M0-009 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-009
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-009 Independent Validation Evidence

## Decision

TASK-M0-009 VALIDATION: PASS

Validated candidate:

`7dfbf04361b5f1ebacabbfc63d7233b896881ed4`

Starting baseline:

`817c57915d9929bfe90d064b3dc9f503a4721972`

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Scope exact | PASS | Console exposes create provider-inventory work, run, manual refresh, work/execution/events/evidence observation, provider inventory result display, and bounded failure presentation only. |
| Deferred surfaces absent | PASS | No scheduler UI, DAG editor, agent console, model routing/generation, arbitrary tool runner, policy editor, IAM/admin console, DataLab, polling/background runtime, or TASK-M0-010+ behavior exists. |
| API boundary exact | PASS | `apps/web/src/apiBoundary.ts` declares only frozen BOOT health/provider routes plus TASK-M0-008 work routes: `POST /work/provider-inventory`, `GET /work/{work_id}`, `POST /work/{work_id}/run`, `GET /work/{work_id}/executions/{execution_id}`, `GET /work/{work_id}/events`, and `GET /work/{work_id}/evidence`. |
| No ad-hoc backend access | PASS | Repository search found no frontend API calls outside `apiBoundary.ts`; no extra clients, routers, WebSocket/SSE/EventSource, or polling transport were added. |
| Frontend presentation authority | PASS | React renders API-returned work, execution, runtime status, events, evidence, and provider descriptors. It does not authorize policy, compute lifecycle transitions, execute provider inventory, or infer runtime success from HTTP 2xx alone. |
| Work creation bounded | PASS | UI submits only `POST /work/provider-inventory` with fixed title/objective; no arbitrary work type, effect selector, policy override, authority injection, executor/provider/model/tool selection, or provider routing control is exposed. |
| Run flow bounded | PASS | Run uses `POST /work/{work_id}/run` through the API boundary; no `SingleStepRuntimeService` logic is reproduced in TypeScript; duplicate run submission is disabled while any request is busy; no retry framework exists. |
| Manual refresh only | PASS | Refresh is explicitly button-driven; source inspection found no polling, `setInterval`, WebSocket, SSE, subscription, hidden retry loop, or background refresh. |
| Stale response protection | PASS | The component uses a monotonically increasing request generation and active work id check. Late cross-work create/run/refresh observations cannot overwrite the selected work. Same-work older refresh overwrite is bounded because concurrent refresh/run submissions are disabled while a request is in flight. |
| Cross-work display | PASS | New work creation replaces state with `initialState` plus the new work, clearing prior execution/events/evidence/provider inventory. Late stale responses are ignored before state mutation. |
| Failure presentation | PASS | UI displays bounded API error code/status/message and policy outcome where present; `BLOCKED`, malformed, not found, conflict/illegal state, runtime unavailable, and provider/runtime failure remain distinguishable by API status/detail. UNKNOWN policy outcome is shown and is not collapsed into success. |
| Canonical data handling | PASS | TypeScript canonical package currently exposes only package identity markers. Frontend response shapes remain API-boundary-owned and do not become canonical authority. |
| Evidence/provider inventory display | PASS | Provider descriptors come only from `executor_result.value.providers`; evidence comes only from API `evidence_refs` or evidence endpoint responses. The UI does not fabricate descriptors or claim evidence payloads beyond returned summaries/kinds/timestamps. |
| Accessibility | PASS | Main/section/headings are semantic; buttons have text names, disabled/busy states, keyboard-native controls, status `role=status` with polite live region, and error `role=alert` with assertive live region. No new a11y framework is required by the frozen toolchain. |
| API base/security | PASS | UI uses same-origin relative URLs by default; no user-controlled API base is wired into the app, no credential-bearing URL construction exists, and secret scan passed. |
| Web topology | PASS | Authorized web source files are exact. A temporary tracked-file probe for `Scheduler.tsx`, `DagEditor.tsx`, `AgentConsole.tsx`, `ModelRouter.tsx`, `DataLab.tsx`, `AdminIam.tsx`, `ToolRunner.tsx`, an unrelated route, and an arbitrary API client module was rejected by the security topology test. Probe files were removed. |
| Architecture | PASS | Web imports no Python package, backend runtime implementation, persistence, policy implementation, or provider implementation. Backend packages do not depend on web; React/Vite remain presentation tooling. |
| Dependencies | PASS | No new dependency was added by TASK-M0-009. Current web dependencies are required bootstrap/tooling dependencies; no router, state manager, query/cache library, UI framework, generated SDK, WebSocket/SSE library, or provider/backend dependency exists. |
| Frozen prerequisites | PASS | Diff from baseline changes web files, docs, and security guardrails only. No semantic change to TASK-M0-008 API, TASK-M0-007 executor, TASK-M0-006 runtime, policy, repository, event/evidence, persistence, or canonical contracts was found. |
| Test quality | PASS | App tests cover route surface, create/run paths, BLOCKED not-success handling, bounded provider failure display, refresh observation routes, and asynchronous cross-work stale observation. Independent review noted no material false-negative for M0 acceptance because same-work stale refresh is prevented by busy gating plus generation checks. |

## Stale Response Matrix

| Scenario | Result | Mechanism |
| --- | --- | --- |
| A: Work A observation resolves after Work B creation/selection | PASS | Request generation plus active work id check ignores late A response. |
| B: Execution observation resolves after Work B creation/selection | PASS | Same refresh generation/work guard covers execution response. |
| C: Events observation resolves after Work B creation/selection | PASS | Same refresh generation/work guard covers events response. |
| D: Evidence observation resolves after Work B creation/selection | PASS | Same refresh generation/work guard covers evidence response. |
| E: Run A resolves after moving to Work B | PASS | Run response is accepted only when generation and active work id still match A. |
| F: Older same-work refresh resolves after newer same-work refresh | PASS | The UI disables refresh while a request is in flight, so overlapping same-work refreshes are not reachable through the console; generation checking is still present for every request. |

## Mechanical Verification

| Check | Result |
| --- | --- |
| Candidate HEAD | PASS: `7dfbf04361b5f1ebacabbfc63d7233b896881ed4`. |
| TOML validation | PASS: 11 `pyproject.toml` files parsed. |
| `uv lock --check` | PASS: resolved 46 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 43 packages. |
| Docker Compose config | PASS: `infrastructure/local/docker/compose.yaml`. |
| Ruff | PASS. |
| Ruff format | PASS: 184 files already formatted. |
| Authoritative mypy | PASS: `uv run mypy apps/api/src packages/python/*/src`; 53 source files. |
| TASK-M0-009 web tests | PASS: 1 file, 6 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| `pnpm install --frozen-lockfile` | PASS. |
| `pnpm check` | PASS. |
| TASK-M0-008 API tests | PASS: 7 passed, 2 known dependency warnings. |
| API tests and integration | PASS: 23 passed, 2 known dependency warnings. |
| TASK-M0-006/007 focused runtime/provider tests | PASS: 33 passed. |
| API/runtime/policy/persistence/contracts/core/provider package regression | PASS: 290 passed, 2 known dependency warnings. |
| Architecture/security/BOOT acceptance | PASS: 77 passed, 2 known dependency warnings. |
| PostgreSQL live integration | PASS: 5 passed serially; named volume preserved; no `docker compose down -v` used. |
| Full pytest | PASS: 399 passed, 2 known dependency warnings. |
| `git diff --check` | PASS. |

Known warnings were the existing Starlette/FastAPI `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings.

An initial web test command was accidentally run concurrently with
`pnpm install --frozen-lockfile` and failed during dependency relinking with a
missing Vitest module. It was discarded as invalid validation evidence; the
post-install rerun passed.

## Lifecycle And Downstream Readiness

TASK-M0-009 is `VALIDATED, FROZEN`.

The validation/freeze commit is required and must be integrated into `main`
before downstream readiness changes. Under the frozen M0 DAG, TASK-M0-010
becomes `READY` only after both TASK-M0-008 and TASK-M0-009 validation/freeze
commits are integrated into `main`. At this task-branch validation point,
TASK-M0-010 remains `BLOCKED`.

No merge, push, correction, or TASK-M0-010+ implementation was performed.

## Files Modified

- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-009-evidence.md`
- `docs/tasks/TASK-M0-009-validation-evidence.md`
