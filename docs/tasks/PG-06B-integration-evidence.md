---
id: PG-06B-INTEGRATION-EVIDENCE
title: PG-06B M0 Contract Baseline Integration Evidence
lifecycle: IMPLEMENTED
artifact_type: evidence
authority: authoritative
tasks:
  - TASK-BOOT-011
  - TASK-BOOT-013
---

# PG-06B M0 Contract Baseline Integration Evidence

PG-06B integrated independently validated commits:

- TASK-BOOT-011: `b6368444ca4e9498bf8c569c11a605055ded40d1`
- TASK-BOOT-013: `6679224e6684a8b7be885a6685020308ff0313e3`

The resulting integrated baseline is the canonical M0 contract baseline for:

- TASK-BOOT-009 primitive contracts;
- TASK-BOOT-010 result, error, artifact, evidence, verification, and
  `ObjectReference` contracts;
- TASK-BOOT-011 work, execution, capability, provider descriptor, and agent
  contracts;
- TASK-BOOT-012 event and observability contracts;
- TASK-BOOT-013 configuration, security, effect, and policy contracts.

This does not declare BOOT-000 complete.

## Integration

| Subject | Result |
| --- | --- |
| Pre-integration baseline | `main` was at `8f606631011139c8e05b2668f690e4addde44770`. |
| TASK-BOOT-011 merge | Merged without conflicts. |
| TASK-BOOT-013 merge | One expected conflict in `curios_contracts/__init__.py`; resolved by preserving the union of public exports from TASK-BOOT-011 and TASK-BOOT-013. |
| TASK-BOOT-011 status | Recorded as `VALIDATED, FROZEN`. |
| TASK-BOOT-013 status | Recorded as `VALIDATED, FROZEN`. |
| TASK-BOOT-014+ status | Not modified beyond frozen planning state. |
| Outstanding verification | `BOOT-VERIFY-PG-READINESS-001` remains open. |

## Cross-Contract Reference Decisions

`ObjectReference(kind, ref_id)` remains the only generic canonical reference
abstraction.

Work, execution, and agent contracts preserve `ObjectReference` fields for
cross-aggregate security/governance relationships:

- `principal_ref` remains a reference to a principal for runtime attribution.
- `authority_ref` remains a reference to an authority grant or record.
- `policy_constraint_refs` remain references because a policy constraint/rule is
  not the same concept as `PolicyDecision`.
- `configuration_requirement_refs` remain references because configuration
  requirement and `ConfigurationProfile` are distinct concepts.

TASK-BOOT-011 does not embed `Principal`, `Authority`, `PolicyDecision`,
`Approval`, or `ConfigurationProfile` objects into `WorkItem`,
`ExecutionRecord`, or `AgentInstance`.

## Semantic Checks

The integrated baseline preserves these distinctions:

- Capability is not Provider.
- Capability is not Agent.
- Provider capability is not caller authority.
- AgentDefinition is not AgentInstance.
- WorkItem is not ExecutionRecord.
- Effect is not Risk.
- Permission is not Authority.
- PolicyDecision is not Approval.
- Principal is not credentials.
- SecretReference is not a secret value.
- EngineeringLifecycle is separate from WorkItemState, ExecutionState, and
  AgentInstanceState.

Detailed deterministic check results are reported in the PG-06B checkpoint
response.

## Deterministic Checks

| Check | Result |
| --- | --- |
| TOML validation | Passed for root and Python package `pyproject.toml` files. |
| `uv lock --check` | Passed. |
| `uv sync --locked --all-groups --all-packages` | Passed. |
| `uv run ruff check .` | Passed. |
| `uv run ruff format --check .` | Passed: 72 files already formatted. |
| `uv run --package curios-contracts mypy packages/python` | Passed: no issues found in 40 source files. |
| `uv run --package curios-contracts pytest packages/python/curios_contracts/tests -q` | Passed: 114 tests passed. |
| Serialization inspection | Passed. |
| Architecture/import scan | Passed. |
| Duplicate generic-reference scan | Passed: one `ObjectReference` class and no generic `Reference` class. |
| Secret-field source scan | Passed: no source secret-value fields or credential-shaped source literals. |
| Lifecycle/state separation scan | Passed. |
| Exact security-vocabulary checks | Passed. |
| `git diff --check` | Passed. |
