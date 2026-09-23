---
id: M0-FREEZE-RECORD
title: M0 Final Freeze Record
lifecycle: FROZEN
artifact_type: freeze_record
authority: authoritative
milestone_id: M0
date: 2026-09-23
---

# M0 Final Freeze Record

## Decision

M0 CLOSURE: PASS

M0 is approved for final `VALIDATED, FROZEN` status after TASK-M0-014 is
committed and integrated into `main`.

## Baselines

| Baseline | Meaning |
| --- | --- |
| `513ab43666ba423a458ba12c09391b76339df155` | Pre-TASK-M0-014 verified baseline containing integrated TASK-M0-013 independent verification. |
| TASK-M0-014 closure commit | Final authoritative M0 baseline after this freeze record, TASK-M0-014 evidence, and the M0 ledger closure are committed and integrated into `main`. |

The final closure commit SHA is intentionally not asserted inside this
uncommitted artifact. Repository history establishes it once TASK-M0-014 is
committed and integrated.

## BOOT Relationship

M0 extends the frozen BOOT-000 foundation. It does not replace BOOT authority
and does not redefine BOOT canonical semantics.

BOOT-000 remains the authority for:

- canonical contracts and `ObjectReference`;
- `Result` and `ContractError`;
- `CoreContext`, `CoreServices`, `ProviderCatalog`, and provider direction;
- `ConfigurationProfileName.LOCAL_DOCKER`;
- `PolicyDecision.UNKNOWN` as distinct and non-authorizing;
- FastAPI and web as outer interface/composition layers;
- security and architecture guardrail patterns.

## Closure Criteria

| Criterion | Result |
| --- | --- |
| TASK-M0-001 through TASK-M0-013 are `VALIDATED, FROZEN`. | PASS |
| TASK-M0-014 records final freeze/status closure. | PASS |
| M0 DAG waves and integration gates through PG-M0-09 are closed. | PASS |
| TASK-M0-012 acceptance remains validated/frozen. | PASS |
| TASK-M0-013 independently verified the integrated M0 baseline. | PASS |
| Final architecture boundary remains intact. | PASS |
| Final security topology remains exact. | PASS |
| Final CI quality-gate workflow remains the validated TASK-M0-011 workflow. | PASS |
| No required M0 work remains only on an unmerged branch. | PASS |
| No unresolved M0 blocker remains. | PASS |
| No M1+ executable task is authorized by this freeze. | PASS |

## Frozen M0 Scope

M0 freezes the governed local work execution slice:

- PostgreSQL runtime persistence foundation;
- minimal policy evaluator;
- event/evidence runtime store;
- work repository and state transitions;
- single-step runtime service;
- provider inventory executor;
- M0 API work endpoints;
- M0 web work console;
- M0 integration suite;
- M0 CI gates;
- M0 acceptance suite;
- architecture and security topology governing those surfaces.

## Deferred Scope

The following remain outside M0 and are not authorized by this freeze:

- scheduler or DAG runtime;
- multi-agent runtime;
- model routing or generation;
- knowledge or memory runtime;
- DataLab;
- learning or self-improvement;
- production IAM or full policy language;
- secret resolver;
- external brokers;
- cloud infrastructure;
- live LLM quality gates.

## Architecture Freeze

The frozen M0 architecture preserves this direction:

```text
curios_contracts
  <- curios_core
  <- persistence / policy / providers / runtime
  <- FastAPI API
  <- web interface
```

Framework, provider, database, runtime, API, and web implementation details do
not become canonical Curios semantics.

## Security Freeze

The final M0 security topology authorizes only the frozen current surfaces:

- BOOT package, app, test, infrastructure, and documentation surfaces;
- `packages/python/curios_persistence`;
- `packages/python/curios_policy`;
- exact authorized `packages/python/curios_runtime` modules;
- exact API and web source/test files;
- exact M0 integration and acceptance test files;
- exact workflow file `.github/workflows/quality-gates.yml`;
- M0 governance/evidence documents.

Security tests preserve governed-file scanning, reference-not-value secret
rules, core authority boundaries, policy `UNKNOWN` safety, exact GitHub
workflow authorization, exact API/web/provider/runtime/test topology, and M1+
blocking.

## CI Freeze

The final workflow is the validated TASK-M0-011 quality-gates workflow. It
includes Python, M0 package, PostgreSQL, integration, BOOT/M0 acceptance, full
pytest, frontend, and repository hygiene gates.

TASK-M0-014 makes no CI changes and does not claim hosted GitHub Actions
execution as M0 closure evidence. The frozen M0 authority accepts local/static
verification and TASK-M0-013 independent verification for closure.

## Acceptance and Verification

M0 closure relies on:

- TASK-M0-010 integration PASS;
- TASK-M0-012 acceptance PASS for VS-M0-001 through VS-M0-004;
- TASK-M0-013 independent verification PASS;
- final TASK-M0-014 closure checks.

## Dependency Freeze

The final M0 dependency state remains unchanged by closure:

- persistence owns Alembic, SQLAlchemy, and psycopg;
- policy depends only on canonical contracts;
- runtime depends on contracts, core, persistence, and policy;
- API owns FastAPI as the outer service framework;
- web owns React/Vite/Vitest/TypeScript presentation tooling;
- PyYAML remains dev/test-only for workflow/security validation.

## Known Non-Blocking Warnings

The accepted local verification surface reports two existing dependency
warnings:

- FastAPI/Starlette `TestClient` `httpx` deprecation warning;
- anyio `BlockingPortal` alias deprecation warning.

They are recorded technical debt and are not M0 closure blockers.

## Next Program State

NEXT: AUTHORIZATION REQUIRED

No executable M1 or post-M0 task pack is present in the frozen repository
artifacts at M0 closure. M0 final freeze does not authorize post-M0
implementation.
