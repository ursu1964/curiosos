---
id: TASK-M1-003-VALIDATION-EVIDENCE
title: TASK-M1-003 Independent Re-Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-003
milestone_id: M1
date: 2026-09-25
---

# TASK-M1-003 Independent Re-Validation Evidence

## Decision

TASK-M1-003 VALIDATION: PASS

Published baseline:

`beec99e887157383afe48ef8e120cd2b4a31caa8`

Original implementation:

`b7dfe9510b46321affec4c216aaf36099330e28d`

Correction 1:

`7c77e8df850ae9d524e6340cea58c0b40f059f53`

## Reconstructed Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite authority | PASS | TASK-M1-002 is validated/frozen/integrated at the published baseline, satisfying TASK-M1-003 prerequisites. |
| Authorized scope | PASS | The task owns an M1 cognitive implementation module, tests, and evidence only. No API, web, persistence, runtime, provider, model, executor, routing, or downstream task surface was added. |
| Deterministic template decomposition | PASS | Decomposition uses fixed in-repo templates and complete-token matching. There is no model, fuzzy matching, embedding, semantic similarity, prompt, or dependency-backed classifier. |
| Fixed supported categories | PASS | Supported categories are `recorded_truth_summary` and `implementation_plan`. No additional categories were introduced by Correction 1. |
| Template selection and tie-breaking | PASS | Template order is fixed by `_TEMPLATES`; ambiguous complete-token input selects the first template, `recorded_truth_summary`, deterministically. |
| Unsupported intent failure | PASS | Unsupported and near-miss inputs return `UNSUPPORTED` with `NO_TEMPLATE_MATCH` and no `Problem`, `Assumption`, `Decision`, `Plan`, or `WorkItem` proposal state. |
| Corrected lexical boundaries | PASS | `Address a philosophical question.` and `Discuss the statusquo of design terms.` are unsupported. Every configured keyword was independently probed for complete-token match and embedded-token rejection. |
| Cognitive records | PASS | Supported decompositions produce canonical `Problem`, `Assumption`, `Decision`, and `Plan` values built from the TASK-M1-002 contracts. |
| Work proposal DAG | PASS | Supported decompositions produce bounded canonical `WorkItem` proposals with explicit `WorkId` dependencies. The generated graph is acyclic and ordered deterministically. |
| Reference semantics | PASS | Cross-record links use `ObjectReference`; `Plan.work_refs` points to work references; no competing generic reference abstraction exists in `curios_cognitive`. |
| Plan/WorkItem boundary | PASS | `Plan` remains inert and does not duplicate `WorkItem` identity, state, dependencies, capabilities, inputs, outputs, policy, principal, evidence, scheduler, provider, or runtime state. |
| Serialization stability | PASS | Decomposition output serializes through the canonical JSON-compatible convention and repeated identical decompositions produce equal payloads. |
| Package architecture | PASS | `curios_cognitive` depends inward on `curios_contracts` only. `curios_contracts` and `curios_core` do not depend on `curios_cognitive`. |
| Dependencies | PASS | Correction 1 changed no manifest or lockfile. No third-party dependencies were added for TASK-M1-003 validation. |

## Correction 1 Review

Correction 1 is bounded to:

- `packages/python/curios_cognitive/src/curios_cognitive/decomposition.py`;
- `packages/python/curios_cognitive/tests/test_task_m1_003_validation_regressions.py`;
- `docs/tasks/TASK-M1-003-evidence.md`.

The root cause was substring keyword matching in `_select_template()`. The fix
uses deterministic complete-token matching over the existing normalized
objective text. The validator reproduced the original defect before correction
and confirmed after correction that:

- `Address a philosophical question.` returns `UNSUPPORTED`;
- `Discuss the statusquo of design terms.` returns `UNSUPPORTED`;
- both return `NO_TEMPLATE_MATCH`;
- both produce no problem, assumptions, decisions, plan, or work items.

## Independent Adversarial Probes

The validator ran an independent Python probe outside the committed regression
tests. It checked:

- repeated identical decomposition equality;
- every configured keyword as a complete token;
- every configured keyword embedded as prefix, suffix, and internal
  containment in larger tokens;
- punctuation adjacency and capitalization;
- unsupported near-miss language;
- whitespace-only objective input accepted by the upstream `Intent` contract
  and decomposed as unsupported;
- multiple matching complete keywords and deterministic tie-breaking;
- canonical object types and `ObjectReference` kinds;
- JSON-compatible serialization stability;
- work proposal dependency references and acyclicity;
- rejection of cross-kind `intent_ref`;
- rejection of partial proposal state on unsupported results.

Probe result: PASS.

## Architecture And Authority Audit

`curios_cognitive` imports only Python standard-library modules and
`curios_contracts`. The implementation contains no imports or call paths for:

- FastAPI, React, frontend code, or API route behavior;
- SQLAlchemy, Alembic, PostgreSQL drivers, persistence repositories, or ORM
  models;
- provider SDKs, network clients, sockets, subprocesses, Docker tooling, or
  external services;
- OpenAI/Ollama/model/LLM/prompt systems;
- memory, learning, graph runtime, scheduler, executor, routing, or agent
  runtime packages.

Architecture and security tests independently enforce this direction.

## Mechanical Verification

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS: 48 packages resolved. |
| `uv sync --locked --all-groups --all-packages` | PASS: 45 packages checked. |
| `pnpm install --frozen-lockfile` | PASS. |
| Docker Compose config | PASS. |
| `uv run ruff format --check .` | PASS: 218 files already formatted. |
| `uv run ruff check .` | PASS. |
| `uv run mypy apps/api/src packages/python/*/src` | PASS: 56 source files. |
| `pnpm check` | PASS. |
| Web tests/typecheck/build | PASS: 6 tests; typecheck and build passed. |
| M1-003, M1-002, contract/schema tests | PASS: 74 tests. |
| Architecture/security tests | PASS: 390 tests. |
| Package/API/provider tests | PASS: 182 tests. |
| Docker-backed API integration | PASS: 6 tests. |
| Docker-backed PostgreSQL provider integration | PASS: 1 test. |
| Docker-backed persistence integration | PASS: 2 tests. |
| Docker-backed event/evidence runtime integration | PASS: 1 test. |
| Docker-backed work repository integration | PASS: 1 test. |
| M0 vertical slice integration | PASS: 2 tests. |
| Acceptance tests | PASS: 8 tests. |
| Full pytest suite | PASS on rerun: 781 tests. |
| `git diff --check` and `git diff --cached --check` | PASS. |

During full pytest, the first all-suite run failed in
`test_task_m0_002_persistence_boundary_against_local_docker` with PostgreSQL
`connection refused` on `127.0.0.1:5432`. The same isolated Docker-backed
persistence slice passed immediately before the full suite and passed again
after the failure. The full suite then passed on rerun. This is classified as
transient Docker service lifecycle/connectivity instability, not a TASK-M1-003
product defect.

Known warnings: FastAPI/Starlette `TestClient` deprecation warnings and the
inherited `VIRTUAL_ENV` mismatch warning from `uv`.

## Lifecycle Transition

TASK-M1-003 is `VALIDATED, FROZEN`.

According to the frozen M1 DAG, TASK-M1-003 does not by itself unblock
TASK-M1-008. TASK-M1-008 still requires TASK-M1-003, TASK-M1-004, TASK-M1-005,
and TASK-M1-007 to be validated, frozen, and integrated.

No merge, push, deployment, main-branch modification, hook modification, or
next-task implementation was performed.
