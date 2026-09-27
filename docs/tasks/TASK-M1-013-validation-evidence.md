---
id: TASK-M1-013-VALIDATION-EVIDENCE
title: TASK-M1-013 Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M1-013
milestone_id: M1
date: 2026-09-27
---

# TASK-M1-013 Validation Evidence

## Scope

Published baseline:
`81af19f99f86a364be52e3acc4f6e3ba9e56ef50`

Implementation:
`87372e059fec914c6883c6a53e1baadb94c7286c`

Correction 1:
`fdb68bb4bff7acc1a1f5e7f5fe87ff87cf0cc9cb`

Correction 2:
`80f3b675e93cb9adaf2a92e0e0937d8c366035c2`

Validation reconstructed TASK-M1-013 from the frozen M1 task pack, M1
implementation DAG, M1 status ledger, M0 API boundary, TASK-M1-003
decomposition, TASK-M1-011 bounded DAG runner, TASK-M1-012 verification loop,
TASK-M1-014 boundary, architecture guardrails, and security constraints.

## Acceptance Mapping

| Criterion | Result | Evidence |
| --- | --- | --- |
| Prerequisites | PASS | TASK-M1-011 and TASK-M1-012 are validated, frozen, integrated, published, and remote-CI-verified in the published baseline. |
| Endpoint inventory | PASS | Exactly `POST /m1/intents/decompose`, `POST /m1/dag/run-once`, and `POST /m1/verification/complete` are exposed. No M1 GET aliases, model-generation endpoint, persistence endpoint, or M1-014 UI surface exists. |
| API adapter boundary | PASS | HTTP input is parsed into canonical records, delegated to frozen M1 modules, and serialized as canonical JSON-compatible output. FastAPI does not become semantic authority. |
| Decomposition boundary | PASS | `/m1/intents/decompose` delegates to frozen deterministic decomposition. Unsupported and lexical near-miss intents remain unsupported domain outcomes. |
| Runner boundary | PASS | `/m1/dag/run-once` delegates to `BoundedM1DagRunner` and preserves DAG readiness, deterministic ordering, max concurrency, route/work compatibility, capability, and active-agent gates. |
| Verification boundary | PASS | `/m1/verification/complete` delegates to `BoundedM1VerificationLoop` and preserves recorded-execution gating, evidence subject binding, duplicate evidence rejection, loop bounds, first-terminal semantics, and completion decisions. |
| HTTP/domain status | PASS | Valid domain outcomes such as unsupported decomposition, `NO_ROUTE`, `ROUTE_NOT_EXECUTABLE`, `DEFERRED`, `REJECTED`, and `APPROVED` remain successful canonical domain responses rather than malformed-request errors. |
| Malformed transport | PASS | M1-owned malformed media, malformed JSON, non-object JSON, missing body, and non-canonical object payloads return bounded HTTP 400 `M1_API_MALFORMED_REQUEST`. |
| Framework preemption | PASS | M1 route bodies are accepted as `Request` objects, media-gated, JSON-parsed, and object-gated before canonical parsing. FastAPI/Pydantic no longer preempts M1 bounded mapping for authoritative endpoint inputs. |
| Safe errors | PASS | M1-generated transport and bounded domain errors use fixed canonical messages and do not echo raw body, header, provider, DB, traceback, or exception text. |
| Cross-domain consistency | PASS | Valid JSON cannot bypass frozen downstream consistency checks for wrong-work routes, incompatible route/work types, wrong evidence subject, duplicate evidence, wrong refs, invalid concurrency, or invalid iteration bounds. |
| OpenAPI/runtime consistency | PASS | OpenAPI declares exactly the three M1 POST paths, required `application/json` object bodies, and no provider/model/persistence/UI schemas. Runtime accepts that contract and rejects unsupported media. |
| Repeated requests | PASS | Repeated and sequential requests preserve semantic behavior and do not share mutable API state. Caller-supplied canonical IDs determine stable semantic output where applicable. |
| No persistence/provider/direct executor | PASS | Source and tests prove no DB writes, no runner/verification persistence, no direct `M1Executor` bypass, no provider/model/Ollama/cloud/network invocation, no route recomputation, and no Work/DAG/Agent/ExecutionRecord mutation. |
| Policy boundary | PASS | M1 endpoints do not grant policy, mutate principal, or infer authorization from verification approval. Existing M0 policy behavior is unchanged. |
| M1-014 boundary | PASS | No React, frontend, web-console route, CSS/layout, browser polling, or UI behavior is introduced. |

## Original Defect Re-Validation

Correction 1 was revalidated across all three M1 endpoints:

- JSON scalar and non-object bodies reach the M1 bounded parser;
- syntactically malformed JSON maps to HTTP 400 `M1_API_MALFORMED_REQUEST`;
- raw body text is not echoed in response JSON, error messages, operations, or
  framework diagnostics;
- domain seams are not invoked for malformed JSON or non-object JSON.

Correction 2 was revalidated across all three M1 endpoints:

