---
id: TASK-M1-017-VALIDATION-EVIDENCE
title: TASK-M1-017 Independent Validation Evidence
task_id: TASK-M1-017
status: VALIDATED / FROZEN
artifact_type: validation_evidence
date: 2026-09-27
---

# TASK-M1-017 Independent Validation Evidence

## Scope

Independent validation covered TASK-M1-017 as an acceptance/proof task. No
production implementation or CI workflow was modified. The implementation under
validation was `977745a7185be89ccc09d139aca96e8960a3330f` on branch
`task/m1-017-acceptance-suite`.

Published baseline:
`c3ce513a08f1c123a250245b3d0aa651fd9d700e`

Validation strengthened the acceptance test surface only: VS-M1-006 now also
checks malformed JSON and missing media-type failures in addition to non-object
JSON and unsupported media.

## Delta Review

Implementation changed:

- `tests/acceptance/test_m1_acceptance.py` - REQUIRED
- `tests/acceptance/test_boot_acceptance.py` - JUSTIFIED SUPPORT
- `tests/security/test_security_baseline.py` - JUSTIFIED SUPPORT
- `docs/tasks/TASK-M1-017-evidence.md` - REQUIRED
- `docs/program/status-ledger/M1-status-ledger.md` - REQUIRED

Validation changed:

- `tests/acceptance/test_m1_acceptance.py` - validator strengthening
- `docs/tasks/TASK-M1-017-validation-evidence.md` - REQUIRED
- `docs/program/status-ledger/M1-status-ledger.md` - REQUIRED

Production and CI diff audit:

```text
git diff c3ce513a08f1c123a250245b3d0aa651fd9d700e..HEAD -- apps packages infrastructure .github
```

Result: no production source, infrastructure, or workflow delta.

The `test_boot_acceptance.py` change is narrowly justified: the existing BOOT
acceptance topology test enumerates the exact tracked acceptance files. Adding
`tests/acceptance/test_m1_acceptance.py` preserves the assertion and does not
remove, skip, weaken, or alter BOOT semantics.

## Acceptance Matrix

| Slice | Authoritative Milestone Criterion | Acceptance Test | Real Boundaries | Fake Boundaries | Positive PASS | Negative FAIL | Durable Truth | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VS-M1-001 | Submit simple intent and observe canonical cognitive records plus acyclic Work DAG. | `test_vs_m1_001_accepts_intent_as_recorded_cognitive_dag_truth` | FastAPI M1 API, deterministic decomposition, Intent/Problem/Assumption/Decision/Plan/WorkItem contracts, WorkDag, PostgreSQL DAG repository | None | Supported intent returns linked cognitive records, bounded work items, acyclic DAG, persisted/recovered DAG identity | Unsupported near-miss returns `UNSUPPORTED` with no DAG/work items | PostgreSQL schema-local DAG persistence and restart readback | PASS |
| VS-M1-002 | Deterministically match task capability requirements to a disposable agent instance. | `test_vs_m1_002_accepts_capability_agent_assignment_as_recorded_truth` | Capability resolver, CapabilityRequirement, Capability, AgentDefinition, AgentInstance, agent repository, lifecycle repository, EventEvidenceRuntimeStore, PostgreSQL | None | Capability resolves to active persisted agent and lifecycle events persist/recover | Missing and duplicate capability produce bounded `MISSING`/`AMBIGUOUS` | PostgreSQL schema-local agent/lifecycle/event persistence | PASS |
| VS-M1-003 | Execute independent DAG nodes up to fixed concurrency while dependent nodes wait. | `test_vs_m1_003_and_004_accept_bounded_execution_and_routing_outcomes` | FastAPI runner endpoint, WorkDag readiness, routing decision input, capability resolution input, active agent gate, BoundedM1DagRunner, deterministic executor seam | Deterministic executor seam only; no live provider | `max_concurrency=1` executes one READY node, defers another READY node, and leaves dependent node `WAITING` in deterministic order | Inactive agent fails boundedly | No DB required by slice | PASS |
| VS-M1-004 | Record deterministic/no-model route decisions without live generation. | `test_vs_m1_003_and_004_accept_bounded_execution_and_routing_outcomes` | Routing selection, RoutingDecisionRecord, runner route consumption, route/work compatibility | No live provider/model | Selected deterministic route produces executor outcome without live model generation | `NO_ROUTE` and `ROUTE_NOT_EXECUTABLE` remain domain outcomes with no executor artifacts | No DB required by slice | PASS |
| VS-M1-005 | Completion requires verification evidence, not executor self-report. | `test_vs_m1_005_accepts_only_verification_gated_completion` | FastAPI runner endpoint, recorded runner output, EvidenceReference, FastAPI verification endpoint, BoundedM1VerificationLoop | None | Same-work PASSED evidence approves; FAILED rejects; non-terminal attempts defer | Wrong subject, duplicate evidence, and non-executed output cannot approve | No DB required by slice | PASS |
| VS-M1-006 | API/web display recorded truth without becoming semantic authority. | `test_vs_m1_006_accepts_recorded_truth_api_web_and_safe_error_boundaries` plus frozen web tests | FastAPI OpenAPI/runtime M1 endpoints, transport gates, web API boundary, App source authority guard, M1-014 web regression coverage | Web tests use fake API boundary; no browser E2E required by task | Exact three POST endpoints with JSON object body contract and explicit web M1 capabilities | Non-object/malformed JSON, missing/unsupported media, no-secret safe errors, direct App network/storage absence, and draft/canonical provenance guard | No DB required by slice | PASS |

