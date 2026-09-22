---
id: TASK-BOOT-012-INTEGRATION-EVIDENCE
title: TASK-BOOT-012 Integration Evidence
lifecycle: IMPLEMENTED
artifact_type: evidence
authority: authoritative
task: TASK-BOOT-012
---

# TASK-BOOT-012 Integration Evidence

TASK-BOOT-012 was integrated into `main` from validated commit
`d9c5edfa98997dc98a428ebc0a72747442117738`.

## Integration

| Subject | Result |
| --- | --- |
| Pre-integration baseline | `main` was at `7f343d5550e28ea046fa9c3f710e3ec3a3623aa3`. |
| Preserved history | Original TASK-BOOT-012 implementation, TASK-BOOT-010 reconciliation merge `b11fddf`, and reconciliation commit `d9c5edf` were preserved. |
| Merge | `task/boot-012-events-observability` merged without conflicts. |
| TASK-BOOT-012 status | Recorded as `VALIDATED, FROZEN`. |
| TASK-BOOT-011 and TASK-BOOT-013 status | Not modified beyond their existing frozen planning state. |
| Outstanding verification | `BOOT-VERIFY-PG-READINESS-001` remains open. |

## Canonical Reference Baseline

`ObjectReference(kind, ref_id)` remains the only generic canonical Curios
object/reference abstraction.

No `Reference(ref_type, ref_id)` implementation, alias, obsolete import, or
authoritative documentation claim was retained in the integrated baseline.

## Semantic Verification

| Subject | Result |
| --- | --- |
| Reference | `ObjectReference` is the single generic reference abstraction. |
| Correlation | `TraceId` and `CorrelationId` are distinct canonical ID types. |
| Causation | No `CausationId` exists; causation uses `ObjectReference` to the immediate cause. |
| EventEnvelope | Transport-neutral; no broker, provider SDK, persistence, UI, or OpenTelemetry-specific semantics. |
| ObservabilityContext | Contextual fields are optional where appropriate and do not require fabricated IDs. |
| Runtime vocabulary | Frozen event vocabulary preserved without additions. |

## Deterministic Checks

Integrated checks were run after merge and status reconciliation from `main`.

| Check | Result |
| --- | --- |
| TOML validation | Passed for root and Python package `pyproject.toml` files. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed: 58 files already formatted. |
| `uv run --package curios-contracts mypy packages/python` | Passed: no issues found in 31 source files. |
| `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` | Passed: 75 tests passed. |
| Serialization inspection | Passed. |
| Architecture/import scan | Passed. |
| Obsolete reference search | Passed: no obsolete generic reference implementation, alias, or source import remains. |
| `git diff --check` | Passed. |
