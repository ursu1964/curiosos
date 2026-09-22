---
id: TASK-M0-001-EVIDENCE
title: TASK-M0-001 M0 Topology and Guardrail Transition Evidence
lifecycle: TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-001
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-001 Evidence

## Objective

Establish the M0 topology and guardrail transition required before M0 runtime
implementation begins.

TASK-M0-001 does not implement persistence, policy runtime, event/evidence
store, work repository, runtime service, executor, API work routes, web work
console, or M1+ functionality.

## Starting Baseline

`3f0776250b99b7652885dc01539c98e8b1948868`

M0 planning is `VALIDATED, FROZEN`. TASK-M0-001 is the first authorized M0
execution unit from that baseline.

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Establish exact M0 topology guardrail mechanism | PASS | Security tests now record task-scoped planned M0 surfaces and keep them blocked until specific task authorization. |
| Preserve BOOT topology | PASS | Existing BOOT package/app/.github/integration/acceptance allowlists remain exact. |
| Do not authorize all future M0 paths | PASS | Planned M0 package roots are represented separately from currently authorized roots and are rejected while tracked early. |
| Preserve secret scanning | PASS | Security scan roots continue covering current source/config/docs surfaces; new docs are under scanned `docs/**`. |
| Preserve core authority boundary and policy UNKNOWN safety | PASS | Existing security tests remain active and pass. |
| Preserve dependency direction | PASS | Architecture tests block `curios_contracts` and `curios_core` from depending on planned M0 implementation packages. |
| Do not modify canonical contracts/core/provider/API/web behavior | PASS | Only tests, M0 docs, and the M0 ledger changed. |
| Keep M1+ scope blocked | PASS | Adversarial package-root checks reject representative agent runtime, DataLab, knowledge, model-router, and secret-resolver package roots. |
| Update lifecycle truthfully | PASS | TASK-M0-001 is recorded as `IMPLEMENTED, TESTED`; TASK-M0-002 through TASK-M0-014 remain `BLOCKED`. |

## Files Changed

- `tests/security/test_security_baseline.py`
- `tests/architecture/test_architecture_conformance.py`
- `docs/security/TASK-M0-001-topology-guardrails.md`
- `docs/architecture/TASK-M0-001-topology-guardrails.md`
- `docs/program/status-ledger/M0-status-ledger.md`
- `docs/tasks/TASK-M0-001-evidence.md`

## Topology Model

The current tracked topology remains the frozen BOOT topology.

TASK-M0-001 adds explicit planned-but-not-currently-authorized M0 surfaces:

- `packages/python/curios_persistence/**` for TASK-M0-002;
- `packages/python/curios_policy/**` for TASK-M0-003;
- `packages/python/curios_runtime/**` for TASK-M0-004 through TASK-M0-007;
- additional `tests/integration/**` for TASK-M0-010;
- additional `tests/acceptance/**` for TASK-M0-012.

Those surfaces remain blocked until their owning tasks update topology
authority and pass independent validation.

## Security Guardrails

- Current package/app roots remain exact.
- `.github` remains restricted to `.github/workflows/quality-gates.yml`.
- Future M0 package roots are rejected before task-specific authorization.
- Broad top-level `runtime/**`, `services/**`, and `providers/**` roots remain
  blocked.
- Additional app roots such as `apps/admin` and `apps/agent-console` are
  rejected.
- Secret scanning and secret-value/reference tests remain active.

## Architecture Guardrails

Architecture conformance now explicitly treats M0 persistence, policy, and
runtime packages as implementation packages that must not become inward
dependencies of `curios_contracts` or `curios_core`.

No new generic reference abstraction, canonical contract, runtime port, provider
selector, API route, or web component was introduced.

## Adversarial Review

The corrected guardrails answer the core adversarial question:

Could an unauthorized M0 or M1+ surface be added under another plausible name
while these tests still pass?

Within the governed structural checks, no:

- unapproved package root can be tracked without failing package-root topology;
- representative M1+ package root can be tracked without failing topology;
- broad runtime/service/provider top-level root can be tracked without failing
  top-level topology;
- unrelated app root can be tracked without failing app-root topology;
- contract/core dependency on M0 implementation package names can be added
  without failing architecture conformance.

Later tasks must still add their own precise authorization and tests when their
surfaces become active.

## Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| Docker Compose config | Passed. |
| Ruff check | Passed. |
| Ruff format check | Passed. |
| mypy strict baseline | Passed: `uv run mypy apps/api/src packages/python/*/src` found no issues in 39 source files. |
| Package/API/provider tests | Passed: 161 passed. |
| Contract tests | Passed: 10 passed. |
| Schema tests | Passed: 5 passed. |
| Architecture tests | Passed: 14 passed. |
| Security tests | Passed: 38 passed. |
| API integration tests | Passed: 6 passed, 2 known dependency warnings. |
| PostgreSQL provider integration test | Passed: 1 passed. |
| BOOT acceptance tests | Passed: 6 passed, 2 known dependency warnings. |
| Full pytest suite | Passed: 241 passed, 2 known dependency warnings. |
| Frontend checks | Passed: frozen install, `pnpm check`, apps/web tests, typecheck, and production build. |
| `git diff --check` | Passed before commit preparation. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings previously classified as
non-blocking dependency warnings.

## Dependency Changes

None.

## Lifecycle State

TASK-M0-001 is `IMPLEMENTED, TESTED`.

It is not `VALIDATED` or `FROZEN`; independent validation must make that
decision. TASK-M0-002 through TASK-M0-014 remain `BLOCKED`.