- `application/json` and `application/json` with legal parameters are accepted;
- missing, empty, malformed, unsupported, form, multipart, octet-stream, and
  unauthorized structured-suffix media are rejected before JSON parsing;
- unsupported media returns HTTP 400 `M1_API_MALFORMED_REQUEST`;
- raw body and header text are not echoed;
- rejected media invokes zero downstream domain seams.

## Validator Regressions

Independent validator coverage was added in
`apps/api/tests/test_task_m1_013_revalidation_regressions.py`.

It covers:

- accepted and rejected media types for every M1 endpoint;
- missing and empty `Content-Type` with zero domain invocation;
- non-object JSON values and malformed JSON with zero domain invocation;
- unsupported decomposition and M1-003 lexical near-miss behavior through HTTP;
- `NO_ROUTE` and incompatible route/work type as runner domain outcomes;
- verification `APPROVED`, `REJECTED`, and `DEFERRED` as domain outcomes;
- authority-looking extra fields proving the frozen API policy is permissive
  to unknown object fields but does not grant execution, retry, provider,
  model, persistence, or concurrency override authority;
- OpenAPI/runtime media and route consistency.

## Authority And Guard Review

TASK-M1-013 authorizes only the three exact FastAPI M1 adapter endpoints. The
implementation has no direct persistence/DB writes, no WorkItem/WorkDag/Agent
or ExecutionRecord mutation, no route recomputation, no direct executor
invocation, no provider/model/Ollama/cloud/network invocation, no retry/cancel
or scheduler authority, no policy grant, no UI, no prompt, and no memory
authority.

Security inventory changes are bounded to the exact M1-013 API source/test
surface and this validation evidence file. No broad API, network, provider,
persistence, direct-executor, or UI exemption was added.

## Delta Classification

| File | Classification | Rationale |
| --- | --- | --- |
| `apps/api/pyproject.toml` | REQUIRED | Workspace-local dependencies for the M1 API adapter. |
| `apps/api/src/curios_api/service.py` | REQUIRED | Exact M1 endpoint adapter, transport gates, canonical parsing, and bounded error mapping. |
| `apps/api/tests/test_fastapi_service_composition.py` | JUSTIFIED SUPPORT | Confirms required local dependency edges. |
| `apps/api/tests/test_m1_cognitive_loop_endpoints.py` | REQUIRED | Focused M1-013 endpoint tests. |
| `apps/api/tests/test_task_m1_013_validation_regressions.py` | REQUIRED VALIDATION SUPPORT | Preserves Correction 1 and Correction 2 regressions. |
| `apps/api/tests/test_task_m1_013_revalidation_regressions.py` | REQUIRED VALIDATION SUPPORT | Independent re-validation regressions for corrected transport and full endpoint boundaries. |
| `docs/program/status-ledger/M1-status-ledger.md` | REQUIRED | Advances TASK-M1-013 to validated/frozen after independent re-validation. |
| `docs/tasks/TASK-M1-013-evidence.md` | REQUIRED | Implementation and correction evidence under validation. |
| `docs/tasks/TASK-M1-013-validation-evidence.md` | REQUIRED | Independent validation/freeze record. |
| `tests/security/test_security_baseline.py` | JUSTIFIED SUPPORT | Exact M1-013 API and validation-evidence authorization. |
| `uv.lock` | REQUIRED | Records workspace-local dependency edges for `curios-api`. |

No changed file was classified as questionable or out of scope.

## Verification

Pre-record validation checks:

- history: PASS, `81af19f9 -> 87372e05 -> fdb68bb4 -> 80f3b675`;
- M1-013 implementation, Correction 1, Correction 2, and independent
  re-validation regressions: PASS, `167 passed`;
- M1-011 and M1-012 boundary regressions: PASS, `54 passed`;
- complete API suite: PASS, `183 passed`;
- OpenAPI inspection: PASS, exact three M1 paths, POST only, required
  `application/json` object bodies;
- contract/schema/architecture/security: PASS, `405 passed`;
- M1 package regressions: PASS, `360 passed`;
- package/API/provider/runtime/persistence non-Docker suite: PASS, `374 passed`;
- Docker-backed serial integrations and acceptance: PASS, API 6, PostgreSQL
  provider 1, persistence 2, event/evidence 1, work repository 1, Work DAG
  repository 1, agent repository 1, agent lifecycle repository 1, routing
  repository 1, M0 vertical slice 2, acceptance 8.

Post-record verification reran complete repository gates and is recorded in the
validation result for this task.

Known warnings:

- the surrounding shell `VIRTUAL_ENV` points at the primary checkout and `uv`
  ignores it for this worktree;
- inherited FastAPI/Starlette `TestClient` deprecation warnings remain.

No skipped or deselected tests were counted as passed.

## Decision

TASK-M1-013 is `VALIDATED, FROZEN`.

TASK-M1-014 remains blocked until TASK-M1-013 is integrated into the main M1
baseline and published according to the authoritative M1 DAG.

No merge, push, deployment, main-branch modification, pre-commit hook
modification, TASK-M1-014 implementation, or M1 closure was performed during
validation.
