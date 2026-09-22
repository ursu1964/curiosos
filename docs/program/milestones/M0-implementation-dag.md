---
id: MILESTONE-M0-IMPLEMENTATION-DAG
title: M0 Implementation DAG
lifecycle: SPECIFIED
artifact_type: implementation_dag
authority: program_planning
milestone_id: M0
date: 2026-09-22
---

# M0 Implementation DAG

## Dependency Graph

```text
BOOT-000
  -> M0-000A
      -> TASK-M0-001
          -> TASK-M0-002
          -> TASK-M0-003
          -> TASK-M0-004

TASK-M0-002
  -> TASK-M0-005

TASK-M0-003
  -> TASK-M0-006

TASK-M0-004
  -> TASK-M0-006

TASK-M0-005 + TASK-M0-006
  -> TASK-M0-007
      -> TASK-M0-008
      -> TASK-M0-009

TASK-M0-007 + TASK-M0-008 + TASK-M0-009
  -> TASK-M0-010
      -> TASK-M0-011
          -> TASK-M0-012
              -> TASK-M0-013
                  -> TASK-M0-014
```

## Parallel Groups

| Group | Tasks | Purpose |
| --- | --- | --- |
| PG-M0-00 | M0-000A | M0 milestone definition and executable task pack. |
| PG-M0-01 | TASK-M0-001 | M0 topology, architecture, and security transition. |
| PG-M0-02 | TASK-M0-002, TASK-M0-003, TASK-M0-004 | Persistence, policy, and event/evidence foundations may proceed in parallel after topology authorization. |
| PG-M0-03 | TASK-M0-005, TASK-M0-006 | Work repository and runtime service foundations integrate persistence, policy, and events. |
| PG-M0-04 | TASK-M0-007 | Provider-inventory executor synchronization point. |
| PG-M0-05 | TASK-M0-008, TASK-M0-009 | API and web surfaces may proceed in parallel after the runtime/provider-inventory boundary is stable. |
| PG-M0-06 | TASK-M0-010 | M0 integration tests. |
| PG-M0-07 | TASK-M0-011 | M0 CI quality gate update. |
| PG-M0-08 | TASK-M0-012 | M0 acceptance suite. |
| PG-M0-09 | TASK-M0-013 | Independent M0 verification record. |
| PG-M0-10 | TASK-M0-014 | M0 final freeze/status-ledger update. |

## Integration Gates

| Gate | Inputs | PASS Criteria |
| --- | --- | --- |
| M0-READINESS | M0-000A | M0 definition, task pack, DAG, ledger, and traceability artifacts are internally consistent. |
| M0-PG-02-INTEGRATION | TASK-M0-002, TASK-M0-003, TASK-M0-004 | Persistence, policy, and event/evidence foundations coexist without contract or topology drift. |
| M0-RUNTIME-INTEGRATION | TASK-M0-005, TASK-M0-006, TASK-M0-007 | Work lifecycle, policy, event/evidence, and provider inventory executor interoperate deterministically. |
| M0-API-WEB-INTEGRATION | TASK-M0-008, TASK-M0-009 | API and web surfaces expose recorded runtime truth without redefining canonical semantics. |
| M0-ACCEPTANCE | TASK-M0-010, TASK-M0-011, TASK-M0-012 | M0 integration, CI, and acceptance checks pass. |
| M0-VERIFY | TASK-M0-013 | Independent verification accepts the complete M0 baseline. |
| M0-FREEZE | TASK-M0-014 | M0 final status ledger and freeze record are approved. |

## Vertical Slices

| Slice | Proved By | Scenario |
| --- | --- | --- |
| VS-M0-001 Provider Inventory Work | TASK-M0-005 through TASK-M0-010 | Submit a READ_ONLY provider-inventory work item, execute it once, persist the result, and observe completion. |
| VS-M0-002 Policy Denial / Unknown Safety | TASK-M0-003, TASK-M0-006, TASK-M0-010 | Submit a governed unsupported effect and verify execution does not proceed when policy denies or cannot decide. |
| VS-M0-003 Runtime Truth After Disposal | TASK-M0-002, TASK-M0-005, TASK-M0-010 | Re-read work, execution, event, evidence, and result facts from PostgreSQL after runtime objects are disposed. |
| VS-M0-004 Web/API Observability | TASK-M0-008, TASK-M0-009, TASK-M0-012 | Web consumes only API routes and displays recorded work/execution state and evidence. |

## No Circular Dependencies

The DAG is intentionally layered:

1. Planning.
2. Topology authorization.
3. Persistence, policy, and event/evidence foundations.
4. Work runtime.
5. Provider-inventory executor.
6. API and web surfaces.
7. Integration, CI, acceptance, independent verification, freeze.

No task depends on a downstream task.
