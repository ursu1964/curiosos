---
id: TASK-M1-001-SECURITY-GUARDRAILS
title: TASK-M1-001 M1 Security Topology Guardrails
lifecycle: IMPLEMENTED
artifact_type: security_guardrail
authority: implementation
task_id: TASK-M1-001
milestone_id: M1
date: 2026-09-23
---

# TASK-M1-001 M1 Security Topology Guardrails

## Purpose

TASK-M1-001 establishes the security topology mechanism for M1 without
authorizing M1 cognitive/runtime/product implementation prematurely.

The frozen rule remains:

Each task authorizes only its explicit new surface.

## Current Authorized Topology

Current tracked topology remains the frozen BOOT+M0 topology:

- frozen BOOT Python packages and TypeScript contracts package;
- `packages/python/curios_persistence/**` for frozen M0 persistence only;
- `packages/python/curios_policy/**` for frozen M0 policy only;
- exact frozen `packages/python/curios_runtime/**` M0 modules only;
- exact frozen `apps/api` M0 composition and work endpoint files only;
- exact frozen `apps/web` M0 work-console files only;
- exact frozen BOOT/M0 integration and acceptance test files only;
- exact `.github/workflows/quality-gates.yml`;
- docs and status/evidence artifacts.

TASK-M1-001 adds guardrail tests and documentation only. It does not authorize
new package roots, runtime modules, contract files, API files, web files,
integration tests, acceptance tests, CI workflow changes, or `.github` paths.

## Planned But Not Yet Authorized M1 Surfaces

| Task | Planned Surface Category |
| --- | --- |
| TASK-M1-002 | cognitive canonical contracts |
| TASK-M1-003 | deterministic decomposition implementation |
| TASK-M1-004 | bounded DAG records/runtime state |
| TASK-M1-005 | capability resolver |
| TASK-M1-006 | agent definition and instance persistence |
| TASK-M1-007 | agent lifecycle repository and events |
| TASK-M1-008 | executor seam and deterministic executors |
| TASK-M1-009 | model/profile discovery records only |
| TASK-M1-010 | routing decision records |
| TASK-M1-011 | bounded local DAG runner |
| TASK-M1-012 | verification loop and evidence binding |
| TASK-M1-013 | M1 API cognitive-loop endpoints |
| TASK-M1-014 | M1 web cognitive-loop console |
| TASK-M1-015 | M1 integration tests |
| TASK-M1-016 | M1 CI quality-gate update |
| TASK-M1-017 | M1 acceptance tests |

These surfaces are represented as planned ownership categories. They are not
currently authorized tracked implementation surfaces.

## Structural Enforcement

The security topology tests now reject representative premature M1 additions
including:

- new cognitive contract files under the already-authorized contracts package;
- new TypeScript contract files;
- arbitrary M1 package roots;
- new `curios_runtime` modules for DAG, agent, executor, model-profile,
  routing, runner, or verification behavior;
- new M1 API source or API test files;
- new M1 web source files;
- new M1 integration or acceptance tests;
- any additional `.github` content beyond the frozen quality-gates workflow.

The checks also preserve current-stage exactness for all frozen BOOT and M0
surfaces.

## Deferred Scope Still Blocked

TASK-M1-001 keeps the following outside current authority:

- autonomous/general agents;
- production-scale scheduler;
- generalized tool execution;
- model generation, chat, completion, inference runtime, or router
  optimization;
- cloud model execution;
- knowledge or memory runtime;
- DataLab;
- learning or self-improvement;
- production IAM or full policy language;
- secret resolver;
- external brokers;
- cloud infrastructure;
- live LLM quality gates.

## Secret Scanning

New M1-001 documentation is under `docs/**`, which remains a scanned security
surface. The task adds no exemptions and does not weaken secret-shaped literal
detection, secret-reference/value checks, or authority boundary checks.

