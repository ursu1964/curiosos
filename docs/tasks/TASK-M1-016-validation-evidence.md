---
id: TASK-M1-016-VALIDATION-EVIDENCE
title: TASK-M1-016 Independent Validation Evidence
task_id: TASK-M1-016
status: VALIDATED / FROZEN
artifact_type: validation_evidence
date: 2026-09-27
---

# TASK-M1-016 Independent Validation Evidence

## Scope

Independent validation covered TASK-M1-016 as a CI-enforcement task. No
production source behavior was modified. The implementation under validation
was `be0e8a573fea48f3e95c18129c2789122525b3f0` on branch
`task/m1-016-ci-quality-gate-update`.

Published baseline:
`22314d9ec2a73a5e137abf2ea20438568c6c2bee`

## Delta Review

Changed implementation files were limited to:

- `.github/workflows/quality-gates.yml` - REQUIRED
- `tests/security/test_security_baseline.py` - REQUIRED
- `docs/tasks/TASK-M1-016-evidence.md` - REQUIRED
- `docs/program/status-ledger/M1-status-ledger.md` - REQUIRED

No production source, schema, migration, dependency, lockfile, API, frontend,
provider/model, release, deployment, or workflow permission expansion was
introduced.

Production diff audit:

```text
git diff 22314d9ec2a73a5e137abf2ea20438568c6c2bee..be0e8a573fea48f3e95c18129c2789122525b3f0 -- apps packages infrastructure
```

Result: no production source delta.

## Acceptance Mapping

| Requirement | Validation Result |
| --- | --- |
| Preserve BOOT/M0 gates | PASS: baseline Python, Frontend, and Repository Hygiene jobs remain present with their existing commands; only three M1 Python steps were added. |
| Add M1 package/API gate | PASS: exact command runs M1 API plus contracts, cognitive, DAG, capability, and runtime non-integration tests. |
| Add M1 PostgreSQL gate | PASS: exact command runs Work DAG, agent repository, agent lifecycle, and routing repository PostgreSQL tests. |
| Add VS-M1-001..006 gate | PASS: exact command discovers six M1 vertical-slice tests and passes with no skips. |
| Hard failure propagation | PASS: required gate steps have no `continue-on-error`, `if`, `|| true`, `set +e`, `exit 0`, advisory matrix, or skip wrapper. |
| Reachability | PASS: workflow triggers remain push-all-branches and pull-request; required jobs have no `needs`, job `if`, matrix, container, defaults, or unreachable condition. |
| Least privilege | PASS: workflow permissions remain exactly `contents: read`; no secrets, releases, deployments, environments, or write scopes were added. |
| Action pinning | PASS: all existing actions remain pinned to full immutable SHAs; no action was added or upgraded. |
| No-live-model | PASS: workflow and tests require no Ollama service/model, generation, chat, embeddings, cloud provider, credentials, or external model network. |
| M1-016/M1-017 boundary | PASS: M1-016 wires existing acceptance command only; it does not add M1 acceptance tests or evidence owned by TASK-M1-017. |

## Gate Preservation Matrix

| Gate | Baseline | Proposed | Result |
| --- | --- | --- | --- |
| TOML manifest validation | Present | Present, unchanged | Preserved |
| `uv lock --check` | Present | Present, unchanged | Preserved |
| locked Python sync | Present | Present, unchanged | Preserved |
| Docker Compose config | Present | Present, unchanged | Preserved |
| Ruff lint/format | Present | Present, unchanged | Preserved |
| mypy | Present | Present, unchanged | Preserved |
| package-local Python tests | Present | Present, unchanged | Preserved |
| M0 runtime/persistence/policy package tests | Present | Present, unchanged | Preserved |
| M1 package/API tests | Absent | Present | Strengthened |
| contract/schema tests | Present | Present, unchanged | Preserved |
| architecture tests | Present | Present, unchanged | Preserved |
| security tests | Present | Present, unchanged | Preserved |
| API integration tests | Present | Present, unchanged | Preserved |
| PostgreSQL provider integration | Present | Present, unchanged | Preserved |
| M0 PostgreSQL integration | Present | Present, unchanged | Preserved |
| M1 PostgreSQL integration | Absent | Present | Strengthened |
| M0 vertical slice | Present | Present, unchanged | Preserved |
| M1 vertical slices | Absent as named gate | Present | Strengthened |
| existing acceptance | Present | Present, unchanged | Preserved |
| full pytest | Present | Present, unchanged | Preserved |
| frontend install/check/test/type/build | Present | Present, unchanged | Preserved |
| repository diff whitespace | Present | Present, unchanged | Preserved |

