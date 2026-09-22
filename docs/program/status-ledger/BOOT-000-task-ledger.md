---
id: BOOT-000-TASK-LEDGER
title: BOOT-000 Task Ledger
lifecycle: FROZEN
artifact_type: status_ledger
authority: authoritative
---

# BOOT-000 Task Ledger

This ledger initializes `TASK-BOOT-001` through `TASK-BOOT-028`.

Pre-implementation status for every task:

```text
DEFINED
SPECIFIED
task specification FROZEN
```

No task is `IMPLEMENTED`, `TESTED`, or `VALIDATED` until execution evidence and verification support that state.

| Task ID | Title | Workstream | Dependencies | Parallel Group | Pre-Implementation Status |
| --- | --- | --- | --- | --- | --- |
| TASK-BOOT-001 | Build Pack foundation | WS-01 | none | PG-01 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-002 | Repository metadata conventions | WS-02 | TASK-BOOT-001 | PG-02 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-003 | Python uv workspace | WS-03 | TASK-BOOT-002 | PG-03 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-004 | pnpm/TypeScript workspace | WS-03 | TASK-BOOT-002 | PG-03 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-005 | Developer command surface | WS-02 | TASK-BOOT-002 | PG-03 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-006 | LOCAL_DOCKER PostgreSQL baseline | WS-04 | TASK-BOOT-002 | PG-03 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-007 | Python package skeletons | WS-05 | TASK-BOOT-003 | PG-04 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-008 | TypeScript package skeletons | WS-03 | TASK-BOOT-004 | PG-04 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-009 | Primitive contracts | WS-05 | TASK-BOOT-007 | PG-05 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-010 | Result, error, artifact/evidence refs | WS-05 | TASK-BOOT-009 | PG-06 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-011 | Work, execution, capability, provider, agent contracts | WS-05 | TASK-BOOT-009, TASK-BOOT-010 | PG-06 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-012 | Event and observability contracts | WS-05 | TASK-BOOT-009, TASK-BOOT-010 | PG-06 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-013 | Config, security, effect, policy contracts | WS-05 | TASK-BOOT-009, TASK-BOOT-010 | PG-06 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-014 | Contract/schema test foundation | WS-06 | TASK-BOOT-009, TASK-BOOT-010, TASK-BOOT-011, TASK-BOOT-012, TASK-BOOT-013 | PG-07A | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-015 | Architecture conformance checks | WS-06 | TASK-BOOT-009, TASK-BOOT-010, TASK-BOOT-011, TASK-BOOT-012, TASK-BOOT-013 | PG-07A | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-016 | Security baseline tests | WS-06 | TASK-BOOT-013, TASK-BOOT-015 | PG-07B | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-017 | Core package foundation | WS-05 | TASK-BOOT-011, TASK-BOOT-013 | PG-07A | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-018 | Configuration provider | WS-07 | TASK-BOOT-013, TASK-BOOT-014 | PG-08 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-019 | PostgreSQL provider boundary | WS-07 | TASK-BOOT-006, TASK-BOOT-011, TASK-BOOT-013, TASK-BOOT-014 | PG-08 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-020 | Ollama provider boundary with deterministic tests | WS-07 | TASK-BOOT-011, TASK-BOOT-013, TASK-BOOT-014 | PG-08 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-021 | Telemetry provider boundary | WS-07 | TASK-BOOT-012, TASK-BOOT-014 | PG-08 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-022 | FastAPI service composition | WS-07 | TASK-BOOT-017, TASK-BOOT-018, TASK-BOOT-019, TASK-BOOT-020, TASK-BOOT-021 | PG-09 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-023 | API integration tests | WS-08 | TASK-BOOT-022 | PG-10 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-024 | Web bootstrap | WS-07 | TASK-BOOT-008, TASK-BOOT-022 | PG-10 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-025 | CI quality gates | WS-08 | TASK-BOOT-003, TASK-BOOT-004, TASK-BOOT-005, TASK-BOOT-006, TASK-BOOT-007, TASK-BOOT-008, TASK-BOOT-009, TASK-BOOT-010, TASK-BOOT-011, TASK-BOOT-012, TASK-BOOT-013, TASK-BOOT-014, TASK-BOOT-015, TASK-BOOT-016, TASK-BOOT-017, TASK-BOOT-018, TASK-BOOT-019, TASK-BOOT-020, TASK-BOOT-021, TASK-BOOT-022, TASK-BOOT-023, TASK-BOOT-024 | PG-11 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-026 | BOOT acceptance suite | WS-08 | TASK-BOOT-023, TASK-BOOT-024, TASK-BOOT-025 | PG-12 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-027 | Independent verification record | WS-08 | TASK-BOOT-026 | PG-13 | DEFINED, SPECIFIED, task specification FROZEN |
| TASK-BOOT-028 | BOOT freeze/status ledger update | WS-01 | TASK-BOOT-027 | PG-14 | DEFINED, SPECIFIED, task specification FROZEN |

