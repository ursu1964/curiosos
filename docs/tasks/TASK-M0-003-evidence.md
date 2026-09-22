---
id: TASK-M0-003-EVIDENCE
title: TASK-M0-003 Minimal Policy Evaluator Evidence
lifecycle: IMPLEMENTED, TESTED
artifact_type: task_evidence
authority: implementation
task_id: TASK-M0-003
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-003 Minimal Policy Evaluator Evidence

## Objective

Implement only the minimal deterministic M0 policy evaluator required for
READ_ONLY provider-inventory work and fail-safe governed effects.

## Implemented Surface

- `packages/python/curios_policy/**`
- policy package tests
- TASK-M0-003 security semantics documentation
- narrow security/architecture test updates authorizing only
  `packages/python/curios_policy/**`
- M0 status ledger transition to `IMPLEMENTED, TESTED`

## Evaluator Semantics

| Input | Outcome | Authorizing |
| --- | --- | --- |
| `provider_inventory` with exactly `READ_ONLY` and known policy state | `ALLOW` | Yes |
| unsupported work type | `DENY` | No |
| any governed effect other than exactly `READ_ONLY` | `DENY` | No |
| `READ_ONLY` mixed with another governed effect | `DENY` | No |
| unknown or incomplete policy state | `UNKNOWN` | No |
| missing/empty work type | `UNKNOWN` | No |
| malformed request object or malformed canonical inputs | deterministic error | No decision/No authorization |

## Boundary Evidence

- The evaluator returns canonical `PolicyDecision` records from
  `curios_contracts`.
- `UNKNOWN` remains serialized as `UNKNOWN` and distinct from `DENY`.
- Authority is neither granted nor mutated by evaluation.
- `curios_contracts` and `curios_core` remain independent of `curios_policy`.
- No persistence, runtime, API, web, secret resolver, approval workflow, IAM,
  RBAC/ABAC, DSL, rule compiler, external policy service, or dynamic policy
  loader was introduced.

## Verification

Local verification was run for TASK-M0-003 and repository gates. See the final
TASK-M0-003 implementation report for exact command outcomes, test counts, and
commit SHA.

## Lifecycle

TASK-M0-003 is implemented and tested only. It is not self-declared
`VALIDATED` or `FROZEN`.

TASK-M0-002 remains unchanged. TASK-M0-004 through TASK-M0-014 remain blocked.
