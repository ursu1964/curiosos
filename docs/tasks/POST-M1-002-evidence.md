---
id: POST-M1-002-EVIDENCE
title: POST-M1-002 M2 Planning Package Evidence
lifecycle: VALIDATED
artifact_type: planning_evidence
authority: implementation
task_id: POST-M1-002
milestone_id: M2
date: 2026-09-27
---

# POST-M1-002 Evidence

## Scope

POST-M1-002 converts POST-M1-001 reconstruction and human M2 decisions into a
reviewable M2 planning package.

This operation does not implement M2 product behavior, tests, CI workflow,
database migrations, API behavior, web behavior, model behavior, tool
execution, release, deployment, or tags.

`1.txt` remains read-only historical input and is not modified or committed.

## Baseline

Planning baseline:

`139274bc146db743e79411fbef04992dd6920839`

M1 state:

`FROZEN / CLOSED / PUBLISHED / REMOTE-CI-VERIFIED`

## Human Decisions Applied

| Decision | Applied M2 planning result |
| --- | --- |
| M2 identity | DataLab Analysis Vertical Slice. |
| Dataset intake | Bounded CSV/tabular upload. |
| Tool execution | Deterministic in-process profiler only; no subprocess framework. |
| LLM generation | Deferred; no generation, chat, embeddings, or cloud model in M2. |
| Persistence | Dataset metadata/reference/integrity plus DataLab run/result/evidence; no arbitrary raw dataset persistence by default. |
| UI | Focused DataLab workspace; no general chat, rich live graph, Library, or full project UI. |
| Session scope | Durable DataLab run identity only; no general project system. |

## Artifacts Created

- `docs/program/milestones/M2-milestone-definition.md`
- `docs/program/milestones/M2-vertical-slices.md`
- `docs/program/milestones/M2-implementation-dag.md`
- `docs/program/milestones/M2-acceptance-matrix.md`
- `docs/program/milestones/M2-traceability.md`
- `docs/program/milestones/M2-readiness-authorization.md`
- `docs/program/milestones/M2-evidence-lifecycle-conventions.md`
- `docs/architecture/M2-architecture-security-delta.md`
- `docs/contracts/M2-contract-delta.md`
- `docs/program/status-ledger/M2-status-ledger.md`
- `docs/tasks/M2-task-pack.md`
- `docs/tasks/POST-M1-002-evidence.md`

## Planning Result

M2 planning is specified but not yet validated/frozen. M2 implementation remains
blocked until independent readiness validation accepts the planning package and
explicitly authorizes `TASK-M2-001`.

## Readiness Verdict

POST-M1-002 planning package: COMPLETE FOR REVIEW.

M2 implementation readiness: NOT YET AUTHORIZED.

## POST-M1-003 Independent Validation Result

POST-M1-003 independent validation failed the first draft of the M2 planning
package. The failure was a planning precision failure, not a rejection of the
human decision that M2 is the DataLab Analysis Vertical Slice.

Root planning defects:

- filename/path semantics left `reject or normalize` ambiguous;
- dataset lifetime/cleanup did not define restart/replay semantics;
- contract ownership used conditional owners;
- contract fields, states, ordering, limits, and safe errors were incomplete;
- canonical WorkItem work types were not frozen;
- tool seam and profiler semantics were underspecified;
- non-dataset resource bounds were incomplete;
- persistence and run-state semantics used `where required` language;
- API endpoint inventory and upload transport were unspecified;
- web boundary/provenance rules were incomplete;
- traceability did not map every requirement to task/slice/evidence/CI;
- planning/readiness pseudo-node lifecycle semantics were ambiguous.

## Correction 1 Decisions

Correction 1 freezes:

- client filename metadata as required `X-Curios-Dataset-Filename`, NFC
  normalized, then rejected when unsafe;
- Curios-generated opaque staged locator with no client path authority;
- ephemeral raw dataset staging from successful intake through terminal run
  state, with no replay after cleanup without a new upload;
- `ArtifactReference(kind=dataset)` reuse and no `DatasetReference` in M2;
- canonical contract owners and shapes for DataLab request, profile, finding,
  result, and run record;
- resource bounds for objective, profiler timeout, findings, warnings,
  evidence references, messages, event payload, upload body, and API response;
- one executable WorkItem work type: `dataset_profile`;
- sole M2 capability identifier `dataset_profiling`;
- DataLab agent semantics as bounded capability declaration, not autonomy;
- deterministic in-process profiler seam and profiler inference rules;
- exact durable persistence model and run states;
- exact M2 API endpoint inventory and raw `text/csv` upload transport;
- explicit web API-boundary functions and draft/canonical provenance states;
- requirement-level traceability through CI gate ownership;
- `M2-000A` and `M2-READINESS` as non-task planning nodes.

Files revised by Correction 1:

- `docs/program/milestones/M2-milestone-definition.md`
- `docs/program/milestones/M2-vertical-slices.md`
- `docs/program/milestones/M2-implementation-dag.md`
- `docs/program/milestones/M2-acceptance-matrix.md`
- `docs/program/milestones/M2-traceability.md`
- `docs/program/milestones/M2-readiness-authorization.md`
- `docs/architecture/M2-architecture-security-delta.md`
- `docs/contracts/M2-contract-delta.md`
- `docs/program/status-ledger/M2-status-ledger.md`
- `docs/tasks/M2-task-pack.md`
- `docs/tasks/POST-M1-002-evidence.md`

