---
id: M2-EVIDENCE-LIFECYCLE-CONVENTIONS
title: M2 Evidence and Lifecycle Conventions
lifecycle: FROZEN
artifact_type: lifecycle_convention
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Evidence and Lifecycle Conventions

## Lifecycle

M2 follows the frozen Build Pack lifecycle:

```text
DEFINED -> SPECIFIED -> IMPLEMENTING -> IMPLEMENTED -> TESTED -> VALIDATED -> FROZEN
```

Planning artifacts may become `VALIDATED / FROZEN` only through independent
readiness validation. Implementation tasks may not self-declare validation or
freeze.

## Evidence Records

Each modifying `TASK-M2-*` implementation must create or update a task evidence
record under `docs/tasks/` with:

- baseline SHA;
- task objective;
- prerequisites;
- changed files;
- authorized vs prohibited surfaces;
- implementation summary;
- verification commands and counts;
- Docker/PostgreSQL or local transient evidence if relevant;
- warnings/skips;
- final worktree status;
- downstream consequence.

Independent validation must create a separate validation/freeze evidence record
when repository precedent requires it.

## Required Gate Types

M2 lifecycle must include:

- implementation;
- independent validation/freeze;
- local integration;
- publication;
- exact-SHA remote CI verification;
- milestone acceptance;
- independent milestone verification;
- final freeze.

## No Shortcut Rule

M2 does not become complete because tests pass locally. It requires the full
lifecycle chain through publication, remote CI, independent verification, and
final freeze.

## Historical Input Handling

`1.txt` remains unmodified historical input. Accepted requirements must be
copied only into reviewed M2 artifacts with traceability. Unaccepted historical
ideas remain deferred.

## Evidence Boundaries

M2 evidence must distinguish:

- product defects;
- planning defects;
- test defects;
- environment/tooling transients;
- known local Docker/PostgreSQL lifecycle instability;
- resolved historical failures.

Do not hide failing evidence by weakening a gate or broadening authority.
