---
id: TASK-M1-009-EVIDENCE
title: TASK-M1-009 Model/Profile Discovery Records Evidence
lifecycle: IMPLEMENTED
artifact_type: implementation_evidence
authority: implementation
task_id: TASK-M1-009
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-009 Implementation Evidence

## Objective

TASK-M1-009 adds local model/profile discovery records for local model
candidates without model generation, prompt execution, cloud models, model
quality evaluation, routing decisions, persistence, API behavior, or UI
behavior.

## Starting Baseline

`198ac27df489602abcb0c1efe06b23c6811d1171`

TASK-M1-001 through TASK-M1-008 are integrated, validated, frozen, published,
and remotely CI-verified at this baseline. TASK-M1-009 is `READY` because its
only authoritative prerequisite, TASK-M1-001, is validated/frozen and
integrated.

## Implementation Architecture

TASK-M1-009 extends the existing `curios_ollama` provider boundary with
`curios_ollama.profiles`.

The module provides:

- `LocalModelProfile`: an immutable provider-local profile record containing a
  canonical provider `ObjectReference`, local model name, schema version,
  availability status, optional context-window metadata, and bounded
  JSON-compatible non-secret metadata;
- `ModelProfileStatus`: provider-local profile availability vocabulary;
- `OllamaModelProfileDiscovery`: a fakeable local discovery adapter that turns
  existing `OllamaModelSummary` inventory records into deterministic
  `LocalModelProfile` candidates;
- `MODEL_PROFILE_STATUS_VALUES`: exported provider-local status values.

The implementation reuses the frozen BOOT/M0 provider boundary and existing
`OllamaModelClient` fakeability. It does not add a new package, schema,
migration, canonical contract export, runtime module, API route, or frontend
surface.

## M1-009 / M1-010 Boundary

M1-009 owns:

- local model/profile candidate shape;
- deterministic provider-local discovery from inventory metadata;
- unavailable-provider behavior as bounded `ContractError` failures;
- non-secret bounded metadata validation;
- no-live-model ordinary tests.

M1-010 owns, and this task deliberately leaves absent:

- routing decision records;
- route candidate lists and selected route persistence;
- routing rationale and no-model route records;
- resource-constraint decision records;
- persistence of routing decisions;
- any route selection over executor/model-profile candidates.

## Authority Inventory

| Capability | M1-009 result |
| --- | --- |
| WorkItem read | ABSENT |
| WorkItem mutation | ABSENT |
| WorkDag read | ABSENT |
| WorkDag mutation | ABSENT |
| capability resolution | ABSENT |
| agent read | ABSENT |
| agent creation | ABSENT |
| agent lifecycle transition | ABSENT |
| executor seam invocation | ABSENT |
| ExecutionRecord creation | ABSENT |
| ExecutionRecord mutation | ABSENT |
| Result creation | AUTHORIZED for bounded discovery success/failure envelope |
| event emission | ABSENT |
| evidence creation | ABSENT |
| persistence | ABSENT |
| DB access | ABSENT |
| scheduling | ABSENT |
| provider inventory read | AUTHORIZED through existing fakeable `OllamaModelClient.list_models` |
| provider selection | ABSENT |
| provider invocation | ABSENT beyond non-generating local inventory discovery |
| model generation/invocation | ABSENT |
| network | ABSENT from ordinary tests and profile records; existing optional `OllamaHttpClient` remains BOOT provider-boundary behavior |
| policy evaluation | ABSENT |
| policy grant | ABSENT |
| retry | ABSENT |
| cancellation | ABSENT |
| API | ABSENT |
| UI | ABSENT |
| prompt | ABSENT |
| memory | ABSENT |

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisite proof | PASS | TASK-M1-001 is validated/frozen/integrated in the published baseline; M1 DAG and ledger record TASK-M1-009 as ready. |
| Provider/profile ownership | PASS | Implementation is provider-local under existing `curios_ollama`; no canonical contracts, runtime package, API, web, persistence, or new package surface is introduced. |
| Profile shape | PASS | `LocalModelProfile` is immutable, reconstructable from JSON-compatible data, provider-referenced, schema-versioned, and bounded. |
| Local candidates represented without invocation | PASS | `OllamaModelProfileDiscovery` converts `OllamaModelSummary` inventory records into sorted profile candidates and exposes them through `Result.success`; no model generate/chat/prompt calls exist. |
| Unavailable-provider behavior | PASS | `OSError` maps to dependency failure, `TimeoutError` maps to timeout failure, malformed inventory maps to non-retryable invalid-profile failure, and duplicate model names map to bounded duplicate-profile failure with no partial success value. |
| No-secret metadata | PASS | Profile metadata uses the same bounded safe-detail normalization as frozen contracts and rejects secret-shaped keys and values. |
| Deterministic fakeable tests | PASS | Focused tests use deterministic fake clients, cover empty inventory, reversed provider order, duplicate identities, invalid payloads, unavailable provider failures, no-live-model behavior, and no added SDK/routing dependencies. |
| Downstream boundary | PASS | TASK-M1-010 remains blocked; no routing decision record, selected route, optimizer, or model routing behavior is implemented. |
| Dependency/schema scope | PASS | No `pyproject.toml`, `uv.lock`, pnpm manifest/lock, migration, or schema change is required. |
| Security guards | PASS | Guard inventory authorizes only TASK-M1-009 evidence and the existing `curios_ollama` provider/profile package surface. |