## Acceptance Strength

The M1-017 suite is not a renamed copy of M1-015. M1-015 proved cross-boundary
integration mechanics; M1-017 adds milestone PASS/FAIL semantics under
`tests/acceptance`, including an explicit VS-M1 acceptance registry, CI
acceptance-command discovery, BOOT/M0 acceptance coexistence, and acceptance
assertions for the milestone public surfaces.

The tests would fail for meaningful milestone regressions: mislinked cognitive
records, cyclic or non-durable DAG truth, capability mismatch, missing lifecycle
events, ignored concurrency, invalid route selection, approval of wrong or
duplicate evidence, M1 API transport regressions, App direct network authority,
or M1-014 draft/canonical provenance regression removal.

## Boundary Audit

Real Curios boundaries: FastAPI M1 API, deterministic decomposition, canonical
contracts, WorkDag, PostgreSQL DAG repository, capability resolver, agent
repositories, lifecycle events, event/evidence store, routing selection/records,
bounded DAG runner, deterministic executor seam, verification loop, OpenAPI,
web API-boundary source, and frozen web regression tests.

Fake/deterministic boundary: external provider/model execution is intentionally
absent. No Ollama server, model download, generation, chat, embeddings, cloud
provider, credentials, or live provider network is required.

## PostgreSQL Authenticity And Isolation

VS-M1-001 and VS-M1-002 use the established local Docker PostgreSQL boundary
through `PersistenceStore`, not SQLite or in-memory stubs. Each DB-backed
acceptance test uses a UUID-derived schema and drops it after execution.
Durable readback and restart/reconstruction are asserted where required.

## CI Discovery And Enforcement

Frozen M1-016 command:

```text
uv run pytest tests/acceptance -q
```

Collection proof:

```text
14 tests collected
```

The original 8 BOOT/M0 acceptance tests remain discovered, and the six M1
acceptance tests are discovered with no skips or deselections. The Quality
Gates workflow still invokes this command as a hard step with no
`continue-on-error`, marker deselection, alternate path, or conditional skip.

## Determinism And Isolation

The M1 acceptance file passed normally and in explicit reverse node order. The
first validation attempt accidentally ran M0 and M1 DB-backed acceptance in
parallel; M0 stopped the shared local PostgreSQL service while M1 was using it,
causing one `connection refused` failure in VS-M1-001 cleanup. Service logs
showed fast shutdowns. The affected M1 acceptance suite passed when rerun
serially. Final DB-backed verification was run serially.

## Scope Boundaries

M1-017/M1-018: no M1 independent verification record, independent milestone
verdict, verification baseline declaration, or M1-018 ledger completion is
introduced.

M1-017/M1-019: no final M1 freeze record, final baseline declaration, tag,
release, deployment, or milestone closure is introduced.

## Verification

Focused validation:

| Check | Result |
| --- | --- |
| Acceptance collection | PASS, 14 collected |
| BOOT acceptance file | PASS, 6 passed |
| M0 acceptance file | PASS, 2 passed |
| M1 acceptance file | PASS after serial rerun, 6 passed |
| M1 acceptance reverse order | PASS, 6 passed |

Complete verification after validation records changed:

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS, 50 packages resolved |
| `uv sync --locked --all-groups --all-packages` | PASS, 47 packages checked |
| `pnpm install --frozen-lockfile` | PASS |
| Docker Compose config | PASS |
| `ruff format --check .` | PASS, 285 files already formatted |
| `ruff check .` | PASS |
| `mypy apps/api/src packages/python/*/src` | PASS, 70 source files |
| `pnpm check` | PASS |
| Web tests | PASS, 26 passed |
| Web typecheck | PASS |
| Web build | PASS |
| Contract/schema/architecture/security | PASS, 412 passed |
| Package-local Python/API/provider suites | PASS, 366 passed |
| M0 runtime/persistence/policy non-integration | PASS, 287 passed, 10 deselected |
| API integration | PASS, 6 passed |
| M1 package/API gate | PASS, 618 passed, 9 deselected |
| PostgreSQL provider | PASS, 1 passed |
| M0 PostgreSQL repositories | PASS, 4 passed |
| M1 PostgreSQL gate | PASS, 4 passed |
| M0 vertical slice | PASS, 2 passed |
| VS-M1 integration gate | PASS, 6 passed |
| M1 acceptance | PASS, 6 passed |
| Frozen acceptance command | PASS, 14 passed |
| Full pytest | PASS, 1175 passed |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |

TASK-M1-017 is validated and frozen. It remains unmerged and unpublished.
