---
id: TASK-M0-003-VALIDATION-EVIDENCE
title: TASK-M0-003 Independent Revalidation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-003
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-003 Independent Revalidation Evidence

## Decision

TASK-M0-003 REVALIDATION: PASS

Validated candidate:

`1c842276e8c79de4d1b2b8acc4cac392b0e49812`

Implementation commit:

`f2a60793b6d3b3fe9b076d9df35a5fbfb9eb92ff`

Corrective commit:

`1c842276e8c79de4d1b2b8acc4cac392b0e49812`

## Correction Audit

The diff from `f2a60793b6d3b3fe9b076d9df35a5fbfb9eb92ff` to
`1c842276e8c79de4d1b2b8acc4cac392b0e49812` changes only
`tests/security/test_security_baseline.py`.

The sole diff collapses the singleton set assertion for
`M0_AUTHORIZED_PACKAGE_ROOTS_BY_TASK["TASK-M0-003"]` from three lines to Ruff's
canonical one-line form.

Validation confirmed:

- assertion semantics are identical;
- topology authorization did not change;
- security semantics did not change;
- policy implementation did not change;
- no test was added or removed;
- no production source changed.

## Authorization Semantics

The frozen M0 task pack and TASK-M0-003 security semantics define exactly one
authorizing case:

- work type is `provider_inventory`;
- governed effects are exactly one `READ_ONLY`;
- policy state is known.

The evaluator reaches `ALLOW` only after:

- rejecting unknown policy state or missing work type as `UNKNOWN`;
- rejecting unsupported work type as `DENY`;
- comparing the normalized requested-effect tuple to exactly
  `(EffectClassification.READ_ONLY,)`.

No alternate path to `ALLOW` was identified.

## UNKNOWN Semantics

Validation confirmed:

- `PolicyDecisionOutcome.UNKNOWN` remains distinct from `DENY`;
- `UNKNOWN` is non-authorizing;
- incomplete or unknown policy state returns `UNKNOWN`;
- malformed evaluator inputs raise deterministic validation errors before a
  decision is created;
- serialization round-trip preserves `UNKNOWN`;
- `PolicyDecision.is_authorizing` is true only for `ALLOW`.

## Adversarial Effect Review

Non-authorization was verified for:

- unsupported work type;
- unsupported governed effect;
- mixed `READ_ONLY` plus unsupported effect;
- duplicate `READ_ONLY` values;
- empty effects;
- malformed or unknown effect token where representable;
- incomplete or unknown policy state.

Unsupported governed effects and duplicate or mixed effect tuples return
`DENY`. Empty effects and malformed canonical inputs fail closed by raising
validation errors before any `ALLOW` decision can be returned.

## Authority Separation

Validation confirmed:

- the evaluator returns canonical `PolicyDecision` records only;
- the evaluator does not create `Authority`;
- the evaluator does not grant `Authority`;
- the evaluator does not mutate `Authority`;
- `CoreContext` remains unchanged and only carries an optional frozen
  `Authority` contract object;
- policy decision evaluation remains distinct from authority representation.

## Architecture And Dependency

Validation confirmed:

- `curios_policy` depends only on `curios-contracts`;
- `curios_contracts` does not depend on `curios_policy`;
- `curios_core` does not depend on `curios_policy`;
- no persistence, runtime, API, or web dependency was introduced;
- no external policy framework exists.

## Guardrail Transition

Validation confirmed:

- `packages/python/curios_policy` is authorized for TASK-M0-003;
- `packages/python/curios_persistence` remains unauthorized on this branch;
- `packages/python/curios_runtime` remains unauthorized;
- representative M1+ policy/IAM/security package roots remain blocked;
- BOOT security protections remain intact.

## Scope

Validation found no:

- policy DSL;
- policy persistence;
- dynamic policy loading;
- IAM;
- role hierarchy;
- secret resolver;
- external policy service;
- runtime service;
- API or web behavior;
- TASK-M0-004+ implementation.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | Passed: 9 TOML files valid. |
| `uv lock --check` | Passed: resolved 41 packages. |
| `uv sync --locked --all-groups --all-packages` | Passed: checked 38 packages. |
| Docker Compose config | Passed: single LOCAL_DOCKER PostgreSQL service, `postgres:18`, named volume preserved. |
| Ruff check | Passed. |
| Ruff format check | Passed: 147 files already formatted. |
| mypy strict baseline | Passed: no issues found in 41 source files. |
| TASK-M0-003 policy tests | Passed: 20 tests. |
| Contracts/core tests | Passed: 123 tests. |
| Repository contract/schema tests | Passed: 15 tests. |
| Provider/API tests | Passed: 38 tests. |
| Architecture tests | Passed: 15 tests. |
| Security tests | Passed: 37 tests. |
| API integration tests | Passed: 6 tests, 2 known dependency warnings. |
| PostgreSQL provider integration test | Passed: 1 test; service stopped cleanly and persistent named volume remained present. |
| BOOT acceptance tests | Passed: 6 tests, 2 known dependency warnings. |
| Full pytest suite | Passed: 261 tests, 2 known dependency warnings. |
| `pnpm install --frozen-lockfile` | Passed. |
| `pnpm check` | Passed. |
| `pnpm --dir apps/web test` | Passed: 2 tests. |
| `pnpm --dir apps/web typecheck` | Passed. |
| `pnpm --dir apps/web build` | Passed. |
| `git diff --check` | Passed. |

The warnings are the existing Starlette/TestClient `httpx` deprecation and
anyio `BlockingPortal` alias deprecation warnings.

## Lifecycle Transition

TASK-M0-003 is `VALIDATED, FROZEN`.

TASK-M0-002 remains unchanged. TASK-M0-004 and TASK-M0-005 are not made ready
by this validation. PG-M0-02 integration with frozen TASK-M0-002 remains
required before downstream readiness changes.
