---
id: TASK-M1-018-INDEPENDENT-VERIFICATION-RECORD
title: TASK-M1-018 Independent M1 Verification Record
lifecycle: VALIDATED / FROZEN
artifact_type: verification_record
authority: independent_verification
task_id: TASK-M1-018
milestone_id: M1
parallel_group: PG-M1-13
date: 2026-09-27
---

# TASK-M1-018 Independent M1 Verification Record

Independent M1 verification was performed against published baseline:

`db7f37555219017a7b1baa8a329cdaded02e8962`

## Verdict

PASS. The M1 baseline through TASK-M1-017 is independently verified as
implemented, validated, frozen, integrated, published, and remote-CI-verified.

M1 is not finally frozen by this record. TASK-M1-019 remains the final M1
freeze and closure task.

## Scope

TASK-M1-018 is a verification-record task. It audits and records the complete
M1 baseline; it does not modify product implementation, tests, CI workflow,
contracts, API behavior, web behavior, persistence schema, providers, models,
runtime behavior, release state, deployment state, or TASK-M1-019 final freeze
state.

Authorized changes for this task are limited to this verification record and
the M1 status ledger.

## Verification Inputs

- M1 task pack and implementation DAG.
- M1 status ledger.
- TASK-M1-001 through TASK-M1-017 implementation, correction, validation, and
  publication evidence available in the repository history.
- VS-M1-001 through VS-M1-006 integration and acceptance definitions.
- M1-015 integration evidence.
- M1-016 CI evidence and frozen Quality Gates workflow.
- M1-017 acceptance evidence.
- Architecture, security, API, frontend, persistence, provider/model,
  dependency, and repository-hygiene guards.
- Exact published remote CI run `36312837839`, attempt 1 and attempt 2.
- TASK-M1-019 scope, read only, to preserve the final-freeze boundary.

## Lifecycle Matrix

All rows are ancestors of the verified published baseline.

| Task | Objective | Implementation | Corrections | Validation / Freeze | Published / Remote CI | Result |
| --- | --- | --- | --- | --- | --- | --- |
| TASK-M1-001 | Topology and guardrail transition | `3525d4f` | `21c4b69`, `0e5e6dd`, `f978bcd`, `1d96598`, `8e854d7` | `2debf19` | Yes | PASS |
| TASK-M1-002 | Cognitive intent and problem contracts | `1c46cfc` | None required | `beec99e` | Yes | PASS |
| TASK-M1-003 | Deterministic intent decomposition | `b7dfe95` | `7c77e8d` | `e600ca6` | Yes | PASS |
| TASK-M1-004 | Work DAG records and state | `f93b4e6` | None required | `dfbe3c3` | Yes | PASS |
| TASK-M1-005 | Capability resolver foundation | `e474167` | None required | `b0b23f4` | Yes | PASS |
| TASK-M1-006 | Agent definition and instance persistence | `c8fb4be` | None required | `e176780` | Yes | PASS |
| TASK-M1-007 | Agent lifecycle repository and events | `2489a0a` | None required | `cba5cbf` | Yes | PASS |
| TASK-M1-008 | Executor seam and deterministic executors | `40749c8` | None required | `198ac27` | Yes | PASS |
| TASK-M1-009 | Model/profile discovery records | `1cf85e7` | `6296302` | `d757005` | Yes | PASS |
| TASK-M1-010 | Routing decision records | `31be8aa` | `ae41a82` | `c0d119a` | Yes | PASS |
| TASK-M1-011 | Bounded DAG runner | `15ea024` | `c1547bd` | `3036163` | Yes | PASS |
| TASK-M1-012 | Verification loop and evidence binding | `7a729bc` | None required | `81af19f` | Yes | PASS |
| TASK-M1-013 | M1 API cognitive-loop endpoints | `87372e0` | `fdb68bb`, `80f3b67` | `99da357` | Yes | PASS |
| TASK-M1-014 | M1 web cognitive-loop console | `d1bc17e` | `82d3829` | `a3e30fc` | Yes | PASS |
| TASK-M1-015 | M1 vertical-slice integration tests | `ff98e43` | None required | `22314d9` | Yes | PASS |
| TASK-M1-016 | M1 CI Quality Gate Update | `be0e8a5` | None required | `c3ce513` | Yes | PASS |
| TASK-M1-017 | M1 Acceptance Suite | `977745a` | None required | `db7f375` | Yes | PASS |

