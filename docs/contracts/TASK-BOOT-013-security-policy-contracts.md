---
id: CONTRACT-BOOT-013-SECURITY-POLICY
title: Configuration, Security, Effect, and Policy Canonical Curios Contracts
lifecycle: IMPLEMENTED
artifact_type: contract
authority: authoritative
task: TASK-BOOT-013
---

# Configuration, Security, Effect, and Policy Canonical Curios Contracts

TASK-BOOT-013 defines the minimum M0 Curios-owned semantics for configuration
profile identity, secret references, principals, permissions, bounded authority,
effects, risk, policy decisions, and approvals.

These contracts are governance records only. They do not implement
authentication, IAM, RBAC, ABAC, policy evaluation, secret resolution, approval
workflow, provider integration, APIs, storage, or TypeScript contracts.

## CONTRACT-BOOT-013-CONFIG-001 ConfigurationProfile

`ConfigurationProfile` identifies a canonical Curios environment profile. The
M0 closed vocabulary contains exactly:

```text
LOCAL_DOCKER
```

Docker Compose implementation profiles such as base, full, and observability
profiles are tooling profiles, not Curios environment profiles. Future Curios
environment profiles require explicit vocabulary extension; they are not read
from environment variables and are not coupled to Pydantic Settings or any
environment-loading implementation.

## CONTRACT-BOOT-013-SECRET-001 SecretReference

`SecretReference` is a provider-neutral pointer to a secret name/key. It may use
exactly one of:

- `resolver_ref`;
- `secret_provider_ref`, which must reference a provider.

It also carries `name`, optional `key`, `scope`, and `purpose`. It never carries
a secret value. Serialization must not resolve the secret, expose provider-native
secret structures, include credential-bearing URLs, or dump environment state.
Access authorization is governed outside the reference itself.

## CONTRACT-BOOT-013-PRINCIPAL-001 Principal

`Principal` describes an actor identity without credentials. Principal types are
exactly:

```text
HUMAN
SERVICE
AGENT_INSTANCE
TOOL_EXECUTOR
PROVIDER
SYSTEM
```

A principal has a type, an identity string, and optional Curios object references
for the represented object, related agent instance, and execution context.
`Principal` is not login state, authentication, session material, OAuth tokens,
API keys, certificates, or provider IAM structure.

## CONTRACT-BOOT-013-PERM-001 Permission

`Permission` is the minimum action/resource/scope/effect abstraction. It
contains:

| Field | Semantics |
| --- | --- |
| `action` | Stable lower-snake action token. |
| `resource_type` | Stable lower-snake resource type token. |
| `resource_ref` | Optional `ObjectReference` to a concrete resource. |
| `scope` | Bounded textual scope. |
| `permitted_effects` | Non-empty collection of allowed `EffectClassification` values. |

Permission is not authority. It does not identify a principal, grantor,
validity period, approval, revocation state, role, RBAC binding, or ABAC rule.

## CONTRACT-BOOT-013-AUTH-001 Authority

`Authority` represents explicit bounded authority granted to a principal. It
contains an authority identity, `Principal`, one or more `Permission` values,
scope, `granted_at`, optional expiration, optional provenance references, and an
optional approval identity.

Authority is the granted boundary. It is not the same as permission, and this
contract does not implement authority issuance, revocation, role assignment,
policy evaluation, or IAM service behavior.

## CONTRACT-BOOT-013-EFFECT-001 EffectClassification

Effects describe consequences. They are separate from risk and separate from
policy outcomes. The M0 vocabulary is exactly:

```text
READ_ONLY
LOCAL_WRITE
EXTERNAL_READ
EXTERNAL_WRITE
DESTRUCTIVE
SECRET_ACCESS
NETWORK_ACCESS
EXECUTION
```

`APPROVAL_REQUIRED` is not an effect. Effects may compose as a collection.

## CONTRACT-BOOT-013-RISK-001 RiskClassification

Risk influences controls; it is not itself permission and is not an effect. The
M0 vocabulary is exactly:

```text
LOW
MODERATE
HIGH
CRITICAL
```

## CONTRACT-BOOT-013-POLICY-001 PolicyDecision

`PolicyDecision` records a policy result without implementing a policy
evaluator. Outcomes are exactly:

```text
ALLOW
DENY
REQUIRES_APPROVAL
UNKNOWN
```

`UNKNOWN` remains distinct from `DENY`. A policy decision records the subject,
principal, requested effects, resource references, scope, outcome, reason,
policy references, optional approval identity, `decided_at`, and optional
`ObservabilityContext`.

## CONTRACT-BOOT-013-UNKNOWN-001 Unknown Policy Semantics

For governed effects, a policy outcome of `UNKNOWN` does not authorize
execution. The contract record must preserve `UNKNOWN` as `UNKNOWN`; it must not
rewrite it into `DENY` to express enforcement behavior.

The enforcement engine is deferred. The canonical contract only preserves the
decision fact and exposes whether the outcome is explicitly authorizing.

## CONTRACT-BOOT-013-APPROVAL-001 Approval

`Approval` is a scoped approval fact. It contains approval identity,
`requested_by`, optional `approved_by` or `rejected_by`, subject reference,
action, requested effects, scope, reason, outcome, requested/decided timestamps,
expiration, bounded conditions, and evidence references.

Approval outcomes are:

```text
PENDING
APPROVED
REJECTED
```

Approval does not imply permanent authority. Any resulting authority must remain
explicit, scoped, and separately bounded.

## CONTRACT-BOOT-013-SEP-001 Required Separations

The M0 contracts preserve these distinctions:

- Effect is not risk.
- Permission is not authority.
- PolicyDecision is not Approval.
- Principal is not credentials.
- SecretReference is not a secret value.

## CONTRACT-BOOT-013-SER-001 Serialization and Security

Serialization follows the frozen conventions from TASK-BOOT-009, TASK-BOOT-010,
and TASK-BOOT-012:

- snake_case field names;
- stable enum strings;
- canonical typed IDs through `ObjectReference` where references are needed;
- canonical UTC timestamps;
- JSON-compatible values.

Security records must not contain secret values, arbitrary exception objects,
credential-bearing URLs, provider-native IAM structures, provider-native secret
structures, or environment dumps.

## CONTRACT-BOOT-013-OBS-001 Observability

Governance records that need traceability use the frozen
`ObservabilityContext`. TASK-BOOT-013 does not define new observability
semantics.

## CONTRACT-BOOT-013-BOUNDARY-001 TASK-BOOT-011 Ownership Boundary

TASK-BOOT-011 owns Capability, CapabilityRequirement, ProviderDescriptor,
WorkItem, ExecutionRecord, AgentDefinition, and AgentInstance contracts.
TASK-BOOT-013 may refer to future entities only through existing typed IDs or
the frozen `ObjectReference`.

TASK-BOOT-013 does not create placeholder WorkItem, ExecutionRecord,
Capability, CapabilityRequirement, ProviderDescriptor, AgentDefinition, or
AgentInstance models.
