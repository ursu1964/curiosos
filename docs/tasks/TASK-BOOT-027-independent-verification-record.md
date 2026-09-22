---
id: TASK-BOOT-027-INDEPENDENT-VERIFICATION-RECORD
title: TASK-BOOT-027 Independent BOOT Verification Record
lifecycle: VALIDATED
artifact_type: verification_record
authority: independent_verification
task_id: TASK-BOOT-027
parallel_group: PG-13
date: 2026-09-22
---

# TASK-BOOT-027 Independent BOOT Verification Record

Independent PG-13 verification was performed against integrated BOOT baseline
`a01d678f343b8eb7245359e035cf3722d0ceb9dd`.

## Scope

TASK-BOOT-027 records independent verification of the complete BOOT baseline
through TASK-BOOT-026. This task does not modify production implementation,
start TASK-BOOT-028, perform the BOOT freeze/status update, push to a remote, or
begin post-BOOT work.

## Verification Matrix

| Area | Result | Evidence |
| --- | --- | --- |
| Lifecycle completeness | PASS | TASK-BOOT-003 through TASK-BOOT-026 are all recorded `VALIDATED, FROZEN` in the BOOT task ledger. TASK-BOOT-027 is now recorded `VALIDATED, FROZEN`; TASK-BOOT-028 remains pending. |
| History and integration | PASS | Required implementation, correction, validation, and integration commits through TASK-BOOT-026 are ancestors of the verified baseline. No required prior BOOT implementation was found only on an unmerged branch. |
| Canonical architecture | PASS | `curios_contracts` remains framework/provider/runtime independent; `curios_core` depends inward on contracts and does not import provider/framework runtime; providers remain outer; FastAPI remains an outer composition layer; web remains an outer interface. |
| Security baseline | PASS | Security tests preserve exact current-stage topology, secret scanning, secret-value/reference rules, core authority boundary, policy `UNKNOWN` semantics, exact `.github` authorization, and API/web/provider/integration/acceptance surface controls. Deferred post-BOOT surfaces remain absent. |
| Provider foundations | PASS | Configuration preserves canonical `ConfigurationProfile` and `LOCAL_DOCKER`; PostgreSQL provider keeps SQLAlchemy/psycopg local and readiness non-mutating; Ollama remains deterministic/fakeable; telemetry keeps OpenTelemetry implementation-local. |
| Application and interface foundations | PASS | FastAPI exposes the frozen outer composition endpoints and canonical error translation; API integration coverage is deterministic; web bootstrap remains route-boundary-only and imports no backend/provider internals. |
| CI foundation | PASS | The quality-gate workflow has authorized triggers, read-only permissions, full-SHA action pins verified against release tags, Python/provider/API/PostgreSQL/frontend/acceptance gates, no live Ollama requirement, and diff hygiene. Hosted GitHub Actions execution is not claimed. |
| Acceptance suite | PASS | TASK-BOOT-026 acceptance tests provide cross-boundary coverage for composition, canonical contracts, provider failures, observability, policy `UNKNOWN`, web route boundary, CI inclusion, and security topology. |
| Mechanical verification | PASS | Complete BOOT verification suite passed locally; see results below. |
| Repository hygiene | PASS | No untracked non-ignored files remained in the verification worktree before evidence creation. Generated caches, `.venv`, `node_modules`, and build outputs are ignored. |

## Lifecycle Audit

All TASK-BOOT-003 through TASK-BOOT-026 ledger entries were inspected and are
recorded as `VALIDATED, FROZEN`.

TASK-BOOT-027 is a verification-record task. The repository lifecycle vocabulary
uses `VALIDATED, FROZEN`, so TASK-BOOT-027 is recorded with that status after
successful independent verification.

No ledger contradiction was identified. `BOOT-VERIFY-PG-READINESS-001` remains
recorded as verified by corrective evidence, including PostgreSQL health,
readiness, clean stop, and persistent named-volume preservation.

## History and Integration Audit

The following representative task commits were confirmed as ancestors of the
verified baseline:

- TASK-BOOT-003: `ee69e11e6a00a774ebf388a4fe91f05eea7e67f9`
- TASK-BOOT-004: `0ae55c9f6b3ce7320d6a700eb8b026c3966cf1df`
- TASK-BOOT-006: `72edf0bd0114ccd074a3404e0a1588b81629066c`
- TASK-BOOT-009: `fccfbe35c337f7c1c7107e10fc6e8f221eb74df0`
- TASK-BOOT-013: `6679224e6684a8b7be885a6685020308ff0313e3`
- TASK-BOOT-016 correction: `93f7c6ffabeaca4b7ce24ff4e18746e11e672eb6`
- TASK-BOOT-022: `fff9156475dbfb792e8908fcabda91922fe36650`
- TASK-BOOT-025 validation: `1a1fcf9`
- TASK-BOOT-026 validation: `958d02e`

Prior task worktrees may still exist locally, but their required commits are in
the verified ancestry. Worktree retirement is not a BOOT validation condition.