The cumulative published baseline `db7f37555219017a7b1baa8a329cdaded02e8962`
contains every listed implementation, correction, and validation/freeze commit.
Exact-SHA Quality Gates for this baseline passed on run `36312837839`, attempt
2, after an attempt-1 transient frontend toolchain failure before repository
frontend steps executed.

## Correction History

| Area | Original defect | Correction | Verification |
| --- | --- | --- | --- |
| M1-001 | Frontend topology and authority hardening required iterative guardrail corrections. | Corrections through `8e854d7`, including Correction 5 web authority hardening. | Frozen topology/security guards remain enforced by architecture and security suites. |
| M1-003 | Intent template matching accepted partial-token matches. | `7c77e8d` required complete-token matching. | Deterministic decomposition regressions remain covered. |
| M1-009 | Provider text could cross the safe-error boundary. | `6296302` bounded provider-local model/profile errors and no-secret metadata. | Safe-error regressions and provider/model audit passed. |
| M1-010 | Provider-reference constraints were insufficiently validated. | `ae41a82` corrected provider constraint validation. | Routing and repository tests preserve deterministic no-route/constraint behavior. |
| M1-011 | Selected route/work incompatibility could be misrepresented. | `c1547bd` enforces `ROUTE_NOT_EXECUTABLE` with no executor success artifacts. | Runner integration and acceptance retain route/work compatibility coverage. |
| M1-013 Correction 1 | Malformed or non-object JSON transport could leak raw body/detail. | `fdb68bb` returns bounded `M1_API_MALFORMED_REQUEST`. | API and acceptance safe-error checks pass. |
| M1-013 Correction 2 | Missing/unsupported media could reach domain invocation. | `80f3b67` rejects media before domain invocation. | API and acceptance media-boundary checks pass. |
| M1-014 Correction 1 | Canonical intent panel could combine accepted IntentId A with mutable draft objective B. | `82d3829` renders canonical panel from accepted decomposition truth and separates draft state. | Web tests and M1 acceptance preserve draft/canonical provenance. |

No current unresolved correction follow-up was found.

## VS-M1 Integration Audit

M1-015 provides executable integration proof in
`tests/integration/test_m1_vertical_slice_integration.py`.

| Slice | Boundaries crossed | Real components | Authorized fake boundary | Durable truth | Negative / failure semantics | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| VS-M1-001 | Intent -> API decomposition -> cognitive records -> Work DAG -> PostgreSQL DAG persistence | M1 API adapter, decomposition, contracts, DAG, PostgreSQL repository | None for internal boundaries | Work DAG persisted and reconstructed | Unsupported intent bounded | PASS |
| VS-M1-002 | Capability requirement -> resolver -> AgentDefinition -> AgentInstance -> lifecycle event persistence | Capability resolver, agent repositories, lifecycle repository, event envelope, PostgreSQL | None for internal boundaries | Agent/lifecycle truth persisted | Missing/ambiguous/inactive bounded | PASS |
| VS-M1-003 | API runner -> DAG readiness -> deterministic READY subset -> executor seam | Bounded runner, readiness, routing input, active agents, executor seam | Deterministic executor only | Runner outcomes and evidence records | Waiting/dependency and route/work compatibility retained | PASS |
| VS-M1-004 | Routing records -> route selection/no-route -> compatibility | Routing contracts and deterministic selector | No live model/provider generation | Routing decisions where required | NO_ROUTE and route/work incompatibility | PASS |
| VS-M1-005 | Recorded execution -> Result -> EvidenceReference -> verification loop | Bounded verification loop, evidence binding, completion decision | Deterministic verifier inputs | Verification references/outcomes | Wrong evidence, duplicate evidence, rejected/deferred | PASS |
| VS-M1-006 | M1 API contract -> web API boundary -> frontend authority/provenance | OpenAPI/API boundary, web apiBoundary, App authority guards | Network transport is not browser-E2E | Canonical UI state provenance | malformed/media errors and draft/canonical regression | PASS |

Local and remote evidence both report the vertical-slice integration gate as
`6 passed`.

## VS-M1 Acceptance Audit

M1-017 provides milestone acceptance proof in
`tests/acceptance/test_m1_acceptance.py`.

