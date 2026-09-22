---
id: TASK-BOOT-011-EVIDENCE
title: TASK-BOOT-011 Work and Agent Contract Evidence
lifecycle: TESTED
artifact_type: evidence
authority: task
task: TASK-BOOT-011
---

# TASK-BOOT-011 Evidence

## Status

TASK-BOOT-011 moved through:

```text
IMPLEMENTING
IMPLEMENTED
TESTED
```

This task does not self-declare `VALIDATED` or `FROZEN`.

## Contracts Added

- `Capability`
- `CapabilityRequirement`
- `ProviderDescriptor`
- `WorkItem`
- `ExecutionRecord`
- `AgentDefinition`
- `AgentInstance`

Supporting enum vocabularies added:

- `CapabilityCategory`
- `CapabilityQuality`
- `ProviderType`
- `ProviderStatus`
- `WorkItemState`
- `ExecutionState`
- `AgentInstanceState`

## Runtime States

`WorkItemState`:

```text
CREATED, READY, RUNNING, WAITING, COMPLETED, FAILED, CANCELLED
```

`ExecutionState`:

```text
CREATED, RUNNING, WAITING, SUCCEEDED, FAILED, CANCELLED
```

`AgentInstanceState`:

```text
CREATED, READY, ACTIVE, WAITING, COMPLETED, FAILED, CANCELLED
```

Inspection confirmed these are distinct enum classes and are not aliases of
`EngineeringLifecycle`.

## Security and Policy Reference Strategy

TASK-BOOT-013-owned concepts were not implemented. Where work, provider, and
agent contracts need future security/policy linkage, TASK-BOOT-011 uses frozen
`ObjectReference` fields:

- `policy_constraint_refs`
- `authority_ref`
- `principal_ref`
- `configuration_requirement_refs`

Typed integration with TASK-BOOT-013 remains a future reconciliation point.

## Dependencies

The implementation reuses frozen TASK-BOOT-009/010/012 contracts:

- typed IDs including `CapabilityId`, `ProviderId`, `WorkId`, `ExecutionId`,
  `AgentDefinitionId`, and `AgentInstanceId`;
- `UtcTimestamp`;
- `SchemaVersion`;
- `ObjectReference`;
- `Result`, `ContractError`, `EvidenceReference`, and `EvidenceId`;
- `ObservabilityContext`.

No runtime or provider dependencies were added.

## Checks

Required checks completed on 2026-09-22:

| Check | Result |
| --- | --- |
| TOML validation | PASS |
| `uv lock --check` | PASS |
| `uv sync --frozen` | PASS |
| Ruff | PASS |
| Ruff format check | PASS |
| mypy | PASS |
| full `curios_contracts` tests | PASS, 87 tests |
| serialization inspection | PASS |
| architecture/import scan | PASS |
| duplicate reference scan | PASS, exactly one `ObjectReference` class |
| lifecycle/state separation inspection | PASS |
| `git diff --check` | PASS |
| complete scope review | PASS |

## Architecture Checks

Inspection found:

- no TASK-BOOT-013 contract class implementations;
- no provider/framework imports;
- no scheduler/router/runtime engine implementation classes;
- exactly one `ObjectReference` abstraction;
- no TypeScript changes.

## Cross-Task Integration

No blocking cross-task integration issue was discovered. The only expected
follow-up is later typed reconciliation with TASK-BOOT-013 security/policy
contracts where `ObjectReference` fields currently preserve the boundary.
