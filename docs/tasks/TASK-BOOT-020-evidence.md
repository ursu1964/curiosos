---
id: TASK-BOOT-020-EVIDENCE
title: TASK-BOOT-020 Ollama Provider Boundary Evidence
lifecycle: VALIDATED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-020
---

# TASK-BOOT-020 Ollama Provider Boundary Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-020-ollama-provider` at required base `122c018eff9ed8b4b8baf9b928cde1c6ce6a511b`; TASK-BOOT-020 implementation began. |
| 2 | IMPLEMENTED | Minimal downstream `curios_ollama` provider boundary, deterministic fake-client tests, and TASK-016 topology transition were added for TASK-BOOT-020 scope. |
| 3 | TESTED | Required deterministic checks were run after implementation; see check evidence below. |
| 4 | VALIDATED | Independent PG-08C validation accepted the Ollama provider boundary. |
| 5 | FROZEN | The BOOT task ledger records TASK-BOOT-020 as `VALIDATED, FROZEN`. |

## Requirements Reconstructed

- Authoritative BOOT artifacts define TASK-BOOT-020 as `Ollama provider boundary with deterministic tests`, owned in WS-07/PG-08 with dependencies on TASK-BOOT-011, TASK-BOOT-013, and TASK-BOOT-014.
- Curios contracts remain canonical; provider-native objects must not become contract or core authority.
- `curios_contracts` and `curios_core` must not depend on Ollama/provider SDKs or provider implementations.
- Ordinary tests and full pytest must not require live Ollama, GPU, network access, or downloaded models.
- Provider behavior must be testable through deterministic fakes/stubs at the provider boundary.
- Model routing, agent runtime, orchestration, API/frontend, policy engine, persistence, telemetry, PostgreSQL, configuration-provider, and later task behavior remain deferred.

## Implementation Summary

- Provider package: `packages/python/curios_ollama`.
- Provider catalog adapter: `OllamaProviderCatalog` implements the existing
  `ProviderCatalog` port and returns frozen `Result[tuple[ProviderDescriptor,
  ...]]` contract values.
- Client boundary: `OllamaModelClient` is a small protocol for deterministic
  fakes/stubs; `OllamaHttpClient` is a stdlib-only `/api/tags` adapter for later
  composition.
- Tests: `packages/python/curios_ollama/tests/test_ollama_provider_boundary.py`.
- TASK-016 topology protection was changed only to allow the authorized
  `packages/python/curios_ollama` package and to security-scan its source.

## Adapter Boundary

- Ollama-native JSON is parsed inside `curios_ollama.client` and normalized into
  adapter-owned `OllamaModelSummary` values.
- Curios-owned `ProviderDescriptor`, `Result`, and `ContractError` remain the
  cross-boundary authority.
- `curios_contracts` and `curios_core` do not import or depend on Ollama,
  provider SDKs, or `curios_ollama`.
- The adapter does not select models, route work, generate text, download
  models, run agents, authorize effects, persist state, expose APIs, or export
  telemetry.

## Dependency Evidence

- Added workspace package dependency metadata for `curios-ollama`.
- Runtime dependencies are only `curios-contracts` and `curios-core`.
- No Ollama SDK, HTTP client package, model framework, router, database,
  telemetry, API, or frontend dependency was added.

## Check Evidence

| Check | Result |
| --- | --- |
| Root and package TOML parse | Passed: 5 `pyproject.toml` files parsed with `tomllib`. |
| `uv lock --check` | Passed after the TASK-020 workspace package lock update. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .` reported 97 files already formatted. |
| mypy strict baseline | Passed: `uv run mypy packages/python` reported no issues in 49 source files. |
| TASK-020 provider tests | Passed: `uv run pytest packages/python/curios_ollama/tests -q` reported 13 passed. |
| Package-local contract tests | Passed: `uv run pytest packages/python/curios_contracts/tests -q` reported 114 passed. |
| Package-local core tests | Passed: `uv run pytest packages/python/curios_core/tests -q` reported 9 passed. |
| Repository contract tests | Passed: `uv run pytest tests/contract -q` reported 10 passed. |
| Repository schema tests | Passed: `uv run pytest tests/schema -q` reported 5 passed. |
| Repository architecture tests | Passed: `uv run pytest tests/architecture -q` reported 11 passed. |
| Repository security tests | Passed: `uv run pytest tests/security -q` reported 20 passed. |
| Full pytest suite | Passed: `uv run pytest -q` reported 182 passed. |
| Diff whitespace | Passed: `git diff --check`. |

## Scope Review

- No canonical contract or core authority was added for Ollama-native objects.
- No model router, agent runtime, orchestration, API/frontend, policy engine,
  persistence implementation, telemetry provider, PostgreSQL provider, or
  configuration provider was implemented.
- Ordinary tests use deterministic fakes/stubs and require no live Ollama
  server, network access, GPU, or downloaded model.

`TASK-BOOT-020` is `VALIDATED, FROZEN` after independent PG-08C validation.