| Slice | Acceptance criterion | Positive PASS condition | Negative FAIL condition | Verdict |
| --- | --- | --- | --- | --- |
| VS-M1-001 | Deterministic intent decomposition produces canonical cognitive records and bounded acyclic Work DAG truth. | Linked records and PostgreSQL reconstruction preserve identity. | Unsupported intent remains bounded. | PASS |
| VS-M1-002 | Capability resolution and agent lifecycle produce recorded canonical agent truth. | Resolved capability, agent instance, and lifecycle event persist. | Missing/ambiguous/inactive cases do not authorize execution. | PASS |
| VS-M1-003 | Bounded execution respects readiness, deterministic ordering, max concurrency, and route/work compatibility. | READY work executes through the seam; dependent work waits. | Incompatible or unready work cannot be reported as successful execution. | PASS |
| VS-M1-004 | Routing acceptance proves deterministic selected route and NO_ROUTE semantics without live model dependency. | Valid route is selected deterministically. | No-route or incompatible route remains bounded. | PASS |
| VS-M1-005 | Verification-gated completion requires same-work recorded execution and evidence. | APPROVED/REJECTED/DEFERRED semantics are preserved. | Wrong, duplicate, or non-executed evidence cannot approve. | PASS |
| VS-M1-006 | Recorded-truth API/web behavior preserves exact M1 API surface, JSON object contract, bounded errors, and frontend authority. | The three explicit API operations and web boundary remain compatible. | App direct network authority and A+B draft/canonical hybrid are rejected. | PASS |

The frozen CI acceptance command `uv run pytest tests/acceptance -q` discovers
`14 passed`: 8 existing BOOT/M0 acceptance tests and 6 M1 acceptance tests,
with no skips or deselections.

## Remote CI Audit

Authoritative Quality Gates run:

- Run ID: `36312837839`
- Workflow: `Quality Gates`
- Event: `push`
- Branch: `main`
- Head SHA: `db7f37555219017a7b1baa8a329cdaded02e8962`

Attempt 1:

- Conclusion: failure.
- Failed job: `Frontend`.
- Failing step: `Enable pinned pnpm`.
- Command: `corepack prepare pnpm@12.5.1 --activate`.
- Runner Node: `v24.21.0`.
- Observed failure: Node internal Undici assertion
  `AssertionError [ERR_ASSERTION]: assert(!this.paused)`.
- Failure occurred before frontend repository install, checks, tests,
  typecheck, or build steps executed.
- Python/backend/providers/integration and repository hygiene jobs succeeded.

Attempt 2:

- Conclusion: success at the exact same SHA with no repository change.
- Jobs: `Frontend` success; `Python, Backend, Providers, Integration`
  success; `Repository Hygiene` success.
- Frontend executed pinned pnpm activation, install, `pnpm check`, web tests,
  typecheck, and build successfully.
- Python job evidence included:
  - acceptance: `14 passed`
  - M1 package/API: `618 passed`, `9 deselected`
  - M1 PostgreSQL: `4 passed`
  - VS-M1 integration: `6 passed`
  - security: `360 passed`
  - full pytest: `1175 passed`

Attempt 1 is retained as a historical transient CI/toolchain infrastructure
failure. It is not classified as an M1 product, acceptance, or repository
defect because the identical published SHA passed on a clean rerun without
repository changes.

## CI Enforcement Audit

The frozen M1-016 Quality Gates workflow enforces:

- Frontend install/check/test/typecheck/build.
- Python/backend/provider/integration gates.
- M1 package/API gate.
- M1 PostgreSQL repository gate.
- VS-M1 integration gate.
- Acceptance command.
- Architecture and security tests.
- Full pytest.
- Repository hygiene.

The workflow keeps `permissions: contents: read`, has no deployment or release
authority, and contains no required-gate `continue-on-error`, `|| true`,
`if: false`, or marker/path deselection that hides required M1 gates.

## Architecture Audit

Architecture verification passed. The package direction remains intact:

- `curios_contracts` stays provider/framework independent.
- Core packages depend inward on contracts/core boundaries.
- API and web remain outer adapters.
- M1 cognitive, DAG, capability, routing, runner, verification, provider, and
  persistence responsibilities remain separated.
- No canonical contract authority moved into FastAPI, React, PostgreSQL,
  provider, or runtime implementation layers.

Local architecture/security/contract/schema verification reported
`412 passed` across the combined command.

## Security and Authority Audit

