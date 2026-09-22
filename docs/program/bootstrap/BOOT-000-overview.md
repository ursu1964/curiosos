---
id: BOOT-000-OVERVIEW
title: BOOT-000 Overview
lifecycle: FROZEN
artifact_type: program_overview
authority: authoritative
---

# BOOT-000 Overview

BOOT-000 establishes the CuriosOS bootstrap foundation before runtime implementation begins. It turns the approved BOOT-000A through BOOT-000K planning sequence into a controlled implementation program with traceable authority, task boundaries, verification expectations, and acceptance gates.

## Purpose

The purpose of BOOT-000 is to create the minimum repository, documentation, workspace, contract, testing, security, observability, provider, API, web, CI, and acceptance foundations needed for later CuriosOS implementation.

BOOT-000 does not implement the complete CuriosOS cognitive platform. It creates the controlled foundation from which later milestones can safely grow.

## Operating Principles

- CuriosOS owns canonical semantics.
- Frameworks and providers implement Curios semantics; they do not define them.
- Capabilities are requested before providers are selected.
- Reuse is preferred before new creation.
- LLM usage is optional and governed by capability need.
- Work/DAG ownership controls execution.
- Agent definitions are separate from agent instances.
- Completion must be evidence-backed.
- Runtime visualization must reflect runtime truth.
- Policy precedes governed effects.
- Least authority is the default.
- Secrets, artifacts, evidence, and provenance are governed boundaries.
- Implementation tasks do not redefine frozen architecture.

## Approved BOOT Sequence

| ID | Title | Status |
| --- | --- | --- |
| BOOT-000A | Repository Discovery | VALIDATED |
| BOOT-000B | Architecture & Technology Decision Freeze | FROZEN |
| BOOT-000C | Enterprise Build Pack | FROZEN |
| BOOT-000D | Repository Topology & Package Boundary Freeze | FROZEN |
| BOOT-000E | Development Environment Specification | FROZEN |
| BOOT-000F | Core Contracts & Conventions | FROZEN |
| BOOT-000G | Testing & Independent Verification | FROZEN |
| BOOT-000H | Security, Configuration & Effect Governance | FROZEN |
| BOOT-000I | Observability, Evidence, Provenance & Runtime Truth | FROZEN |
| BOOT-000J | CI, Quality Gates & Merge Eligibility | FROZEN |
| BOOT-000K | Implementation DAG & Atomic Task Pack | FROZEN |

## Implementation Boundary

BOOT-000 implementation is limited to the task pack in `TASK-BOOT-001` through `TASK-BOOT-028`.

Implementation must not introduce M1+ features such as full cognitive graph runtime, multi-agent orchestration runtime, application intelligence, DataLab, self-improvement, production IAM, cloud infrastructure provisioning, external event brokers, or live LLM quality gates.

## Milestone Relationship

BOOT-000 is the bootstrap milestone. Later milestones use the approved sequence `M0`, `M1`, and onward. BOOT-000 prepares M0 foundations; it is not itself the complete M0 platform.

## Acceptance Model

BOOT-000 completion uses separate states:

- `IMPLEMENTED`: expected task outputs exist.
- `TESTED`: required tests and checks have evidence.
- `VALIDATED`: independent verification accepts the evidence.
- `FROZEN`: the status ledger and BOOT freeze record are approved with no unresolved blocking issues.

CI passing and implementation-agent self-report are not sufficient by themselves for `VALIDATED`.
