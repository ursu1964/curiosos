---
id: MILESTONE-M1-IMPLEMENTATION-DAG
title: M1 Implementation DAG
lifecycle: FROZEN
artifact_type: implementation_dag
authority: program_planning
milestone_id: M1
date: 2026-09-23
---

# M1 Implementation DAG

## Dependency Graph

```text
M0
  -> M1-000A
      -> M1-READINESS
          -> TASK-M1-001

TASK-M1-001
  -> TASK-M1-002
  -> TASK-M1-005
  -> TASK-M1-006
  -> TASK-M1-009

TASK-M1-002
  -> TASK-M1-003
  -> TASK-M1-004

TASK-M1-005 + TASK-M1-006
  -> TASK-M1-007

TASK-M1-003 + TASK-M1-004 + TASK-M1-005 + TASK-M1-007
  -> TASK-M1-008

TASK-M1-008 + TASK-M1-009
  -> TASK-M1-010

TASK-M1-004 + TASK-M1-007 + TASK-M1-008 + TASK-M1-010
  -> TASK-M1-011

TASK-M1-011
  -> TASK-M1-012

TASK-M1-011 + TASK-M1-012
  -> TASK-M1-013
      -> TASK-M1-014
          -> TASK-M1-015
              -> TASK-M1-016
                  -> TASK-M1-017
                      -> TASK-M1-018
                          -> TASK-M1-019
```

## Routing Dependency Decision

The proposed relationship `TASK-M1-008 -> TASK-M1-009 -> TASK-M1-010` is not
frozen. M1 resolves it as:

```text
TASK-M1-008 executor seam
TASK-M1-009 model/profile discovery
        \       /
         v     v
TASK-M1-010 routing decision records
```

`TASK-M1-009` can proceed independently after topology authorization because it
owns profile discovery only. `TASK-M1-010` consumes both executor choices and
model/profile candidates. M1 does not authorize model generation.

## Parallel Groups

| Group | Units | Purpose |
| --- | --- | --- |
| PG-M1-00 | M1-000A, M1-READINESS | M1 milestone definition, executable task pack, and independent readiness validation. |
| PG-M1-01 | TASK-M1-001 | M1 topology and guardrail transition. |
| PG-M1-02A | TASK-M1-002, TASK-M1-005, TASK-M1-006, TASK-M1-009 | Cognitive contracts, capability resolver, agent contracts/repository planning, and model/profile discovery may proceed after topology. |
| PG-M1-02B | TASK-M1-003, TASK-M1-004 | Intent decomposition and DAG records both consume cognitive contracts. |
| PG-M1-03 | TASK-M1-007 | Agent lifecycle repository consumes capability and agent foundations. |
| PG-M1-04 | TASK-M1-008 | Executor seam consumes decomposition, DAG, capability, and agent lifecycle boundaries. |
| PG-M1-05 | TASK-M1-010 | Routing decision records consume executor seam and model/profile discovery. |
| PG-M1-06 | TASK-M1-011 | Bounded DAG runner consumes DAG, agent lifecycle, executor, and routing decisions. |
| PG-M1-07 | TASK-M1-012 | Verification loop consumes runner outcomes. |
| PG-M1-08 | TASK-M1-013 | API observation/control surface. |
| PG-M1-09 | TASK-M1-014 | Web cognitive-loop console. |
| PG-M1-10 | TASK-M1-015 | M1 integration tests. |
| PG-M1-11 | TASK-M1-016 | M1 CI update. |
| PG-M1-12 | TASK-M1-017 | M1 acceptance suite. |
| PG-M1-13 | TASK-M1-018 | Independent M1 verification. |
| PG-M1-14 | TASK-M1-019 | Final M1 freeze. |

## Execution Waves

