---
id: TASK-BOOT-017-EVIDENCE
title: TASK-BOOT-017 Core Package Foundation Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-017
---

# TASK-BOOT-017 Core Package Foundation Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-017-core-foundation` at required base `ad9901090f57a76249989fa882b8774d14f79875`; TASK-BOOT-017 implementation began. |
| 2 | IMPLEMENTED | Minimal `curios_core` foundation, package-local tests, documentation, and workspace dependency metadata were added for TASK-BOOT-017 scope. |
| 3 | TESTED | Deterministic checks were run after implementation; see check evidence below. |

## Implementation Summary

- Core package documentation: `packages/python/curios_core/README.md`.
- Core context: `packages/python/curios_core/src/curios_core/context.py`.
- Core application boundary: `packages/python/curios_core/src/curios_core/application.py`.
- Provider-port namespace: `packages/python/curios_core/src/curios_core/ports/`.
- Package exports and typing marker: `__init__.py` and `py.typed`.
- Package-local tests: `packages/python/curios_core/tests/test_core_foundation.py`.

## Core Concepts Introduced

- `CoreContext`: a core-owned composition object using frozen
  `ObservabilityContext` and optional `Authority`.
- `ProviderCatalog`: a read-only provider descriptor port returning frozen
  `Result[tuple[ProviderDescriptor, ...]]`.
- `CoreServices`: a minimal service boundary that delegates descriptor listing
  to the `ProviderCatalog` port when an outer implementation is wired.

## Dependency Direction

- `curios_core` declares `curios-contracts` as its only runtime dependency.
- `curios_core` imports frozen contract types from `curios_contracts`.
- No provider, framework, SDK, persistence, telemetry, HTTP, model, or database
  dependency was added.

## Explicitly Deferred

Schedulers, DAG engines, capability resolution, model routing, agent execution,
policy engines, event buses, persistence repositories, Ollama calls,
PostgreSQL repositories, FastAPI, telemetry exporters, cognitive graphs,
memory, patterns, learning, workflows, and application generation remain
unimplemented.

## Check Evidence

| Check | Result |
| --- | --- |
| Path, branch, and base verification | Passed: `/home/user/projects/curiosos-wt-017`, branch `task/boot-017-core-foundation`, base `ad9901090f57a76249989fa882b8774d14f79875`. |
| Root and package TOML parse | Passed: root and all Python package `pyproject.toml` files parsed with `tomllib`. |
| Initial `uv lock --check` | Correctly reported the lockfile needed an update after adding the workspace dependency. |
| `uv lock` | Passed: refreshed workspace dependency metadata for `curios-core`. |
| `uv lock --check` after lock update | Passed. |
| `uv sync --frozen` | Passed. |
| Import check | Passed: `CoreServices().list_provider_descriptors(CoreContext())` returned `Result.success(())`. |
| Ruff check | Passed after Ruff fixed one import-order issue. |
| Ruff format check | Passed: 79 files already formatted. |
| mypy strict baseline | Passed: `uv run --package curios-core mypy packages/python`. |
| Package-local core tests | Passed: `uv run --package curios-core pytest packages/python/curios_core/tests -q` reported 9 passed. |
| Existing contract tests | Passed: `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` reported 114 passed. |
| Dependency/import scan | Passed: core source import roots are `__future__`, `curios_contracts`, `curios_core`, `dataclasses`, and `typing`; no provider/framework imports found. |
| Duplicate-contract scan | Passed: core source declares only `CoreContext`, `CoreServices`, and `ProviderCatalog`; no canonical contract classes duplicated. |
| Deferred behavior scan | Passed: no scheduler, DAG engine, capability resolver, model router, agent executor, policy engine, event bus, repository, provider implementation, API, telemetry exporter, memory, pattern, workflow, or application generator implementation found in core. |
| Diff whitespace | Passed: `git diff --check`. |
| Scope review | Passed: changes are limited to `packages/python/curios_core/**`, `packages/python/curios_core/pyproject.toml`, `uv.lock`, and TASK-BOOT-017 evidence/status. |
