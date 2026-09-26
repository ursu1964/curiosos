---
id: TASK-M1-009-VALIDATION-EVIDENCE
title: TASK-M1-009 Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-009
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-009 Validation Evidence

## Scope

Validated implementation:
`1cf85e795109344b3f4d80342c6e79c8ef9b61d9`

Correction 1:
`62963022d9a271a1ac7ce0dc51afafcddb1dde8c`

Published baseline:
`198ac27df489602abcb0c1efe06b23c6811d1171`

TASK-M1-009 adds local Ollama model/profile discovery records. Validation
reconstructed the contract from the frozen M1 task pack, M1 implementation DAG,
M1 status ledger, M0 provider contracts, BOOT result/error contracts, existing
Ollama provider boundary, architecture guardrails, and security/no-secret
requirements.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | TASK-M1-001 is validated/frozen and integrated in the published baseline; the M1 DAG authorizes TASK-M1-009 independently after TASK-M1-001. |
| Authorized ownership | PASS | The implementation extends the existing `curios_ollama` provider/profile boundary only. No new package, dependency, lockfile, schema, migration, API, UI, persistence, runtime scheduler, or routing surface is introduced. |
| Profile contract | PASS | `LocalModelProfile` is immutable, provider-referenced, schema-versioned, JSON-reconstructable, and limited to provider-local non-secret metadata. |
| Status semantics | PASS | `ModelProfileStatus` and `MODEL_PROFILE_STATUS_VALUES` expose only the authorized `available` status and do not encode ranking or quality. |
| Discovery semantics | PASS | `OllamaModelProfileDiscovery` calls only the fakeable `OllamaModelClient.list_models` inventory boundary and maps canonical `OllamaModelSummary` values to sorted profile candidates. |
| Unavailable provider | PASS | `OSError` returns `OLLAMA_MODEL_PROFILE_DISCOVERY_UNAVAILABLE` with dependency category and retryable true; `TimeoutError` uses the same code with timeout category and retryable true. Neither exposes raw client text. |
| Invalid inventory | PASS | Malformed inventory returns `OLLAMA_MODEL_PROFILE_INVALID`, retryable false, no value, no partial profiles, and the fixed provider-neutral message accepted by Correction 1. |
| Bounded safe-error/no-secret boundary | PASS | Secret-shaped and ordinary provider exception strings are absent from public `ContractError` message/details, error JSON, result JSON, and canonical repr surfaces. |
| Metadata boundary | PASS | Profiles project only allowlisted normalized fields: provider family, modified timestamp, size, and digest. Secret-shaped keys/values, provider objects, callables, and arbitrary provider dictionaries are rejected or ignored. |
| Determinism and duplicates | PASS | Empty inventory succeeds with an empty tuple. Equivalent reversed inventories serialize identically after sorting by model name. Duplicate local model identity fails boundedly with no partial success value. |
| Fakeability/no live model | PASS | Unit and validation tests use deterministic fake clients and require no Ollama server, installed model, download, localhost service, generation, chat, or embeddings. |
| M1-010 boundary | PASS | The implementation reports candidates/status only and contains no routing decision record, route ranking, route rationale, selected route, no-model route, routing persistence, or model choice for execution. |
| Authority boundary | PASS | Actual imports and calls provide no WorkItem/DAG mutation, capability resolution, agent lifecycle, executor invocation, ExecutionRecord mutation, persistence, DB, scheduler, retry/cancellation, policy, API/UI, prompt/memory, cloud catalog, or model generation authority. |
| Guard changes | PASS | Security changes are additive and bounded to TASK-M1-009 evidence, validation evidence, and the existing `curios_ollama` provider/profile package. Existing M1 restrictions remain active. |

## Delta Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `packages/python/curios_ollama/src/curios_ollama/profiles.py` | REQUIRED | Owns the authorized local model/profile records and fakeable discovery adapter. |
| `packages/python/curios_ollama/src/curios_ollama/__init__.py` | JUSTIFIED SUPPORT | Exports the authorized profile/discovery symbols from the provider package. |
| `packages/python/curios_ollama/tests/test_ollama_provider_boundary.py` | REQUIRED | Covers implementation behavior and provider/profile boundary constraints. |
| `packages/python/curios_ollama/tests/test_task_m1_009_validation_regressions.py` | REQUIRED VALIDATION SUPPORT | Preserves the safe-error correction regression and no-generation fakeability proof. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Adds bounded authorization for the exact M1-009 surface. |
| `docs/tasks/TASK-M1-009-evidence.md` | REQUIRED | Implementation and Correction 1 evidence. |
| `docs/tasks/TASK-M1-009-validation-evidence.md` | REQUIRED | Independent validation/freeze evidence. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Advances TASK-M1-009 from `IMPLEMENTED, TESTED` to `VALIDATED, FROZEN`. |

