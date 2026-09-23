---
id: TASK-M0-001-SECURITY-GUARDRAILS
title: TASK-M0-001 M0 Security Topology Guardrails
lifecycle: FROZEN
artifact_type: security_guardrail
authority: implementation
task_id: TASK-M0-001
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-001 M0 Security Topology Guardrails

## Purpose

TASK-M0-001 establishes the security topology mechanism for M0 without
authorizing M0 runtime implementation prematurely.

The frozen rule remains:

Each task authorizes only its explicit new surface.

## Current Authorized Topology

Current tracked roots remain the frozen BOOT roots:

- existing BOOT Python packages;
- `packages/python/curios_persistence/**` for TASK-M0-002 only;
- `packages/python/curios_policy/**` for TASK-M0-003 only;
- `packages/python/curios_runtime/**` event/evidence modules for TASK-M0-004,
  work repository modules for TASK-M0-005, and single-step runtime service
  module for TASK-M0-006, and provider-inventory executor module for
  TASK-M0-007 only;
- `apps/api/src/curios_api/composition.py` and
  `apps/api/src/curios_api/service.py` for TASK-M0-008 M0 work endpoint
  composition/translation only;
- exact `apps/api/tests/test_fastapi_service_composition.py` and
  `apps/api/tests/test_m0_work_endpoints.py`;
- exact `apps/web/src/App.tsx`, `apps/web/src/App.css`,
  `apps/web/src/App.test.tsx`, `apps/web/src/apiBoundary.ts`, and
  `apps/web/src/main.tsx` for TASK-M0-009 only;
- exact `tests/integration/test_m0_vertical_slice_integration.py` for
  TASK-M0-010 only;
- existing BOOT TypeScript package;
- exact `.github/workflows/quality-gates.yml`;
- exact BOOT integration and acceptance tests.

TASK-M0-001 does not add new runtime package roots, app roots, broad test roots,
service roots, provider roots, or `.github` surfaces.

TASK-M0-002 narrowly authorizes the planned `curios_persistence` package root.
TASK-M0-003 narrowly authorizes the planned `curios_policy` package root.
TASK-M0-004 narrowly authorizes event/evidence runtime store modules under the
planned `curios_runtime` package root. TASK-M0-005 authorizes work repository
modules under that root. TASK-M0-006 authorizes only the single-step runtime
service module under that root. TASK-M0-007 authorizes only the provider
inventory executor module under that root. TASK-M0-008 authorizes only the
existing API composition/service modules and the M0 API work endpoint test
surface. TASK-M0-009 authorizes only the minimal web work console source files
and deterministic package-local tests. TASK-M0-010 authorizes only the exact
M0 vertical-slice integration test file. Arbitrary API modules, arbitrary web
pages, arbitrary integration tests, arbitrary tool executors, and broader
runtime/service roots remain blocked until their owning tasks.

## Planned But Not Yet Authorized M0 Surfaces

The security tests now record planned M0 surfaces by task so future tasks can
authorize them narrowly:

| Task | Planned Surface |
| --- | --- |
| TASK-M0-012 | `tests/acceptance/**` additions beyond frozen BOOT acceptance tests |

Those planned surfaces remain blocked until their specific tasks are
implemented, tested, independently validated, frozen, and integrated according
to the M0 DAG.

## Preserved Security Controls

- repository secret scanning;
- secret-reference/value rules;
- core authority boundary;
- `PolicyDecision.UNKNOWN` non-authorizing semantics;
- exact `.github` authorization;
- provider isolation;
- API/web outer-boundary controls;
- exact integration/acceptance test surfaces;
- M1+ deferred-scope rejection.

## Adversarial Protection

The security topology tests reject:

- future M0 packages before their owning task authorizes them;
- future `curios_runtime` modules before their owning task authorizes them;
- future `apps/api` source or test files before their owning task authorizes
  them;
- future `apps/web` source files before their owning task authorizes them;
- future integration test files before their owning task authorizes them;
- plausible M1+ package names such as agent runtime, DataLab, knowledge,
  model-router, and secret-resolver packages;
- broad top-level runtime/service/provider roots;
- additional unrelated app roots;
- arbitrary `.github` paths.
