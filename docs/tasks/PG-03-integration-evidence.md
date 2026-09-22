---
id: PG-03-INTEGRATION-EVIDENCE
title: PG-03 Integration Evidence
lifecycle: TESTED
artifact_type: integration_evidence
authority: evidence
workstream: PG-03
---

# PG-03 Integration Evidence

## Scope

This record covers integration of the accepted PG-03 task outputs into `main`.

Integrated task commits:

- `TASK-BOOT-003`: `ee69e11e6a00a774ebf388a4fe91f05eea7e67f9`
- `TASK-BOOT-004`: `0ae55c9f6b3ce7320d6a700eb8b026c3966cf1df`
- `TASK-BOOT-005`: `389302e`
- `TASK-BOOT-006`: `72edf0bd0114ccd074a3404e0a1588b81629066c`

The PG-03 integration baseline is the `main` commit containing this evidence record.

## Conflict Resolution

Conflicts occurred only in `docs/program/status-ledger/BOOT-000-task-ledger.md`.

Resolution:

- preserved all four task implementation outputs;
- recorded `TASK-BOOT-003` through `TASK-BOOT-006` as `VALIDATED, FROZEN`;
- preserved `TASK-BOOT-006` live PostgreSQL readiness as a deferred BOOT acceptance verification item;
- did not alter `TASK-BOOT-007` or later implementation lifecycle states.

## Combined Python Checks

| Check | Result |
| --- | --- |
| `pyproject.toml` parsed with Python `tomllib` | passed |
| `requires-python` is `>=3.14,<3.15` | passed |
| `uv lock --check` | passed |
| `uv sync --locked --all-groups` | passed |
| `uv run ruff check .` | passed |
| `uv run ruff format --check .` | passed |
| `uv run mypy --version` | passed, `mypy 2.3.1` |
| `uv run pytest --collect-only` | parsed configuration; collected 0 tests as expected for current bootstrap scope |
| `.venv` ignore behavior | passed; `.venv` is ignored and untracked |

## Combined TypeScript Checks

| Check | Result |
| --- | --- |
| `node --version` | passed, `v24.18.0` |
| `pnpm --version` | passed, `12.5.1` |
| `pnpm install --frozen-lockfile` | passed |
| `pnpm list --depth -1 --recursive` | passed |
| `pnpm typecheck` | passed |
| `pnpm lint` | passed |
| `pnpm format:check` | passed |
| `pnpm check` | passed |
| `node_modules` ignore behavior | passed; `node_modules` is ignored and untracked |

## Developer Command Checks

| Check | Result |
| --- | --- |
| `bash -n tooling/curios` | passed |
| `tooling/curios help` | passed, exit 0 |
| `tooling/curios commands` | passed, exit 0 |
| `tooling/curios status` | passed, exit 0 |
| required but unavailable command intentions | passed, each exited 78 |
| unknown command | passed, exited 2 |

## LOCAL_DOCKER Checks

| Check | Result |
| --- | --- |
| `docker --version` | passed, Docker 29.8.0 |
| `docker compose version` | passed, Docker Compose v5.5.1 |
| `docker compose --env-file infrastructure/local/docker/.env.example -f infrastructure/local/docker/compose.yaml config --quiet` | passed |
| Docker daemon availability | failed; daemon socket unavailable at `unix:///var/run/docker.sock` |
| PostgreSQL live health/readiness | deferred because daemon was unavailable |

## Cross-Task Checks

| Check | Result |
| --- | --- |
| `git diff --check` | passed |
| `uv.lock` tracked | passed |
| `pnpm-lock.yaml` tracked | passed |
| lockfiles not ignored | passed |
| `.venv` not tracked | passed |
| `node_modules` not tracked | passed |
| `README.md` unchanged | passed |
| `1.txt` unchanged and untracked | passed |
| no API/web/provider/package skeletons | passed |
| no CI files | passed |
| no database schemas or migrations | passed |

## Deferred BOOT Acceptance Item

`BOOT-VERIFY-PG-READINESS-001` remains open:

Start the TASK-BOOT-006 PostgreSQL service, verify health/readiness, and stop it cleanly without destroying the persistent volume.

This must be completed before final BOOT-000 acceptance.
