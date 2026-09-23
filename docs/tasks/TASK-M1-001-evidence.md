---
id: TASK-M1-001-EVIDENCE
title: TASK-M1-001 M1 Topology and Guardrail Transition Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-001
milestone_id: M1
date: 2026-09-23
---

# TASK-M1-001 Evidence

## Objective

Establish the M1 topology and guardrail transition required before M1
implementation begins.

TASK-M1-001 does not implement cognitive contracts, deterministic
decomposition, DAG records/runtime, capability resolution, agent persistence,
executor seams, model/profile discovery, routing records, bounded runner,
verification loop, API routes, web UI, integration tests, acceptance tests, CI,
or M2+ behavior.

## Starting Baseline

`97e52872e8e087cd0da4dea72d2ac1a8e90868c1`

M1 planning is `VALIDATED, FROZEN`. TASK-M1-001 is the first authorized M1
execution unit from that baseline.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Reconstruct current frozen topology | PASS | Current topology remains frozen BOOT+M0; no production package/app/runtime/API/web surface was added. |
| Represent planned M1 surfaces | PASS | Security tests include a planned M1 surface registry by owning task while keeping only TASK-M1-001 currently authorized. |
| Enforce planned is not authorized | PASS | Adversarial tests reject premature M1 package, contract, runtime, API, web, integration, and acceptance surfaces. |
| Preserve BOOT/M0 security | PASS | Existing secret scanning, `.github`, provider, API/web, integration, acceptance, policy, and authority tests remain active. |
| Preserve architecture direction | PASS | Architecture tests block contracts/core from depending on representative M1 implementation roots. |
| Protect canonical authority | PASS | New contract file topology tests reject premature `Intent`, cognitive graph, DAG, routing, and model-profile contract files. |
| Keep agent/execution separate | PASS | TASK-M1-001 adds no agent semantics; architecture/security tests reject premature agent runtime/lifecycle surfaces. |
| Keep model scope bounded | PASS | Model generation, inference, router optimization, and live quality gates remain blocked by topology examples and workflow checks. |
| Keep DAG scheduler separate | PASS | M1 bounded DAG surfaces remain planned only; production scheduler/orchestration examples remain blocked. |
| Preserve API/web exactness | PASS | M1 API/web examples are rejected until TASK-M1-013 and TASK-M1-014 authorize exact files. |
| Preserve test-surface exactness | PASS | M1 integration and acceptance examples are rejected until TASK-M1-015 and TASK-M1-017. |
| Preserve CI exactness | PASS | `.github/workflows/quality-gates.yml` remains the only authorized GitHub path; workflow content unchanged. |
| Update lifecycle truthfully | PASS | TASK-M1-001 is recorded as `IMPLEMENTED, TESTED`; TASK-M1-002 through TASK-M1-019 remain `BLOCKED`. |

## Files Changed

- `tests/security/test_security_baseline.py`
- `tests/architecture/test_architecture_conformance.py`
- `docs/security/TASK-M1-001-topology-guardrails.md`
- `docs/architecture/TASK-M1-001-topology-guardrails.md`
- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-001-evidence.md`

## Topology Model

M1 surfaces are represented as planned task-owned categories. They are not
currently authorized implementation files.

Current authorization remains frozen BOOT+M0 plus TASK-M1-001 guardrail docs,
security tests, architecture tests, task evidence, and ledger updates.

## Adversarial Coverage

The guardrail tests reject representative premature additions for:

- M1 cognitive contract files;
- TypeScript contract files;
- M1 package roots;
- DAG/agent/executor/model/routing/runner/verification runtime modules;
- M1 API source and API tests;
- M1 web source files;
- M1 integration tests;
- M1 acceptance tests;
- M2+ package roots and top-level runtime/service/provider roots.

## Dependency Changes

None.

## Frozen Baseline Integrity

TASK-M1-001 changed only guardrail tests and governance documentation. It did
not change frozen production semantics, package manifests, dependency locks,
CI workflow content, API behavior, web behavior, or runtime implementation.

## Verification

| Check | Result |
| --- | --- |
| Security and architecture focused suite | Passed: `269 passed`. |
| TOML validation | Passed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed. |
| mypy strict baseline | Passed: no issues in 53 source files. |
| Package/API/provider tests | Passed: 168 passed, 2 known dependency warnings. |
| M0 runtime, persistence, and policy package tests | Passed: 128 passed, 4 deselected. |
| Contract and schema tests | Passed: 15 passed. |
| Security tests | Passed: 236 passed. |
| Architecture tests | Passed: 33 passed. |
| API integration tests | Passed: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration test | Passed: 1 passed. |
| M0 PostgreSQL integration tests | Passed: 4 passed. |
| M0 vertical-slice integration tests | Passed: 2 passed, 2 known dependency warnings. |
| BOOT/M0 acceptance tests | Passed: 8 passed, 2 known dependency warnings. |
| Full pytest suite | Passed: 601 passed, 2 known dependency warnings. |
| PostgreSQL health and lifecycle | Passed: `postgres` reached healthy, stopped cleanly, and `curios-local-docker_postgres_data` remained present. |
| Frontend checks | Passed: frozen install, `pnpm check`, apps/web tests (6 passed), typecheck, and production build. |
| Workflow Prettier check | Passed. |
| `git diff --check` | Passed. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings previously classified as
non-blocking dependency warnings.

## Lifecycle State

TASK-M1-001 is `IMPLEMENTED, TESTED`.

TASK-M1-002 through TASK-M1-019 remain `BLOCKED`.
