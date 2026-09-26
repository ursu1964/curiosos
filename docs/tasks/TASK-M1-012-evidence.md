---
id: TASK-M1-012-EVIDENCE
title: TASK-M1-012 Verification Loop and Evidence Binding Evidence
lifecycle: IMPLEMENTED
artifact_type: implementation_evidence
authority: implementation
task_id: TASK-M1-012
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-012 Implementation Evidence

## Objective

TASK-M1-012 gates M1 work/DAG completion on recorded verification evidence.
It separates recorded execution output, verification attempts, verification
records, evidence references, verification events, and completion decisions.

It does not implement API endpoints, frontend behavior, model/provider
invocation, route recomputation, executor retry, scheduling, state mutation,
policy grant, durable verification-loop state, or M1 milestone closure.

## Starting Baseline

`303616366d183808d91ffdcd6a26b354fb527d3b`

TASK-M1-001 through TASK-M1-011 are integrated, validated, frozen, published,
and remotely CI-verified at this baseline.

## Prerequisite Proof And Ledger Reconciliation

The authoritative M1 DAG requires TASK-M1-011 before TASK-M1-012. TASK-M1-011
was validated, frozen, integrated, published, and remote-CI-verified before
this task began. No additional TASK-M1-012 entry gate exists in the M1 task
pack, implementation DAG, milestone definition, or status-ledger semantics.

The M1 status ledger still recorded TASK-M1-012 as `BLOCKED` after TASK-M1-011
publication. That row was stale reporting state. This implementation
reconciles the row as part of normal TASK-M1-012 evidence and records
TASK-M1-012 as `IMPLEMENTED, TESTED`.

## Implementation Architecture

The implementation adds `curios_runtime.m1_verification_loop` with:

- `M1VerificationAttempt`;
- `M1VerificationLoopRequest`;
- `M1VerificationLoopResult`;
- `M1VerificationCompletionDecision`;
- `M1VerificationReasonCode`;
- `M1VerificationError` and `M1VerificationErrorCode`;
- `BoundedM1VerificationLoop`.

The verifier consumes a `WorkItem`, one recorded `M1DagRunnerNodeResult`, and
bounded verification attempts. It verifies that the runner node belongs to the
requested work, that execution completed successfully through the frozen
executor outcome, and that terminal verification attempts carry
`EvidenceReference` values bound to that same work.

For terminal verification outcomes it creates canonical in-memory:

- `VerificationReference`;
- `EventEnvelope` using `RuntimeEventType.VERIFICATION_COMPLETED`;
- deterministic evidence-reference aggregation;
- a completion decision.

No DB write, repository call, event/evidence persistence, WorkItem mutation,
WorkDag mutation, AgentInstance transition, ExecutionRecord mutation, runner
invocation, executor invocation, route recomputation, provider/model call,
network call, API route, or UI behavior is introduced.

## Verification Loop Semantics

The bounded loop accepts `max_iterations` from 1 through 8. The number of
supplied attempts must not exceed that configured bound.

Loop behavior:

- zero attempts -> `DEFERRED` / `NO_VERIFICATION_ATTEMPTS`, no verification
  record and no event;
- `INCONCLUSIVE` or `NOT_EVALUATED` attempts continue until attempts are
  exhausted, then return `DEFERRED` / `VERIFICATION_INCONCLUSIVE`;
- first `PASSED` attempt stops the loop and returns `APPROVED`;
- first `FAILED` attempt stops the loop and returns `REJECTED`;
- `NOT_EVALUATED` final output is normalized to canonical
  `VerificationOutcome.INCONCLUSIVE`;
- verification attempts beyond the configured bound are invalid.

The loop is deterministic over caller-supplied canonical IDs and timestamps.
It has no hidden cache or global state.

## Evidence Binding

Evidence binding is to the requested `WorkItem` through canonical
`ObjectReference.from_id(work.work_id)`.

Terminal `PASSED` and `FAILED` attempts require at least one
`EvidenceReference`. Every supplied evidence reference must:

- be an `EvidenceReference`, not an arbitrary object;
- have distinct `EvidenceId`;
- have `subject_ref` equal to the requested WorkItem reference.

