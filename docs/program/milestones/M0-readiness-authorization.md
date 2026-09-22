---
id: M0-READINESS-AUTHORIZATION
title: M0 Readiness and First Execution Authorization
lifecycle: SPECIFIED
artifact_type: readiness_record
authority: program_planning
milestone_id: M0
date: 2026-09-22
---

# M0 Readiness and First Execution Authorization

## Readiness Decision

M0 EXECUTION AUTHORIZED:

`TASK-M0-001 — M0 Topology and Guardrail Transition`

Only this task is ready from the frozen BOOT baseline plus M0 planning
authority. No other M0 implementation task may start until TASK-M0-001 is
implemented, tested, independently validated, frozen, and integrated.

## Prerequisites

| Prerequisite | Status |
| --- | --- |
| BOOT-000 `VALIDATED, FROZEN` | SATISFIED |
| main synchronized with `origin/main` at BOOT final baseline | SATISFIED |
| M0 milestone definition exists | SATISFIED by M0-000A artifacts |
| M0 task pack exists | SATISFIED by `docs/tasks/M0-task-pack.md` |
| M0 DAG exists | SATISFIED by `docs/program/milestones/M0-implementation-dag.md` |
| M0 status ledger exists | SATISFIED by `docs/program/status-ledger/M0-status-ledger.md` |
| P1-P6 traceability limits documented | SATISFIED by `docs/program/milestones/M0-p1-p6-traceability.md` |

## First Task Scope

TASK-M0-001 may create or modify only the surfaces needed to authorize M0
topology and guardrails:

- M0 task evidence under `docs/tasks/**`.
- M0 status updates under `docs/program/status-ledger/**`.
- M0 architecture/security planning docs under `docs/program/milestones/**` or
  `docs/architecture/**` if needed.
- `tests/security/**` and `tests/architecture/**` to extend topology and
  dependency-direction guards.
- Root workspace metadata only if placeholder package membership is required
  for exact M0 topology checks.

TASK-M0-001 must not implement runtime behavior, persistence schemas, API
routes, web UI, policy evaluation, event stores, provider execution, or M1+
features.

## Recommended Branch / Worktree

```text
branch:   task/m0-001-topology-guardrails
worktree: /home/user/projects/curiosos-wt-m0-001
base:     current main after committing M0-000A
```

## Parallelism

No parallel M0 implementation task is authorized before TASK-M0-001 completes.

After TASK-M0-001 is validated/frozen, the DAG allows parallel preparation of
TASK-M0-002 and TASK-M0-003. TASK-M0-004 depends on TASK-M0-002 in addition to
TASK-M0-001.

## Authorization Limits

This record does not authorize:

- TASK-M0-002 or later.
- post-M0 or M1 work.
- runtime/product implementation outside TASK-M0-001 scope.
- broad security topology relaxation.
