---
id: TASK-BOOT-021-EVIDENCE
title: TASK-BOOT-021 Telemetry Provider Boundary Evidence
lifecycle: VALIDATED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-021
---

# TASK-BOOT-021 Telemetry Provider Boundary Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-021-telemetry-provider` at required base `122c018eff9ed8b4b8baf9b928cde1c6ce6a511b`; TASK-BOOT-021 implementation began. |
| 2 | IMPLEMENTED | Minimal telemetry provider boundary was added inside the existing `curios_observability` package. |
| 3 | TESTED | Deterministic repository checks were run after implementation; see check evidence below. |
| 4 | VALIDATED | Independent PG-08C validation accepted the telemetry provider boundary. |
| 5 | FROZEN | The BOOT task ledger records TASK-BOOT-021 as `VALIDATED, FROZEN`. |

## Implementation Summary

- `curios_observability.telemetry` defines the Curios-facing
  `TelemetryProvider` protocol, `NoopTelemetryProvider`, and canonical
  event/context attribute projection helpers.
- `curios_observability._opentelemetry` implements the OpenTelemetry-current-span
  adapter as an implementation detail behind the Curios provider boundary.
- `curios_observability` now depends on frozen `curios-contracts` and
  `opentelemetry-api`; no OpenTelemetry dependency was added to
  `curios_contracts` or `curios_core`.
- Repository pytest source paths now include `curios_core` and
  `curios_observability` so repository-level tests can import the workspace
  packages they inspect.

## Boundary Notes

- Curios `TraceId`, `CorrelationId`, `ObservabilityContext`, and
  `EventEnvelope` remain canonical.
- OpenTelemetry receives scalar Curios attributes and is not used as semantic
  authority.
- Event payloads are not promoted into telemetry attributes by the provider
  boundary.
- No API, frontend, orchestration, agent runtime, provider routing, PostgreSQL,
  Ollama, or configuration-provider behavior was implemented.

## Check Evidence

| Check | Result |
| --- | --- |
| TASK-BOOT-021 package tests | Passed: `uv run --package curios-observability pytest packages/python/curios_observability/tests -q` reported 4 passed. |
| Root and package TOML parse | Passed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .` reported 94 files already formatted. |
| mypy strict baseline | Passed: `uv run mypy packages/python` reported no issues. |
| Package-local contracts/core/observability tests | Passed: `uv run pytest packages/python/curios_contracts/tests packages/python/curios_core/tests packages/python/curios_observability/tests -q` reported 127 passed. |
| Repository contract/schema tests | Passed: `uv run pytest tests/contract tests/schema -q` reported 15 passed. |
| Repository architecture tests | Passed: `uv run pytest tests/architecture -q` reported 11 passed. |
| Repository security tests | Passed: `uv run pytest tests/security -q` reported 20 passed. |
| Full pytest suite | Passed: `uv run pytest -q` reported 173 passed. |
| Diff whitespace | Passed: `git diff --check`. |

## Lifecycle Limit

`TASK-BOOT-021` is `VALIDATED, FROZEN` after independent PG-08C validation.
