---
id: TASK-M1-016-EVIDENCE
title: TASK-M1-016 Implementation Evidence
task_id: TASK-M1-016
status: IMPLEMENTED / TESTED
artifact_type: implementation_evidence
date: 2026-09-27
---

# TASK-M1-016 Implementation Evidence

## Objective

TASK-M1-016 updates the existing Quality Gates workflow so M1 deterministic
package, API, PostgreSQL repository, vertical-slice integration, frontend,
architecture, security, acceptance, and repository-hygiene checks are explicit
CI gates without weakening BOOT/M0 coverage.

The task is CI-only. No production API, web, runtime, contract, persistence,
schema, migration, provider/model, release, deployment, or acceptance-suite
behavior is changed.

## Prerequisite Proof

Baseline:
`22314d9ec2a73a5e137abf2ea20438568c6c2bee`

Prerequisites were satisfied before implementation started:

| Prerequisite | Required State | Actual State |
| --- | --- | --- |
| TASK-M1-015 | VALIDATED / FROZEN / INTEGRATED / PUBLISHED / REMOTE-CI-VERIFIED | Satisfied at published baseline. |

No additional non-task entry gate was found. The stale M1 status-ledger row was
reconciled from `BLOCKED` to `IMPLEMENTED, TESTED` after the CI workflow and
security guard checks passed locally.

## Baseline CI Inventory

The published baseline workflow already contained these jobs:

| Job | Existing Scope | Result |
| --- | --- | --- |
| Python, Backend, Providers, Integration | Python setup, locked sync, Docker Compose config, ruff, mypy, package tests, contract/schema, architecture, security, API integration, PostgreSQL provider, M0 PostgreSQL integration, M0 vertical slice, acceptance, full pytest | Preserved |
| Frontend | locked Node install, repository frontend checks, web tests, typecheck, production build | Preserved |
| Repository Hygiene | whitespace diff check | Preserved |

The workflow retained exact triggers, `contents: read` permissions, pinned
actions, Ubuntu runners, existing BOOT/M0 commands, and the existing acceptance
invocation.

## Workflow Changes

M1-016 adds three explicit Python-job gates:

| Gate | Command | Purpose |
| --- | --- | --- |
| M1 package and API tests | `uv run pytest apps/api/tests packages/python/curios_contracts/tests packages/python/curios_cognitive/tests packages/python/curios_dag/tests packages/python/curios_capability/tests packages/python/curios_runtime/tests -m "not integration" -q` | Explicit M1 package/API gate for contracts, decomposition, DAG, capability, runtime, and M1 API behavior. |
| M1 PostgreSQL integration tests | `uv run pytest packages/python/curios_dag/tests/test_postgres_work_dag_repository_integration.py packages/python/curios_runtime/tests/test_postgres_agent_repository_integration.py packages/python/curios_runtime/tests/test_postgres_agent_lifecycle_repository_integration.py packages/python/curios_runtime/tests/test_postgres_routing_decision_repository_integration.py -q` | Serial M1 repository persistence gate using the established local Docker PostgreSQL boundary. |
| M1 vertical-slice integration tests | `uv run pytest tests/integration/test_m1_vertical_slice_integration.py -q` | Explicit VS-M1-001 through VS-M1-006 CI gate. |

No CI service, credential, workflow permission, release, deployment, artifact
promotion, cloud resource, or live model capability was added.

## M1 Gate Mapping

| Requirement | CI Gate |
| --- | --- |
| M1 package/runtime tests | `M1 package and API tests` |
| M1 API tests | `M1 package and API tests` plus existing API/full pytest gates |
| VS-M1-001..006 integration | `M1 vertical-slice integration tests` |
| M1 PostgreSQL repository integration | `M1 PostgreSQL integration tests` |
| Frontend and M1-014 web tests | existing `apps/web tests`, `typecheck`, `build`, and `pnpm check` |
| Architecture/security | existing `Architecture tests` and `Security tests` |
| Existing acceptance | existing `BOOT acceptance tests` command |
| Repository hygiene | existing `Diff whitespace` plus lock/format/lint checks |

