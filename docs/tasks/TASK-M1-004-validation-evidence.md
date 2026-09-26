---
id: TASK-M1-004-VALIDATION-EVIDENCE
title: TASK-M1-004 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-004
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-004 Independent Validation Evidence

## Decision

TASK-M1-004 VALIDATION: PASS

Published baseline:

`e600ca6d665d5996f04c1ccf109cd671742cee68`

Implementation:

`f93b4e610c4ac4cff79fa4dfacd8799d9c5ab888`

## Reconstructed Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite authority | PASS | TASK-M1-002 is validated/frozen/integrated in the published baseline; M1-003 is also integrated/frozen but is not a prerequisite for TASK-M1-004. |
| Authorized package ownership | PASS | TASK-M1-004 owns bounded work-DAG records/runtime state. A dedicated `curios_dag` package is the bounded M1 implementation surface; canonical contracts remain in `curios_contracts`. |
| DAG identity and shape | PASS | `WorkDagId`, `WorkDag`, `WorkDagNode`, and `WorkDagEdge` provide DAG identity, node refs, edge refs, bounded node/edge counts, deterministic ordering, and empty-DAG rejection. |
| Work references only | PASS | Nodes and edges require canonical `ObjectReference` values whose kind is `work`. Cross-kind references fail construction. No second generic reference abstraction exists. |
| Acyclic graph invariants | PASS | Construction rejects self edges, duplicate nodes, duplicate edges, missing edge endpoints, two-node cycles, and longer cycles. Disconnected acyclic components, multiple roots/leaves, and diamond DAGs are allowed. |
| Reconstructability and serialization | PASS | `WorkDag.to_json_compatible()` and `WorkDag.from_json_compatible()` round-trip deterministically; alternate input order normalizes to the same node/edge order. |
| No duplicated WorkItem state | PASS | Persisted DAG payloads contain DAG ID, created timestamp, work refs, and dependency edges only. Work status, capabilities, inputs, outputs, policies, authority, principal, and evidence remain canonical `WorkItem` state. |
| Derived readiness/terminal state | PASS | `derive_work_dag_state()` computes dependency read models from supplied canonical `WorkItem` values and does not persist or mutate work. No-dependency nodes are ready, unsatisfied dependencies wait, failed/cancelled dependencies block downstream nodes, and completed/failed/cancelled own state is terminal. |
| Failure/cancellation propagation | PASS | Failed or cancelled upstream work blocks direct dependents and propagates through dependent nodes without changing canonical `WorkItem.state`. |
| Persistence fidelity | PASS | `M1WorkDagRepository` uses `PersistenceStore` and `PersistenceRecordKind.WORK_DAG`, handles missing reads as `None`, duplicate inserts as bounded conflicts, lists by append order, and reconstructs stored DAG records deterministically. |
| Malformed persistence payloads | PASS | Corrupt stored `work_dag` payloads are translated to bounded `WorkDagErrorCode.CORRUPT_RECORD` without leaking native persistence details. |
| Migration fidelity | PASS | `0003_m1_work_dag_records` follows `0002_m0_append_order_ordinals`, creates only `curios_m1_work_dag_records`, uses the existing generic record-table shape, and supports the repository contract. Supported relative downgrade `-1` removes the M1 table and returns the version to `0002`. |
| Architecture direction | PASS | `curios_dag` imports only `curios_contracts` and `curios_persistence`; `curios_contracts` and `curios_core` do not import `curios_dag`; `curios_persistence` does not import `curios_dag`. |
| Authority boundary | PASS | No scheduler, runner, executor, retry engine, provider selection/invocation, model/prompt system, network/API/UI behavior, agent routing, workflow engine, or graph runtime authority is introduced. |
| Dependency scope | PASS | `uv.lock` changed only to add local editable `curios-dag` with local workspace dependencies on `curios-contracts` and `curios-persistence`; no third-party dependency drift occurred. |
| Guard changes | PASS | Architecture/security changes are additive bounded authorizations for `packages/python/curios_dag` and the exact persistence transition; M1-001/M1-002/M1-003 restrictions remain intact. |

## Delta Review

