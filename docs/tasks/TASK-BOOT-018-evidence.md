---
id: TASK-BOOT-018-EVIDENCE
title: TASK-BOOT-018 Configuration Provider Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-018
---

# TASK-BOOT-018 Configuration Provider Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-018-config-provider` at required base `122c018eff9ed8b4b8baf9b928cde1c6ce6a511b`; TASK-BOOT-018 implementation began. |
| 2 | IMPLEMENTED | Minimal `curios_config` provider boundary, package-local tests, workspace metadata, and security-transition checks were added for TASK-BOOT-018 scope. |
| 3 | TESTED | Required deterministic checks were run after implementation; see check evidence below. |

## Implementation Summary

- Configuration package: `packages/python/curios_config/`.
- Provider boundary: `ConfigurationProvider`.
- Provider result alias: `ConfigurationProfileResult`.
- Deterministic M0 implementation: `StaticConfigurationProvider`.
- LOCAL_DOCKER helpers: `local_docker_configuration_profile` and `local_docker_configuration_provider`.
- Tests: `packages/python/curios_config/tests/test_configuration_provider.py`.
- Security transition: TASK-BOOT-016 PG-08 absence guard now permits only the authorized `curios_config` surface.

## Boundary Semantics

- `ConfigurationProfile` remains the canonical configuration semantic contract.
- `LOCAL_DOCKER` remains the only M0 Curios environment profile.
- The provider returns `Result[ConfigurationProfile]` and does not introduce a settings object as semantic authority.
- No environment loading, secret resolution, IAM, policy evaluation, API, frontend, orchestration, persistence, Ollama, PostgreSQL, or telemetry behavior is implemented.
- `curios_config` depends only on `curios-contracts`.

## Check Evidence

| Check | Result |
| --- | --- |
| Path, branch, and base verification | Passed: `/home/user/projects/curiosos-wt-018`, branch `task/boot-018-config-provider`, base `122c018eff9ed8b4b8baf9b928cde1c6ce6a511b`. |
| Root and package TOML parse | Passed: root and all Python package `pyproject.toml` files parsed with `tomllib`. |
| Initial `uv lock --check` | Correctly reported the lockfile needed an update after adding the `curios_config` workspace member. |
| `uv lock` | Passed: added `curios-config v0.0.0` to `uv.lock`. |
| `uv lock --check` after lock update | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .` reported 95 files already formatted. |
| mypy strict baseline | Passed: `uv run mypy packages/python` reported no issues in 48 source files. |
| Package-local configuration tests | Passed: `uv run pytest packages/python/curios_config/tests -q` reported 6 passed. |
| Package-local contract tests | Passed: `uv run pytest packages/python/curios_contracts/tests -q` reported 114 passed. |
| Package-local core tests | Passed: `uv run pytest packages/python/curios_core/tests -q` reported 9 passed. |
| Repository contract/schema/architecture/security tests | Passed: `uv run pytest tests/contract tests/schema tests/architecture tests/security -q` reported 46 passed. |
| Full pytest suite | Passed: `uv run pytest -q` reported 175 passed. |
| Diff whitespace | Passed: `git diff --check` and `git diff --cached --check`. |

## Final Status

`TASK-BOOT-018` is `TESTED`. This task does not self-declare `VALIDATED` or `FROZEN`.