Evidence references are sorted by `EvidenceId` for stable representation.
The verifier does not treat an evidence reference as proof of external
artifact validity beyond the frozen `EvidenceReference` trust model.

## Success, Failure, And Inconclusive Semantics

| Verification outcome | Completion decision | Record/event |
| --- | --- | --- |
| `PASSED` | `APPROVED` | Verification record and verification event are returned. |
| `FAILED` | `REJECTED` | Verification record and verification event are returned. |
| `INCONCLUSIVE` / `NOT_EVALUATED` | `DEFERRED` | A verification record/event is returned when an attempted verification exists; zero attempts return no record/event. |

Malformed or inconsistent inputs fail boundedly with `M1VerificationError`.
Execution self-report alone cannot produce `APPROVED`; bound verification
evidence is required.

## Authority Inventory

| Capability | M1-012 result |
| --- | --- |
| WorkItem read | AUTHORIZED as supplied canonical input |
| WorkItem mutation | ABSENT |
| WorkDag read/mutation | ABSENT |
| runner invocation | ABSENT |
| runner outcome read | AUTHORIZED as supplied canonical input |
| route read/recompute | ABSENT |
| capability resolution | ABSENT |
| agent read/transition | ABSENT |
| executor invocation | ABSENT |
| ExecutionRecord read/mutation | ABSENT |
| Result read | AUTHORIZED only through supplied executor outcome |
| Result create/mutate | ABSENT |
| EventEnvelope create | AUTHORIZED for in-memory `verification.completed` output |
| EventEnvelope persist | ABSENT |
| EvidenceReference read | AUTHORIZED as supplied evidence binding input |
| EvidenceReference create/persist | ABSENT |
| VerificationReference create | AUTHORIZED for in-memory verification output |
| verification record persist | ABSENT |
| DB | ABSENT |
| scheduling/retry/cancellation | ABSENT |
| provider/model invocation | ABSENT |
| network | ABSENT |
| policy evaluation/grant | ABSENT |
| API/UI | ABSENT |
| prompt/memory | ABSENT |

## Boundaries

M1-011 remains the owner of bounded in-memory DAG runner behavior, READY-node
selection, concurrency limiting, route consumption, capability gate passage to
the executor seam, active-agent gate, and executor invocation.

M1-012 consumes recorded M1-011 node results. Verification is not permission
to rerun execution, recompute routing, discover models, mutate the DAG, or
transition agents.

M1-013 remains the owner of API cognitive-loop endpoints. TASK-M1-012 adds no
FastAPI route, HTTP handler, frontend contract, web behavior, or API
presentation surface.

## Failure And Adversarial Coverage

Focused tests cover:

- passed verification with bound evidence;
- failed verification with bound evidence;
- inconclusive and not-evaluated attempts;
- zero attempts;
- invalid iteration bounds;
- supplied attempts exceeding the loop bound;
- terminal verification attempts with no evidence;
- evidence subject mismatch;
- duplicate evidence identity;
- non-executed runner nodes;
- failed executor outcomes;
- deterministic evidence ordering with reversed inputs;
- repeated equivalent verification requests;
- secret-shaped upstream evidence text on bounded error surfaces;
- absence of provider/model, runner/executor invocation, persistence, API,
  and state-mutation authority.

## Dependency And Schema Changes

No package, third-party dependency, lockfile, pnpm manifest, schema, migration,
or persistence-kind change is introduced.

## Verification

Focused verification before evidence update:

- `uv sync --locked --all-groups --all-packages`: PASS;
- `ruff format --check` on M1-012 implementation/test/security files: PASS;
- `ruff check` on M1-012 implementation/test/security files: PASS;
- `pytest packages/python/curios_runtime/tests/test_task_m1_012_verification_loop.py -q`:
  PASS, 17 passed;
- `pytest packages/python/curios_runtime/tests/test_task_m1_012_verification_loop.py tests/security/test_security_baseline.py -q`:
  PASS, 370 passed, 2 known deprecation warnings.

Complete repository verification is recorded in the implementation result for
this task.

## Downstream

TASK-M1-012 remains awaiting independent validation/freeze. TASK-M1-013 must
not start until TASK-M1-012 is validated, frozen, integrated, and published
according to the authoritative DAG.
