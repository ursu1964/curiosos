---
id: CONTRACT-BOOT-011-WORK-AGENT
title: Work, Execution, Capability, Provider, and Agent Canonical Curios Contracts
lifecycle: FROZEN
artifact_type: contract
authority: authoritative
task: TASK-BOOT-011
---

# Work, Execution, Capability, Provider, and Agent Contracts

This contract defines the M0 Curios-owned semantic boundary for capabilities,
capability requirements, provider descriptors, bounded work, execution attempts,
agent definitions, and agent instances.

It does not define schedulers, routers, capability resolution, model routing,
provider execution, agent executors, persistence, APIs, cognitive graph
behavior, pattern contracts, or TASK-BOOT-013 security/policy contracts.

## CONTRACT-BOOT-011-CAP-001 Capability

`Capability` is a provider-neutral statement of what can be done. It contains:

| Field | Semantics |
| --- | --- |
| `capability_id` | Canonical typed `CapabilityId`. |
| `key` | Stable lower-snake capability key such as `coding` or `dataset_profiling`. |
| `version` | Explicit semantic contract version for the capability definition. |
| `description` | Human-readable provider-neutral capability meaning. |
| `category` | Small provider-neutral category: cognitive, data, storage, execution, integration, or other. |
| `metadata` | Optional bounded provider-neutral semantic metadata. |

Capabilities must not identify a provider, model, agent, pattern, credential, or
execution method.

## CONTRACT-BOOT-011-CAPREQ-001 CapabilityRequirement

`CapabilityRequirement` represents what bounded work requires. It contains a
typed `capability_id` plus optional provider-neutral hints:

- `quality`;
- `privacy_constraints`;
- `latency_budget_ms`;
- `cost_budget`;
- `resource_constraints`;
- `policy_constraint_refs`.

These fields do not route, score, resolve, or select providers. Policy/risk
facts owned by TASK-BOOT-013 are represented only as frozen `ObjectReference`
values until typed integration is reconciled later.

## CONTRACT-BOOT-011-PRV-001 ProviderDescriptor

`ProviderDescriptor` describes a replaceable implementation/provider. It
contains:

| Field | Semantics |
| --- | --- |
| `provider_id` | Canonical typed `ProviderId`. |
| `provider_type` | Descriptor-level provider category. |
| `version` | Descriptor/schema version for the provider declaration. |
| `declared_capability_ids` | Capability IDs the provider declares it can support. |
| `configuration_requirement_refs` | Optional references to configuration requirements, deferred to TASK-BOOT-013 where needed. |
| `status` | Descriptor-level availability status only. |
| `implementation_metadata` | Bounded non-secret implementation metadata. |

Provider descriptors describe capability. They are not authority grants, do not
contain credentials, and do not define a universal provider execution method.

## CONTRACT-BOOT-011-WORK-001 WorkItem

`WorkItem` is the canonical bounded unit of executable work. Work owns execution
intent and scope. Agents execute bounded work; they do not own milestones or
redefine task scope.

`WorkItem` contains:

- typed `work_id`;
- `work_type`, `title`, and `objective`;
- dependency `WorkId` values, not embedded `WorkItem` objects;
- `required_capabilities`;
- provider-neutral `inputs` and `expected_outputs`;
- deferred `policy_constraint_refs`, `authority_ref`, and `principal_ref`;
- `evidence_requirement_refs`;
- `created_at` and `updated_at`;
- runtime `state`.

The M0 `WorkItemState` vocabulary is:

```text
CREATED
READY
RUNNING
WAITING
COMPLETED
FAILED
CANCELLED
```

This state describes work intent progress. It is distinct from
`EngineeringLifecycle`, `ExecutionState`, and `AgentInstanceState`.

## CONTRACT-BOOT-011-EXEC-001 ExecutionRecord

`ExecutionRecord` represents one attempt to execute a `WorkItem`. It is not the
work item itself.

It contains:

- typed `execution_id`;
- associated typed `work_id`;
- provider-neutral `executor_ref`;
- optional `agent_instance_id`;
- provider `ObjectReference` values;
- `started_at` and optional `ended_at`;
- attempt `state`;
- optional bounded `Result`;
- `evidence_refs`;
- `error_refs` and translated `ContractError` values;
- optional `ObservabilityContext`.

The M0 `ExecutionState` vocabulary is:

```text
CREATED
RUNNING
WAITING
SUCCEEDED
FAILED
CANCELLED
```

This state describes an execution attempt, not engineering lifecycle, work
intent, or agent runtime participation.

## CONTRACT-BOOT-011-AGD-001 AgentDefinition

`AgentDefinition` is a reusable provider-neutral specification of an agent
role. It contains:

- typed `agent_definition_id`;
- stable `name`;
- `version`;
- `purpose`;
- `allowed_capability_ids`;
- optional bounded `constraints`;
- optional `model_requirement_refs`;
- optional input/output contract references.

`AgentDefinition` does not grant runtime authority and does not implement
prompts, personality systems, schedulers, executors, or provider behavior.

## CONTRACT-BOOT-011-AGI-001 AgentInstance

`AgentInstance` is a concrete runtime participant bound to work and optionally
to one execution attempt. It contains:

- typed `agent_instance_id`;
- typed `agent_definition_id`;
- typed `work_id`;
- optional typed `execution_id`;
- runtime `state`;
- optional `ObservabilityContext`;
- deferred `authority_ref` and `principal_ref`;
- `created_at`, optional `started_at`, and optional `ended_at`.

The M0 `AgentInstanceState` vocabulary is:

```text
CREATED
READY
ACTIVE
WAITING
COMPLETED
FAILED
CANCELLED
```

This intentionally preserves future lifecycle extensibility without
implementing sleep/wake/rebirth semantics in M0.

## CONTRACT-BOOT-011-BOUNDARY-001 Architecture Boundaries

The following distinctions are normative:

- Capability is not Provider.
- Capability is not Agent.
- Capability is not Pattern.
- AgentDefinition is not AgentInstance.
- Work owns execution intent.
- ExecutionRecord is one attempt for a WorkItem.
- Provider capability is not caller authority.

TASK-BOOT-011 does not implement Pattern contracts.

## CONTRACT-BOOT-011-SEC-001 Security and Policy Deferral

TASK-BOOT-013 owns Principal/security identity, Authority, Permission,
EffectClassification, Risk classification, PolicyDecision, Approval,
SecretReference, and ConfigurationProfile.

TASK-BOOT-011 uses only frozen `ObjectReference` fields where those future
security/policy concepts must be referenced:

- `policy_constraint_refs`;
- `authority_ref`;
- `principal_ref`;
- `configuration_requirement_refs`.

The integrated M0 baseline preserves these as `ObjectReference` fields. A
principal or authority reference is runtime attribution or authorization
provenance; it is not an embedded security record. `policy_constraint_refs`
remain generic because a policy constraint/rule contract is distinct from
`PolicyDecision`. `configuration_requirement_refs` remain generic because a
configuration requirement is distinct from `ConfigurationProfile`.

## CONTRACT-BOOT-011-SER-001 Serialization

Serialization follows the frozen conventions:

- snake_case field names;
- stable string enums;
- canonical typed IDs;
- UTC timestamps;
- JSON-compatible structures;
- explicit optional `null` fields where emitted;
- no provider-native objects.

## Explicitly Deferred

TASK-BOOT-011 does not implement schedulers, routers, agents, providers,
provider execution engines, capability resolvers, model routers, APIs, database
persistence, cognitive graph behavior, patterns, credentials, or TASK-BOOT-013
policy/security contracts.
