---
id: TASK-BOOT-013-EVIDENCE
title: TASK-BOOT-013 Configuration, Security, Effect, and Policy Contracts Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-013
---

# TASK-BOOT-013 Configuration, Security, Effect, and Policy Contracts Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-013-security-policy-contracts` at required base `8f606631011139c8e05b2668f690e4addde44770`; TASK-BOOT-013 implementation began. |
| 2 | IMPLEMENTED | Python contracts, package exports, focused tests, and authoritative contract documentation were added for TASK-BOOT-013 scope. |
| 3 | TESTED | Deterministic checks were run after implementation; see check evidence below. |

## Implementation Summary

- Contract documentation: `docs/contracts/TASK-BOOT-013-security-policy-contracts.md`.
- Python contracts: `packages/python/curios_contracts/src/curios_contracts/security.py`.
- Package exports: `packages/python/curios_contracts/src/curios_contracts/__init__.py`.
- Tests: `packages/python/curios_contracts/tests/test_security_policy_contracts.py`.

## Contracts Added

- `ConfigurationProfile` and `ConfigurationProfileName`.
- `SecretReference`.
- `Principal` and `PrincipalType`.
- `Permission`.
- `Authority`.
- `EffectClassification`.
- `RiskClassification`.
- `PolicyDecision` and `PolicyDecisionOutcome`.
- `Approval` and `ApprovalOutcome`.

## Frozen Vocabularies

Effect classifications:

```text
READ_ONLY
LOCAL_WRITE
EXTERNAL_READ
EXTERNAL_WRITE
DESTRUCTIVE
SECRET_ACCESS
NETWORK_ACCESS
EXECUTION
```

Risk classifications:

```text
LOW
MODERATE
HIGH
CRITICAL
```

Policy decision outcomes:

```text
ALLOW
DENY
REQUIRES_APPROVAL
UNKNOWN
```

Approval outcomes:

```text
PENDING
APPROVED
REJECTED
```

## Semantic Policies

- `LOCAL_DOCKER` is the only M0 canonical configuration environment profile.
- Docker Compose base/full/observability profiles are tooling profiles, not
  Curios environment profiles.
- `SecretReference` contains no secret value and does not resolve secrets during
  serialization.
- Principal records contain identity and optional references, not credentials.
- Permission is an action/resource/scope/effect abstraction; authority is the
  explicit bounded grant to a principal.
- Effects describe consequences; risk classifications describe control pressure.
- `PolicyDecision.UNKNOWN` is preserved as `UNKNOWN`; governed effects are not
  authorized by an unknown decision.
- Approval is scoped, expiring, and separate from permanent authority.
- TASK-BOOT-011-owned models are not implemented by this task.

## Check Evidence

| Check | Result |
| --- | --- |
| Path, branch, and base verification | Passed: `/home/user/projects/curiosos-wt-013`, branch `task/boot-013-security-policy-contracts`, base `8f606631011139c8e05b2668f690e4addde44770`. |
| Root and package TOML parse | Passed: `pyproject.toml` and all Python package `pyproject.toml` files parsed with `tomllib`. |
| `uv lock --check` | Passed: lockfile resolved without update. |
| `uv sync --frozen` | Passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .`. |
| mypy strict baseline | Passed: `uv run --package curios-contracts mypy packages/python`. |
| Full `curios_contracts` tests | Passed: `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` reported 102 passed. |
| Serialization inspection | Passed: configuration, secret reference, principal, permission, authority, policy decision, and approval records serialize to JSON-compatible snake_case data with canonical IDs/references and UTC timestamps. |
| Architecture/import scan | Passed: no authentication, RBAC, ABAC, policy evaluator, secret resolver, approval workflow, provider SDK, API, persistence, OpenTelemetry, broker, or TASK-BOOT-011 model implementation was added. |
| Secret-field scan | Passed: canonical source rejects secret-shaped unsafe fields for sensitive references/details and contains no `secret_value` contract field. |
| Exact effect/risk/outcome vocabulary checks | Passed: effect, risk, policy-decision outcome, approval outcome, principal type, and configuration profile vocabularies are exact. |
| Duplicate reference scan | Passed: `ObjectReference` remains the only generic object-reference contract; `SecretReference` is a secret pointer, not a replacement generic reference. |
| Diff whitespace | Passed: `git diff --check`. |
| Scope review | Passed: changes are limited to `packages/python/curios_contracts/**`, TASK-BOOT-013 docs/evidence/status, and no TypeScript, README, historical source, provider, API, persistence, auth, RBAC, ABAC, policy evaluator, secret resolver, approval workflow, or TASK-BOOT-011 model implementation files were modified. |
