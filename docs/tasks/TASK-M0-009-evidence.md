---
id: TASK-M0-009-EVIDENCE
title: TASK-M0-009 M0 Web Work Console Evidence
lifecycle: VALIDATED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-009
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-009 Evidence

## Objective

Implement the minimal M0 web work console over the frozen TASK-M0-008 API
route contract.

The console is an outer React/TypeScript presentation layer. It does not own
runtime coordination, policy decisions, persistence, provider inventory
execution, event/evidence semantics, canonical IDs, or canonical state
vocabularies.

## Starting Baseline

`817c57915d9929bfe90d064b3dc9f503a4721972`

## Implemented Surface

- `apps/web/src/App.tsx`
- `apps/web/src/App.css`
- `apps/web/src/App.test.tsx`
- `apps/web/src/apiBoundary.ts`
- narrow security/architecture guardrail updates for the exact web source
  files
- M0 ledger transition to `IMPLEMENTED, TESTED`

No backend route, API semantic change, runtime service, policy evaluator,
persistence behavior, provider executor, scheduler, DAG editor, agent console,
model router UI, DataLab UI, admin/IAM UI, arbitrary tool runner, polling,
WebSocket, SSE, or generated API SDK was added.

## Console Capability

The web console lets a user:

1. create provider-inventory work through `POST /work/provider-inventory`;
2. run that work through `POST /work/{work_id}/run`;
3. observe recorded work and execution state;
4. observe runtime events;
5. observe evidence;
6. observe provider inventory descriptor results;
7. manually refresh recorded API truth.

The UI exposes only the M0 provider-inventory operation. It does not expose
arbitrary work-type selection, arbitrary effects, policy overrides, authority
inputs, executor selection, provider routing, model selection, or tool
definitions.

## API Boundary

`apps/web/src/apiBoundary.ts` is the sole web API boundary module. It declares
the frozen TASK-M0-008 route set:

- `GET /health/live`
- `GET /health/ready`
- `GET /providers`
- `POST /work/provider-inventory`
- `GET /work/{work_id}`
- `POST /work/{work_id}/run`
- `GET /work/{work_id}/executions/{execution_id}`
- `GET /work/{work_id}/events`
- `GET /work/{work_id}/evidence`

The module contains API-specific response shapes only. Those shapes are not
promoted into canonical TypeScript contracts because the frozen TypeScript
contract package currently provides only the package boundary marker, not
generated canonical runtime models.

## Failure and Stale-Response Behavior

The console displays bounded API failures without exposing stack traces,
database details, provider-native payloads, or backend internals.

It distinguishes:

- `BLOCKED` / non-authorizing policy truth;
- bounded provider/runtime failure;
- missing or unavailable API/runtime composition.

The console tracks the active work ID and request generation. If a late
response for a prior work item arrives after a newer work item is selected, it
is ignored and cannot overwrite the displayed runtime truth.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Web remains outer UI | PASS | React components call API helpers and do not import backend/Python packages. |
| Uses frozen M0 API routes only | PASS | API boundary path list is exact and tested. |
| Provider-inventory creation | PASS | Web test submits `POST /work/provider-inventory` only. |
| Run action | PASS | Web test invokes `POST /work/{work_id}/run` with no arbitrary effects. |
| Work/execution observation | PASS | UI displays API-returned work and execution IDs/states. |
| Events/evidence presentation | PASS | UI displays API-returned event and evidence facts only. |
| Provider inventory result | PASS | UI displays provider descriptors returned by the API runtime result. |
| BLOCKED/failure display | PASS | Tests cover `BLOCKED` and provider failure without stack/native detail. |
| Stale response protection | PASS | Test proves stale observations for work A do not overwrite newly selected work B. |
| Deterministic tests | PASS | Tests mock `fetch`; no live backend is required. |
| Accessibility basics | PASS | Controls use semantic buttons, disabled busy states, labeled sections, and status/alert live regions. |
| Topology exact | PASS | Security tests authorize exact web source files and reject future scheduler/DAG/agent/model/DataLab/admin/tool UI files. |

## Verification

Focused implementation verification:

- apps/web tests: `1 file`, `6 passed`
- apps/web typecheck: passed
- apps/web production build: passed
- `pnpm check`: passed after formatting

Repository verification performed:

- TOML validation: passed
- `uv lock --check`: passed
- `uv sync --locked --all-groups --all-packages`: passed
- Docker Compose config: passed
- Ruff: passed
- Ruff format check: passed
- mypy: passed, `53 source files`
- API tests and API integration: `22 passed`, `2` known dependency warnings
- `curios_runtime` tests: `91 passed`
- policy/persistence-boundary/contracts/core tests: `162 passed`
- provider package tests: `29 passed`
- contract/schema/architecture/security/acceptance tests: `92 passed`, `2`
  known dependency warnings
- PostgreSQL live integration tests: `5 passed`; postgres became healthy,
  `pg_isready` accepted connections, service stopped cleanly, and the named
  volume remained present
- full pytest: `399 passed`, `2` known dependency warnings
- `pnpm install --frozen-lockfile`: passed
- `pnpm check`: passed
- apps/web tests: `1 file`, `6 passed`
- apps/web typecheck: passed
- apps/web production build: passed
- `git diff --check`: passed

## Lifecycle

TASK-M0-009 is `VALIDATED, FROZEN` after independent validation at candidate
`7dfbf04361b5f1ebacabbfc63d7233b896881ed4`.

The validation/freeze commit must be integrated into `main` before
TASK-M0-010 can become ready.
