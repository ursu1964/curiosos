---
id: TASK-BOOT-026-EVIDENCE
title: TASK-BOOT-026 BOOT Acceptance Suite Evidence
lifecycle: VALIDATED
artifact_type: task_evidence
authority: implementation
task_id: TASK-BOOT-026
date: 2026-09-22
---

# TASK-BOOT-026 BOOT Acceptance Suite Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Work began on branch `task/boot-026-acceptance-suite` from baseline `c188fe4414de9aef3dcbf8556578fdcef37a8f9e`, matching `main` after TASK-BOOT-025 integration. |
| 2 | IMPLEMENTED | Added the BOOT acceptance suite under `tests/acceptance`, wired it into CI, and narrowly authorized the new acceptance-test topology in the security baseline. |
| 3 | TESTED | Required acceptance and BOOT verification checks passed; see verification evidence below. |
| 4 | VALIDATED | Independent PG-12 validation accepted TASK-BOOT-026 at commit `6263f0eb26a87d6c730d42bbffc1b3f3bde2a220`; see `docs/tasks/PG-12-validation-evidence.md`. |
| 5 | FROZEN | The BOOT task ledger records TASK-BOOT-026 as `VALIDATED, FROZEN`. BOOT closure still requires TASK-BOOT-027 and TASK-BOOT-028. |

## Authoritative Acceptance Matrix

| Criterion | Acceptance Scenario | Cross-Component Failure Detected |
| --- | --- | --- |
| Canonical contracts remain semantic authority across the foundation. | `test_boot_composition_serves_canonical_configuration_and_provider_catalogs_over_api` round-trips API provider payloads back into `ProviderDescriptor` contract objects. | API/provider JSON drift that lower-level provider tests or route tests could miss. |
| Core composition uses provider catalogs without selecting runtime work. | The same scenario composes `CoreServices`, `CompositeProviderCatalog`, `PostgresProvider`, and deterministic `OllamaProviderCatalog`. | Broken core/provider protocol wiring or provider descriptor aggregation. |
| Configuration provider reaches the API readiness boundary. | The same scenario verifies `/health/ready` reports the canonical `LOCAL_DOCKER` profile through FastAPI. | Readiness serialization that omits or mutates frozen configuration semantics. |
| PostgreSQL provider boundary participates without requiring extra live behavior. | The same scenario includes an unconfigured `PostgresProvider` descriptor; `test_postgresql_acceptance_uses_authorized_local_docker_readiness_behavior` verifies live readiness remains delegated to the authorized LOCAL_DOCKER integration test. | PostgreSQL native details leaking out of provider descriptors, destructive Compose behavior, or missing live-readiness gate. |
| Ollama remains deterministic and fakeable. | Happy-path and failure scenarios use fake model clients only. | Accidental live Ollama, network, GPU, model download, or nondeterministic model dependency in acceptance or CI. |
| Canonical provider failures translate through FastAPI. | `test_ollama_provider_failure_remains_deterministic_and_translates_canonically` drives a real Ollama provider-boundary failure through composed core/API HTTP. | Failure-envelope translation gaps between real provider adapters and API HTTP responses. |
| Observability/telemetry remains provider-safe. | `test_observability_and_policy_contracts_survive_provider_boundary_projection` records a canonical `EventEnvelope` with `NoopTelemetryProvider` and checks telemetry attributes. | Telemetry provider projection that drops canonical correlation fields or exposes provider-native objects. |
| Policy `UNKNOWN` remains non-authorizing. | The same scenario round-trips a `PolicyDecision` with all governed effects and `UNKNOWN` outcome. | Security semantics regression where unknown policy becomes allow/deny or authorizes effects. |
| Web bootstrap uses only the frozen API boundary. | API route paths are compared to `apps/web/src/apiBoundary.ts`. | Frontend/API surface drift not visible to isolated web smoke tests. |
| CI quality gates include acceptance and all frozen prerequisite gates. | `test_ci_quality_gates_include_boot_acceptance_without_live_ollama_requirement` verifies the workflow commands and acceptance ordering. | CI omission of TASK-026 or prerequisite gates after local tests pass. |
| Security topology permits only the new acceptance-test path. | `test_acceptance_test_surface_is_narrowly_authorized_by_security_topology` checks tracked acceptance paths and the security baseline allowlist. | Accidental broadening of current-stage topology or unscanned acceptance content. |

## Scope

Implemented surface:

- `tests/acceptance/test_boot_acceptance.py`
- `.github/workflows/quality-gates.yml`
- `tests/security/test_security_baseline.py`
- `pyproject.toml`
- `docs/tasks/TASK-BOOT-026-evidence.md`
- `docs/program/status-ledger/BOOT-000-task-ledger.md`

No production contract, core, provider, API, or web runtime behavior was changed.

## PostgreSQL Acceptance Behavior

TASK-BOOT-026 does not add a second live PostgreSQL test. Acceptance verifies:

- the BOOT composition includes the frozen PostgreSQL provider descriptor boundary;
- CI runs `tests/integration/test_postgres_provider_integration.py`;
- the live test starts only `postgres`, stops it cleanly, avoids `down`, and preserves the named volume;
- readiness remains bounded to the existing non-mutating provider check.

## Ollama Determinism

The acceptance suite uses fake Ollama clients for both success and failure paths.
It does not require live Ollama, GPU, downloaded models, external network model
calls, or nondeterministic output.

## Dependencies

No runtime or test dependency was added.

## Verification Evidence

| Check | Result |
| --- | --- |
| TOML validation | Passed: 8 Python manifests parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed: 37 packages checked. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 127 files already formatted. |
| mypy strict baseline | Passed: no issues found in 39 source files. |
| Package-local Python tests | Passed: 161 tests. |
| Repository contract and schema tests | Passed: 15 tests. |
| Architecture tests | Passed: 13 tests. |
| Security tests | Passed: 25 tests. |
| API integration tests | Passed: 6 tests, 2 expected dependency warnings. |
| PostgreSQL provider integration test | Passed: 1 test; service stopped cleanly and persistent named volume remained present. |
| TASK-BOOT-026 acceptance tests | Passed: 6 tests, 2 expected dependency warnings. |
| Staged security plus acceptance topology check | Passed: 31 tests, 2 expected dependency warnings. |
| Full pytest suite | Passed: 227 tests, 2 expected dependency warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |
| Workflow YAML Prettier check | Passed. |
| `git diff --check` | Passed. |

## Explicitly Out Of Scope

TASK-BOOT-026 does not implement scheduler, DAG/router, agent runtime, policy or
authority engine, new persistence architecture, new API endpoints, product UI,
deployment, CD, release behavior, or later BOOT tasks.

## Final Implementation Status

`TASK-BOOT-026` is `IMPLEMENTED, TESTED`.

Independent PG-12 validation passed. TASK-BOOT-026 is `VALIDATED, FROZEN`.
