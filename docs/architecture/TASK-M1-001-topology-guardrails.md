---
id: TASK-M1-001-ARCHITECTURE-GUARDRAILS
title: TASK-M1-001 M1 Topology Architecture Guardrails
lifecycle: IMPLEMENTED
artifact_type: architecture_guardrail
authority: implementation
task_id: TASK-M1-001
milestone_id: M1
date: 2026-09-23
---

# TASK-M1-001 M1 Topology Architecture Guardrails

## Purpose

TASK-M1-001 transitions the repository from the frozen BOOT+M0 topology to an
M1 execution-control topology. It does not create cognitive contracts, runtime
packages, model/profile discovery, API routes, web UI, or product behavior.

## Guardrail Model

M1 implementation surfaces are planned but not currently authorized as tracked
implementation files. The frozen rule remains:

Each task authorizes only its explicit new surface.

M1 planning names broad ownership categories rather than final package names
for several future tasks. TASK-M1-001 therefore records task-owned categories
without promoting representative package names into executable authority.

## Planned M1 Ownership

| Task | Planned Ownership |
| --- | --- |
| TASK-M1-002 | cognitive intent/problem/assumption/decision/plan contracts |
| TASK-M1-003 | deterministic intent decomposition implementation |
| TASK-M1-004 | bounded work-DAG records and state |
| TASK-M1-005 | capability resolver foundation |
| TASK-M1-006 | agent definition and instance persistence |
| TASK-M1-007 | agent lifecycle repository and events |
| TASK-M1-008 | executor seam and deterministic executors |
| TASK-M1-009 | model/profile discovery records only |
| TASK-M1-010 | routing decision records |
| TASK-M1-011 | bounded local DAG runner |
| TASK-M1-012 | verification loop and evidence binding |
| TASK-M1-013 | exact M1 API cognitive-loop endpoints |
| TASK-M1-014 | exact M1 web cognitive-loop console |
| TASK-M1-015 | exact M1 integration test surface |
| TASK-M1-016 | exact M1 CI workflow update |
| TASK-M1-017 | exact M1 acceptance test surface |

Those categories remain planned until their owning task validates, freezes, and
integrates the exact repository surface.

TASK-M1-001 also freezes the current public `curios_contracts` canonical
authority inventory. A future task must explicitly update that inventory before
adding public contract declarations, schema fields, enum/vocabulary members,
type aliases, factories/functions, or package-level exports.

## Preserved Architecture

- `curios_contracts` remains canonical semantic authority.
- `curios_core` remains inward-facing and does not depend on persistence,
  policy, runtime, provider, API, web, infrastructure, framework, or planned M1
  implementation roots.
- M0 implementation packages remain outer implementation packages.
- FastAPI and web remain outer adapter surfaces.
- `ObjectReference` remains the single generic reference abstraction.
- Agent contracts remain the frozen BOOT contracts until TASK-M1-006 and
  TASK-M1-007 authorize persistence and lifecycle behavior.
- Model/profile discovery remains profile-only planning; generation,
  inference, router optimization, and live-model quality gates remain outside
  M1.

## New Architecture Checks

TASK-M1-001 extends architecture tests so `curios_contracts` and `curios_core`
cannot import or depend on representative M1 implementation roots. The
detector is intentionally structural and works even while those future packages
are absent.

Security topology tests provide the companion canonical-authority guard for
`curios_contracts`: the current module declaration inventory and
package-export inventory are exact. Package exports include a lossless ordered
inventory of `__init__.py` import statements, so duplicate imports, aliases,
plain imports, assignment aliases, and `__all__` changes are treated as
authority transitions. Planned M1 concepts remain registered as future
ownership only.

TASK-M1-001 does not authorize:

- new cognitive contract files;
- new cognitive contract classes, enums, type aliases, factories, fields, or
  package exports inside existing contract files;
- new runtime modules;
- new executor or tool framework modules;
- scheduler/DAG production runtime;
- model generation or router optimization;
- API or web M1 surfaces;
- M1 integration, CI, acceptance, verification, or freeze implementation.
