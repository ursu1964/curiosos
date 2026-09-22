---
id: M0-P1-P6-TRACEABILITY
title: M0 P1-P6 Traceability Record
lifecycle: SPECIFIED
artifact_type: traceability_record
authority: program_planning
milestone_id: M0
date: 2026-09-22
---

# M0 P1-P6 Traceability Record

## Traceability Limits

Tracked repository artifacts identify P1-P6 architecture/specification work and
Phase 0 Reconstruction & Reconciliation as authority sources, but the detailed
P1-P6 artifacts are not present in the tracked repository.

Therefore, this record cannot honestly map individual P1 requirements,
P2 decomposition, P3 invariants, P4 implementation architecture, P5 executable
specification, or P6 reconciled implementation order to M0 tasks.

## Available Evidence

| Evidence | Classification | Traceability Use |
| --- | --- | --- |
| Historical source note | FROZEN AUTHORITY for source handling | Establishes that P1-P6 are authority sources but raw historical material is not direct implementation authority. |
| BOOT-000 decision baseline | FROZEN AUTHORITY | Summarizes reconciled BOOT decisions derived from earlier architecture work. |
| BOOT-000 architecture baseline | FROZEN AUTHORITY | Provides implementation constraints that M0 must preserve. |
| BOOT contracts and evidence | FROZEN AUTHORITY | Provide concrete M0-facing semantic boundaries. |
| `1.txt` | HISTORICAL DESIGN INPUT | Untracked kickoff/reference material; not used as direct M0 authority. |

## Derived M0 Mapping

| Frozen BOOT Theme | M0 Work |
| --- | --- |
| Curios-owned canonical contracts | TASK-M0-002 through TASK-M0-008 must use frozen contracts and may not redefine them. |
| Work/DAG ownership controls execution | TASK-M0-006 implements only a single-step work runtime; DAG scheduling remains deferred. |
| Evidence-backed completion | TASK-M0-004, TASK-M0-005, TASK-M0-010, and TASK-M0-012 persist and verify evidence paths. |
| Runtime visualization reflects runtime truth | TASK-M0-008 and TASK-M0-009 expose recorded state only. |
| Policy before governed effects | TASK-M0-003 and TASK-M0-006 require policy decision before execution. |
| Provider replaceability | TASK-M0-007 uses existing provider catalog ports rather than provider-native semantics. |
| Persistence/provenance | TASK-M0-002 and TASK-M0-004 introduce bounded local persistence for runtime facts. |

## Unresolved P1-P6 Mappings

Detailed mappings remain unresolved for:

- specific P1 requirements;
- P2 subsystem decomposition;
- P3 invariants beyond those already frozen in BOOT;
- P4 implementation architecture beyond the BOOT topology;
- P5 executable specification slices;
- P6 reconciled implementation order after BOOT.

Resolving those mappings requires importing or reconstructing the detailed
P1-P6 artifacts into frozen Build Pack form before they can govern tasks beyond
the derived M0 slice.

## Rule For Future Tasks

No future task may cite P1-P6 directly as implementation authority unless the
specific P1-P6 material has been reconciled into a tracked, reviewed, frozen
Build Pack artifact.
