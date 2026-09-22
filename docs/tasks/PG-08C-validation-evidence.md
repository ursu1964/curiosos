---
id: PG-08C-VALIDATION-EVIDENCE
title: PG-08C Provider Boundary Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: verification_evidence
authority: independent_verification
tasks:
  - TASK-BOOT-018
  - TASK-BOOT-019
  - TASK-BOOT-020
  - TASK-BOOT-021
---

# PG-08C Provider Boundary Independent Validation Evidence

Independent PG-08C validation was performed against integrated baseline
`e8028e0f682243373037e5c1ef0ec0162510575c`.

## Scope

PG-08C validates the integrated provider-boundary foundation:

- TASK-BOOT-018 configuration provider;
- TASK-BOOT-019 PostgreSQL provider;
- TASK-BOOT-020 Ollama provider;
- TASK-BOOT-021 telemetry provider.

This validation does not start TASK-BOOT-022.

## Acceptance Summary

| Task | Result | Basis |
| --- | --- | --- |
| TASK-BOOT-018 | PASS | `ConfigurationProfile` remains canonical; `LOCAL_DOCKER` remains the only M0 profile; no settings framework, secret resolver, policy engine, or provider-native semantic authority was introduced. |
| TASK-BOOT-019 | PASS | PostgreSQL and SQLAlchemy remain provider-local; the provider implements the core `ProviderCatalog` boundary, translates failures into bounded `ContractError` records, and readiness checks are non-mutating and persistence-safe. |
| TASK-BOOT-020 | PASS | Ollama native payloads remain inside `curios_ollama`; ordinary tests use deterministic fakes and require no live Ollama, network, GPU, or downloaded model. |
| TASK-BOOT-021 | PASS | Telemetry lives in the existing `curios_observability` package; OpenTelemetry remains provider-local and canonical Curios observability/event contracts remain authoritative. |

## Dependency Validation

| Package | Dependency | Validation |
| --- | --- | --- |
| `curios_config` | `curios-contracts` | REQUIRED: uses `ConfigurationProfile`, `ConfigurationProfileName`, and `Result`. |
| `curios_postgres_provider` | `curios-contracts` | REQUIRED: exposes `ProviderDescriptor`, `Result`, and `ContractError` at the boundary. |
| `curios_postgres_provider` | `curios-core` | REQUIRED: implements the existing core provider catalog boundary using `CoreContext`. |
| `curios_postgres_provider` | `sqlalchemy`, `psycopg` | REQUIRED: provider-local PostgreSQL connectivity and readiness check. |
| `curios_ollama` | `curios-contracts` | REQUIRED: exposes `ProviderDescriptor`, `Result`, and `ContractError`. |
| `curios_ollama` | `curios-core` | REQUIRED: implements the existing core provider catalog boundary using `CoreContext`. |
| `curios_observability` | `curios-contracts` | REQUIRED: projects canonical `EventEnvelope` and `ObservabilityContext`. |
| `curios_observability` | `opentelemetry-api` | REQUIRED: provider-local OpenTelemetry adapter. |

No unused or architecturally invalid dependency was identified. Neither
`curios_contracts` nor `curios_core` acquired outward provider dependencies.

## Security and Architecture

- The reconciled TASK-BOOT-016 security baseline permits exactly the authorized
  PG-08 package roots and the TASK-BOOT-019 integration test.
- Deferred `apps`, `services`, top-level `providers`, `curios_postgres`, and
  `curios_telemetry` surfaces remain blocked.
- Secret scanning includes the new PG-08 source surfaces.
- `curios_contracts` remains framework/provider/runtime independent.
- `curios_core` remains inward-facing and does not import provider
  implementations.
- No provider package depends on another PG-08 provider package.
- No duplicate generic reference abstraction, provider-native canonical type,
  policy engine, authority engine, model router, agent runtime, API, frontend,
  migration system, or TASK-BOOT-022 implementation was introduced.

## Verification

| Check | Result |
| --- | --- |
| TASK-BOOT-018 tests | Passed: 6 tests. |
| TASK-BOOT-019 provider tests | Passed: 6 tests. |
| TASK-BOOT-019 Docker integration test | Passed: 1 test. |
| TASK-BOOT-020 tests | Passed: 13 tests. |
| TASK-BOOT-021 tests | Passed: 4 tests. |
| PostgreSQL live readiness | Passed: container reached healthy state, `pg_isready` accepted connections, service stopped cleanly, and persistent volume remained present. |
| TOML validation | Passed for root and all Python package manifests. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 111 files already formatted. |
| mypy strict baseline | Passed: no issues found in 58 source files. |
| `curios_contracts` tests | Passed: 114 tests. |
| `curios_core` tests | Passed: 9 tests. |
| Repository contract tests | Passed: 10 tests. |
| Repository schema tests | Passed: 5 tests. |
| Architecture tests | Passed: 11 tests. |
| Security tests | Passed: 20 tests. |
| Full pytest suite | Passed: 199 tests. |
| Diff whitespace | Passed. |

## Final Status

PG-08C validation passes. TASK-BOOT-018 through TASK-BOOT-021 are
`VALIDATED, FROZEN`; PG-08 is closed.
