---
id: TASK-BOOT-025-EVIDENCE
title: TASK-BOOT-025 CI Quality Gates Evidence
lifecycle: VALIDATED
artifact_type: task_evidence
authority: implementation
task_id: TASK-BOOT-025
date: 2026-09-22
---

# TASK-BOOT-025 CI Quality Gates Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Work began on branch `task/boot-025-ci-quality-gates` from baseline `27d571fd6e08ab94950054da9741ea78c42dd56e`. |
| 2 | IMPLEMENTED | GitHub Actions quality-gate workflow, narrow security topology transition, and ledger/evidence documentation were added. |
| 3 | TESTED | Required local/static workflow checks and repository verification passed; see verification evidence below. |
| 4 | CORRECTED | After PG-11 validation identified a `.github` topology false negative, security topology tests were strengthened to authorize only `.github/workflows/quality-gates.yml`. |
| 5 | VALIDATED | Independent PG-11 revalidation accepted the corrected TASK-BOOT-025 implementation at commit `1aebc56e89de20ab7cbf6193ac6977c2f73ecfc0`; see `docs/tasks/PG-11-validation-evidence.md`. |
| 6 | FROZEN | The BOOT task ledger records TASK-BOOT-025 as `VALIDATED, FROZEN`. |

TASK-BOOT-025 was not self-declared `VALIDATED` or `FROZEN` by the
implementation agent. Independent PG-11 revalidation made that lifecycle
decision.

## Scope

TASK-BOOT-025 implements PG-11 CI quality gates for the already frozen
BOOT-000 foundations through PG-10.

Implemented surface:

- `.github/workflows/quality-gates.yml`

Supporting governance surface:

- `tests/security/test_security_baseline.py` authorizes the exact CI workflow
  surface and includes `.github/workflows` in tracked secret scanning.
- A corrective security topology check rejects tracked `.github/**` content
  outside `.github/workflows/quality-gates.yml`.
- `docs/program/status-ledger/BOOT-000-task-ledger.md` records
  TASK-BOOT-025 as `IMPLEMENTED, TESTED`.

## Quality Gates Implemented

| Job | Gate Surface |
| --- | --- |
| Python, Backend, Providers, Integration | TOML validation, uv lock check, locked uv sync, LOCAL_DOCKER Compose config, Ruff, Ruff format check, mypy, package-local tests, contract/schema tests, architecture tests, security tests, API integration tests, PostgreSQL provider integration test, and full pytest. |
| Frontend | Node 24 setup, pinned pnpm activation, frozen pnpm install, repository frontend checks, `apps/web` tests, `apps/web` typecheck, and `apps/web` production build. |
| Repository Hygiene | Git diff whitespace check. |

The workflow is configured for `push` and `pull_request` triggers with
read-only repository contents permission.

## Pinned Actions

| Action | Pinned Reference | Verified Release Identity |
| --- | --- | --- |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | `v7.0.1` |
| `actions/setup-python` | `5fda3b95a4ea91299a34e894583c3862153e4b97` | `v7.0.0` |
| `astral-sh/setup-uv` | `c771a70e6277c0a99b617c7a806ffedaca235ff9` | `v9.0.0` |
| `actions/setup-node` | `820762786026740c76f36085b0efc47a31fe5020` | `v7.0.0` |

Pinned action identities were verified during TASK-BOOT-025 implementation.

## CI Strategy

Python/backend verification:

- Root and package TOML manifests are parsed.
- `uv.lock` must match the manifests.
- The full Python workspace syncs with locked dependencies.
- Ruff, Ruff format check, and mypy run before tests.

Provider/API/integration verification:

- Package-local tests cover contracts, core, configuration, PostgreSQL,
  Ollama, telemetry, and API package surfaces.
- Repository contract, schema, architecture, and security tests run as
  separate gate lanes.
- API integration tests run without live Ollama, network, GPU, or model
  download.

PostgreSQL CI strategy:

- The workflow validates TASK-006 LOCAL_DOCKER Compose configuration.
- The PostgreSQL provider integration test is included in the CI test plan and
  relies on the repository's existing non-destructive integration-test behavior.

Ollama strategy:

- Ordinary CI uses deterministic Ollama provider tests and fakeable provider
  boundaries.
- No live Ollama service, GPU, model download, or nondeterministic model output
  is required.

Frontend verification:

- Node 24 is used.
- pnpm is activated through Corepack at the pinned repository version
  `12.5.1`.
- `pnpm install --frozen-lockfile`, `pnpm check`, web tests, typecheck, and
  production build are required.

Diff/config hygiene:

- Docker Compose config is validated.
- Workflow YAML formatting is covered by the repository Prettier check.
- `git diff --check` is included as a repository hygiene job.

## Explicitly Out Of Scope

TASK-BOOT-025 does not implement deployment, CD, release publishing, artifact
upload policy, branch protection administration, TASK-BOOT-026 acceptance
suite, independent verification records, or BOOT freeze status.

No hosted GitHub Actions run is claimed as having executed during this task.
The verification below is local/static workflow verification plus repository
test execution.

## Verification Evidence

| Check | Result |
| --- | --- |
| TOML validation | Passed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed. |
| mypy strict baseline | Passed. |
| Full pytest suite | Passed: 216 tests, 2 expected dependency warnings. |
| PostgreSQL integration | Passed. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed. |
| `pnpm --dir apps/web test` | Passed. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |
| Workflow YAML Prettier check | Passed. |
| `git diff --check` | Passed. |

## Corrective Implementation

Independent PG-11 validation failed because `.github` was allowed as a tracked
top-level path while only `.github/workflows` was included in secret scanning.
That allowed unauthorized tracked `.github` content outside the workflow
surface to evade the topology invariant.

Corrective behavior:

- Authorized `.github` surface is exactly
  `.github/workflows/quality-gates.yml`.
- Tracked `.github` paths are compared against an explicit current-stage
  allowlist.
- Representative unauthorized paths are covered by adversarial detector tests:
  `.github/ISSUE_TEMPLATE/example.md`, `.github/dependabot.yml`,
  `.github/workflows/another-workflow.yml`, and `.github/CODEOWNERS`.
- `.github/workflows` remains included in tracked secret scanning.
- Existing provider, API, web, secret-field, and core-authority protections
  remain intact.

Corrective verification:

| Check | Result |
| --- | --- |
| Security tests | Passed: 25 tests. |
| Architecture tests | Passed: 13 tests. |
| Workflow YAML Prettier check | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed: 124 files already formatted. |
| mypy strict baseline | Passed: no issues found in 39 source files. |
| Full pytest suite | Passed: 221 tests, 2 expected dependency warnings. |
| `git diff --check` | Passed. |

## Scope Compliance

Expected TASK-BOOT-025 paths:

- `.github/workflows/quality-gates.yml`
- `tests/security/test_security_baseline.py`
- `docs/program/status-ledger/BOOT-000-task-ledger.md`
- `docs/tasks/TASK-BOOT-025-evidence.md`

No deployment/CD/release workflow, application/runtime implementation,
TASK-BOOT-026+ implementation, source contract changes, provider runtime
changes, frontend product behavior, database migration, or `1.txt` change was
introduced.

## Final Implementation Status

`TASK-BOOT-025` is `VALIDATED, FROZEN` after independent PG-11 revalidation.
