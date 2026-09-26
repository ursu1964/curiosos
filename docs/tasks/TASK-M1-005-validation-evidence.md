---
id: TASK-M1-005-VALIDATION-EVIDENCE
title: TASK-M1-005 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-005
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-005 Independent Validation Evidence

## Decision

TASK-M1-005 VALIDATION: PASS

Published baseline:

`dfbe3c3a2a17abaca77709852d825bf48b17a892`

Implementation:

`e474167679a0ce891cc8557a93010ac2cfe055f3`

## Reconstructed Acceptance Criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite authority | PASS | TASK-M1-001 is integrated, validated, frozen, published, and remotely CI-verified in the baseline. The integrated M1 ledger marks TASK-M1-005 `READY` before implementation. |
| Authorized package ownership | PASS | TASK-M1-005 owns the M1 capability resolver module. A dedicated `curios_capability` package is the bounded implementation surface; canonical capability and agent contracts remain in `curios_contracts`. |
| Canonical contract reuse | PASS | The resolver consumes existing `CapabilityRequirement`, `Capability`, and `AgentDefinition` values and uses canonical `CapabilityId`, `AgentDefinitionId`, and `ObjectReference` semantics. No shadow capability, requirement, agent, or reference representation was introduced. |
| Exact deterministic matching | PASS | Matching is by exact required `CapabilityId` and exactly one eligible `AgentDefinition.allowed_capability_ids` entry. Provider-neutral hints, metadata, constraints, provider identity, and runtime state are not used for ranking or preference. |
| Known requirement success | PASS | A known requirement with one matching capability and one eligible agent definition returns `MATCHED` / `EXACT_MATCH` with canonical capability and agent-definition refs. |
| Missing capability semantics | PASS | No offered capability with the required ID returns `MISSING` / `CAPABILITY_NOT_OFFERED` with no selected refs or partial proposal state. |
| Missing agent semantics | PASS | A known capability without any eligible agent definition returns `MISSING` / `AGENT_NOT_ELIGIBLE`, preserving only the matched capability ref and no selected agent ref. |
| Ambiguity semantics | PASS | Multiple offered capabilities for the same required ID return `AMBIGUOUS` / `DUPLICATE_CAPABILITY`. Multiple eligible agent definitions return `AMBIGUOUS` / `MULTIPLE_ELIGIBLE_AGENTS`. The resolver does not silently choose the first, lexically preferred, provider-hinted, or insertion-order candidate. |
| Deterministic ordering | PASS | Capability and agent ambiguity outputs are stable under reversed candidate order and repeated calls. Multiple requirement resolution preserves caller requirement order deterministically. |
| Serialization and immutability | PASS | `CapabilityResolution.to_json_compatible()` and `from_json_compatible()` round-trip deterministically. Resolution records are frozen dataclasses with bounded status/reason enums. |
| Provider-neutral hint boundary | PASS | `quality`, `privacy_constraints`, `latency_budget_ms`, `cost_budget`, `resource_constraints`, capability metadata, and agent constraints remain inert provider-neutral data; they do not rank, route, score, select providers, select models, or alter policy. |
| Agent boundary | PASS | Agent definitions are compatibility candidates only. The implementation does not create, mutate, persist, activate, schedule, invoke, rank, or route agent instances. |
| Policy/authority boundary | PASS | Capability compatibility is not authorization. The implementation does not grant capabilities, bypass policy, infer authority, change principal/ownership, create approvals, mutate evidence, or authorize execution. |
| Architecture direction | PASS | `curios_capability` imports only stdlib modules and `curios_contracts`; `curios_contracts`, `curios_core`, persistence, runtime, provider, API, and web surfaces do not import `curios_capability`. |
| Dependency scope | PASS | `uv.lock` changed only to add local editable `curios-capability` with local workspace dependency `curios-contracts`; no third-party dependency drift occurred. |
| Guard changes | PASS | Architecture/security changes are additive bounded authorizations for `packages/python/curios_capability`; M1-001 through M1-004 restrictions remain active and downstream M1 packages remain blocked. |

## Delta Review

| Surface | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_capability/**` | REQUIRED | Owns deterministic M1 capability matching and inert resolution records. |
| `pyproject.toml`, `uv.lock` | REQUIRED | Registers the authorized local workspace package and source path. |
| `tests/architecture/test_architecture_conformance.py` | JUSTIFIED SUPPORT | Adds dependency-direction guard for `curios_capability` so it remains contract-backed and inert. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Moves only the exact M1-005 package from planned to authorized and updates workspace/package inventories. |
| `docs/program/status-ledger/M1-status-ledger.md`, `docs/tasks/TASK-M1-005-evidence.md` | REQUIRED | Repository convention requires lifecycle and implementation evidence. |

No changed file was classified as out of scope.

## Independent Adversarial Probe

The validator ran an independent Python probe outside the committed
implementation tests. It checked:

- exact match repeated calls produce identical output;
- JSON-compatible serialization round-trips;
- missing capability does not choose unrelated capabilities or agents;
- known capability without eligible agent remains bounded missing;
- capability ambiguity is stable under reversed candidate order;
- agent ambiguity is stable under reversed candidate order and sorted by
  canonical agent-definition ID;
- duplicate same capability candidate identity remains ambiguous and is not
  first-picked;
- multiple requirement resolution preserves caller order;
- empty requirement collection returns an empty result;
- cross-kind capability and agent references are rejected;
- result records are frozen/inert;
- output contains no provider, execution, work, state, authority, principal,
  route, schedule, or policy-decision fields.

Probe result: PASS.

## Authority Audit

`curios_capability` contains no imports or call paths for:

- persistence, SQLAlchemy, Alembic, PostgreSQL, or repositories;
- runtime work/execution services;
- FastAPI, API routes, web/frontend code, browser/network behavior;
- provider implementations or provider SDKs;
- model/LLM/prompt systems;
- agent lifecycle, agent instances, schedulers, executors, runners, queues,
  retries, cancellation, workflow runtimes, routing, memory, or learning.

## Verification

| Check | Result |
| --- | --- |
| Implementation ancestry | PASS: `dfbe3c3a2a17abaca77709852d825bf48b17a892..e474167679a0ce891cc8557a93010ac2cfe055f3` is one task implementation commit. |
| Lockfile review | PASS: only local editable `curios-capability` was added to `uv.lock`; no third-party package changed. |
| Independent adversarial probe | PASS. The first probe invocation failed before product code because plain `uv run python` did not include `tests/fixtures`; rerun with `PYTHONPATH=tests/fixtures` passed. |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 231 files already formatted. |
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

Full repository verification was rerun after validation-record changes before
the validation commit.

## Lifecycle Transition

TASK-M1-005 is `VALIDATED, FROZEN`.

No merge, push, deployment, main-branch modification, hook modification, or
next-task implementation was performed.
