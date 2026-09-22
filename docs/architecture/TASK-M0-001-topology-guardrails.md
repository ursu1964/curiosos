---
id: TASK-M0-001-ARCHITECTURE-GUARDRAILS
title: TASK-M0-001 M0 Topology Architecture Guardrails
lifecycle: FROZEN
artifact_type: architecture_guardrail
authority: implementation
task_id: TASK-M0-001
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-001 M0 Topology Architecture Guardrails

## Purpose

TASK-M0-001 transitions the repository from the frozen BOOT topology to an M0
execution-control topology. It does not create M0 runtime packages or product
behavior.

## Guardrail Model

M0 implementation packages are outer implementation surfaces. They must not
become dependencies of `curios_contracts` or `curios_core`.

The initial M0 implementation package roots are planned but not currently
authorized as tracked package roots, except TASK-M0-002's persistence package
after the TASK-M0-002 transition, TASK-M0-003's policy package after the
TASK-M0-003 transition, and TASK-M0-004's event/evidence runtime store package
after the TASK-M0-004 transition:

| Task | Planned Surface |
| --- | --- |
| TASK-M0-002 | `packages/python/curios_persistence/**` (authorized by TASK-M0-002) |
| TASK-M0-003 | `packages/python/curios_policy/**` (authorized by TASK-M0-003) |
| TASK-M0-004 | `packages/python/curios_runtime/**` event/evidence modules only (authorized by TASK-M0-004) |
| TASK-M0-005 through TASK-M0-007 | `packages/python/curios_runtime/**` downstream modules blocked until their owning tasks |

TASK-M0-001 establishes architecture tests that already block inward imports or
metadata dependencies from contracts/core to those implementation packages.
Later tasks must still explicitly authorize their own package roots through the
security topology before adding implementation.

## Preserved Boundaries

- `curios_contracts` remains canonical semantic authority.
- `curios_core` remains inward-facing and does not depend on runtime,
  persistence, policy, provider, API, web, infrastructure, or framework
  implementations.
- Provider packages, FastAPI, and the web remain outer surfaces.
- `ObjectReference` remains the single generic reference abstraction.
- No new canonical contract, generic reference, runtime service, scheduler,
  event store, persistence repository, API route, or web console is introduced
  by TASK-M0-001.

## Deferred Architecture

TASK-M0-001 does not authorize:

- DAG scheduler/runtime;
- multi-agent runtime;
- model generation or routing;
- knowledge or memory runtime;
- DataLab;
- learning or self-improvement;
- production IAM;
- full policy language;
- secret resolver;
- external brokers;
- cloud infrastructure;
- live LLM quality gates.
