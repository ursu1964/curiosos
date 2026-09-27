---
id: MILESTONE-M2-IMPLEMENTATION-DAG
title: M2 Implementation DAG
lifecycle: FROZEN
artifact_type: implementation_dag
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Implementation DAG

## Dependency Graph

```text
M1 final freeze
  -> M2-000A
      -> M2-READINESS
          -> TASK-M2-001

TASK-M2-001
  -> TASK-M2-002

TASK-M2-002
  -> TASK-M2-003
  -> TASK-M2-004
  -> TASK-M2-005
  -> TASK-M2-006
  -> TASK-M2-008

TASK-M2-006 + TASK-M2-003
  -> TASK-M2-007

TASK-M2-004 + TASK-M2-005 + TASK-M2-007 + TASK-M2-008
  -> TASK-M2-009
      -> TASK-M2-010
          -> TASK-M2-011
              -> TASK-M2-012
                  -> TASK-M2-013
                      -> TASK-M2-014
                          -> TASK-M2-015
                              -> TASK-M2-016
```

## Planning Nodes And Task Count

M2 contains one planning package node, one readiness gate node, and sixteen
implementation/lifecycle tasks:

- `M2-000A`: planning package node. It is not a `TASK-M2-*`
  implementation task and does not count in the task count.
- `M2-READINESS`: planning validation/readiness gate. It is not a
  `TASK-M2-*` implementation task and does not count in the task count.
- `TASK-M2-001` through `TASK-M2-016`: implementation/lifecycle tasks.

Exact `TASK-M2-*` count: `16`.

## Node Semantics

| Node | Type | Prerequisites | Lifecycle owner | Counts as TASK-M2? | Implementation-bearing? | Validation/freeze required? |
| --- | --- | --- | --- | --- | --- | --- |
| `M2-000A` | Planning package | M1 final freeze | POST-M1 planning operation | No | No product/test/CI implementation | Yes, through POST-M1 readiness validation. |
| `M2-READINESS` | Planning gate | M2-000A | Independent planning validation | No | No product/test/CI implementation | Yes, it must pass before TASK-M2-001 can become READY. |
| `TASK-M2-001`..`TASK-M2-016` | M2 task | As listed below | Individual task evidence/validation lifecycle | Yes | Yes, except verification/freeze record tasks are documentation-only by specification. | Yes, each follows implementation, independent validation/freeze, integration, publication, and remote-CI verification where applicable. |

## Parallel Groups

| Group | Units | Purpose |
| --- | --- | --- |
| PG-M2-00 | M2-000A, M2-READINESS | M2 planning package and independent readiness validation. |
| PG-M2-01 | TASK-M2-001 | Topology, architecture, and security guardrail transition. |
| PG-M2-02 | TASK-M2-002 | DataLab contracts. |
| PG-M2-03A | TASK-M2-003, TASK-M2-004, TASK-M2-005, TASK-M2-006, TASK-M2-008 | Dataset intake, deterministic decomposition, persistence, profiler seam, capability/agent integration after contracts. |
| PG-M2-03B | TASK-M2-007 | Deterministic in-process profiler after the seam and intake boundary. |
| PG-M2-04 | TASK-M2-009 | Runner and verification binding. |
| PG-M2-05 | TASK-M2-010 | DataLab API. |
| PG-M2-06 | TASK-M2-011 | Focused DataLab web workspace. |
| PG-M2-07 | TASK-M2-012 | M2 vertical-slice integration tests. |
| PG-M2-08 | TASK-M2-013 | M2 CI quality-gate update. |
| PG-M2-09 | TASK-M2-014 | M2 acceptance suite. |
| PG-M2-10 | TASK-M2-015 | Independent M2 verification record. |
| PG-M2-11 | TASK-M2-016 | Final M2 freeze. |

## Execution Waves

| Wave | Units | Start Condition |
| --- | --- | --- |
| M2-WAVE-00 | M2-000A, M2-READINESS | M1 final freeze is published and remote-CI-verified. |
| M2-WAVE-01 | TASK-M2-001 | M2 readiness validation passes. |
| M2-WAVE-02 | TASK-M2-002 | TASK-M2-001 validated, frozen, and integrated. |
| M2-WAVE-03 | TASK-M2-003, TASK-M2-004, TASK-M2-005, TASK-M2-006, TASK-M2-008 | TASK-M2-002 validated, frozen, and integrated. |
| M2-WAVE-04 | TASK-M2-007 | TASK-M2-003 and TASK-M2-006 validated, frozen, and integrated. |
| M2-WAVE-05 | TASK-M2-009 | TASK-M2-004, TASK-M2-005, TASK-M2-007, and TASK-M2-008 validated, frozen, and integrated. |
| M2-WAVE-06 | TASK-M2-010 | TASK-M2-009 validated, frozen, and integrated. |
| M2-WAVE-07 | TASK-M2-011 | TASK-M2-010 validated, frozen, and integrated. |
| M2-WAVE-08 | TASK-M2-012 | TASK-M2-010 and TASK-M2-011 validated, frozen, and integrated. |
| M2-WAVE-09 | TASK-M2-013 | TASK-M2-012 validated, frozen, and integrated. |
| M2-WAVE-10 | TASK-M2-014 | TASK-M2-013 validated, frozen, and integrated. |
| M2-WAVE-11 | TASK-M2-015 | TASK-M2-014 validated, frozen, and integrated. |
| M2-WAVE-12 | TASK-M2-016 | TASK-M2-015 validated, frozen, and integrated. |

## Program Gates

| Gate | Inputs | PASS Criteria |
| --- | --- | --- |
| M2-READINESS | M2-000A | Planning artifacts are complete, acyclic, scoped, bounded, and honest about authority. |
| M2-DATALAB-CONTRACTS | TASK-M2-002 | Contracts reuse BOOT/M1 primitives and do not duplicate WorkItem, Result, EvidenceReference, ArtifactReference, VerificationReference, Capability, or AgentInstance. |
| M2-DATASET-BOUNDARY | TASK-M2-003 | Upload, validation, integrity, metadata, and safe-error rules are enforced without arbitrary file authority. |
| M2-PROFILER-BOUNDARY | TASK-M2-006, TASK-M2-007 | Deterministic profiler is in-process, bounded, no-network, no-subprocess, and evidence-producing. |
| M2-DATALAB-RUNTIME | TASK-M2-004, TASK-M2-005, TASK-M2-008, TASK-M2-009 | Decomposition, persistence, capability/agent assignment, runner, and verification interoperate as recorded truth. |
| M2-API-WEB | TASK-M2-010, TASK-M2-011 | DataLab API/web display persisted recorded truth through explicit API-boundary capabilities. |
| M2-INTEGRATION | TASK-M2-012 | VS-M2-001 through VS-M2-006 integration tests pass. |
| M2-CI | TASK-M2-013 | CI invokes M2 deterministic gates without weakening BOOT/M0/M1 gates. |
| M2-ACCEPTANCE | TASK-M2-014 | VS-M2-001 through VS-M2-006 pass milestone acceptance. |
| M2-VERIFY | TASK-M2-015 | Independent verification accepts complete M2 baseline. |
| M2-FREEZE | TASK-M2-016 | Final M2 status/freeze closure passes. |

## No Circular Dependencies

The graph is layered from readiness and topology to contracts, data/tool
foundations, runtime, API/web, integration, CI, acceptance, independent
verification, and final freeze. No task depends on a downstream task.