## Architecture Verification

Verified dependency direction:

```text
curios_contracts
  <- curios_core
  <- provider implementations / observability
  <- FastAPI application
  <- web/interface
```

Allowed outer dependencies appear only in their authorized layers:

- SQLAlchemy/psycopg are local to `curios_postgres_provider`.
- OpenTelemetry is local to `curios_observability`.
- Ollama-native concerns are local to `curios_ollama`.
- FastAPI is local to `apps/api`.
- React/Vite are local to `apps/web`.

`ObjectReference(kind, ref_id)` remains the canonical generic reference
abstraction. No `Reference(ref_type, ref_id)` or `CausationId` replacement was
identified.

## Security Verification

The final topology contains only authorized BOOT surfaces:

- `.github/workflows/quality-gates.yml`
- `apps/api`
- `apps/web`
- authorized Python packages
- authorized TypeScript contracts package
- authorized contract/schema/architecture/security/integration/acceptance tests
- `infrastructure/local/docker`
- Build Pack documentation and tooling

No top-level `services/` or `providers/` surface exists. Security tests passed
and continue to enforce:

- repository secret scanning over governed source/config/documentation surfaces;
- reference-not-value secret-field rules;
- `CoreContext`/`CoreServices` authority boundaries;
- exact `.github` workflow authorization;
- exact authorized API, web, provider, integration, and acceptance surfaces;
- policy `UNKNOWN` remains distinct from `DENY` and non-authorizing.

## Provider Verification

Configuration:

- `ConfigurationProfileName.LOCAL_DOCKER` remains the canonical local profile.
- Configuration provider code does not become security or policy authority.

PostgreSQL:

- SQLAlchemy and psycopg remain provider-local implementation details.
- Docker-backed integration test passed.
- PostgreSQL service stopped cleanly after verification.
- Persistent named volume `curios-local-docker_postgres_data` remained present.
- No destructive volume operation was performed.

Ollama:

- Deterministic tests use fakeable provider boundaries.
- Ordinary tests require no live Ollama, network, GPU, or downloaded model.

Observability:

- `ObservabilityContext`, `EventEnvelope`, `TraceId`, `CorrelationId`, and
  `ObjectReference` remain canonical Curios contracts.
- OpenTelemetry remains an implementation detail of the observability provider.

## Application, Web, and CI Verification

FastAPI:

- `/health/live`, `/health/ready`, and `/providers` remain the frozen outer API
  surface.
- HTTP status/error behavior remains an outer-boundary translation of canonical
  `Result` and `ContractError` semantics.

Web:

- `apps/web` remains bootstrap-only.
- It references the frozen API boundary and imports no Python implementation or
  provider-native objects.

CI:

- Workflow triggers are `push` and `pull_request`.
- Permissions are `contents: read`.
- Actions are pinned to full SHAs and verified against release tags:
  `actions/checkout@v7.0.1`,
  `actions/setup-python@v7.0.0`,
  `astral-sh/setup-uv@v9.0.0`, and
  `actions/setup-node@v7.0.0`.
- Python, PostgreSQL integration, deterministic Ollama, frontend, acceptance,
  and repository hygiene gates are present.
- Hosted GitHub Actions execution has not been claimed as evidence.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed: 8 Python manifests parsed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed: 37 packages installed in the isolated verification worktree. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 128 files already formatted. |
| mypy strict baseline | Passed: no issues found in 39 source files. |
| Package-local Python tests | Passed: 161 tests. |
| Repository contract and schema tests | Passed: 15 tests. |
| Architecture tests | Passed: 13 tests. |
| Security tests | Passed: 25 tests. |
| API integration tests | Passed: 6 tests, 2 dependency deprecation warnings. |
| PostgreSQL provider integration test | Passed: 1 test; service stopped cleanly and persistent named volume remained present. |
| BOOT acceptance tests | Passed: 6 tests, 2 dependency deprecation warnings. |
| Full pytest suite | Passed: 227 tests, 2 dependency deprecation warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |
| Workflow YAML Prettier check | Passed. |
| `git diff --check` | Passed. |

The two warnings are existing FastAPI/Starlette/httpx and anyio dependency
deprecation warnings. They are not BOOT verification blockers.

## Repository Hygiene

Before creating this verification record, the verification worktree had no
tracked modifications and no untracked non-ignored files. Ignored generated
surfaces included `.venv`, `node_modules`, build outputs, and test/tool caches.

The historical untracked `1.txt` exists in the primary repository only. It is
not present in this verification worktree and was not modified.

## Decision

TASK-BOOT-027 VERIFICATION: PASS

The integrated BOOT baseline through TASK-BOOT-026 is independently verified.
No unresolved BOOT blocker was found.

## Next DAG Unit

The authoritative DAG identifies `TASK-BOOT-028` / PG-14 as the next and final
BOOT implementation unit. TASK-BOOT-028 records the BOOT freeze/status ledger
update after this independent verification record is committed and integrated.

TASK-BOOT-028 was not started during TASK-BOOT-027.
