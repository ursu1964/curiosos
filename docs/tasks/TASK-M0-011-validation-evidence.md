---
id: TASK-M0-011-VALIDATION-EVIDENCE
title: TASK-M0-011 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-011
milestone_id: M0
date: 2026-09-23
---

# TASK-M0-011 Independent Validation Evidence

## Decision

TASK-M0-011 REVALIDATION: PASS

Validated candidate:

`c915614273479b71e124a902cff580599743f5d7`

Starting baseline:

`002ba8932e46caaf63d4d012903a9a5121f72490`

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Scope exact | PASS | Full diff from baseline changes only `.github/workflows/quality-gates.yml`, M0 status/evidence, security regression tests, and root dev/test PyYAML lock state. No contracts, core, persistence, policy, runtime, provider, API, or web implementation semantics changed. |
| TASK-M0-012+ absent | PASS | No acceptance-suite implementation, M0 verification/freeze implementation, deployment, release, publishing, cloud, or post-M0 behavior was added. TASK-M0-012 through TASK-M0-014 remain blocked on this branch. |
| Actual workflow | PASS | Checked-in workflow has exact top-level `name`, `on`, `permissions`, `jobs`; triggers are push branches `["**"]` and `pull_request`; permissions are `contents: read`; jobs are exactly `python`, `frontend`, `repository`. |
| BOOT gates preserved | PASS | TOML, uv lock/sync, Compose config, Ruff, Ruff format, mypy, package tests, contract/schema, architecture, security, API integration, PostgreSQL provider integration, BOOT acceptance, full pytest, frontend gates, and diff hygiene remain blocking workflow steps. |
| M0 gates added | PASS | Workflow explicitly runs M0 runtime/persistence/policy package tests, M0 PostgreSQL integration tests, and `uv run pytest tests/integration/test_m0_vertical_slice_integration.py -q`. |
| Workflow security model | PASS | Actions are exact allowlisted full-SHA references; no write permissions, secrets, env/defaults, services, containers, deployment trigger, release trigger, or arbitrary executable workflow surface is authorized. |
| YAML parser | PASS | Test-only PyYAML loader preserves `on` as a string key, rejects duplicate keys recursively, rejects merge keys, rejects anchors/aliases, and fails closed on malformed structures before semantic audit. |
| Exact permissions | PASS | The audit requires top-level `{"contents": "read"}` and no job-level `permissions` key. Write, extra, missing, null/scalar, duplicate, merge, alias, and job-level permission variants reject. |
| Exact triggers | PASS | The audit requires exact push/pull_request trigger shape. Dispatch, workflow_run, schedule, pull_request_target, release, missing trigger, branch-filter drift, malformed, duplicate, merge, and alias trigger variants reject. |
| Exact execution surface | PASS | The audit requires exact top-level keys, job set, job key/value contracts, ordered step sets, action identities/SHAs/inputs, and normalized run scripts. Extra jobs, steps, actions, env, defaults, services, containers, strategy, needs, runners, and timeouts reject. |
| Failure behavior | PASS | Required gates cannot add `if`, `continue-on-error`, `set +e`, `|| true`, `; true`, `exit 0`, shell wrappers, dead command text, duplicate safe/unsafe gates, or env/defaults-based behavior changes without failing security tests. |
| GitHub topology | PASS | Tracked `.github` surface remains exactly `.github/workflows/quality-gates.yml`; adversarial topology detector rejects second workflow, dependabot, CODEOWNERS, custom action, and issue template paths. |
| PostgreSQL strategy | PASS | Workflow validates frozen LOCAL_DOCKER Compose config and runs Docker-backed tests serially; tests use PostgreSQL 18, readiness loops, isolated schemas, clean stop, named volume preservation, and no `down -v`. |
| Deterministic providers | PASS | CI requires no live Ollama, GPU, model download, external provider account, or external model call. M0 provider inventory tests use deterministic fake provider seams. |
| Frontend coverage | PASS | `pnpm install --frozen-lockfile`, `pnpm check`, `pnpm --dir apps/web test`, `typecheck`, and production build remain blocking and exact. |
| PyYAML dependency | PASS | `PyYAML>=6.0.3` is root dev/test-only, locked as `pyyaml 6.0.3`, imported only by security tests, and required for robust YAML structural audit. |
| Hosted CI | NOT RUN | Frozen authority does not require hosted GitHub Actions execution before validation; no hosted run is claimed. |

