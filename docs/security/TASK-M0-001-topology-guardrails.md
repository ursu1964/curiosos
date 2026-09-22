---
id: TASK-M0-001-SECURITY-GUARDRAILS
title: TASK-M0-001 M0 Security Topology Guardrails
lifecycle: IMPLEMENTED
artifact_type: security_guardrail
authority: implementation
task_id: TASK-M0-001
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-001 M0 Security Topology Guardrails

## Purpose

TASK-M0-001 establishes the security topology mechanism for M0 without
authorizing M0 runtime implementation prematurely.

The frozen rule remains:

Each task authorizes only its explicit new surface.

## Current Authorized Topology

Current tracked roots remain the frozen BOOT roots:

- existing BOOT Python packages;
- existing BOOT TypeScript package;
- `apps/api`;
- `apps/web`;
- exact `.github/workflows/quality-gates.yml`;
- exact BOOT integration and acceptance tests.

TASK-M0-001 does not add new runtime package roots, app roots, broad test roots,
service roots, provider roots, or `.github` surfaces.

## Planned But Not Yet Authorized M0 Surfaces

The security tests now record planned M0 surfaces by task so future tasks can
authorize them narrowly:

| Task | Planned Surface |
| --- | --- |
| TASK-M0-002 | `packages/python/curios_persistence/**` |
| TASK-M0-003 | `packages/python/curios_policy/**` |
| TASK-M0-004 through TASK-M0-007 | `packages/python/curios_runtime/**` |
| TASK-M0-010 | `tests/integration/**` additions beyond frozen BOOT integration tests |
| TASK-M0-012 | `tests/acceptance/**` additions beyond frozen BOOT acceptance tests |

Those planned surfaces remain blocked until their specific tasks are
implemented, tested, independently validated, frozen, and integrated according
to the M0 DAG.

## Preserved Security Controls

- repository secret scanning;
- secret-reference/value rules;
- core authority boundary;
- `PolicyDecision.UNKNOWN` non-authorizing semantics;
- exact `.github` authorization;
- provider isolation;
- API/web outer-boundary controls;
- exact integration/acceptance test surfaces;
- M1+ deferred-scope rejection.

## Adversarial Protection

The security topology tests reject:

- future M0 packages before their owning task authorizes them;
- plausible M1+ package names such as agent runtime, DataLab, knowledge,
  model-router, and secret-resolver packages;
- broad top-level runtime/service/provider roots;
- additional unrelated app roots;
- arbitrary `.github` paths.
