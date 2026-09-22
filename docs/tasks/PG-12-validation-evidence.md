---
id: PG-12-VALIDATION-EVIDENCE
title: PG-12 BOOT Acceptance Suite Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: verification_evidence
authority: independent_verification
tasks:
  - TASK-BOOT-026
date: 2026-09-22
---

# PG-12 BOOT Acceptance Suite Independent Validation Evidence

Independent PG-12 validation was performed against TASK-BOOT-026 commit
`6263f0eb26a87d6c730d42bbffc1b3f3bde2a220`.

## Scope

PG-12 validates the BOOT acceptance suite only. This validation does not
integrate the branch into `main`, start TASK-BOOT-027, start TASK-BOOT-028, or
begin post-BOOT work.

## Acceptance Summary

| Criterion | Result | Basis |
| --- | --- | --- |
| TASK-BOOT-026 scope | PASS | The diff from baseline `c188fe4414de9aef3dcbf8556578fdcef37a8f9e` is limited to `tests/acceptance/test_boot_acceptance.py`, CI acceptance invocation, security topology authorization, pytest marker metadata, ledger, and evidence. No production contract, core, provider, API, or web runtime implementation changed. |
| Acceptance-level value | PASS | Acceptance tests exercise cross-boundary behavior across API composition, canonical contracts, providers, observability projection, policy `UNKNOWN`, frontend route boundary, CI gate inclusion, and security topology. |
| Canonical contracts and core | PASS | Provider API payloads round-trip through `ProviderDescriptor`; `ObjectReference`, `Result`, `ContractError`, `CoreContext`, and `CoreServices` remain frozen. Framework/provider-native objects did not become canonical. |
| Configuration | PASS | `/health/ready` exposes the canonical `LOCAL_DOCKER` profile through the existing configuration provider boundary. No secret resolver or policy authority was introduced. |
| PostgreSQL | PASS | Acceptance uses the frozen `PostgresProvider` descriptor boundary and delegates live readiness to `tests/integration/test_postgres_provider_integration.py`; the integration test passed, stopped the service cleanly, and preserved the named volume. |
| Ollama | PASS | Acceptance uses deterministic fake Ollama clients for success and failure. No live Ollama service, network, GPU, model download, model router, generation, or agent runtime is required. |
| Observability and telemetry | PASS | `EventEnvelope`, `ObservabilityContext`, `TraceId`, `CorrelationId`, and `ObjectReference` fields survive telemetry projection through `NoopTelemetryProvider`; OpenTelemetry types remain non-canonical. |
| Policy `UNKNOWN` | PASS | `PolicyDecisionOutcome.UNKNOWN` serializes/deserializes distinctly and remains non-authorizing through `is_authorizing is False`. No runtime policy engine is required or introduced. |
| API | PASS | Acceptance covers `/health/ready`, `/providers`, provider descriptor serialization, composed provider behavior, and canonical failure to HTTP translation without new endpoints or provider-native leakage. |
| Web | PASS | The web bootstrap remains bootstrap-only and references only frozen API routes. It does not import Python internals or define new canonical semantics. |
| CI | PASS | `.github/workflows/quality-gates.yml` invokes `uv run pytest tests/acceptance -q` before full pytest while preserving existing TASK-025 gates, least-privilege permissions, and pinned actions. Hosted GitHub Actions execution is not claimed. |
| Security topology | PASS | The only newly authorized acceptance surface is `tests/acceptance/test_boot_acceptance.py`; arbitrary additional acceptance files remain blocked by tracked-path topology checks, and the acceptance path is included in secret scanning. |
| Frozen prerequisite integrity | PASS | No frozen prerequisite production implementation was modified. The `pyproject.toml` change only declares the pytest `acceptance` marker and adds no dependency. |

## Acceptance-Test Quality Review

The acceptance scenarios are not merely duplicates of lower-level tests:

- API composition is built with the real FastAPI application factory, real
  composite provider catalog, `PostgresProvider`, and deterministic
  `OllamaProviderCatalog`, then HTTP responses are parsed back into canonical
  contracts.
- Ollama failure is driven through the provider boundary and API translation
  path, proving bounded canonical `Result`/`ContractError` behavior.
- Observability and policy checks combine canonical event, reference,
  telemetry projection, and `UNKNOWN` authorization semantics in one boundary
  scenario.
- CI and security topology checks provide static acceptance coverage for
  repository gates that lower-level package tests cannot prove.

Adversarial review found no material false negative within TASK-BOOT-026
scope. Static source/config assertions are used only for static acceptance
subjects such as CI command inclusion, authorized route names, and tracked
security topology.

## Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed: 8 Python manifests parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed: 37 packages checked. |
| Docker Compose config | Passed. |
| Workflow YAML Prettier check | Passed. |
| `git diff --check` | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 127 files already formatted. |
| mypy strict baseline | Passed: no issues found in 39 source files. |
| Package-local Python tests | Passed: 161 tests. |
| Repository contract and schema tests | Passed: 15 tests. |
| Architecture tests | Passed: 13 tests. |
| Security tests | Passed: 25 tests. |
| API integration tests | Passed: 6 tests, 2 dependency deprecation warnings. |
| PostgreSQL provider integration test | Passed: 1 test; service stopped cleanly and persistent named volume `curios-local-docker_postgres_data` remained present. |
| TASK-BOOT-026 acceptance tests | Passed: 6 tests, 2 dependency deprecation warnings. |
| Full pytest suite | Passed: 227 tests, 2 dependency deprecation warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |

The two warnings are existing FastAPI/Starlette/httpx and anyio dependency
deprecation warnings. They are technical debt to monitor, not PG-12 validation
defects.

## PostgreSQL Live/Persistence Result

The authorized TASK-019 PostgreSQL integration test passed from the PG-12
candidate worktree. After the test, `docker compose ps postgres` showed no
running service entry, and Docker volume inspection confirmed the persistent
named volume `curios-local-docker_postgres_data` remains present. No
destructive volume operation was performed.

## BOOT Closure Analysis

TASK-BOOT-026 passing does not complete BOOT-000. The authoritative DAG still
requires:

1. `TASK-BOOT-027` / PG-13: independent verification record.
2. `TASK-BOOT-028` / PG-14: BOOT freeze/status ledger update.

The exact next permitted execution unit after TASK-BOOT-026 is integrated is
`TASK-BOOT-027`. There is no additional readiness gate documented between
TASK-BOOT-026 validation and TASK-BOOT-027, but this validation/freeze evidence
must be committed and the TASK-BOOT-026 branch must be integrated into `main`
before downstream work proceeds from the accepted baseline.

## Final Status

PG-12 validation passes. TASK-BOOT-026 is `VALIDATED, FROZEN`; PG-12 is closed
after this evidence is committed.
