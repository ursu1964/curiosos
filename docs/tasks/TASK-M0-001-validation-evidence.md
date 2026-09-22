---
id: TASK-M0-001-VALIDATION-EVIDENCE
title: TASK-M0-001 Independent Validation Evidence
lifecycle: VALIDATED
artifact_type: validation_evidence
authority: independent_validation
task_id: TASK-M0-001
milestone_id: M0
date: 2026-09-22
---

# TASK-M0-001 Independent Validation Evidence

## Decision

TASK-M0-001 VALIDATION: PASS

Validated candidate:

`2ef5aea32c2cca1c6f36ba6fdb41fa61e9aefe16`

Starting M0 authority baseline:

`3f0776250b99b7652885dc01539c98e8b1948868`

## Acceptance Matrix

| Criterion | Result | Evidence |
| --- | --- | --- |
| Exact M0 topology guardrail mechanism exists | PASS | Security baseline records planned M0 surfaces separately from currently authorized surfaces. |
| Planned surfaces are not authorized merely by being planned | PASS | Current tracked package roots are still checked against the frozen authorized package set; planned M0 package roots fail while tracked early. |
| Current tracked topology remains exact | PASS | Top-level, package, app, `.github`, integration, and acceptance roots remain bounded by structural checks. |
| Future tasks can authorize only their own surfaces | PASS | M0 planned roots are represented by owning task; later task changes can update only the relevant task-owned surface. |
| Runtime/product implementation absent | PASS | Diff contains no production persistence, policy, event store, work repository, runtime service, provider executor, API route, or web console implementation. |
| Frozen BOOT security invariants preserved | PASS | Existing secret scanning, secret-field, policy `UNKNOWN`, core authority, provider/API/web, `.github`, integration, and acceptance checks remain active and pass. |
| Architecture direction preserved | PASS | `curios_contracts` and `curios_core` are guarded against dependencies on planned M0 implementation packages. |
| M1+ deferred scope blocked | PASS | Representative M1+ package roots and broad runtime/service/provider roots are rejected; M0 docs preserve deferred scope. |
| Verification green | PASS | Complete deterministic verification passed locally; warnings are known dependency deprecations. |

## Scope Audit

Changed files are limited to:

- M0 guardrail documentation;
- M0 task evidence;
- M0 status ledger;
- architecture conformance tests;
- security baseline tests.

No production implementation changed under contracts, core, providers, API, web,
database, infrastructure, or CI.

## Adversarial Review

The validation reviewed representative unauthorized additions:

- `packages/python/curios_persistence`, `curios_policy`, and `curios_runtime`
  before their owning tasks;
- plausible M1+ package roots for agent runtime, model routing, knowledge,
  DataLab, and secret resolution;
- broad top-level `runtime`, `services`, and `providers` roots;
- unrelated app roots;
- additional `.github` paths;
- additional integration or acceptance tests beyond frozen BOOT surfaces.

Within the governed repository topology, those tracked surfaces would fail the
current security topology checks.

## Mechanical Verification

| Check | Result |
| --- | --- |
| TOML validation | PASS |
| `uv lock --check` | PASS |
| `uv sync --locked --all-groups --all-packages` | PASS |
| Docker Compose config | PASS |
| Ruff | PASS |
| Ruff format | PASS |
| mypy strict baseline | PASS |
| Package/API/provider tests | PASS |
| Contract tests | PASS |
| Schema tests | PASS |
| Architecture tests | PASS |
| Security tests | PASS |
| API integration | PASS |
| PostgreSQL integration | PASS |
| BOOT acceptance | PASS |
| Full pytest | PASS |
| Frontend checks/build | PASS |
| `git diff --check` | PASS |

## Lifecycle Transition

TASK-M0-001 is `VALIDATED, FROZEN`.

According to the frozen M0 DAG, the next executable units are:

- TASK-M0-002 — PostgreSQL Runtime Persistence Foundation;
- TASK-M0-003 — Minimal Policy Evaluator.

They may proceed in parallel only after the TASK-M0-001 validation/freeze
commit is integrated into the main M0 baseline. TASK-M0-004 through TASK-M0-014
remain blocked.