## Deselection Audit

The exact M1 package/API command passed with `618 passed, 9 deselected`.
The nine deselected tests are all `integration`-marked tests outside that
non-integration gate's ownership:

- six PostgreSQL repository tests;
- three M1-007 lifecycle/PostgreSQL validation tests.

Required integration coverage is not hidden by this deselection. The workflow
also runs explicit M1 PostgreSQL integration, explicit VS-M1 integration, and
full pytest gates.

## Bypass And Failure-Propagation Audit

Existing and validation-time adversarial checks rejected mutations equivalent
to:

- removing M1 package/API, M1 PostgreSQL, or M1 vertical-slice gates;
- dropping runtime/package coverage from the M1 package/API gate;
- adding `continue-on-error`;
- adding `if: false` or branch-only reachability to a required M1 gate;
- appending `|| true`;
- changing the VS-M1 path;
- adding `-m "not integration"` or `--ignore=tests/integration` to the VS-M1 gate;
- changing an M1 PostgreSQL test path;
- removing the security gate.

The workflow security model remains structural: expected top-level keys, jobs,
job keys, step count, step names, commands, action SHAs, permissions, and
triggers are exact.

## PostgreSQL Service Result

CI continues to use the repository-authorized local Docker Compose PostgreSQL
boundary. The compose file includes `postgres:18`, deterministic local
credentials from `.env.example`, a `pg_isready` healthcheck, and no cloud
database dependency. DB-backed workflow commands are sequential steps in the
single Python job, avoiding the known local shared-service overlap.

During validation, one accidental concurrent local run of the M1 PostgreSQL
gate and VS-M1 gate reproduced the known lifecycle failure:
`connection to server at "127.0.0.1", port 5432 failed: server closed the
connection unexpectedly`. The affected VS-M1 gate passed when rerun serially.
A later PostgreSQL provider readiness transient also passed on isolated rerun.
All DB-backed groups passed in the final serial rerun.

## Local Parity And Verification

Exact introduced CI commands were run locally:

| Gate | Result |
| --- | --- |
| M1 package/API gate | PASS, 618 passed, 9 deselected |
| M1 PostgreSQL gate | PASS, 4 passed |
| VS-M1-001..006 gate | PASS, 6 passed |

Complete validation verification:

| Check | Result |
| --- | --- |
| `uv lock --check` | PASS, 50 packages resolved |
| `uv sync --locked --all-groups --all-packages` | PASS, 47 packages checked |
| `pnpm install --frozen-lockfile` | PASS |
| Docker Compose config | PASS |
| `ruff format --check .` | PASS, 281 files already formatted |
| `ruff check .` | PASS |
| `mypy apps/api/src packages/python/*/src` | PASS, 70 source files |
| `pnpm check` | PASS |
| Web tests | PASS, 26 passed |
| Web typecheck | PASS |
| Web build | PASS |
| Contract/schema | PASS, 16 passed |
| Architecture | PASS, 36 passed |
| Security | PASS, 360 passed |
| API suite | PASS, 183 passed |
| Package/provider/runtime/persistence non-integration suites | PASS, 470 passed, 10 deselected |
| Docker-backed serial API integration | PASS, 6 passed |
| Docker-backed serial PostgreSQL provider | PASS after isolated rerun, 1 passed |
| Docker-backed serial M0 PostgreSQL repositories | PASS, 4 passed |
| Docker-backed serial M0 vertical slice | PASS, 2 passed |
| Docker-backed serial M1 PostgreSQL repositories | PASS, 4 passed |
| Docker-backed serial VS-M1-001..006 | PASS, 6 passed |
| Acceptance | PASS, 8 passed |
| Full pytest | PASS, 1169 passed |

Warnings were limited to the existing Starlette/httpx and anyio deprecation
warnings through FastAPI `TestClient`, plus the local `VIRTUAL_ENV` mismatch
warning emitted by `uv` in the shared shell environment.

## Remote-CI Limitation

This validation occurred before publication. It proves workflow structure,
security, local command parity, and deterministic gate behavior. It does not
claim that the modified GitHub Actions workflow has executed remotely. Exact
remote-CI proof belongs to the later integration/publication sequence for this
validated SHA.

TASK-M1-016 is validated and frozen. It remains unmerged and unpublished.