| Surface | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_dag/**` | REQUIRED | Owns the M1-004 DAG records/state/repository surface without modifying canonical contracts. |
| `pyproject.toml`, `uv.lock` | REQUIRED | Registers the authorized local workspace package and source path. |
| `PersistenceRecordKind.WORK_DAG` | REQUIRED | Persistence primitive needed to store DAG records through the existing persistence boundary. |
| `curios_m1_work_dag_records` and migration `0003_m1_work_dag_records` | REQUIRED | PostgreSQL persistence is added, so a dedicated M1 table and migration are required. |
| `curios_persistence.boundary.record_to_canonical()` `WORK_DAG` rejection | JUSTIFIED SUPPORT | Keeps M1 DAG decoding owned by `curios_dag` and avoids reverse dependency from persistence to DAG implementation. |
| Persistence boundary tests | JUSTIFIED SUPPORT | Preserve M0 table inventory while proving bounded M1 `work_dag` persistence errors. |
| Architecture/security guards | JUSTIFIED SUPPORT | Transition planned M1-004 surface to exact authorized package and enforce dependency direction. |
| Ledger/evidence | REQUIRED | Repository convention requires implementation and validation state evidence. |

No changed file was classified as out of scope.

## Independent Adversarial Probes

The validator ran an independent Python probe outside the committed
implementation tests. It checked:

- maximum permitted 100 nodes accepted;
- 101 nodes rejected;
- maximum permitted 1000 edges accepted;
- 1001 edges rejected;
- self edge rejected;
- duplicate node rejected;
- duplicate edge rejected;
- missing edge endpoint rejected;
- longer four-node cycle rejected;
- diamond DAG accepted;
- disconnected acyclic components accepted;
- reverse-order construction normalized deterministically;
- cross-kind `intent` reference rejected for work DAG nodes;
- extra unrelated `WorkItem` ignored during state derivation;
- missing DAG work item rejected during state derivation;
- duplicate supplied `WorkItem` rejected during state derivation;
- failed dependency mixed with satisfied dependency blocks downstream;
- serialization -> deserialization -> serialization stability;
- malformed persisted payload maps to `CORRUPT_RECORD`.

Probe result: PASS.

## Migration Probe

The validator ran a Docker-backed migration probe:

1. migrate a clean isolated schema to `0002_m0_append_order_ordinals`;
2. verify M0 tables exist and `curios_m1_work_dag_records` is absent;
3. migrate to `head`;
4. inspect `curios_m1_work_dag_records` columns and primary key;
5. downgrade by the repository-supported relative revision `-1`;
6. verify the M1 table is removed and Alembic version returns to `0002`;
7. re-upgrade to `head`.

Probe result: PASS.

Note: passing the concrete prior revision string
`0002_m0_append_order_ordinals` to `apply_schema_migrations()` after head is an
upgrade no-op by existing helper policy. The supported downgrade forms are
`base` and relative revisions such as `-1`.

## Authority Audit

`curios_dag` contains no imports or call paths for:

- FastAPI, API routes, web/frontend code, or browser/network behavior;
- provider implementations or provider SDKs;
- OpenAI/Ollama/model/LLM/prompt systems;
- agent lifecycle, routing, executor, runner, scheduler, retry, queue, or
  workflow runtime packages;
- subprocess, sockets, HTTP clients, Docker tooling, or external services in
  production code.

Docker/subprocess/SQLAlchemy imports appear only in integration tests or the
existing persistence package where they are already authorized.

## Verification

| Check | Result |
| --- | --- |
| Implementation ancestry | PASS: `e600ca6d665d5996f04c1ccf109cd671742cee68..f93b4e610c4ac4cff79fa4dfacd8799d9c5ab888` is one task commit. |
| Lockfile review | PASS: only local editable `curios-dag` was added to `uv.lock`; no third-party package changed. |
| Independent adversarial probe | PASS. |
| Docker-backed migration probe | PASS. |
| Dependency lock check | PASS: `uv lock --check` resolved 49 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 46 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 226 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python type checking | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 59 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| M1-001/M1-002/M1-003/M1-004 regression, contract, schema, architecture, and security tests | PASS: combined slice passed 492 tests with 2 known FastAPI/Starlette deprecation warnings. |
| BOOT contract architecture regressions | PASS: 14 tests. |
| Package/API/provider tests | PASS: 157 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Docker-backed integrations | PASS: serial Docker slices passed API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, M1-004 DAG repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: 8 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Full pytest suite | PASS on rerun: 791 tests with 2 known FastAPI/Starlette deprecation warnings. Initial full-suite run after evidence update passed 790 tests and hit a PostgreSQL connection-refused failure in the M1-004 Docker repository test; Docker state showed no running Curios PostgreSQL container after rapid start/shutdown cycles, the exact failed slice passed immediately in isolation, and full pytest passed on rerun. |
| Repository diff integrity | PASS: `git diff --check` and `git diff --cached --check`. |

Known warnings: `uv` reported that inherited
`VIRTUAL_ENV=/home/user/projects/curiosos/.venv` did not match the task
worktree `.venv` and was ignored. FastAPI/Starlette `TestClient` deprecation
warnings appeared in security, API/integration, acceptance, and full-suite
tests.

## Lifecycle Transition

TASK-M1-004 is `VALIDATED, FROZEN`.

No merge, push, deployment, main-branch modification, hook modification, or
next-task implementation was performed.