The M1 vertical-slice gate is intentionally explicit rather than relying on
full pytest discovery. A failing VS-M1-001..006 slice fails the Python CI job.

## PostgreSQL And Serialization

M1-016 reuses the established Docker Compose PostgreSQL configuration and the
test-owned startup/cleanup helpers already used by DB-backed suites. It does
not add GitHub Actions service containers or external/cloud databases.

The workflow runs DB-backed groups as separate serial steps in one Python job:
PostgreSQL provider, M0 PostgreSQL repositories, M1 PostgreSQL repositories,
M0 vertical slice, and M1 vertical slices. No retry wrapper or ignored exit
code was added.

## No-Live-Model Boundary

The workflow does not install Ollama, download models, start a model server,
invoke generation/chat/embedding, use cloud model credentials, or introduce
provider secrets. M1 tests continue to rely on deterministic fakeable provider
and executor seams.

## Security Guard Update

`tests/security/test_security_baseline.py` now authorizes TASK-M1-016's exact
workflow/evidence/security surfaces and models the new workflow commands as
required gates. Representative bypass tests reject:

- removing the M1 package/API gate;
- deselecting runtime/package coverage from the M1 gate;
- making M1 PostgreSQL integration advisory;
- replacing M1 PostgreSQL integration with a broad non-authoritative command;
- conditionally skipping the M1 vertical-slice gate;
- swallowing M1 vertical-slice failures;
- replacing the VS-M1 integration test path.

The existing workflow guard still rejects unapproved jobs, steps, permissions,
triggers, environments, services, containers, unpinned actions, and deployment
or release surfaces.

## Boundary With TASK-M1-017

TASK-M1-016 only wires existing deterministic gates into CI. It does not define
the final M1 acceptance suite, create new acceptance tests, mark milestone
acceptance complete, or produce final M1 verification/freeze records. TASK-M1-017
remains the owner of M1 acceptance.

## Production Diff Guard

Authorized implementation surfaces are limited to:

- `.github/workflows/quality-gates.yml`
- `tests/security/test_security_baseline.py`
- `docs/tasks/TASK-M1-016-evidence.md`
- `docs/program/status-ledger/M1-status-ledger.md`

Production source under `apps/`, `packages/`, and `infrastructure/` is not
changed.

## Verification Snapshot

Implementation verification was run locally from the M1-016 worktree:

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS, 50 packages resolved |
| `uv sync --locked --all-groups --all-packages` | PASS, locked workspace synced |
| `pnpm install --frozen-lockfile` | PASS |
| Docker Compose config | PASS |
| `ruff format --check .` | PASS, 281 files already formatted |
| `ruff check .` | PASS |
| `mypy apps/api/src packages/python/*/src` | PASS, 70 source files |
| `pnpm check` | PASS |
| Web tests | PASS, 26 passed |
| Web typecheck | PASS |
| Web build | PASS |
| Contract/schema/architecture | PASS, 52 passed |
| Security baseline | PASS, 360 passed |
| API suite | PASS, 183 passed |
| Exact M1 package/API CI gate | PASS, 618 passed, 9 deselected |
| M1 focused regression block | PASS, 240 passed |
| Package/provider/runtime/persistence non-integration suites | PASS, 470 passed, 10 deselected |
| Exact M1 PostgreSQL CI gate | PASS, 4 passed |
| Exact VS-M1-001..006 CI gate | PASS, 6 passed |
| Docker-backed serial API integration | PASS, 6 passed |
| Docker-backed serial PostgreSQL provider | PASS, 1 passed |
| Docker-backed serial persistence/event/work/DAG/agent/lifecycle/routing | PASS, 10 passed |
| Docker-backed serial M0 vertical slice | PASS, 2 passed |
| Acceptance | PASS, 8 passed |
| Full pytest | PASS, 1169 passed |

No Docker/PostgreSQL transient occurred during the M1-016 implementation
verification run. Existing warnings were limited to the Starlette/httpx and
anyio deprecation warnings emitted through FastAPI `TestClient`, plus the local
`VIRTUAL_ENV` mismatch warning emitted by `uv` in the shared shell environment.

TASK-M1-016 remains awaiting independent validation/freeze.
