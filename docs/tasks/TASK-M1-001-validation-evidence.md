---
id: TASK-M1-001-VALIDATION-EVIDENCE
title: TASK-M1-001 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-001
milestone_id: M1
date: 2026-09-25
---

# TASK-M1-001 Independent Validation Evidence

## Decision

TASK-M1-001 VALIDATION: PASS

Validated candidate:

`8e854d785d4dbd6f933c8593f161eaca20d78b33`

Starting M1 authority baseline:

`97e52872e8e087cd0da4dea72d2ac1a8e90868c1`

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite authority | PASS | M1 readiness is validated/frozen and authorizes only TASK-M1-001 from the frozen BOOT+M0 baseline. |
| Scope | PASS | Diff is limited to M1 guardrail docs/evidence/ledger plus architecture and security tests. No production package, runtime, contract, persistence, API, web, integration, acceptance, CI, manifest, lockfile, or dependency semantics changed. |
| Planned-vs-authorized topology | PASS | `M1_PLANNED_SURFACES_BY_TASK` records future task ownership while `M1_CURRENTLY_AUTHORIZED_SURFACES_BY_TASK` authorizes only TASK-M1-001 guardrail surfaces. |
| Future M1 surfaces blocked | PASS | Security topology rejects premature cognitive contracts, TypeScript contracts, runtime modules, M1 package roots, API/web files, integration tests, acceptance tests, and M2+ roots. |
| Existing canonical authority frozen | PASS | `curios_contracts` source files, public declarations, class/schema members, initializer import sequence, `__all__`, and package exports are exact and fail closed against aliases, nested exports, dynamic exports, and public authority mutation. |
| Existing outer-boundary authority frozen | PASS | FastAPI application route authority is exact by path/method/name/endpoint/schema visibility; web API-boundary requests and App interactive capabilities are exact. |
| Correction 5 web bypass closed | PASS | The computed `globalThis.fetch.bind(globalThis)` plus `String.fromCharCode(...)` probe is now rejected because App may not hold browser/network capability and handlers reduce to frozen API-boundary capabilities. |
| Architecture direction preserved | PASS | Architecture tests block `curios_contracts` and `curios_core` from depending on representative M1 implementation roots. |
| M0 baseline preserved | PASS | Existing BOOT/M0 secret, workflow, package/app, runtime, API/web, integration, acceptance, policy, and topology guards remain active and pass where runnable. |
| No architecture drift | PASS | No duplicate abstractions, broad topology relaxations, new package roots, weakened guards, or unauthorized dependencies were found. |
| Lifecycle | PASS | TASK-M1-001 is recorded as `VALIDATED, FROZEN`; TASK-M1-002, TASK-M1-005, TASK-M1-006, and TASK-M1-009 are ready only after integration; later tasks remain blocked. |

## Correction 5 Review

The final validation specifically reviewed the prior frontend authority bypass.
The implemented guard no longer depends on literal future path strings or a
small list of selected network call spellings. Instead:

- App imports are structurally frozen;
- authority-bearing imports from `./apiBoundary` and the contracts package are
  exact, including type-only status and aliases;
- App references to `fetch`, `globalThis`, `window`, `XMLHttpRequest`,
  `WebSocket`, `EventSource`, `navigator`, and `sendBeacon` are rejected after
  stripping comments and strings;
- JSX `button`, `form`, and `a` handlers are reduced to frozen API-boundary
  capabilities;
- the only current App interactive capabilities are create provider-inventory
  work, run provider-inventory work, and refresh recorded work/execution/event/
  evidence truth.

No alternate App authority path was found in the current implementation.

## Mechanical Verification

| Check | Result |
| --- | --- |
| `git status --short --branch` | PASS: validation worktree clean before closure edits. |
| Branch/head | PASS: `task/m1-001-topology-guardrails` at `8e854d785d4dbd6f933c8593f161eaca20d78b33`. |
| `uv lock --check` | PASS: 47 packages resolved. |
| `pnpm install --frozen-lockfile` | PASS. |
| Docker Compose config | PASS. |
| `git diff --check` | PASS. |
| Ruff check | PASS. |
| Ruff format check | PASS: 207 files already formatted. |
| mypy strict baseline | PASS: no issues in 53 source files. |
| `pnpm check` | PASS: TypeScript build mode, ESLint, and Prettier. |
| Architecture tests | PASS: 33 passed. |
| Security tests | PASS: 357 passed, 2 known dependency warnings. |
| Contract and schema tests | PASS: 15 passed. |
| Web tests | PASS: 1 file, 6 tests. |
| Package/API/provider tests | PASS: 168 passed, 2 known dependency warnings. |
| M0 runtime, persistence, and policy package tests | PASS: 128 passed, 4 deselected. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| API integration tests | PASS: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration test | ENVIRONMENT SKIP: 1 skipped because the Docker daemon was unavailable. |
| M0 PostgreSQL integration tests | ENVIRONMENT SKIP: 4 skipped because the Docker daemon was unavailable. |
| M0 vertical-slice integration tests | PASS where runnable: 1 passed, 1 skipped because the Docker daemon was unavailable, 2 known dependency warnings. |
| Docker daemon probe | PASS as environment evidence: client installed, server unavailable at `/var/run/docker.sock`. |
| BOOT/M0 acceptance tests | PASS where runnable: 7 passed, 1 skipped because the Docker daemon was unavailable, 2 known dependency warnings. |
| Full pytest suite | PASS where runnable: 715 passed, 7 skipped because the Docker daemon was unavailable, 2 known dependency warnings. |

Known warnings are the existing Starlette/FastAPI `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings.

## Lifecycle Transition

TASK-M1-001 is `VALIDATED, FROZEN`.

According to the frozen M1 DAG, the next executable units are:

- TASK-M1-002 — Cognitive Intent and Problem Contracts;
- TASK-M1-005 — Capability Resolver Foundation;
- TASK-M1-006 — Agent Definition and Instance Persistence;
- TASK-M1-009 — Model/Profile Discovery Records.

They may proceed only after the TASK-M1-001 validation/freeze commit is
integrated into the main M1 baseline. TASK-M1-003, TASK-M1-004,
TASK-M1-007, and TASK-M1-008 through TASK-M1-019 remain blocked.

No merge, push, TASK-M1-002/TASK-M1-005/TASK-M1-006/TASK-M1-009
implementation, CI workflow edit, production correction, deployment, release,
publishing, or cloud behavior was performed.

## Files Modified For Closure

- `docs/architecture/TASK-M1-001-topology-guardrails.md`
- `docs/security/TASK-M1-001-topology-guardrails.md`
- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-001-evidence.md`
- `docs/tasks/TASK-M1-001-validation-evidence.md`
