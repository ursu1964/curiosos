---
id: CONTRACT-M1-002-COGNITIVE
title: M1 Cognitive Intent, Problem, Assumption, Decision, and Plan Contracts
lifecycle: IMPLEMENTED
artifact_type: contract
authority: authoritative
task_id: TASK-M1-002
milestone_id: M1
date: 2026-09-25
---

# M1 Cognitive Contracts

TASK-M1-002 adds the minimal canonical cognitive records required by M1:
`Intent`, `Problem`, `Assumption`, `Decision`, and `Plan`.

These contracts define recorded facts only. They do not implement knowledge
graphs, memory, model prompts, deterministic decomposition, DAG persistence,
workflow engines, API routes, web UI, routing, agents, executors, or model
generation.

## Identifiers And References

TASK-M1-002 adds typed runtime IDs for the new records:

| Contract | ID | Prefix | Reference kind |
| --- | --- | --- | --- |
| `Intent` | `IntentId` | `int` | `intent` |
| `Problem` | `ProblemId` | `prb` | `problem` |
| `Assumption` | `AssumptionId` | `asm` | `assumption` |
| `Decision` | `DecisionId` | `dcn` | `decision` |
| `Plan` | `PlanId` | `pln` | `plan` |

`ObjectReference` remains the single generic reference abstraction. Cognitive
records refer to each other and to existing Curios objects through
`ObjectReference`; TASK-M1-002 does not introduce a second reference primitive.

## Intent

`Intent` is a submitted user/system intent.

Fields:

| Field | Semantics |
| --- | --- |
| `intent_id` | Canonical `IntentId`. |
| `objective` | Bounded human-readable objective text. |
| `submitted_at` | Canonical UTC timestamp. |
| `source_ref` | Optional `ObjectReference` for the submitting source/actor. |
| `context_refs` | Optional references to existing context objects. |

`Intent` does not embed work state, execution state, prompts, model messages, or
planner behavior.

## Problem

`Problem` is a bounded problem statement derived from an `Intent`.

Fields:

| Field | Semantics |
| --- | --- |
| `problem_id` | Canonical `ProblemId`. |
| `intent_ref` | Required `ObjectReference` whose kind is `intent`. |
| `objective` | Bounded objective text. |
| `statement` | Bounded problem statement text. |
| `created_at` | Canonical UTC timestamp. |
| `context_refs` | Optional references to existing context objects. |

`Problem` does not decompose work, schedule execution, or duplicate `WorkItem`.

## Assumption

`Assumption` is a bounded cognitive fact linked to a canonical subject.

Fields:

| Field | Semantics |
| --- | --- |
| `assumption_id` | Canonical `AssumptionId`. |
| `subject_ref` | Required `ObjectReference` for the subject. |
| `statement` | Bounded assumption text. |
| `created_at` | Canonical UTC timestamp. |
| `basis_refs` | Optional references supporting the assumption. |

## Decision

`Decision` is a bounded cognitive decision fact.

Fields:

| Field | Semantics |
| --- | --- |
| `decision_id` | Canonical `DecisionId`. |
| `subject_ref` | Required `ObjectReference` for the decision subject. |
| `question` | Bounded question being decided. |
| `selected_option` | Bounded selected option text. |
| `rationale` | Bounded rationale text. |
| `decided_at` | Canonical UTC timestamp. |
| `input_refs` | Optional references to inputs used by the decision. |

`Decision` is not `PolicyDecision` and does not authorize effects.

## Plan

`Plan` is a bounded cognitive plan record.

Fields:

| Field | Semantics |
| --- | --- |
| `plan_id` | Canonical `PlanId`. |
| `problem_ref` | Required `ObjectReference` whose kind is `problem`. |
| `objective` | Bounded objective text. |
| `created_at` | Canonical UTC timestamp. |
| `assumption_refs` | References whose kind is `assumption`. |
| `decision_refs` | References whose kind is `decision`. |
| `work_refs` | References whose kind is `work`. |

`Plan` may reference generated or associated work, but it does not duplicate
`WorkItem` identity, state, dependencies, required capabilities, inputs,
expected outputs, policy links, authority links, principal links, or evidence
requirements. TASK-M1-004 owns future work-DAG records and edges.

## Serialization

Serialization follows the frozen Curios conventions:

- snake_case field names;
- stable typed IDs;
- UTC timestamps;
- JSON-compatible object/array/scalar values;
- explicit `null` where optional fields are emitted;
- `ObjectReference` for cross-record links.

## Explicitly Deferred

TASK-M1-002 does not implement deterministic decomposition, cognitive graph
storage, work DAG persistence, schedulers, runners, capability resolution,
agent assignment, routing, verification loops, API routes, web UI, model
generation, model prompts, memory, DataLab, or M2+ behavior.
