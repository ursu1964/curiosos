---
id: M2-ACCEPTANCE-MATRIX
title: M2 Acceptance Matrix
lifecycle: FROZEN
artifact_type: acceptance_matrix
authority: program_planning
milestone_id: M2
date: 2026-09-27
---

# M2 Acceptance Matrix

## Milestone Acceptance Principle

M2 acceptance proves the user-visible DataLab vertical slice, not merely the
existence of contracts or isolated units. Passing M2 acceptance means a bounded
CSV dataset and analytical objective produce verified, evidence-backed,
recorded findings visible through the DataLab API/web workspace.

## Slice Matrix

| Slice | Positive scenario | Negative scenario(s) | Real boundaries | Allowed fakes | Persistent truth | Deterministic assertion | Safe-error assertion | Exact PASS condition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VS-M2-001 Dataset Intake | `POST /m2/datalab/datasets` with raw `text/csv`, safe filename header, valid UTF-8 CSV. | Missing/unsupported media, oversize body, invalid encoding, malformed CSV, duplicate columns, empty dataset, unsafe filename/path, client locator, secret-shaped metadata. | FastAPI upload boundary, intake parser, artifact contract, safe-error mapper. | None for internal boundaries. | Dataset artifact metadata/reference, SHA-256, accepted filename, size, row/column summary, provenance. Raw bytes are ephemeral. | Same bytes and filename metadata produce same SHA-256 and equivalent metadata. | Bounded Curios error, no raw body/header, parser exception, path, or secret echo. | Accepted upload returns `ArtifactReference(kind=dataset)` and durable metadata; every negative fails before analysis. |
| VS-M2-002 Analysis Intent to DAG | `PROFILE_DATASET` objective plus accepted dataset reference creates run, request, and one-node `dataset_profile` DAG. | Missing dataset, unsupported objective, invalid artifact kind/media/hash, unavailable staged bytes, excessive objective length. | DataLab request contract, deterministic decomposition, Work DAG creation, runtime-owned run repository, persistence storage. | None for decomposition/DAG. | `DataLabAnalysisRequest`, runtime-owned `DataLabRunRecord`, Work DAG/work identity. | Equivalent canonical request yields equivalent DAG shape and work metadata. | Unsupported objectives and invalid refs fail boundedly with no tool/model execution. | Run reaches `READY` with exactly one `dataset_profile` WorkItem carrying dataset ref/hash. |
| VS-M2-003 Capability / Agent Assignment | `dataset_profile` work requiring `dataset_profiling` resolves to one active DataLab agent instance. | Missing capability, ambiguous capability, inactive agent, mismatched work type, duplicate eligible agents. | Capability resolver, agent definition/instance repository, lifecycle repository/events. | None for resolver/agent lifecycle. | Capability resolution, agent instance, lifecycle event truth. | Equivalent registered capabilities resolve to same status/reference. | Negative resolution emits bounded no-secret error/status. | Exactly one active agent is bound to the same WorkItem/run without granting extra authority. |
| VS-M2-004 Deterministic Profiling Execution | READY `dataset_profile` work executes in-process profiler and records profile/findings/result/evidence. | Missing staged bytes, hash mismatch, timeout, parser/resource failure, route/work incompatibility, unsafe profiler error. | DAG readiness, M1 runner, routing record, profiler seam, event/evidence/result recording. | External model/provider remains absent; no live model fake is needed. | `DataLabAnalysisResult` with embedded `DatasetProfile`, findings, warnings, evidence refs, events. | Same dataset bytes and bounds produce equivalent profile/findings ordering. | Profiler/native errors map to fixed bounded errors without raw cells/paths/tracebacks. | Run transitions to `AWAITING_VERIFICATION` with same-run same-dataset result/evidence. |
| VS-M2-005 Verification-Gated Findings | Same-run, same-work, same-dataset evidence verifies result through M1 verification. | Wrong evidence subject, duplicate evidence, missing/failed execution, stale run/work, dataset hash mismatch, `FAILED`, `INCONCLUSIVE`, `NOT_EVALUATED`, zero attempts. | M1 verification loop, evidence binding, DataLab run/result repository, event store. | None for verification. | Verification reference and run/result verification state. | Equivalent verification attempts yield equivalent completion decision. | Invalid evidence cannot approve; errors are bounded. | `PASSED -> APPROVED -> COMPLETED`; `FAILED -> REJECTED -> FAILED`; `INCONCLUSIVE`, `NOT_EVALUATED`, and zero attempts -> `DEFERRED -> AWAITING_VERIFICATION`; first terminal attempt cannot be overridden. |
| VS-M2-006 Recorded-Truth API / Web | Focused DataLab workspace uses explicit API-boundary functions to show dataset, run, profile, findings, evidence, and verification truth. | Malformed upload/request, unsupported media, stale draft/canonical mismatch, late stale response, generation mismatch, direct App network authority, unsafe error leakage. | FastAPI DataLab endpoints, web API boundary, read models/repositories, frontend authority guards. | Browser/network environment may be test-harness simulated; App network authority must remain absent. | Web renders API/persistence truth, not fabricated local-only state. | Equivalent persisted truth renders equivalent semantic UI state for the active generation only. | Bounded error state, no framework/raw exception or stale relabeling. | Acceptance proves 8 BOOT/M0 plus M1 acceptance remain intact and all 6 M2 slices pass with no skips/deselections. |

## Required Web Provenance Regressions

M2 acceptance must include executable coverage for:

- dataset A accepted; draft dataset B does not mutate A;
- failed B upload preserves A;
- successful B upload replaces A and clears A-derived analysis/run/profile/
  findings/verification state;
- late A-era upload response cannot overwrite B;
- analysis A accepted; draft objective B does not mutate A;
- failed B analysis creation preserves A;
- successful B analysis replaces A and clears stale run/profile/findings/
  verification state;
- late A-era run or verification response cannot overwrite B state;
- double-submit/single-flight behavior for mutating actions;
- no canonical hybrid assembled from different dataset, analysis, run, result,
  evidence, or verification generations.

## Required Acceptance Command Placement

M2 acceptance tests should live under `tests/acceptance` so the M2 CI gate can
discover them explicitly. M2 must not rely only on full pytest discovery.

## PASS Semantics

M2 acceptance passes only when:

- every VS-M2 slice has executable PASS/FAIL proof;
- DataLab acceptance includes the complete happy path from CSV upload to
  verified displayed findings;
- required negative cases fail boundedly;
- no skip or deselection is counted as pass;
- no live model, network, cloud credential, subprocess, or arbitrary file
  access is required.

## FAIL Semantics

If a frozen product defect is exposed during M2 acceptance work, the owning
task/surface must be identified and M2 acceptance must not be marked complete
by weakening the test.
