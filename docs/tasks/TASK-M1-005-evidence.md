---
id: TASK-M1-005-EVIDENCE
title: TASK-M1-005 Capability Resolver Foundation Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M1-005
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-005 Evidence

## Objective

Implement deterministic capability matching over frozen provider-neutral
`CapabilityRequirement`, `Capability`, and `AgentDefinition` contracts.

TASK-M1-005 does not implement provider selection, policy grants, persistence,
agent instance creation, lifecycle transitions, scheduling, execution, routing,
model/profile discovery, API routes, frontend authority, marketplace behavior,
ontology expansion, learning-based ranking, or downstream executor behavior.

## Starting Baseline

`dfbe3c3a2a17abaca77709852d825bf48b17a892`

TASK-M1-001 through TASK-M1-004 are integrated, validated, frozen, published,
and remotely CI-verified at this baseline. TASK-M1-001 satisfies the frozen
prerequisite for TASK-M1-005, and the integrated M1 ledger records
TASK-M1-005 as `READY`.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Deterministic exact matching | PASS | `resolve_capability_requirement()` matches one `CapabilityRequirement` to exactly one offered `Capability` with the same `CapabilityId` and exactly one eligible `AgentDefinition` whose `allowed_capability_ids` contains that ID. |
| Known requirement succeeds | PASS | Focused tests prove a known requirement returns `MATCHED` with `EXACT_MATCH`, a canonical capability reference, and a canonical agent-definition reference. |
| Missing capability fails boundedly | PASS | Missing offered capability returns a `MISSING` resolution with `CAPABILITY_NOT_OFFERED` and no partial selected refs. |
| Missing eligible agent fails boundedly | PASS | Known capability with no eligible agent returns `MISSING` with `AGENT_NOT_ELIGIBLE`, preserving only the matched capability fact and no selected agent ref. |
| Ambiguous capability fails boundedly | PASS | Duplicate offered capabilities for the same required ID return `AMBIGUOUS` with `DUPLICATE_CAPABILITY` and stable ambiguous capability refs. |
| Ambiguous agent definitions fail boundedly | PASS | Multiple eligible agent definitions return `AMBIGUOUS` with `MULTIPLE_ELIGIBLE_AGENTS` and stable agent-definition refs. |
| Canonical references only | PASS | Resolution records use `ObjectReference` values whose kinds must be `capability` or `agent_definition`; cross-kind references are rejected. No second generic reference abstraction is introduced. |
| Deterministic serialization | PASS | `CapabilityResolution.to_json_compatible()` and `from_json_compatible()` round-trip through sorted JSON; ambiguity refs are sorted by canonical ID. |
| Provider-neutral hints do not grant ranking authority | PASS | Requirement hints and agent/capability metadata do not introduce scoring, provider selection, or route choice; matching remains exact ID based. |
| No runtime authority | PASS | `curios_capability` depends only on `curios_contracts`; it has no persistence, database, API, UI, provider, network, scheduler, executor, routing, model, prompt, memory, or DAG mutation authority. |
| Dependency scope | PASS | `uv.lock` adds only the local workspace package `curios-capability`; no third-party dependency was added. |

## Files Changed

- `docs/program/status-ledger/M1-status-ledger.md`
- `docs/tasks/TASK-M1-005-evidence.md`
- `packages/python/curios_capability/pyproject.toml`
- `packages/python/curios_capability/src/curios_capability/__init__.py`
- `packages/python/curios_capability/src/curios_capability/resolver.py`
- `packages/python/curios_capability/src/curios_capability/py.typed`
- `packages/python/curios_capability/tests/test_task_m1_005_capability_resolver.py`
- `pyproject.toml`
- `tests/architecture/test_architecture_conformance.py`
- `tests/security/test_security_baseline.py`
- `uv.lock`

## Boundary And Authority Inventory

TASK-M1-005 introduces these capabilities:

- deterministic in-memory exact capability matching;
- inert `CapabilityResolution` records for matched, missing, and ambiguous
  outcomes;
- JSON-compatible serialization and reconstruction of those records;
- architecture/security guard authorization for `packages/python/curios_capability`.

TASK-M1-005 does not introduce:

- mutation of canonical `Capability`, `CapabilityRequirement`, or
  `AgentDefinition` records;
- persistence, migrations, database access, or repository ownership;
- provider invocation, network access, model calls, prompts, routing, or
  policy grants;
- `AgentInstance` creation or lifecycle transitions;
- scheduling, execution, retry/cancel behavior, or DAG state mutation.

## Verification

| Check | Result |
| --- | --- |
| Focused M1-005 tests | PASS: `uv run pytest -q packages/python/curios_capability/tests/test_task_m1_005_capability_resolver.py` passed 11 tests. |
| Architecture guard tests | PASS: `uv run pytest -q tests/architecture/test_architecture_conformance.py` passed 36 tests. |
| Security guard tests | PASS after locked workspace sync: `uv run pytest -q tests/security/test_security_baseline.py` passed 354 tests with 2 known FastAPI/Starlette deprecation warnings. Initial pre-sync run failed because `curios_config` was not installed in the fresh task-worktree `.venv`; `uv sync --locked --all-groups --all-packages` corrected the environment and the failure did not recur. |
| Combined focused slice | PASS: `uv run pytest -q packages/python/curios_capability/tests/test_task_m1_005_capability_resolver.py tests/architecture/test_architecture_conformance.py tests/security/test_security_baseline.py` passed 401 tests with 2 known deprecation warnings. |
| Focused typing | PASS: `uv run mypy packages/python/curios_capability/src` found no issues in 2 source files. |
| Focused formatting/lint | PASS: `uv run ruff format --check packages/python/curios_capability tests/architecture/test_architecture_conformance.py tests/security/test_security_baseline.py pyproject.toml` and `uv run ruff check packages/python/curios_capability tests/architecture/test_architecture_conformance.py tests/security/test_security_baseline.py` passed after formatting one edited security file. |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` built/installed all workspace packages, including `curios-capability`. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 230 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python type checking | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 61 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| M1-001/M1-002/M1-003/M1-004/M1-005 regression, contract, schema, architecture, and security tests | PASS: combined slice passed 503 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Package/API/provider tests | PASS: non-Docker package/API/provider slice passed 157 tests with 2 known FastAPI/Starlette deprecation warnings. |
| Docker-backed integrations | PASS: serial Docker slices passed API 6, PostgreSQL provider 1, persistence 2, event/evidence runtime 1, work repository 1, M1-004 DAG repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: `uv run pytest -q tests/acceptance` passed 8 tests with 2 known deprecation warnings. |
| Full pytest suite | PASS: `uv run pytest -q` passed 802 tests with 2 known FastAPI/Starlette deprecation warnings. |

Full repository verification was run after evidence/ledger updates before the
implementation commit.

## Lifecycle State

TASK-M1-005 is `IMPLEMENTED, TESTED`.

Independent validation/freeze is still required before TASK-M1-005 can be
treated as a frozen downstream prerequisite.
