---
id: PG-08B-INTEGRATION-EVIDENCE
title: PG-08B Provider Boundary Integration Evidence
lifecycle: TESTED
artifact_type: evidence
authority: integration
tasks:
  - TASK-BOOT-018
  - TASK-BOOT-019
  - TASK-BOOT-020
  - TASK-BOOT-021
---

# PG-08B Provider Boundary Integration Evidence

PG-08B integrated independently implemented provider-boundary commits:

- TASK-BOOT-018: `5d1f6ea572ab350fc7c002e9806b64a2ad659193`
- TASK-BOOT-019: `4b8e1ebf010eca381fab856ccd875018358cc3cf`
- TASK-BOOT-020: `fc8e849f674b65f13e31f086b48b57b9d72e88f3`
- TASK-BOOT-021: `1987ab805845a95fb03346c7a7840b302e682c39`

## Integration

| Subject | Result |
| --- | --- |
| Pre-integration baseline | `main` was at `122c018eff9ed8b4b8baf9b928cde1c6ce6a511b`. |
| TASK-BOOT-018 merge | Merged without conflicts. |
| TASK-BOOT-021 merge | Merged without manual conflicts. |
| TASK-BOOT-020 merge | Conflict in root `pyproject.toml`; resolved by preserving both `curios_config` and `curios_ollama` workspace members. |
| TASK-BOOT-019 merge | Conflicts in status ledger, root `pyproject.toml`, security baseline test, and `uv.lock`. |
| Status reconciliation | TASK-BOOT-018 through TASK-BOOT-021 remain `IMPLEMENTED`/`TESTED`; none are marked `VALIDATED` or `FROZEN`. |
| Later task status | TASK-BOOT-022+ not advanced. |

## Conflict Resolutions

Root workspace metadata preserves all authorized PG-08 Python workspace
members:

- `packages/python/curios_config`
- `packages/python/curios_postgres_provider`
- `packages/python/curios_ollama`
- `packages/python/curios_observability`

The security baseline keeps the topology invariant while allowing exactly the
authorized PG-08 provider-boundary surfaces and the TASK-BOOT-019 Docker-backed
integration test. Deferred top-level service, API, provider-tree, and unrelated
runtime surfaces remain blocked.

`uv.lock` was regenerated with `uv lock` from the reconciled manifests rather
than hand-merged.

## Dependency Audit

| Package | Dependency | Justification |
| --- | --- | --- |
| `curios_config` | `curios-contracts` | Uses `ConfigurationProfile`, `ConfigurationProfileName`, and `Result`. |
| `curios_postgres_provider` | `curios-contracts` | Exposes canonical `ProviderDescriptor`, `Result`, and `ContractError` records. |
| `curios_postgres_provider` | `curios-core` | Implements a core-facing provider catalog boundary requiring `CoreContext`. |
| `curios_postgres_provider` | `sqlalchemy`, `psycopg` | Provider-local PostgreSQL connectivity and readiness implementation. |
| `curios_ollama` | `curios-contracts` | Exposes canonical provider descriptor and translated contract errors. |
| `curios_ollama` | `curios-core` | Implements a core-facing provider catalog boundary requiring `CoreContext`. |
| `curios_observability` | `curios-contracts` | Projects canonical event and observability contracts. |
| `curios_observability` | `opentelemetry-api` | Provider-local telemetry adapter hidden behind Curios telemetry boundary. |

No dependency was removed during integration. No dependency from
`curios_contracts` or `curios_core` to provider implementation packages was
introduced.

## Architecture Review

- Configuration profile semantics remain canonical in `curios_contracts`.
- PostgreSQL and SQLAlchemy objects remain provider-local.
- Ollama native response payloads remain provider-local and ordinary tests use
  deterministic fakes.
- OpenTelemetry remains an implementation provider; Curios trace,
  correlation, event, and observability contracts remain canonical.
- No API, frontend, scheduler, DAG engine, model router, agent runtime,
  persistence repository architecture, policy engine, authority engine, or
  TASK-BOOT-022 implementation was introduced.

## Verification

| Check | Result |
| --- | --- |
| TASK-BOOT-018 provider tests | Passed: 6 tests. |
| TASK-BOOT-019 provider tests | Passed: 6 tests. |
| TASK-BOOT-019 Docker-backed integration test | Passed: 1 test. |
| TASK-BOOT-020 provider tests | Passed: 13 tests. |
| TASK-BOOT-021 telemetry tests | Passed: 4 tests. |
| Compose configuration | Passed. |
| PostgreSQL persistent volume | Present after integration verification. |
| TOML validation | Passed for root and all Python package `pyproject.toml` files. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 110 files already formatted. |
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

PG-08B integration is `TESTED`. TASK-BOOT-018 through TASK-BOOT-021 remain
pending independent PG-08C validation.