Security verification passed with `360 passed` in the remote successful run.

No unauthorized M1 authority expansion was found:

- No direct App network authority.
- No generic frontend request escape hatch.
- No provider/model authority in the wrong layer.
- No executor authority outside the frozen executor seam.
- No scheduler daemon or arbitrary routing/execution loop.
- No policy grant/bypass expansion.
- No browser durable persistence for M1 canonical state.
- No cloud credentials, release authority, deployment authority, or provider
  credential use in M1 gates.

## Frontend Audit

The M1-001 frontend authority invariant remains enforced. `App` has no direct
or indirect `fetch`, `globalThis.fetch`, `window.fetch`, `fetch.bind`,
`XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon`, or
computed network bypass authority.

M1-014 uses only explicit `apiBoundary` capabilities:

- `decomposeM1Intent`
- `runM1DagOnce`
- `completeM1Verification`

The draft/canonical provenance correction remains covered: mutable draft input
does not mutate accepted canonical intent truth, accepted B replaces A, and
failed B preserves canonical A with bounded error presentation.

## API Audit

The exact M1 API surface remains:

- `POST /m1/intents/decompose`
- `POST /m1/dag/run-once`
- `POST /m1/verification/complete`

M1-013 corrections remain enforced:

- malformed or non-object JSON returns bounded
  `M1_API_MALFORMED_REQUEST` without raw body echo;
- missing or unsupported media type is rejected before domain invocation;
- domain outcomes such as `UNSUPPORTED`, `NO_ROUTE`,
  `ROUTE_NOT_EXECUTABLE`, `WAITING`, `BLOCKED`, `TERMINAL`, `DEFERRED`,
  `APPROVED`, and `REJECTED` remain domain outcomes rather than generic
  transport failures.

No unauthorized M1 API expansion was found.

## Persistence and Migration Audit

Migration chain through the verified baseline:

- `0001_m0_runtime_records.py`
- `0002_m0_append_order_ordinals.py`
- `0003_m1_work_dag_records.py`
- `0004_m1_agent_records.py`
- `0005_m1_routing_decision_records.py`

The M1 durable truth surfaces are covered:

- Work DAG records.
- AgentDefinition and AgentInstance records.
- Agent lifecycle events.
- RoutingDecision records.
- Existing M0 event/evidence/work persistence.

PostgreSQL-backed verification confirmed persisted readback and canonical
reconstruction for the repository and vertical-slice surfaces. No schema or
migration change is part of TASK-M1-018.

## Dependency and Lockfile Audit

Dependency and lockfile verification passed:

- `uv lock --check` resolved 50 packages without lock drift.
- `uv sync --locked --all-groups --all-packages` installed the locked
  workspace environment.
- `pnpm install --frozen-lockfile` completed with repository-pinned pnpm.
- Root Python policy remains `>=3.14,<3.15`.
- Root package manager policy remains `pnpm@12.5.1` with Node `>=24 <25`.
- No unexplained third-party dependency drift was found.

## Provider and Model Audit

M1 requires no live model:

- M1-009 discovery remains provider-local and fakeable.
- M1-010 routing remains deterministic and inert.
- M1-011 runner uses the executor seam.
- M1 integration, acceptance, and CI require no Ollama service, model download,
  generation, chat, embeddings, cloud provider, API key, or external model
  network.

## Determinism Audit

Semantic determinism is preserved for:

- deterministic decomposition over frozen intent templates;
- DAG structure, ordering, readiness, and terminal derivations;
- capability matching;
- route/no-route decisions;
- runner READY selection and max-concurrency behavior;
- verification semantics and first-terminal outcomes;
- recorded-truth reconstruction.

Fresh identifiers and timestamps remain intentionally caller-supplied or
generated where the contracts define them as fresh values; semantic outcomes
do not depend on live model or external network behavior.

## Safe-Error Audit

Safe-error verification passed. Retained public boundaries do not leak known
secret-shaped provider, client, transport, PostgreSQL, framework, traceback, or
raw response details. Bounded errors remain explicitly authorized and
task-scoped.

## Repository Hygiene Audit

Repository hygiene passed:

- no tracked generated junk;
- lock consistency preserved;
- task/evidence consistency preserved;
- `git diff --check` and `git diff --cached --check` passed;
- known `1.txt` remains unrelated and untracked in the primary repository;
- no release, tag, deployment, or M1 closure artifact exists.

