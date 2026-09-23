---
id: TASK-M0-011-EVIDENCE
title: TASK-M0-011 M0 CI Quality Gate Update Evidence
lifecycle: IMPLEMENTED_TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-011
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-011 Evidence

## Objective

Update the existing frozen GitHub Actions quality-gate workflow so CI executes
the validated M0 verification surface, including the frozen TASK-M0-010
integration tests, while preserving the TASK-BOOT-025 CI security model.

TASK-M0-011 owns CI quality-gate evolution only. It does not implement
deployment, release automation, production runtime behavior, cloud
infrastructure, credentials, post-M0 acceptance semantics, or M1+ scope.

## Starting Baseline

`002ba8932e46caaf63d4d012903a9a5121f72490`

## Implemented Surface

- `.github/workflows/quality-gates.yml`
- `tests/security/test_security_baseline.py`
- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-011-evidence.md`
- `pyproject.toml`
- `uv.lock`

No other GitHub workflow or `.github` configuration was added. No production
source, runtime behavior, API route, web product behavior, deployment surface,
release surface, cloud infrastructure, or credential/secret configuration was
changed. The only dependency change is the root dev/test PyYAML dependency used
by the security test workflow parser.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Scope exact | PASS | Only the existing quality-gates workflow, relevant security workflow audit, M0 ledger, and this evidence changed. |
| BOOT CI preserved | PASS | Existing BOOT gates remain: TOML, uv lock/sync, Compose config, Ruff, Ruff format, mypy, package tests, contract/schema, architecture, security, API integration, PostgreSQL provider integration, BOOT acceptance, full pytest, frontend, and diff hygiene. |
| M0 runtime/persistence/API/web/integration gates | PASS | CI now includes M0 package tests, M0 PostgreSQL integration tests, explicit TASK-M0-010 integration tests, API integration, web tests/typecheck/build, and full pytest. |
| TASK-M0-010 explicit gate | PASS | Added `uv run pytest tests/integration/test_m0_vertical_slice_integration.py -q`. |
| PostgreSQL CI lifecycle | PASS | CI validates LOCAL_DOCKER Compose config and runs Docker-backed PostgreSQL tests serially through existing non-destructive tests. Tests start only `postgres`, wait for readiness, stop cleanly, inspect the named volume, and do not use `down -v`. |
| Deterministic provider boundary | PASS | Provider-inventory integration uses fake provider catalogs; CI does not start live Ollama, download models, require GPU, require external accounts, or add network provider calls. |
| Action security | PASS | No new actions were added. All 6 `uses:` references are pinned to full SHAs, workflow permissions remain `contents: read`, and no secrets or write permissions were introduced. |
| Trigger security | PASS | Triggers remain branch `push` and `pull_request`; no schedule, release, deployment, or unsafe dispatch trigger was added. |
| Failure behavior | PASS | No `continue-on-error`, `|| true`, allow-failure semantics, or broad conditional skips were added. |
| Topology transition | PASS | Authorized GitHub topology remains exactly `.github/workflows/quality-gates.yml`; tests continue rejecting unrelated `.github` paths. |
| Frontend coverage | PASS | `pnpm install --frozen-lockfile`, `pnpm check`, apps/web tests, apps/web typecheck, and apps/web production build remain required. |
| Dependencies | PASS | Added root dev/test-only `PyYAML>=6.0.3` for structural workflow YAML security parsing; no production package imports it. |
| Hosted CI status | NOT RUN | No hosted GitHub Actions execution was performed or claimed. Local/static reproduction was performed. |

## Workflow Changes

The existing `python` job timeout was raised from 30 to 45 minutes to keep the
expanded M0 verification surface auditable without weakening any gate.

Added Python gates:

- `M0 runtime, persistence, and policy package tests`
  - `uv run pytest packages/python/curios_persistence/tests packages/python/curios_policy/tests packages/python/curios_runtime/tests -m "not integration" -q`
- `M0 PostgreSQL integration tests`
  - `uv run pytest packages/python/curios_persistence/tests/test_postgres_persistence_integration.py packages/python/curios_runtime/tests/test_postgres_event_evidence_store_integration.py packages/python/curios_runtime/tests/test_postgres_work_repository_integration.py -q`
- `M0 integration tests`
  - `uv run pytest tests/integration/test_m0_vertical_slice_integration.py -q`

Preserved Python gates:

- TOML validation
- `uv lock --check`
- `uv sync --locked --all-groups --all-packages`
- LOCAL_DOCKER Docker Compose config validation
- Ruff lint
- Ruff format check
- authoritative mypy source scope: `apps/api/src packages/python/*/src`
- package-local BOOT/API/provider tests
- contract/schema tests
- architecture tests
- security tests
- API integration tests
- PostgreSQL provider integration test
- BOOT acceptance tests
- full pytest suite

Preserved frontend gates:

- Node 24 setup
- pinned pnpm activation through Corepack at `pnpm@12.5.1`
- `pnpm install --frozen-lockfile`
- `pnpm check`
- `pnpm --dir apps/web test`
- `pnpm --dir apps/web typecheck`
- `pnpm --dir apps/web build`

Preserved repository hygiene:

- `git diff --check`

## Security Audit

Action references in `.github/workflows/quality-gates.yml`:

| Action | SHA | Release identity |
| --- | --- | --- |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | `v7.0.1` |
| `actions/setup-python` | `5fda3b95a4ea91299a34e894583c3862153e4b97` | `v7.0.0` |
| `astral-sh/setup-uv` | `c771a70e6277c0a99b617c7a806ffedaca235ff9` | `v9.0.0` |
| `actions/setup-node` | `820762786026740c76f36085b0efc47a31fe5020` | `v7.0.0` |

Local audit found 6 total `uses:` references and all were pinned to full
immutable SHAs. `git ls-remote` confirmed each documented release tag resolves
to the pinned SHA above.

The security baseline now includes a workflow audit that verifies:

- every action reference is a full SHA pin;
- workflow permissions are structurally exact: top-level `contents: read`
  only, with no job-level permission overrides;
- only authorized push/pull request triggers are present;
- required BOOT and M0 gates remain present;
- TASK-M0-010 integration runs before BOOT acceptance and full pytest;
- prohibited CI patterns such as deployment, release, unsafe dispatch,
  `continue-on-error`, `|| true`, live Ollama startup, secret access, and
  `down -v` are absent.

## Corrective Permission Enforcement

Independent validation of candidate
`a20a6537e0332d9efaeecb198d696f47a2232c96` failed because the workflow itself
preserved least privilege but the new security regression test did not
structurally enforce the permission invariant.

False negatives reproduced by independent validation:

- adding top-level `id-token` with write access while keeping `contents` read-only;
- adding job-level `contents` with write access.

Corrective behavior added:

- parse the workflow permission blocks structurally instead of checking for the
  substring `contents: read`;
- require the top-level permission model to be exactly `contents: read`;
- reject all job-level permission overrides, including any write permission;
- reject missing top-level permissions, scalar `read-all`, `contents` write
  access, `id-token` write access, `packages` write access, and unexpected
  permission keys.

The workflow YAML did not change during this correction.

Second independent revalidation of corrective candidate
`b51ce3482a40db0610815f7ade312d7c5b117f76` failed because the first corrective
permission detector still depended on exact indentation widths. A YAML-valid
workflow using alternate four-space job indentation could hide a job-level
`contents` write override from the detector.

Second corrective behavior added:

- replaced the indentation-sensitive permission scanner with PyYAML structural
  parsing using `yaml.BaseLoader`;
- confirmed the actual workflow parses with string keys, including the `on`
  trigger key, and with top-level permissions equal to `contents` read access;
- enforce the exact top-level permission mapping semantically;
- inspect every parsed job mapping and reject any job-level `permissions` key
  regardless of job name, key order, comments, indentation, or scalar/mapping
  value;
- added adversarial coverage for top-level cases A-J, job-level cases K-T, and
  valid current workflow case U;
- added formatting variants for two-space job indentation, four-space job
  indentation, deeper valid indentation, comments between job and permissions,
  permissions before or after other job keys, and multiple jobs where only the
  second job declares permissions.

Dependency change: `PyYAML>=6.0.3` was added to the root dev dependency group
and locked as `pyyaml v6.0.3` solely for structural YAML security testing.

Third independent revalidation of corrective candidate
`2816b1c6177fc659787fcead9f57828aaa429fe8` failed because PyYAML
`BaseLoader` parsed ordinary formatting structurally but still silently
overwrote duplicate mapping keys before the security audit. The same parser
also left YAML merge keys as ordinary `<<` entries, allowing merge/alias
patterns to create ambiguous effective permission semantics.

False negatives reproduced by independent revalidation:

- duplicate top-level `permissions` where an unsafe `contents: write` block was
  overwritten by a later allowed `contents: read` block;
- duplicate job names where an earlier job-level permission override was
  overwritten by a later duplicate job mapping;
- merge-key patterns such as `<<: *anchor` that could hide inherited
  permissions from the checker.

Third corrective behavior added:

- introduced a test-only `_QualityGateWorkflowLoader` based on PyYAML
  `BaseLoader`;
- reject duplicate mapping keys at every YAML mapping level before any mapping
  can be overwritten;
- reject YAML merge keys (`<<`) fail-closed anywhere in the workflow;
- reject all anchors and aliases fail-closed because the quality-gates workflow
  does not need YAML indirection;
- keep the already-frozen semantic permission invariant after successful parse:
  top-level permissions must equal `contents: read`, and every job-level
  `permissions` key must be absent;
- added adversarial parser coverage for duplicate cases A-I, merge/anchor cases
  J-M, the previous permission cases A-T, valid workflow case U, formatting
  variants, flow-style mappings, CRLF, and malformed security structures.

## PostgreSQL Strategy

CI continues to use the frozen PostgreSQL 18 `LOCAL_DOCKER` service in
`infrastructure/local/docker/compose.yaml`; no cloud database infrastructure
was added.

The Docker-backed tests are explicit, serial workflow steps. They rely on the
existing frozen test lifecycle:

- validate Compose config;
- start only the `postgres` service;
- wait for readiness through provider/store initialization loops;
- use generated isolated schemas;
- drop only generated schemas;
- stop `postgres` cleanly;
- inspect and preserve the named `curios-local-docker_postgres_data` volume;
- never run `docker compose down -v`.

## Deterministic Provider Strategy

M0 provider-inventory integration uses deterministic fake provider catalogs at
the frozen runtime/API seam. Ordinary CI does not require a live Ollama server,
GPU, downloaded model, nondeterministic model output, external provider account,
cloud infrastructure, or deployment credential.

## Local And Static Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS: 11 Python manifests parsed. |
| `uv lock --check` | PASS: resolved 47 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: checked 44 packages. |
| Docker Compose config | PASS. |
| `actionlint` | NOT AVAILABLE locally; no dependency was added. |
| Ruff | PASS. |
| Ruff format | PASS: 189 files already formatted. |
| Authoritative mypy source scope | PASS: no issues in 53 source files. |
| Package-local Python tests | PASS: 168 passed, 2 known dependency warnings. |
| M0 runtime/persistence/policy package tests | PASS: 128 passed, 4 deselected. |
| Contract/schema tests | PASS: 15 passed. |
| Architecture tests | PASS: 16 passed. |
| Security tests | PASS: 114 passed. |
| Parser adversarial matrices | PASS: 53 targeted cases passed, including duplicate A-I, merge/anchor J-M, previous permission A-T, valid current workflow U, formatting variants, comments between duplicate definitions, and malformed structures. |
| Actual workflow YAML parse | PASS: parsed as a mapping with string `on` key, permissions `contents: read`, jobs `frontend`, `python`, and `repository`, and no permission violations. |
| API integration tests | PASS: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration test | PASS: 1 passed. |
| M0 PostgreSQL integration tests | PASS: 4 passed. |
| TASK-M0-010 integration tests | PASS: 2 passed, 2 known dependency warnings. |
| BOOT acceptance tests | PASS: 6 passed, 2 known dependency warnings. |
| Full pytest | PASS: 437 passed, 2 known dependency warnings. |
| PostgreSQL clean stop/volume preservation | PASS: Compose showed no running `postgres` container and `curios-local-docker_postgres_data` remained present. |
| `pnpm install --frozen-lockfile` | PASS. |
| `pnpm check` | PASS. |
| apps/web tests | PASS: 1 test file, 6 tests. |
| apps/web typecheck | PASS. |
| apps/web production build | PASS: 18 modules transformed. |
| Workflow YAML Prettier check | PASS. |
| `git diff --check` | PASS. |

Known warnings are the existing Starlette/FastAPI `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings.

## Hosted CI Status

Hosted GitHub Actions execution was not run and is not claimed. TASK-M0-011
verification is local/static workflow validation plus local reproduction of the
represented quality gates.

## Lifecycle

TASK-M0-011 is `IMPLEMENTED, TESTED`.

This task does not self-declare `VALIDATED` or `FROZEN`. TASK-M0-012,
TASK-M0-013, and TASK-M0-014 remain blocked until independent validation/freeze
accepts and integrates TASK-M0-011.
