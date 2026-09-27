---
id: TASK-M2-001-EVIDENCE
title: TASK-M2-001 M2 Topology and Guardrail Transition Evidence
lifecycle: IMPLEMENTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M2-001
milestone_id: M2
date: 2026-09-27
---

# TASK-M2-001 Evidence

## Objective

Transition repository topology, architecture checks, security inventories, and
ownership guardrails so the exact future DataLab surfaces authorized by frozen
M2 planning have explicit owners and prohibited authority is structurally
blocked before those surfaces are implemented.

TASK-M2-001 does not implement DataLab contracts, CSV intake, decomposition,
persistence, profiler seams, profiler execution, capability/agent integration,
runner binding, API routes, web UI, integration tests, acceptance tests, CI
changes, M3+ behavior, release, deployment, or tags.

## Starting Baseline

`935935d64d30c266e270faad03122c97a15fdbc5`

M1 is `FROZEN / CLOSED / PUBLISHED / REMOTE-CI-VERIFIED`.

M2 planning is `VALIDATED / FROZEN / PUBLISHED / REMOTE-CI-VERIFIED`.

M2 readiness is `PASS`, and the frozen readiness record authorizes only
`TASK-M2-001 - M2 Topology and Guardrail Transition` as the first M2
implementation unit.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Represent planned M2 surfaces | PASS | Security tests now carry an exact TASK-M2-001..016 planned-surface registry and current authorization registry. |
| Keep TASK-M2-001 topology-only | PASS | Product DataLab contracts, runtime records, API routes, web functions, profiler behavior, persistence schema, and CI changes remain absent. |
| Preserve DataLab contract ownership | PASS | Architecture/security guards keep `DataLabAnalysisRequest`, `DatasetProfile`, `DataLabFinding`, and `DataLabAnalysisResult` planned for `curios_contracts` without implementing them in TASK-M2-001. |
| Preserve run-record ownership | PASS | Guards reject `DataLabRunState` and `DataLabRunRecord` definitions under `curios_persistence`; persistence remains storage/reconstruction authority only. |
| Preserve dataset reference decision | PASS | Guards reject a duplicate `DatasetReference`; M2 remains planned around `ArtifactReference(kind=dataset)`. |
| Preserve work/capability topology | PASS | Frozen work type `dataset_profile` and capability identifier `dataset_profiling` remain planned and are not present in product source. |
| Preserve dataset authority boundary | PASS | TASK-M2-001 implements no upload parsing, filename validation, staging, SHA-256 calculation, cleanup, or dataset persistence. |
| Preserve tool authority boundary | PASS | Architecture probes reject representative DataLab subprocess, shell, dynamic import, network, and model/provider authority. |
| Preserve API/web boundary | PASS | Security probes reject premature `/m2/datalab/*` FastAPI routes and premature DataLab web API-boundary functions. |
| Preserve M1 non-regression | PASS | Existing M1 architecture/security inventories and exact route/web/CI guards remain active and unchanged except for additive M2 topology tests. |
| Preserve M3+ boundary | PASS | Security topology rejects broad future package roots for agent runtime, knowledge, model routing, scheduler, tools, and general DataLab package expansion. |
| Dependency/schema hygiene | PASS | No dependency manifests, lockfiles, schemas, migrations, app code, package code, infrastructure, or CI workflow files changed. |

## Correction 1

Independent validation of implementation
`b3a755a6365d33aac8cee7ad5445228e72578dd2` failed the future-surface
compatibility criterion. The original guard design incorrectly converted
TASK-M2-001's temporal "not implemented yet" fact into permanent repository
absence rules.

Correction 1 changes the guard model to ownership/authority invariants:

- valid future DataLab contracts are allowed in `curios_contracts`;
- valid future DataLab run state/record semantics are allowed in
  `curios_runtime`;
- valid future persistence storage representation is allowed in
  `curios_persistence` while canonical run state/record ownership remains
  forbidden there;
- exact future M2 work type and capability identifiers remain allowed;
- exact future M2 API endpoints and explicit web boundary functions remain
  allowed when introduced by their frozen owner tasks;
- wrong-owner definitions, duplicate `DatasetReference`, alternate M2 tokens,
  extra M2 endpoints, generic DataLab web request escapes, forbidden
  execution/model/network authority, and M3+ roots remain rejected.

Independent re-validation after Correction 1 failed because API adapter
authority guards detected provider/model authority but did not reject synthetic
DataLab API adapter fixtures with arbitrary filesystem reads, direct
`curios_persistence` usage, or direct profiler/runtime implementation imports.

