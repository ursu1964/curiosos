---
id: TASK-BOOT-009-INTEGRATION-EVIDENCE
title: TASK-BOOT-009 Integration Evidence
lifecycle: TESTED
artifact_type: integration_evidence
authority: evidence
task: TASK-BOOT-009
---

# TASK-BOOT-009 Integration Evidence

## Scope

This record covers integration of the independently validated primitive
canonical contracts into `main`.

Validated task commit:

- `fccfbe35c337f7c1c7107e10fc6e8f221eb74df0`

## Merge And Status

- Merge commit before status reconciliation: `42af051`.
- Conflicts: none.
- Status ledger reconciliation: `TASK-BOOT-009` recorded as `VALIDATED, FROZEN`.
- `TASK-BOOT-010` through `TASK-BOOT-013` implementation states were not changed.

## Deterministic Checks

| Check | Result |
| --- | --- |
| TOML validation for root and Python package metadata | passed |
| `uv lock --check` | passed |
| `uv sync --locked --all-groups --all-packages` | passed |
| `uv run ruff check .` | passed |
| `uv run ruff format --check .` | passed |
| `uv run --package curios-contracts mypy packages/python` | passed |
| `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` | passed, 30 tests |
| `uv run --package curios-contracts pytest --collect-only` | passed, 30 tests collected |
| `git diff --check` | passed |

## Semantic Inspection

| Requirement | Result |
| --- | --- |
| Runtime IDs remain opaque typed strings | passed |
| Database IDs are not canonical identity | passed; docs distinguish runtime IDs from database primary keys |
| ID serialization does not expose implementation-library objects | passed |
| Timestamp input rejects naive datetime | passed |
| Timezone-aware non-UTC input normalizes to UTC | passed |
| Serialized timestamp uses canonical `Z` | passed |
| `SchemaVersion` is distinct from package/API/entity/provider versions | passed |
| `EngineeringLifecycle` values are exactly `DEFINED`, `SPECIFIED`, `IMPLEMENTING`, `IMPLEMENTED`, `TESTED`, `VALIDATED`, `FROZEN` | passed |
| No runtime lifecycle was introduced | passed |
| No provider/framework imports exist in canonical primitives | passed |
| Serialization remains JSON-compatible | passed |

## ID Alphabet And Length Tests

The documented ID contract specifies a 26-character Crockford Base32 ULID-style
suffix. Tests verify generated suffix length and reject malformed suffixes,
including invalid characters. The integration semantic inspection additionally
verified generated suffixes are contained within the documented alphabet.

## Architecture And Scope

Import scan found only standard-library imports and local `curios_contracts`
module imports in primitive source.

No implementation was introduced for:

- Result/Error;
- Artifact/Evidence/Verification object contracts beyond primitive ID types;
- WorkItem;
- ExecutionRecord;
- Capability models beyond primitive `CapabilityId`;
- ProviderDescriptor;
- AgentDefinition or AgentInstance object models beyond primitive ID types;
- EventEnvelope;
- ObservabilityContext;
- security/effect/policy contracts;
- provider implementations;
- API/runtime behavior.

## Preserved Deferred Item

`BOOT-VERIFY-PG-READINESS-001` remains open and deferred for final BOOT-000
acceptance.
