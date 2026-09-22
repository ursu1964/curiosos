---
id: PG-11-VALIDATION-EVIDENCE
title: PG-11 CI Quality Gates Independent Revalidation Evidence
lifecycle: VALIDATED
artifact_type: verification_evidence
authority: independent_verification
tasks:
  - TASK-BOOT-025
---

# PG-11 CI Quality Gates Independent Revalidation Evidence

Independent PG-11 revalidation was performed against corrected TASK-BOOT-025
commit `1aebc56e89de20ab7cbf6193ac6977c2f73ecfc0`.

## Scope

PG-11 validates the TASK-BOOT-025 CI quality-gate foundation after the
corrective CI topology enforcement commit.

This validation does not start TASK-BOOT-026.

## Acceptance Summary

| Criterion | Result | Basis |
| --- | --- | --- |
| TASK-BOOT-025 scope | PASS | The implementation adds CI quality gates, security topology checks, and evidence only. No deployment, release, publishing, production environment, product/runtime semantics, or TASK-BOOT-026+ surface was introduced. |
| GitHub Actions implementation | PASS | `.github/workflows/quality-gates.yml` is the single authorized GitHub Actions workflow surface. GitHub Actions remains engineering tooling, not Curios semantic authority. |
| Workflow triggers | PASS | Workflow runs on pull requests and pushes to branches; no scheduled, deployment, or release trigger exists. |
| Permissions | PASS | Workflow-level permissions are `contents: read`; no write, deployment, package, or secret permission is requested. |
| Action pinning | PASS | Every `uses:` entry is pinned to a full commit SHA and independently matched to the documented release tag. |
| Python/backend gates | PASS | CI invokes TOML validation, uv lock check, locked sync, Compose config validation, Ruff, Ruff format, mypy, package tests, contract/schema tests, architecture tests, security tests, API integration tests, PostgreSQL integration, and full pytest. |
| PostgreSQL CI strategy | PASS | The authorized TASK-019 integration test starts only the LOCAL_DOCKER PostgreSQL service, waits for readiness, stops it cleanly, and preserves the named volume. |
| Ollama determinism | PASS | CI requires no live Ollama service, GPU, model download, or nondeterministic model output. |
| Frontend gates | PASS | CI uses Node 24, pinned pnpm activation, frozen pnpm install, root frontend check, web tests, web typecheck, and web production build. |
| Diff hygiene | PASS | The workflow includes `git diff --check`; local reproduction left no tracked or untracked generated artifacts. |
| Previous `.github` topology defect | PASS | The only authorized tracked `.github` path is `.github/workflows/quality-gates.yml`; representative unauthorized paths are rejected by the topology detector. |
| Hosted GitHub Actions execution | NOT APPLICABLE | Authoritative TASK-BOOT-025 verification is "CI syntax/dry validation where possible"; no frozen artifact requires a hosted run before validation. Hosted execution has not been claimed. |

## Previous Defect Resolution

Previous PG-11 validation failed because `.github` was allowed as a tracked
top-level path while topology enforcement did not restrict tracked descendants.

The corrected security baseline now:

- defines `AUTHORIZED_GITHUB_PATHS` as exactly
  `.github/workflows/quality-gates.yml`;
- collects tracked `.github/**` paths structurally from `git ls-files`;
- fails the topology test for any tracked `.github` path outside the allowlist;
- keeps `.github/workflows` in tracked secret scanning;
- preserves existing API, web, provider, secret-field, and core-authority
  protections.

Independent adversarial inspection verified that the following paths are
rejected:

- `.github/ISSUE_TEMPLATE/example.md`
- `.github/dependabot.yml`
- `.github/CODEOWNERS`
- `.github/workflows/another-workflow.yml`
- `.github/actions/example/action.yml`

No alternate tracked `.github` path can pass the current topology check within
the frozen TASK-BOOT-025 scope.

## Action SHA Audit

| Action | Pinned SHA | Verified Release Identity | Validation |
| --- | --- | --- | --- |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | `v7.0.1` | `git ls-remote` confirmed the tag resolves to this SHA. |
| `actions/setup-python` | `5fda3b95a4ea91299a34e894583c3862153e4b97` | `v7.0.0` | `git ls-remote` confirmed the tag resolves to this SHA. |
| `astral-sh/setup-uv` | `c771a70e6277c0a99b617c7a806ffedaca235ff9` | `v9.0.0` | `git ls-remote` confirmed the tag resolves to this SHA. |
| `actions/setup-node` | `820762786026740c76f36085b0efc47a31fe5020` | `v7.0.0` | `git ls-remote` confirmed the tag resolves to this SHA. |

## Static Workflow Validation

- Workflow YAML was parsed/formatted by Prettier successfully.
- Required workflow commands and referenced repository paths were inspected.
- Job definitions have no `needs` graph inconsistency.
- The PostgreSQL path relies on the existing TASK-019 integration test rather
  than a separate GitHub Actions service container.
- No hosted GitHub Actions run was performed or claimed.
- `actionlint` was not available locally; no new dependency was added for this
  validation.

## Local Reproduction

| Check | Result |
| --- | --- |
| TOML validation | Passed: 8 Python manifests parsed. |
| Docker Compose config | Passed. |
| Workflow YAML Prettier check | Passed. |
| Static workflow command/path inspection | Passed. |
| Action SHA/tag audit | Passed. |
| `.github` adversarial topology inspection | Passed: only `.github/workflows/quality-gates.yml` is authorized/tracked. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed: 37 packages checked. |
| Ruff check | Passed. |
| Ruff format check | Passed: 124 files already formatted. |
| mypy strict baseline | Passed: no issues found in 39 source files. |
| Package-local Python tests | Passed: 161 tests. |
| Repository contract and schema tests | Passed: 15 tests. |
| Architecture tests | Passed: 13 tests. |
| Security tests | Passed: 25 tests. |
| API integration tests | Passed: 6 tests, 2 expected dependency warnings. |
| PostgreSQL provider integration test | Passed: 1 test; service stopped cleanly and persistent named volume remained present. |
| Full pytest suite | Passed: 221 tests, 2 expected dependency warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |
| `git diff --check` | Passed. |

## Hosted CI Acceptance Decision

Hosted GitHub Actions execution required before TASK-BOOT-025 validation:
`NO`.

Authoritative basis:

- `docs/tasks/BOOT-000-task-pack.md` defines TASK-BOOT-025 verification as
  "CI syntax/dry validation where possible".
- BOOT-000J states GitHub Actions is the initial implementation assumption and
  that CI enforces deterministic quality gates, but it does not require hosted
  execution before TASK-BOOT-025 validation.
- GitHub branch protection and administrative repository settings remain
  separate governed actions.

## Final Status

PG-11 revalidation passes. TASK-BOOT-025 is `VALIDATED, FROZEN`; PG-11 is
closed.
