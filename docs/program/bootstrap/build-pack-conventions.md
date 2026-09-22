---
id: BUILD-PACK-CONVENTIONS-0001
title: Enterprise Build Pack Conventions
lifecycle: FROZEN
artifact_type: convention
authority: authoritative
---

# Enterprise Build Pack Conventions

The Enterprise Build Pack is the authority and traceability system for CuriosOS implementation.

## Artifact Format

Human-authored authoritative artifacts use Markdown with YAML front matter.

Minimum front matter:

```yaml
id:
title:
lifecycle:
artifact_type:
authority:
```

Additional metadata may be added only when it serves traceability, lifecycle, ownership, evidence, or acceptance.

## Stable IDs

Stable IDs use durable prefixes such as:

```text
REQ, INV, ADR, CTX, COG, GRF, MEM, PAT, CAP, WRK, AGT, EXE, MOD, PRV,
POL, EFF, EVT, EVD, VER, ART, APP, INF, OBS, SEC, DOC, LRN, BOOT,
MILESTONE, WORKSTREAM, TASK, TEST, ACCEPTANCE
```

Runtime IDs and Build Pack IDs are separate systems. Build Pack IDs are human-stable semantic references. Runtime IDs are opaque runtime identifiers.

## Authority Hierarchy

When artifacts conflict, precedence is:

1. Frozen contracts and invariants.
2. Approved ADRs.
3. Approved architecture specifications.
4. Approved milestone specifications.
5. Approved task specifications.
6. Implementation.
7. Tests.
8. Generated documentation.
9. Historical source material.

Conflicts must be recorded and escalated. They must not be silently resolved by an implementation task.

## Lifecycle Semantics

Engineering/build lifecycle:

```text
DEFINED -> SPECIFIED -> IMPLEMENTING -> IMPLEMENTED -> TESTED -> VALIDATED -> FROZEN
```

Specification artifacts usually use:

```text
DEFINED -> SPECIFIED -> VALIDATED -> FROZEN
```

Implementation artifacts usually use:

```text
DEFINED -> SPECIFIED -> IMPLEMENTING -> IMPLEMENTED -> TESTED -> VALIDATED -> FROZEN
```

Do not mark an implementation task `IMPLEMENTED`, `TESTED`, or `VALIDATED` merely because its plan exists.

## Traceability

The intended trace chain is:

```text
Requirement
-> Architecture
-> Invariant
-> Decision
-> Contract
-> Milestone
-> Workstream
-> Atomic Task
-> Implementation
-> Test
-> Evidence
-> Verification
-> Acceptance
-> Freeze
```

Not every artifact must link to every other artifact directly, but each layer must retain enough references to reconstruct authority and proof.

## Change Control

Frozen artifacts do not silently mutate. A change to a frozen contract, invariant, ADR, security rule, acceptance criterion, or lifecycle authority requires:

- affected IDs;
- reason;
- impact analysis;
- compatibility assessment;
- migration or rollback notes where applicable;
- approving revision or ADR;
- preservation of prior history.

## Generated Documents

Generated documentation is a view, not authority, unless explicitly promoted through Build Pack change control. Generated documentation is not committed automatically.

## Historical Source Policy

Historical material may inform requirements, architecture, and decisions, but raw historical material is not by itself the implementation specification. Reconciled and frozen Build Pack artifacts govern implementation.
