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
      -> M0-READINESS
          -> TASK-M0-001
              -> TASK-M0-002
              -> TASK-M0-003

TASK-M0-002
  -> TASK-M0-005
  -> TASK-M0-004

TASK-M0-003
  -> TASK-M0-006

TASK-M0-004
  -> TASK-M0-006

TASK-M0-005
  -> TASK-M0-006

TASK-M0-006
  -> TASK-M0-007

TASK-M0-007
  -> TASK-M0-008

TASK-M0-008
  -> TASK-M0-009

TASK-M0-008 + TASK-M0-009
  -> TASK-M0-010
      -> TASK-M0-011
          -> TASK-M0-012
              -> TASK-M0-013
                  -> TASK-M0-014
```

## Parallel Groups

| Group | Tasks | Purpose |
| --- | --- | --- |
| PG-M0-00 | M0-000A, M0-READINESS | M0 milestone definition, executable task pack, and independent readiness validation. |
| PG-M0-01 | TASK-M0-001 | M0 topology, architecture, and security transition after readiness passes. |
| PG-M0-02A | TASK-M0-002, TASK-M0-003 | Persistence and policy foundations may proceed in parallel after topology authorization. |
| PG-M0-02B | TASK-M0-004, TASK-M0-005 | Event/evidence store and work repositories may proceed in parallel only after persistence exists. |
| PG-M0-03 | TASK-M0-006 | Runtime service integrates persistence, policy, event/evidence, and work state boundaries. |
| PG-M0-04 | TASK-M0-007 | Provider-inventory executor synchronization point. |
| PG-M0-05A | TASK-M0-008 | API work endpoints expose the frozen runtime/provider-inventory boundary. |
| PG-M0-05B | TASK-M0-009 | Web work console consumes the M0 API endpoint contract after it exists. |
| PG-M0-06 | TASK-M0-010 | M0 integration tests. |
| PG-M0-07 | TASK-M0-011 | M0 CI quality gate update. |
| PG-M0-08 | TASK-M0-012 | M0 acceptance suite. |
| PG-M0-09 | TASK-M0-013 | Independent M0 verification record. |
| PG-M0-10 | TASK-M0-014 | M0 final freeze/status-ledger update. |

## Execution Waves

| Wave | Units | Start Condition | Notes |
| --- | --- | --- | --- |
| M0-WAVE-00 | M0-000A, M0-READINESS | BOOT-000 final baseline exists. | Planning and independent readiness validation only. |
| M0-WAVE-01 | TASK-M0-001 | M0 readiness validation passes. | No runtime implementation; topology/guardrails only. |
| M0-WAVE-02 | TASK-M0-002, TASK-M0-003 | TASK-M0-001 is validated, frozen, and integrated. | Persistence and policy can proceed independently. |
| M0-WAVE-03 | TASK-M0-004, TASK-M0-005 | TASK-M0-002 is validated, frozen, and integrated. | Both consume persistence; neither consumes the policy evaluator. |
| M0-WAVE-04 | TASK-M0-006 | TASK-M0-003, TASK-M0-004, and TASK-M0-005 are validated, frozen, and integrated. | Runtime service consumes policy, event/evidence, and work repository boundaries. |
| M0-WAVE-05 | TASK-M0-007 | TASK-M0-006 is validated, frozen, and integrated. | Provider-inventory executor consumes the runtime service boundary. |
| M0-WAVE-06 | TASK-M0-008 | TASK-M0-007 is validated, frozen, and integrated. | API establishes the M0 work route contract. |
| M0-WAVE-07 | TASK-M0-009 | TASK-M0-008 is validated, frozen, and integrated. | Web consumes the API contract; it is not parallel with API implementation. |
| M0-WAVE-08 | TASK-M0-010 | TASK-M0-008 and TASK-M0-009 are validated, frozen, and integrated. | Integration tests prove the integrated runtime/API/web baseline. |
| M0-WAVE-09 | TASK-M0-011 | TASK-M0-010 is validated, frozen, and integrated. | CI adds M0 checks after integration tests exist. |
| M0-WAVE-10 | TASK-M0-012 | TASK-M0-011 is validated, frozen, and integrated. | Acceptance suite runs under the updated quality gate model. |
| M0-WAVE-11 | TASK-M0-013 | TASK-M0-012 is validated, frozen, and integrated. | Independent verification of the complete M0 baseline. |
| M0-WAVE-12 | TASK-M0-014 | TASK-M0-013 is validated, frozen, and integrated. | Final freeze/status closure. |

## Integration Gates

| Gate | Inputs | Entry Condition | PASS Criteria |
| --- | --- | --- | --- |
| M0-READINESS | M0-000A | Corrected M0 planning artifacts are committed. | M0 definition, task pack, DAG, ledger, and traceability artifacts are internally consistent. |
| M0-PG-02A-INTEGRATION | TASK-M0-002, TASK-M0-003 | TASK-M0-002 and TASK-M0-003 are implemented/tested from the same frozen topology baseline. | Persistence and policy foundations coexist without contract, topology, or security drift. |
| M0-PG-02B-INTEGRATION | TASK-M0-004, TASK-M0-005 | TASK-M0-002 is validated/frozen/integrated and TASK-M0-004/005 are implemented/tested. | Event/evidence and work repository foundations consume the persistence foundation without redefining canonical contracts. |
| M0-RUNTIME-INTEGRATION | TASK-M0-006, TASK-M0-007 | TASK-M0-003/004/005 are validated/frozen/integrated and TASK-M0-006/007 are implemented/tested in order. | Work lifecycle, policy, event/evidence, and provider inventory executor interoperate deterministically. |
| M0-API-INTEGRATION | TASK-M0-008 | TASK-M0-007 is validated/frozen/integrated and TASK-M0-008 is implemented/tested. | API endpoints expose recorded runtime truth without redefining canonical semantics. |
| M0-WEB-INTEGRATION | TASK-M0-009 | TASK-M0-008 is validated/frozen/integrated and TASK-M0-009 is implemented/tested. | Web consumes only M0 API routes and does not become semantic authority. |
| M0-ACCEPTANCE | TASK-M0-010, TASK-M0-011, TASK-M0-012 | TASK-M0-010/011/012 are implemented/tested in order after API/web integration. | M0 integration, CI, and acceptance checks pass. |
| M0-VERIFY | TASK-M0-013 | TASK-M0-012 is validated/frozen/integrated. | Independent verification accepts the complete M0 baseline. |
| M0-FREEZE | TASK-M0-014 | TASK-M0-013 is validated/frozen/integrated. | M0 final status ledger and freeze record are approved. |

## Vertical Slices

| Slice | Proved By | Scenario |
| --- | --- | --- |
| VS-M0-001 Provider Inventory Work | TASK-M0-002, TASK-M0-004, TASK-M0-005, TASK-M0-006, TASK-M0-007, TASK-M0-008, TASK-M0-010 | Submit a READ_ONLY provider-inventory work item, execute it once, persist the result, and observe completion. Evidence is produced at M0-RUNTIME-INTEGRATION and M0-ACCEPTANCE. |
| VS-M0-002 Policy Denial / Unknown Safety | TASK-M0-003, TASK-M0-006, TASK-M0-008, TASK-M0-010 | Submit a governed unsupported effect and verify execution does not proceed when policy denies or cannot decide. Evidence is produced at M0-RUNTIME-INTEGRATION and M0-ACCEPTANCE. |
| VS-M0-003 Runtime Truth After Disposal | TASK-M0-002, TASK-M0-004, TASK-M0-005, TASK-M0-010 | Re-read work, execution, event, evidence, and result facts from PostgreSQL after runtime objects are disposed. Evidence is produced at M0-PG-02B-INTEGRATION and M0-ACCEPTANCE. |
| VS-M0-004 Web/API Observability | TASK-M0-008, TASK-M0-009, TASK-M0-012 | Web consumes only API routes and displays recorded work/execution state and evidence. Evidence is produced at M0-WEB-INTEGRATION and M0-ACCEPTANCE. |

## No Circular Dependencies

The DAG is intentionally layered:

1. Planning.
2. Independent readiness validation.
3. Topology authorization.
4. Persistence and policy foundations.
5. Event/evidence and work repository foundations.
6. Runtime service.
7. Provider-inventory executor.
8. API then web surfaces.
9. Integration, CI, acceptance, independent verification, freeze.

No task depends on a downstream task.
