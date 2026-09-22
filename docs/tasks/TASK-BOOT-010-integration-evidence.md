---
id: TASK-BOOT-010-INTEGRATION-EVIDENCE
title: TASK-BOOT-010 Integration Evidence
lifecycle: IMPLEMENTED
artifact_type: evidence
authority: authoritative
task: TASK-BOOT-010
---

# TASK-BOOT-010 Integration Evidence

TASK-BOOT-010 was integrated into `main` from validated commit
`118688dfb8bc03387ea0a6b3e423bf252bb02f36`.

## Integration

| Subject | Result |
| --- | --- |
| Pre-integration baseline | `main` was at `ffbf8c5828eba954e06d24742ad168d9dfa38ab1`. |
| Merge | `task/boot-010-result-evidence` merged without conflicts. |
| TASK-BOOT-010 status | Recorded as `VALIDATED, FROZEN`. |
| TASK-BOOT-012 status | Not integrated and not marked `VALIDATED` or `FROZEN`. |
| Outstanding verification | `BOOT-VERIFY-PG-READINESS-001` remains open. |

## Canonical Reference Baseline

`ObjectReference(kind, ref_id)` is the canonical generic Curios
object/reference contract for the M0 baseline.

TASK-BOOT-012's independently created `Reference(ref_type, ref_id)` is not
authoritative and must be reconciled before TASK-BOOT-012 validation.

## Deterministic Checks

| Check | Result |
| --- | --- |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed: 49 files already formatted. |
| `uv run --package curios-contracts mypy packages/python` | Passed: no issues found in 26 source files. |
| `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` | Passed: 53 tests passed. |
| `git diff --check` | Passed. |

## Architecture And Import Boundary

Source imports in `packages/python/curios_contracts/src/curios_contracts` were
inspected with Python AST parsing. The package imports only standard-library
modules and local `curios_contracts` modules.

Forbidden provider/framework names appeared only inside the architecture test's
own forbidden-name list, not as source imports.