## Execution Status

| Task ID | Current Lifecycle | Evidence |
| --- | --- | --- |
| TASK-BOOT-001 | VALIDATED, FROZEN | Independent review accepted the Enterprise Build Pack foundation. |
| TASK-BOOT-002 | VALIDATED, FROZEN | Independent review accepted the repository metadata and convention updates. |
| TASK-BOOT-003 | VALIDATED, FROZEN | Independent review accepted the Python uv workspace foundation in commit `ee69e11e6a00a774ebf388a4fe91f05eea7e67f9`. |
| TASK-BOOT-004 | VALIDATED, FROZEN | Independent review accepted the TypeScript/pnpm workspace foundation in commit `0ae55c9f6b3ce7320d6a700eb8b026c3966cf1df`. |
| TASK-BOOT-005 | VALIDATED, FROZEN | Independent review accepted the developer command surface in commit `389302e`. |
| TASK-BOOT-006 | VALIDATED, FROZEN | Independent review accepted the `LOCAL_DOCKER` PostgreSQL baseline in commit `72edf0bd0114ccd074a3404e0a1588b81629066c`; live PostgreSQL readiness remains deferred for BOOT acceptance. |
| TASK-BOOT-007 | VALIDATED, FROZEN | Independent review accepted the Python package skeletons in commit `507f12362e9588470f3c556ebf30c36e15b3d141`. |
| TASK-BOOT-008 | VALIDATED, FROZEN | Independent review accepted the TypeScript package skeletons in commit `45b1e7f0e2b99f2e19edb86e7cf02214c90b6097`. |
| TASK-BOOT-009 | VALIDATED, FROZEN | Independent review accepted the primitive canonical contracts in commit `fccfbe35c337f7c1c7107e10fc6e8f221eb74df0`. |
| TASK-BOOT-010 | VALIDATED, FROZEN | Independent review accepted the result, error, artifact, evidence, verification, and `ObjectReference` contracts in commit `118688dfb8bc03387ea0a6b3e423bf252bb02f36`. `ObjectReference(kind, ref_id)` is the canonical generic Curios object/reference contract for the M0 baseline. |
| TASK-BOOT-011 | VALIDATED, FROZEN | Independent review accepted the work, execution, capability, provider descriptor, and agent contracts in commit `b6368444ca4e9498bf8c569c11a605055ded40d1`; integration preserves `ObjectReference` for security/governance references across aggregate boundaries. |
| TASK-BOOT-012 | VALIDATED, FROZEN | Independent review accepted the reconciled event and observability contracts in commit `d9c5edfa98997dc98a428ebc0a72747442117738`; TASK-BOOT-012 uses the frozen `ObjectReference(kind, ref_id)` contract and does not define a second generic reference abstraction. |
| TASK-BOOT-013 | VALIDATED, FROZEN | Independent review accepted the configuration, security, effect, and policy contracts in commit `6679224e6684a8b7be885a6685020308ff0313e3`; integrated with TASK-BOOT-011 without embedding governance records into work or agent runtime contracts. |
| TASK-BOOT-014 | VALIDATED, FROZEN | Independent review accepted the repository-level contract/schema verification foundation in commit `20b27f31c17b09708885e7447ef2bde2ab93a865`; formal generated JSON Schema remains a later derived representation. |
| TASK-BOOT-015 | VALIDATED, FROZEN | Independent review accepted the architecture conformance checks in commit `12bb41da9695ef35ca69e99d24a132972a348edb`; violations map to `ARCHITECTURE_FAILURE`. |
| TASK-BOOT-016 | VALIDATED, FROZEN | Independent PG-07B revalidation accepted the corrected security baseline tests in commit `93f7c6ffabeaca4b7ce24ff4e18746e11e672eb6`; PG-07B is closed. |
| TASK-BOOT-017 | VALIDATED, FROZEN | Independent review accepted the core package foundation in commit `56428d8fcdd8b67ab822691e96c0a9a44bf39642`; `curios_core` preserves inward dependency direction and does not implement deferred runtime engines. |
| TASK-BOOT-018 | VALIDATED, FROZEN | Independent PG-08C validation accepted the configuration provider boundary; see `docs/tasks/PG-08C-validation-evidence.md`. |
| TASK-BOOT-019 | VALIDATED, FROZEN | Independent PG-08C validation accepted the PostgreSQL provider boundary and Docker-backed readiness evidence; see `docs/tasks/PG-08C-validation-evidence.md`. |
| TASK-BOOT-020 | VALIDATED, FROZEN | Independent PG-08C validation accepted the deterministic Ollama provider boundary; see `docs/tasks/PG-08C-validation-evidence.md`. |
| TASK-BOOT-021 | VALIDATED, FROZEN | Independent PG-08C validation accepted the telemetry provider boundary; see `docs/tasks/PG-08C-validation-evidence.md`. |
| TASK-BOOT-022 | VALIDATED, FROZEN | Independent validation accepted the FastAPI service-composition boundary at commit `fff9156475dbfb792e8908fcabda91922fe36650`; see `docs/tasks/TASK-BOOT-022-evidence.md`. |
| TASK-BOOT-023 | VALIDATED, FROZEN | Independent PG-10 validation accepted the API integration-test foundation; see `docs/tasks/PG-10-validation-evidence.md`. |
| TASK-BOOT-024 | VALIDATED, FROZEN | Independent PG-10 validation accepted the minimal React/TypeScript/Vite web bootstrap; see `docs/tasks/PG-10-validation-evidence.md`. |
| TASK-BOOT-025 | VALIDATED, FROZEN | Independent PG-11 revalidation accepted the corrected CI quality gates at commit `1aebc56e89de20ab7cbf6193ac6977c2f73ecfc0`; see `docs/tasks/PG-11-validation-evidence.md`. Hosted GitHub Actions execution has not yet been claimed as validation evidence. |
| TASK-BOOT-026 | IMPLEMENTED, TESTED | Implementation added the BOOT acceptance suite and CI gate; see `docs/tasks/TASK-BOOT-026-evidence.md`. Independent PG-12 validation remains pending. |

## Outstanding BOOT Acceptance Verification Items

| ID | Subject | Status | Required Before |
| --- | --- | --- | --- |
| BOOT-VERIFY-PG-READINESS-001 | Start the TASK-BOOT-006 PostgreSQL service, verify health/readiness, and stop it cleanly without destroying the persistent volume. | VERIFIED by corrective evidence in `docs/tasks/BOOT-VERIFY-PG-READINESS-001-evidence.md`; PostgreSQL reached healthy state, readiness passed, service stopped cleanly, and the named volume remained present. | Final BOOT-000 acceptance |
