---
id: TASK-M1-012-VALIDATION-EVIDENCE
title: TASK-M1-012 Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-012
milestone_id: M1
date: 2026-09-26
---

# TASK-M1-012 Validation Evidence

## Scope

Published baseline:
`303616366d183808d91ffdcd6a26b354fb527d3b`

Implementation:
`7a729bcc2a310ecb87f812b7392ce966aa015a2b`

Validation reconstructed TASK-M1-012 from the frozen M1 task pack, M1
implementation DAG, status ledger, M1 milestone acceptance criteria,
canonical `VerificationReference`, `EvidenceReference`, `EventEnvelope`, and
`Result` contracts, M1-008 executor seam, M1-011 bounded DAG runner, M1-013
boundary, architecture guardrails, and security constraints.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | TASK-M1-011 is validated/frozen/integrated/published/remote-CI-verified in the published baseline. |
| Authorized surface | PASS | Implementation is limited to an M1 runtime verification module, runtime exports, tests, evidence, ledger, and bounded security inventory. |
| M1-011 boundary | PASS | Verification consumes supplied runner node results and does not invoke `BoundedM1DagRunner`, `M1Executor`, routing, agents, or execution retries. |
| M1-013 boundary | PASS | No FastAPI routes, HTTP handlers, DTO/API layer, frontend, or web contract is introduced. |
| Recorded-execution gate | PASS | Approval requires the runner node to belong to the requested work, have `EXECUTED` status, carry a completed executor outcome, and contain a successful canonical `Result`. |
| Evidence subject binding | PASS | Terminal verification requires evidence bound to `ObjectReference.from_id(work.work_id)`. Wrong-work and wrong-kind subjects fail boundedly. |
| Evidence provenance trust model | PASS | Frozen contracts require evidence subject binding and canonical evidence identity. No additional execution/event provenance field exists in `EvidenceReference`; subject-bound evidence is preserved as canonical evidence, while event payloads copy only evidence IDs. |
| Duplicate evidence | PASS | Duplicate `EvidenceId` values fail even when other evidence fields differ. Distinct IDs with equivalent content are separate canonical references. |
| Terminal evidence | PASS | `PASSED` and `FAILED` attempts require evidence. `INCONCLUSIVE`, `NOT_EVALUATED`, and zero-attempt cases do not approve completion. |
| Loop bound | PASS | `max_iterations` accepts 1 through 8, rejects 0, negative, non-integer, 9, and attempts exceeding the configured bound. No unbounded loop or hidden retry exists. |
| Attempt order | PASS | Attempts are chronological inputs. The first terminal `PASSED` or `FAILED` stops processing; later attempts cannot override it. |
| Completion decisions | PASS | `PASSED -> APPROVED`, `FAILED -> REJECTED`, inconclusive/not-evaluated/no attempts -> `DEFERRED`; no decision mutates WorkItem or DAG truth. |
| VerificationReference | PASS | Subject is the work reference, outcome is canonical, evidence refs are deterministic and bound, and the record does not claim persistence. |
| EventEnvelope | PASS | Attempted verification returns `verification.completed` for approved, rejected, and attempted-deferred outcomes; zero attempts return no event. Payload contains bounded reason/outcome IDs and does not claim WorkItem/DAG completion mutation. |
| Determinism/idempotency | PASS | Repeated equivalent requests with caller-supplied IDs/timestamps serialize identically; evidence order is canonical by `EvidenceId`; attempt order remains semantically significant. |
| Safe errors | PASS | M1-012 generated errors use bounded fixed messages and do not copy upstream secret-shaped evidence text. |
| No persistence/mutation | PASS | Source audit and tests prove no DB/repository imports or writes, no WorkItem/WorkDag/AgentInstance/ExecutionRecord/routing mutation, and no hidden durable state. |
| No provider/model authority | PASS | Source audit proves no Ollama/provider/model/network/generation/chat/embed/cloud discovery authority. |

## Validator Regressions

Independent validator coverage was added in
`packages/python/curios_runtime/tests/test_task_m1_012_validation_regressions.py`.

It covers:

- first-terminal attempt precedence;
- inconclusive-then-terminal attempts;
- fewer attempts than the configured bound;
- wrong-work runner output;
- completed executor status with failed `Result`;
- non-executed node statuses including `NO_ROUTE`, route-not-executable,
  waiting, blocked, terminal, deferred, and failed;
- duplicate `EvidenceId` with different evidence fields;
- wrong-kind evidence subject;
- subject-bound evidence with unrelated trace/provenance accepted under the
  frozen subject-binding trust model;
- maximum loop bound and maximum-plus-one rejection;
- non-integer loop bound rejection;
- event payload does not claim state mutation;
- repeated request determinism;
- source audit for no execution, persistence, provider/model, network, or API
  authority.

## Changed Files Classification

| File | Classification | Reason |
| --- | --- | --- |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Advances TASK-M1-012 to validated/frozen after independent validation. |
| `docs/tasks/TASK-M1-012-evidence.md` | REQUIRED | Implementation evidence under validation. |
| `docs/tasks/TASK-M1-012-validation-evidence.md` | REQUIRED | Independent validation/freeze record. |
| `packages/python/curios_runtime/src/curios_runtime/__init__.py` | REQUIRED | Exports authorized M1-012 verification symbols. |
| `packages/python/curios_runtime/src/curios_runtime/m1_verification_loop.py` | REQUIRED | Authorized M1-012 runtime verification module. |
| `packages/python/curios_runtime/tests/test_task_m1_012_verification_loop.py` | REQUIRED | Implementation tests, with security-safe adversarial string construction. |
| `packages/python/curios_runtime/tests/test_task_m1_012_validation_regressions.py` | REQUIRED | Independent validator regressions. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Bounded authorization of the exact M1-012 runtime/evidence surface. |

No questionable or out-of-scope changes remain.

## Verification

Pre-record validation checks:

- `pytest packages/python/curios_runtime/tests/test_task_m1_012_validation_regressions.py -q`:
  PASS, 19 passed;
- `pytest packages/python/curios_runtime/tests/test_task_m1_012_verification_loop.py packages/python/curios_runtime/tests/test_task_m1_012_validation_regressions.py -q`:
  PASS, 36 passed;
- `ruff format --check` on M1-012 implementation and tests: PASS;
- `ruff check` on M1-012 implementation and tests: PASS;
- `pytest tests/security/test_security_baseline.py tests/architecture/test_architecture_conformance.py -q`:
  PASS, 389 passed, 2 known deprecation warnings.

Complete repository verification is recorded in the validation result for this
task.

## Downstream

TASK-M1-012 is `VALIDATED, FROZEN`.

TASK-M1-013 remains blocked until TASK-M1-012 is integrated into main and
published according to the authoritative M1 DAG. No M1-013 implementation,
M1-014+ implementation, publication, deployment, or M1 closure was performed
during validation.
