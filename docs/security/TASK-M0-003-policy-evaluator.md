---
id: TASK-M0-003-POLICY-EVALUATOR
title: TASK-M0-003 Minimal Policy Evaluator Security Semantics
lifecycle: IMPLEMENTED
artifact_type: security_semantics
authority: implementation
task_id: TASK-M0-003
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-003 Minimal Policy Evaluator Security Semantics

## Scope

TASK-M0-003 adds only `packages/python/curios_policy/**`.

The evaluator is not a policy language, IAM service, RBAC/ABAC layer, approval
workflow, secret resolver, policy persistence store, external policy service,
or dynamic policy loader.

## Supported M0 Authorization Case

The only authorizing M0 case is:

- work type: `provider_inventory`;
- requested effects: exactly `READ_ONLY`;
- policy state: known.

That case returns a canonical `PolicyDecision` with outcome `ALLOW`.

## Non-Authorizing Cases

The evaluator returns non-authorizing canonical `PolicyDecision` outcomes for:

- unsupported work types: `DENY`;
- supported work with any effect other than exactly `READ_ONLY`: `DENY`;
- mixed `READ_ONLY` plus another governed effect: `DENY`;
- unknown or incomplete policy state: `UNKNOWN`;
- missing/empty work type: `UNKNOWN`.

Malformed evaluator inputs raise deterministic validation errors before a
decision is created; no malformed path returns `ALLOW`.

## Preserved Boundaries

- Canonical effect, risk, approval, authority, and policy vocabulary remains in
  `curios_contracts`.
- `PolicyDecision.UNKNOWN` remains distinct from `DENY` and is
  non-authorizing.
- Authority is not granted, mutated, persisted, or interpreted as IAM.
- `curios_contracts` and `curios_core` do not depend on `curios_policy`.
- Persistence, runtime, API, web, secret resolution, and production IAM remain
  deferred to their owning tasks or milestones.