## Adversarial Review

Independent probes and committed tests rejected representative mutations for:

- top-level `env`, `defaults`, `concurrency`, `run-name`, and unknown keys;
- `contents: write`, `id-token: write`, extra permissions, missing/null/scalar
  permissions, and job-level read/write permissions;
- duplicate keys, alternate indentation, merge keys, anchors, aliases, and
  malformed structures;
- extra triggers including `repository_dispatch`, `workflow_run`, `schedule`,
  `workflow_dispatch`, `pull_request_target`, and `release`;
- extra deploy/publish/release/exfiltrate/arbitrary jobs, including jobs with
  only an otherwise authorized action;
- extra run/action steps, duplicated authorized steps, missing/reordered steps,
  and renamed duplicate steps;
- unknown full-SHA actions, changed action identities, changed action SHAs,
  floating tags, extra action inputs, and authorized actions in wrong locations;
- `set +e`, `|| true`, `; true`, `exit 0`, curl/network, printenv, git push,
  test path drift, pytest deselection, command wrappers, and dead expected
  command text;
- workflow/job/step `PYTEST_ADDOPTS`, `PYTHONPATH`, `PATH`, `UV_*`,
  `working-directory`, `container`, `services`, `strategy`, and `needs`.

No material unauthorized executable GitHub Actions behavior was found that can
be introduced while preserving the final structural audit.

## Mechanical Verification

| Check | Result |
| --- | --- |
| Targeted workflow adversarial tests | PASS: 70 passed. |
| Security tests | PASS: 187 passed. |
| Architecture tests | PASS: 16 passed. |
| Actual workflow structural audit | PASS: parsed with string `on`, exact top-level keys, exact jobs, and no security violations. |
| Workflow Prettier | PASS. |
| `actionlint` | NOT AVAILABLE locally. |
| TOML validation | PASS: 11 manifests parsed. |
| `uv lock --check` | PASS: resolved 47 packages. |
| `uv sync --locked --all-groups --all-packages` | PASS: resolved 47 packages; checked 44 packages. |
| Docker Compose config | PASS. |
| Ruff | PASS. |
| Ruff format | PASS: 189 files already formatted. |
| Authoritative mypy source scope | PASS: no issues in 53 source files. |
| Package-local Python tests | PASS: 168 passed, 2 known dependency warnings. |
| M0 runtime/persistence/policy package tests | PASS: 128 passed, 4 deselected. |
| Contract/schema tests | PASS: 15 passed. |
| API integration tests | PASS: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration | PASS: 1 passed. |
| M0 PostgreSQL integrations | PASS: 4 passed. |
| BOOT acceptance | PASS: 6 passed, 2 known dependency warnings. |
| TASK-M0-010 integration | PASS: 2 passed, 2 known dependency warnings. |
| Full pytest | PASS: 533 passed, 2 known dependency warnings. |
| `pnpm install --frozen-lockfile` | PASS. |
| `pnpm check` | PASS. |
| Web tests | PASS: 1 file, 6 tests. |
| Web typecheck | PASS. |
| Web production build | PASS: 18 modules transformed. |
| `git diff --check` | PASS. |

Known warnings are the existing Starlette/FastAPI `TestClient` `httpx`
deprecation and anyio `BlockingPortal` alias deprecation warnings.

## Lifecycle And Downstream Readiness

TASK-M0-011 is `VALIDATED, FROZEN`.

TASK-M0-012 remains `BLOCKED` on this branch. Under the frozen M0 DAG,
TASK-M0-012 becomes ready only after the complete TASK-M0-011
validation/freeze history is integrated into `main`.

No merge, push, TASK-M0-012 implementation, deployment, release, publishing, or
cloud behavior was performed.

## Files Modified

- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-011-evidence.md`
- `docs/tasks/TASK-M0-011-validation-evidence.md`