## Remaining Planning State After Correction 1

Correction 1 does not claim POST-M1-003 validation passed.

M2 implementation readiness remains: NOT YET AUTHORIZED.

The corrected planning package requires a fresh independent validation pass
before it may be frozen and before `TASK-M2-001` can become READY.

## POST-M1-003 Independent Re-Validation Result

POST-M1-003 independent re-validation failed after Correction 1. Four
planning blockers remained:

- `DataLabRunRecord` ownership placed domain/runtime lifecycle semantics in
  `curios_persistence`;
- M2 API failure/status semantics lacked endpoint-level failure mapping;
- DataLab verification attempts were not mapped exactly to M1 completion
  decisions and DataLab run states;
- frontend stale-response/request-generation provenance was incomplete.

## Correction 2 Decisions

Correction 2 freezes:

- `curios_runtime` ownership for `DataLabRunState`, `DataLabRunRecord`,
  lifecycle semantics, runtime invariants, and DataLab run repository behavior;
- `curios_persistence` ownership only for durable record kinds, tables,
  migrations, transaction primitives, payload hash/version mechanics, and
  bounded storage errors;
- exact persisted-run reconstruction requirement: persisted representation
  reconstructs `curios_runtime.DataLabRunRecord` exactly or fails boundedly;
- bounded M2 API error envelope and endpoint-by-endpoint HTTP status/error
  mappings;
- raw `text/csv` upload failure mapping and JSON endpoint M1-013-style
  transport rejection before domain invocation;
- domain-outcome vs HTTP-failure distinction;
- DataLab verification attempt mapping:
  `PASSED -> APPROVED -> COMPLETED`,
  `FAILED -> REJECTED -> FAILED`,
  `INCONCLUSIVE|NOT_EVALUATED|zero attempts -> DEFERRED -> AWAITING_VERIFICATION`;
- first-terminal verification semantics;
- explicit caller-driven re-verification while awaiting verification, with no
  automatic retry loop;
- evidence binding to work, run, dataset artifact, SHA-256, result, and
  profile identity;
- web request generations for dataset, analysis, run, and verification state;
- stale-response rejection, single-flight semantics, dataset replacement,
  analysis replacement, and run/verification generation binding;
- acceptance regressions for stale responses and no hybrid canonical truth.

Files revised by Correction 2:

- `docs/contracts/M2-contract-delta.md`
- `docs/architecture/M2-architecture-security-delta.md`
- `docs/program/milestones/M2-milestone-definition.md`
- `docs/program/milestones/M2-vertical-slices.md`
- `docs/program/milestones/M2-acceptance-matrix.md`
- `docs/program/milestones/M2-traceability.md`
- `docs/tasks/M2-task-pack.md`
- `docs/program/status-ledger/M2-status-ledger.md`
- `docs/program/milestones/M2-readiness-authorization.md`
- `docs/tasks/POST-M1-002-evidence.md`

## Remaining Planning State After Correction 2

Correction 2 does not claim POST-M1-003 validation passed.

M2 planning state: AWAITING INDEPENDENT RE-VALIDATION.

M2 execution readiness: NOT AUTHORIZED.

`TASK-M2-001`: NOT AUTHORIZED.

## POST-M1-003 Final Independent Validation Result

POST-M1-003 final independent re-validation passed after Correction 2.

The validation accepted the corrected M2 planning package as complete,
internally consistent, bounded, secure, traceable, implementable, and
acceptance-ready for the DataLab Analysis Vertical Slice.

Planning lifecycle after POST-M1-004 freeze:

- M2 planning: `VALIDATED, FROZEN`.
- M2-000A: `VALIDATED, FROZEN`.
- M2-READINESS: `VALIDATED, FROZEN`.
- TASK-M2-001: `READY`.
- TASK-M2-002 through TASK-M2-016: `BLOCKED`.

M2 implementation did not start during POST-M1-002, either correction, or
POST-M1-003 validation.

## Publication Correction 1

M2 planning publication succeeded at:

`911819612cfc44d1dfc4b0270f64a99ea83aebe5`

Exact-SHA Quality Gates run `36344923985` failed in the security step
`test_tracked_security_surfaces_do_not_contain_secret_shaped_literals`.

The scanner flagged this evidence file because the Correction 1 history used
ordinary planning prose that resembled sensitive key/value syntax. The flagged
text described the canonical M2 capability identifier `dataset_profiling`;
it was not product source, not a credential, not generated secret material, not
an environment value, not `1.txt`, and not unrelated historical content.

Classification:

`PLANNING-DOCUMENT / SECURITY-HYGIENE DEFECT`

Correction:

- preserve the frozen semantic requirement that `dataset_profiling` is the
  sole M2 capability identifier;
- replace the scanner-shaped wording with ordinary domain prose;
- leave M2 objective, dataset bounds, contract ownership, API inventory,
  profiler authority, verification mapping, web provenance, vertical slices,
  task DAG, readiness, and all product/test/CI/schema/dependency surfaces
  unchanged.

M2 planning remains `VALIDATED / FROZEN / PUBLISHED` and awaits correction
validation/publication before it may be treated as remote-CI-verified.

TASK-M2-001 did not start.
