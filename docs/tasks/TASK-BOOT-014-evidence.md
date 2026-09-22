---
id: TASK-BOOT-014-EVIDENCE
title: TASK-BOOT-014 Contract and Schema Test Foundation Evidence
lifecycle: TESTED
artifact_type: evidence
authority: implementation_agent
task: TASK-BOOT-014
---

# TASK-BOOT-014 Contract and Schema Test Foundation Evidence

## Lifecycle Trace

| Step | Status | Evidence |
| --- | --- | --- |
| 1 | IMPLEMENTING | Worktree verified on `task/boot-014-contract-tests` at required base `ad9901090f57a76249989fa882b8774d14f79875`; TASK-BOOT-014 implementation began. |
| 2 | IMPLEMENTED | Repository-level contract/schema test lanes, deterministic fixtures, and pytest discovery configuration were added for TASK-BOOT-014 scope. |
| 3 | TESTED | Required deterministic checks were run after implementation; see check evidence below. |

## Implementation Summary

- Shared deterministic fixtures: `tests/fixtures/contract_fixtures.py`.
- Repository contract tests: `tests/contract/test_cross_contract_boundaries.py`.
- Repository schema/serialization tests: `tests/schema/test_contract_serialization.py`.
- Pytest discovery support: root `pyproject.toml` adds `pythonpath` entries for the canonical Python contracts package and shared test fixtures.
- Status evidence: this document and the TASK-BOOT-014 row in `docs/program/status-ledger/BOOT-000-task-ledger.md`.

No canonical contract implementation files were modified.

## Contract Test Categories

- Primitive compatibility: typed ID serialization, UTC/RFC3339 timestamps, schema-version strings, and engineering lifecycle separation from runtime states.
- Reference compatibility: `ObjectReference` namespace validation and round-trip behavior across contract families.
- Work/security boundary: work, execution, and agent runtime records keep authority/principal/policy links bounded as references.
- Capability/provider boundary: capabilities and requirements remain provider-neutral; providers declare capability IDs without becoming authority records.
- Event/observability boundary: events use `ObjectReference`, keep trace/correlation IDs distinct, use reference-based causation, and remain transport-neutral.
- Security boundary: exact effect/risk/policy-decision vocabularies, `UNKNOWN` distinct from `DENY`, approval outcomes separate from effects, and secret references without secret values.
- Result/evidence boundary: result success/failure invariants, evidence/verification references remain records rather than engines, and artifact locators remain provider-neutral.

## Schema and Serialization Strategy

TASK-BOOT-014 tests the actual frozen serialization contract:

- JSON-compatible output via `to_json_compatible`, `to_json`, and JSON encode/decode.
- Snake-case serialized field names.
- Stable enum strings.
- Canonical typed IDs.
- UTC timestamp strings with `Z`.
- Stable schema-version strings.
- Optional/null semantics for aggregate fields and contextual omission for `ObservabilityContext`.
- Round-trip behavior for contracts that expose `from_json_compatible` or `from_json`.

The current implementation does not use Pydantic as semantic authority and does not expose formal generated JSON Schema. TASK-BOOT-014 does not add or fake JSON Schema generation; formal generated JSON Schema remains a later derived representation.

## Fixtures and Isolation

- Fixtures are deterministic and synthetic.
- No production data is used.
- No real secrets are used.
- No live providers are used.
- No Ollama, PostgreSQL, Docker, database, or network dependency is required.
- Tests mutate no repository state and require no filesystem writes beyond normal pytest cache behavior.

## Check Evidence

| Check | Result |
| --- | --- |
| Required base and branch | Passed: branch `task/boot-014-contract-tests` at base `ad9901090f57a76249989fa882b8774d14f79875`. |
| Existing package-local contract tests | Passed: `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` reported 114 passed. |
| New repository contract tests | Passed: `uv run pytest tests/contract -q` reported 10 passed. |
| New repository schema tests | Passed: `uv run pytest tests/schema -q` reported 5 passed. |
| Full pytest suite | Passed: `uv run pytest -q` reported 129 passed. |
| Ruff check | Passed: `uv run ruff check .`. |
| Ruff format check | Passed: `uv run ruff format --check .`. |
| mypy strict baseline | Passed: `uv run --package curios-contracts mypy packages/python` reported no issues in 40 source files. |
| Diff whitespace | Passed: `git diff --check`. |
| Scope review | Passed: changes are limited to `tests/contract/**`, `tests/schema/**`, `tests/fixtures/**`, root pytest discovery configuration, and TASK-BOOT-014 docs/status evidence. `tooling/curios` and canonical contract implementations were not modified. |

## Defects

No frozen-contract defect was discovered.

## Final Status

`TASK-BOOT-014` is `TESTED`. This task does not self-declare `VALIDATED` or `FROZEN`.