## Failure And Boundary Coverage

Focused tests cover:

- valid minimal local profile record;
- valid full profile record with metadata;
- JSON-compatible serialization/reconstruction;
- wrong reference kind;
- empty model name;
- secret-shaped model name;
- non-positive context window;
- secret-shaped metadata key and value;
- deterministic sorting of candidates;
- empty candidate set;
- unavailable provider;
- timeout;
- invalid provider payload;
- duplicate model names;
- absence of generation, prompt, routing, persistence, DB, provider SDK, or
  network authority in the profile surface.

## Verification

## Correction 1: Safe Malformed-Inventory Error Translation

Independent validation found that malformed-inventory handling exposed raw
provider/client exception text through the public `ContractError.message` for
`OLLAMA_MODEL_PROFILE_INVALID`. A credential-shaped provider exception string
crossed the M1-009 discovery boundary unchanged.

Correction 1 replaces that raw exception text with the fixed provider-neutral
message:

`Ollama model profile discovery received invalid local inventory metadata.`

The correction preserves:

- error code `OLLAMA_MODEL_PROFILE_INVALID`;
- non-retryable malformed-inventory semantics;
- no partial candidate value on failure;
- separate unavailable-provider handling;
- profile shape, status semantics, candidate ordering, duplicate handling, and
  provider-local identity;
- no routing, generation, persistence, scheduler, API, UI, prompt, or memory
  authority.

Validator regression coverage now probes representative token-like,
password-like, API-key-like, authorization-header-like, credential-like, and
secret-like provider exception strings plus a normal non-secret malformed
provider message across public error message, details, JSON-compatible
serialization, result serialization, and repr surfaces. It also verifies
unavailable-provider errors do not leak raw client exception text and that
discovery uses only `list_models`, not generation/chat methods.

Final implementation verification:

| Check | Result |
| --- | --- |
| Lock check | PASS: `uv lock --check` resolved 50 packages. |
| Locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages after installing the task worktree environment. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker Compose config | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 252 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python typing | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 66 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build`. |
| Validator regression before correction | FAIL: `uv run pytest packages/python/curios_ollama/tests/test_task_m1_009_validation_regressions.py -q` failed because credential-shaped provider exception text appeared in `ContractError.message`. |
| Validator regression after correction | PASS: `uv run pytest packages/python/curios_ollama/tests/test_task_m1_009_validation_regressions.py -q` passed 10 tests. |
| Complete M1-009 provider tests | PASS: `uv run pytest packages/python/curios_ollama/tests/test_ollama_provider_boundary.py packages/python/curios_ollama/tests/test_task_m1_009_validation_regressions.py -q` passed 37 tests. |
| Contract/schema/architecture/security | PASS: `uv run pytest tests/contract tests/schema tests/architecture tests/security -q` passed 407 tests with 2 known FastAPI/Starlette warnings. |
| M1-001 through M1-008 regression slice plus M1-009 focused tests | PASS: combined focused package slice passed 239 tests. |
| Package/API/provider tests | PASS: package-local API/core/config/provider/observability/Ollama slice passed 78 tests with 2 known FastAPI/Starlette warnings. |
| Runtime/persistence/policy unit suites | PASS: non-integration slice passed 201 tests with 9 deselected integration tests. |
| Docker-backed serial integrations | PASS: API 6, PostgreSQL provider 1, persistence 2, event/evidence 1, work repository 1, Work DAG repository 1, agent repository 1, agent lifecycle repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: `uv run pytest tests/acceptance -q` passed 8 tests with 2 known FastAPI/Starlette warnings. |
| Full pytest | PASS: `uv run pytest -q` passed 904 tests with 2 known FastAPI/Starlette warnings. |
| Repository whitespace | PASS: `git diff --check` and `git diff --cached --check`. |

Known warning: inherited `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` does
not match this task worktree `.venv`; `uv` ignored it and used the project
environment. The FastAPI/Starlette `TestClient` deprecation warnings are
inherited from the existing test stack. No Docker/PostgreSQL lifecycle failure
occurred during TASK-M1-009 verification.

## Lifecycle State

TASK-M1-009 is `IMPLEMENTED, TESTED`.

Independent validation/freeze is still required before TASK-M1-009 can become
an integrated prerequisite for TASK-M1-010.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-010 implementation, or TASK-M1-011 implementation was
performed.