| Wave | Units | Start Condition |
| --- | --- | --- |
| M1-WAVE-00 | M1-000A, M1-READINESS | M0 final baseline exists. |
| M1-WAVE-01 | TASK-M1-001 | M1 readiness validation passes. |
| M1-WAVE-02 | TASK-M1-002, TASK-M1-005, TASK-M1-006, TASK-M1-009 | TASK-M1-001 validated, frozen, and integrated. |
| M1-WAVE-03 | TASK-M1-003, TASK-M1-004 | TASK-M1-002 validated, frozen, and integrated. |
| M1-WAVE-04 | TASK-M1-007 | TASK-M1-005 and TASK-M1-006 validated, frozen, and integrated. |
| M1-WAVE-05 | TASK-M1-008 | TASK-M1-003, TASK-M1-004, TASK-M1-005, and TASK-M1-007 validated, frozen, and integrated. |
| M1-WAVE-06 | TASK-M1-010 | TASK-M1-008 and TASK-M1-009 validated, frozen, and integrated. |
| M1-WAVE-07 | TASK-M1-011 | TASK-M1-004, TASK-M1-007, TASK-M1-008, and TASK-M1-010 validated, frozen, and integrated. |
| M1-WAVE-08 | TASK-M1-012 | TASK-M1-011 validated, frozen, and integrated. |
| M1-WAVE-09 | TASK-M1-013 | TASK-M1-011 and TASK-M1-012 validated, frozen, and integrated. |
| M1-WAVE-10 | TASK-M1-014 | TASK-M1-013 validated, frozen, and integrated. |
| M1-WAVE-11 | TASK-M1-015 | TASK-M1-013 and TASK-M1-014 validated, frozen, and integrated. |
| M1-WAVE-12 | TASK-M1-016 | TASK-M1-015 validated, frozen, and integrated. |
| M1-WAVE-13 | TASK-M1-017 | TASK-M1-016 validated, frozen, and integrated. |
| M1-WAVE-14 | TASK-M1-018 | TASK-M1-017 validated, frozen, and integrated. |
| M1-WAVE-15 | TASK-M1-019 | TASK-M1-018 validated, frozen, and integrated. |

## Program Gates

| Gate | Inputs | PASS Criteria |
| --- | --- | --- |
| M1-READINESS | M1-000A | Planning artifacts are complete, acyclic, scoped, and honest about authority. |
| M1-COGNITIVE-CONTRACTS | TASK-M1-002 | Cognitive contracts extend BOOT/M0 without duplicating canonical work/execution/capability/agent contracts. |
| M1-DAG-CAPABILITY-AGENT-INTEGRATION | TASK-M1-003 through TASK-M1-007 | Intent decomposition, DAG records, capability matching, and agent lifecycle coexist without semantic overlap. |
| M1-RUNTIME-ROUTING-INTEGRATION | TASK-M1-008 through TASK-M1-011 | Executor seam, model/profile discovery, routing decisions, and bounded DAG runner interoperate deterministically. |
| M1-API-WEB-INTEGRATION | TASK-M1-013, TASK-M1-014 | API/web display recorded M1 truth and do not become semantic authority. |
| M1-INTEGRATION | TASK-M1-015 | Vertical-slice integration tests pass. |
| M1-CI | TASK-M1-016 | CI invokes M1 deterministic gates without weakening M0 gates. |
| M1-ACCEPTANCE | TASK-M1-017 | VS-M1-001 through VS-M1-006 pass. |
| M1-VERIFY | TASK-M1-018 | Independent verification accepts complete M1 baseline. |
| M1-FREEZE | TASK-M1-019 | Final M1 status/freeze closure passes. |

## Vertical Slices

| Slice | Producing Tasks | Scenario |
| --- | --- | --- |
| VS-M1-001 Intent to DAG | TASK-M1-002, TASK-M1-003, TASK-M1-004, TASK-M1-013 | Submit a simple intent and observe persisted intent/problem/plan records plus an acyclic work DAG. |
| VS-M1-002 Capability to Agent Assignment | TASK-M1-005, TASK-M1-006, TASK-M1-007 | Deterministically match task capability requirements to a disposable agent instance. |
| VS-M1-003 Bounded Parallel Execution | TASK-M1-008, TASK-M1-010, TASK-M1-011 | Execute independent DAG nodes up to a fixed concurrency limit while dependent nodes wait. |
| VS-M1-004 Routing Decision Record | TASK-M1-009, TASK-M1-010 | Record deterministic/no-model or profile-only route decisions without live generation. |
| VS-M1-005 Verification-Gated Completion | TASK-M1-012 | Completion requires verification evidence, not executor self-report. |
| VS-M1-006 Recorded-Truth Presentation | TASK-M1-013, TASK-M1-014 | API/web display persisted cognitive/DAG/agent/routing/verification truth. |

## No Circular Dependencies

The graph is layered from topology to contracts, DAG/capability/agent
foundations, runtime/routing, API/web, integration, CI, acceptance, independent
verification, and final freeze. No task depends on a downstream task.