Correction 2 freezes the DataLab API adapter rule: future M2 API routes may
perform transport/adaptation, construct canonical requests, call explicit
public DataLab runtime/application seams, serialize canonical results, and
translate bounded errors. DataLab API adapter modules must not own raw
filesystem/staging authority, persistence implementation, profiler
implementation, provider/model authority, or network authority. The guard
allows composition-root dependency wiring while rejecting those bypasses in
DataLab route/adapter modules.

## Files Changed

- `docs/program/status-ledger/M2-status-ledger.md`
- `docs/tasks/TASK-M2-001-evidence.md`
- `tests/architecture/test_architecture_conformance.py`
- `tests/security/test_security_baseline.py`

## Topology Result

TASK-M2-001 records M2 planned ownership without adding DataLab product
surfaces:

- `curios_contracts` remains the planned owner for DataLab analysis request,
  profile, finding, and result contracts.
- `curios_runtime` remains the planned owner for DataLab run lifecycle
  semantics and run records.
- `curios_persistence` remains the planned owner for durable storage mechanics
  only.
- Existing M1 owners remain authoritative for artifacts, object references,
  work, result, evidence, verification, capabilities, agents, routing, events,
  and verification.

## Guardrail Result

Added architecture/security guardrails cover:

- planned M2 surface ownership by task;
- no product implementation during TASK-M2-001;
- no duplicate dataset reference abstraction;
- runtime-owned DataLab run semantics;
- persistence not owning DataLab lifecycle semantics;
- no premature M2 API/web authority;
- no forbidden DataLab subprocess, shell, dynamic import, network, model, or
  cloud-provider authority;
- no M3+ package/root expansion.

## Adversarial Guard Probes

Synthetic probes were added for:

- fake `DataLabRunRecord` and `DataLabRunState` under persistence ownership;
- fake duplicate `DatasetReference`;
- fake DataLab subprocess, `os.system`, dynamic import, network/client import,
  and model-provider import;
- exact future `/m2/datalab/*` FastAPI route inventory accepted and
  partial/extra inventory rejected;
- exact future DataLab web API-boundary function inventory accepted and
  generic/extra DataLab web request escapes rejected;
- fake DataLab API adapter filesystem, client-filename path, tempfile/staging,
  persistence bypass, profiler bypass, network, and provider/model authority;
- valid future DataLab API adapter delegation to an explicit public runtime
  seam and valid composition-root dependency wiring;
- fake M3+ package roots.

The probes are temporary/synthetic test inputs only and do not remain as
repository product state.

## Verification

Final verification was performed after implementation:

- `uv lock --check`: PASS.
- `uv sync --locked --all-groups --all-packages`: PASS.
- `pnpm install --frozen-lockfile`: PASS.
- Docker Compose config: PASS.
- `ruff format --check .`: PASS, 302 files already formatted.
- `ruff check .`: PASS.
- `mypy apps/api/src packages/python/*/src`: PASS, 70 source files.
- `pnpm check`: PASS.
- `pnpm --dir apps/web test`: PASS, 26 tests.
- `pnpm --dir apps/web typecheck`: PASS.
- `pnpm --dir apps/web build`: PASS.
- `uv run pytest tests/contract tests/schema -q`: PASS, 16 tests.
- `uv run pytest tests/architecture -q`: PASS, 45 tests.
- `uv run pytest tests/security -q`: PASS, 382 tests, 2 existing
  FastAPI/Starlette deprecation warnings.
- M1 package/API gate: PASS, 618 tests, 9 intentional deselections, 2 existing
  FastAPI/Starlette deprecation warnings.
- M1 PostgreSQL gate: PASS, 4 tests.
- VS-M1 integration: PASS, 6 tests, 2 existing FastAPI/Starlette deprecation
  warnings.
- M1 acceptance: initial correction-run attempt exposed a local PostgreSQL
  lifecycle transient (`Connection refused` during a DB-backed acceptance
  operation); after restarting the local compose PostgreSQL service and
  waiting for healthy state, the serial rerun passed with 14 tests and 2
  existing FastAPI/Starlette deprecation warnings.
- Full pytest: PASS, 1206 tests, 2 existing FastAPI/Starlette deprecation
  warnings.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS.

## 1.txt Guard

`1.txt` remains untracked and untouched.

Expected SHA-256:

`d3db09d30c2b8ee24cad0339c140f7256eac3ea89f1bc9eafa9e86c55bb38b88`

## Downstream Status

TASK-M2-001 is `IMPLEMENTED, TESTED` after this task's local verification.

TASK-M2-001 still requires independent validation/freeze, integration,
publication, and remote-CI verification before TASK-M2-002 may start under the
frozen DAG.

TASK-M2-002 through TASK-M2-016 remain blocked.