No changed file was classified as out of scope. The older
`curios_ollama.catalog` provider-descriptor error translation predates
TASK-M1-009, is outside the profile-discovery surface, and was not modified.

## Independent Re-Validation

Validation rechecked Correction 1 by injecting malformed provider inventory
errors carrying token-like, password-like, API-key-like, authorization-like,
credential-like, secret-like, and ordinary malformed-provider text. All public
result/error surfaces used the fixed safe invalid-inventory message and did not
include raw provider text.

Additional probes confirmed:

- unavailable-provider and timeout failures stay distinct from invalid
  inventory and remain retryable;
- malformed model summaries fail as invalid inventory without partial
  candidates;
- successful discovery is sorted and stable across reversed provider order;
- empty inventory is success with no candidates;
- duplicate local model identity fails boundedly;
- suspicious metadata does not cross into successful profiles;
- discovery invokes only `list_models`, never generation, chat, routing, or
  provider execution methods.

## Verification

Pre-validation-record checks:

| Check | Result |
| --- | --- |
| Correction history | PASS: `198ac27d -> 1cf85e79 -> 62963022` ancestry verified. |
| Correction scope | PASS: Correction 1 changed only profile error translation, validation regression coverage, and implementation evidence. |
| M1-009 validation regressions | PASS: 10 tests. |
| M1-009 provider/profile tests | PASS: 27 tests. |
| Independent re-validation probe | PASS. |

Post-record complete verification:

| Check | Result |
| --- | --- |
| Dependency lock check | PASS: `uv lock --check` resolved 50 packages. |
| Python locked sync | PASS: `uv sync --locked --all-groups --all-packages` checked 47 packages. |
| Frontend locked install | PASS: `pnpm install --frozen-lockfile`. |
| Docker compose configuration | PASS: `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet`. |
| Python formatting | PASS: `uv run ruff format --check .` reported 253 files already formatted. |
| Python lint | PASS: `uv run ruff check .`. |
| Python typing | PASS: `uv run mypy apps/api/src packages/python/*/src` checked 66 source files. |
| Frontend checks | PASS: `pnpm check`. |
| Web tests | PASS: `pnpm --dir apps/web test` passed 6 tests. |
| Web typecheck | PASS: `pnpm --dir apps/web typecheck`. |
| Web build | PASS: `pnpm --dir apps/web build` transformed 18 modules. |
| Contract/schema/architecture/security | PASS: `uv run pytest tests/contract tests/schema tests/architecture tests/security -q` passed 407 tests with 2 known FastAPI/Starlette warnings. |
| M1-001 through M1-009 regression slice | PASS: focused package slice passed 239 tests. |
| Package/API/provider tests | PASS: package-local API/core/config/provider/observability/Ollama slice passed 78 tests with 2 known FastAPI/Starlette warnings. |
| Runtime/persistence/policy unit suites | PASS: non-integration slice passed 201 tests with 9 deselected integration tests. |
| Docker-backed serial integrations | PASS: API 6, PostgreSQL provider 1, persistence 2, event/evidence 1, work repository 1, Work DAG repository 1, agent repository 1, agent lifecycle repository 1, and M0 vertical slice 2. |
| Acceptance tests | PASS: `uv run pytest tests/acceptance -q` passed 8 tests with 2 known FastAPI/Starlette warnings. |
| Full pytest suite | PASS: `uv run pytest -q` passed 904 tests with 2 known FastAPI/Starlette warnings. |
| Repository diff checks | PASS: `git diff --check` and `git diff --cached --check`. |

Post-evidence edit verification reran doc-sensitive checks:

- `uv run ruff format --check .`;
- `uv run ruff check .`;
- `uv run pytest tests/security -q`;
- `uv run pytest -q`;
- `git diff --check`;
- `git diff --cached --check`.

Known warnings:

- `VIRTUAL_ENV=/home/user/projects/curiosos/.venv` does not match the task
  worktree `.venv`; `uv` ignored it.
- FastAPI/Starlette `TestClient` deprecation warnings remain inherited from the
  existing test stack.

No Docker/PostgreSQL lifecycle instability occurred during re-validation.

## Decision

TASK-M1-009 is `VALIDATED, FROZEN`.

TASK-M1-010 remains blocked until this TASK-M1-009 validation/freeze commit is
integrated into the main M1 baseline alongside the already integrated
TASK-M1-008 baseline. TASK-M1-011 remains blocked by its documented downstream
prerequisites.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-010 implementation, or TASK-M1-011 implementation was
performed.