Release/deployment check:

- TAGS: none.
- RELEASES: none.
- DEPLOYMENT NOT ESTABLISHED.

## Unresolved Blocker Audit

Searches for current unresolved `FAILED`, `BLOCKED`, `TODO`, `unresolved`,
`deferred defect`, `temporary waiver`, `follow-up required`, `known defect`,
and `incomplete correction` signals found no genuine current M1 blocker.

Historical failures and blockers were classified separately:

- prior task validation failures with validated corrections are resolved;
- M1-017 remote CI attempt 1 is a resolved transient toolchain failure;
- TASK-M1-018 ledger `BLOCKED` was stale after TASK-M1-017 publication and is
  reconciled by this verification record;
- TASK-M1-019 remains blocked by design until TASK-M1-018 is integrated and the
  final-freeze task is explicitly performed.

## Mechanical Verification

All commands were run from the M1-018 worktree at
`db7f37555219017a7b1baa8a329cdaded02e8962` before this record was created.

| Area | Command / suite | Result |
| --- | --- | --- |
| Lock | `uv lock --check` | PASS, 50 packages resolved |
| Sync | `uv sync --locked --all-groups --all-packages` | PASS |
| Frontend install | `pnpm install --frozen-lockfile` | PASS |
| Docker config | Docker Compose config check | PASS |
| Python format | `ruff format --check .` | PASS, 285 files |
| Python lint | `ruff check .` | PASS |
| Python typing | `mypy apps/api/src packages/python/*/src` | PASS, 70 source files |
| Frontend workspace | `pnpm check` | PASS |
| Web tests | `pnpm --dir apps/web test` | PASS, 26 tests |
| Web typecheck | `pnpm --dir apps/web typecheck` | PASS |
| Web build | `pnpm --dir apps/web build` | PASS |
| Contract/schema/architecture/security | combined pytest command | PASS, 412 passed |
| API/package/provider/config/observability | combined pytest command | PASS, 366 passed |
| M0 runtime/persistence/policy non-integration | pytest command | PASS, 287 passed, 10 deselected |
| M1 package/API | pytest command | PASS, 618 passed, 9 deselected |
| API integration | serial pytest command | PASS, 6 passed |
| PostgreSQL provider | serial pytest command | PASS, 1 passed |
| PostgreSQL persistence | serial pytest command | PASS, 2 passed |
| Event/evidence store | serial pytest command | PASS, 1 passed |
| Work repository | serial pytest command | PASS, 1 passed |
| Work DAG repository | serial pytest command | PASS, 1 passed |
| Agent repository | serial pytest command | PASS, 1 passed |
| Agent lifecycle repository | serial pytest command | PASS, 1 passed |
| Routing repository | serial pytest command | PASS, 1 passed |
| M0 vertical slice | serial pytest command | PASS, 2 passed |
| VS-M1 integration | serial pytest command | PASS, 6 passed |
| M1 acceptance | serial pytest command | PASS, 6 passed |
| Complete acceptance | `uv run pytest tests/acceptance -q` | PASS, 14 passed |
| Full pytest | `uv run pytest -q` | PASS, 1175 passed |
| Diff hygiene | `git diff --check`, `git diff --cached --check` | PASS |

Deselects were not counted as passed. They are intentional ownership
selections and are covered by explicit integration gates.

## Warnings and Transients

- Local `uv` emitted a virtualenv path mismatch warning because the shell
  environment pointed at the primary worktree `.venv` while the isolated
  worktree created its own `.venv`; commands still used the project
  environment and passed.
- FastAPI, Starlette, and AnyIO deprecation warnings appeared in relevant test
  suites; they are existing warnings, not M1 blockers.
- No local Docker/PostgreSQL transient occurred during this verification run.
- Remote run `36312837839` attempt 1 failed transiently in Corepack/Node Undici
  before frontend repository steps; attempt 2 succeeded at the same SHA with no
  repository change.

## Downstream State

TASK-M1-019 direct prerequisite is TASK-M1-018.

After this record is committed, TASK-M1-018 is `VALIDATED / FROZEN` on the task
branch but not yet integrated or published by this record. TASK-M1-019 remains
blocked until the TASK-M1-018 lifecycle is integrated and the final-freeze task
is explicitly authorized.

M1 IS NOT YET FINALLY FROZEN. TASK-M1-019 remains the final closure step.
