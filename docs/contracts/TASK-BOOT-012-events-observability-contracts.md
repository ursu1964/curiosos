---
id: CONTRACT-BOOT-012-EVENTS-OBSERVABILITY
title: Event and Observability Canonical Curios Contracts
lifecycle: IMPLEMENTED
artifact_type: contract
authority: authoritative
task: TASK-BOOT-012
---

# Event and Observability Canonical Curios Contracts

This contract defines the M0 Curios-owned event and observability semantics. It
does not define logging, OpenTelemetry integration, event brokers, persistence,
runtime orchestration, UI visualization, provider adapters, or the
Result/Error/Artifact/Evidence/Verification contracts owned by TASK-BOOT-010.

## CONTRACT-BOOT-012-OBS-001 ObservabilityContext

`ObservabilityContext` is a composable context object for relating canonical
runtime facts. It may contain:

| Field | Semantics |
| --- | --- |
| `project_id` | Project scope when the subject belongs to a project. |
| `application_id` | Application scope when the subject belongs to an application. |
| `milestone_id` | Milestone scope when applicable. |
| `workstream_id` | Workstream scope when applicable. |
| `work_id` | Canonical work item when execution or facts derive from work. |
| `execution_id` | One execution attempt when the fact is execution activity. |
| `agent_instance_id` | Runtime agent participant when the fact is agent activity. |
| `principal_ref` | Provider-neutral actor reference for governed actions. |
| `trace_id` | Curios-owned technical/runtime execution path identifier. |
| `correlation_id` | Curios-owned logical grouping identifier. |
| `causation_ref` | Immediate cause of this event, action, or record. |

No field is globally mandatory. Contexts must not fabricate unrelated IDs merely
to satisfy a schema. Runtime execution requires trace context, work-derived
execution has `work_id`, execution activity has `execution_id`, agent activity
has `agent_instance_id`, governed action later requires principal attribution,
and project/application/milestone/workstream IDs exist only when the subject
belongs to those scopes.

## CONTRACT-BOOT-012-CORR-001 Correlation Semantics

`trace_id`, `correlation_id`, `causation_ref`, `work_id`, `execution_id`, and
`agent_instance_id` are distinct concepts:

- `trace_id` is the technical/runtime execution path.
- `correlation_id` is the logical grouping across related work, events,
  requests, and acceptance flows.
- `causation_ref` is the immediate cause of this event, action, or record.
- `work_id` is the canonical work item.
- `execution_id` is one execution attempt.
- `agent_instance_id` is one runtime agent participant.

TASK-BOOT-012 adds the minimum missing primitive `CorrelationId` with the runtime
prefix `cor`. It does not add a distinct `CausationId`. Causation is represented
as a `Reference` to the immediate cause because the cause is an existing fact or
record, most commonly the prior canonical event's `event_id`, rather than a new
generated namespace.

## CONTRACT-BOOT-012-REF-001 Reference

`Reference` is the provider-neutral typed reference used by event producers,
subjects, principals, and causation links. It serializes as:

```json
{
  "ref_type": "work",
  "ref_id": "wrk_..."
}
```

`ref_type` is a stable lower-case Curios-owned type string. `ref_id` is the
canonical identifier in the referenced namespace. This primitive intentionally
does not implement TASK-BOOT-010 artifact, evidence, or verification reference
contracts.

## CONTRACT-BOOT-012-EVT-001 EventEnvelope

`EventEnvelope` is the canonical transport-neutral event fact envelope. It
contains:

| Field | Semantics |
| --- | --- |
| `event_id` | Unique canonical event identifier. |
| `event_type` | Stable serializable event type string. |
| `schema_version` | Explicit envelope/payload schema version. |
| `occurred_at` | Canonical UTC occurrence timestamp. |
| `producer` | Provider-neutral `Reference` for the producer. |
| `subject_ref` | Provider-neutral `Reference` for the primary subject. |
| `observability_context` | `ObservabilityContext` for trace, correlation, scope, and cause. |
| `payload` | JSON-compatible event-specific fact payload. |
| `metadata` | Optional bounded JSON-compatible metadata. |

Events represent canonical facts, not arbitrary log messages. The envelope has
no Kafka, NATS, RabbitMQ, Redis, OpenTelemetry, provider SDK, persistence, API,
or UI semantics.

## CONTRACT-BOOT-012-TYPE-001 Event Type and Version

Event type is a stable lower-case dotted string such as
`execution.started`. It is not derived from a Python class name and must not
encode schema version suffixes such as `.v1`. Schema evolution is expressed by
the separate explicit `schema_version` field.

## CONTRACT-BOOT-012-VOCAB-001 Minimal Runtime Event Vocabulary

The M0/M1-facing runtime vocabulary is intentionally bounded:

```text
work.created
execution.started
execution.completed
execution.failed
provider.invoked
policy.evaluated
approval.requested
approval.resolved
evidence.produced
verification.completed
```

These names establish the event boundary only. Domain payload contracts for
provider invocations, policy decisions, approvals, evidence, and verification
remain owned by later tasks or integration points.

## CONTRACT-BOOT-012-PAYLOAD-001 Payload Safety

`payload` and `metadata` must be JSON-compatible. They must not contain secret
values, arbitrary exception objects, provider-native response objects, or
implicit executable content semantics. JSON shape alone does not prove that a
value is non-sensitive; producers remain responsible for redaction and for
emitting only canonical fact payloads.

`metadata` is optional, transport-neutral, and bounded. It is not a universal
dumping ground for runtime state.

## CONTRACT-BOOT-012-SER-001 Serialization

Serialization follows the frozen conventions:

- snake_case field names;
- stable strings;
- canonical IDs;
- UTC timestamps;
- explicit schema version;
- JSON-compatible values.

## CONTRACT-BOOT-012-OTEL-001 Telemetry Boundary

`TraceId` and `CorrelationId` are Curios-owned. No OpenTelemetry dependency or
semantic convention is part of this contract. Future telemetry adapters may map
Curios identifiers outward without changing these canonical contracts.

## Explicitly Deferred

TASK-BOOT-012 does not implement logging, OpenTelemetry, event transport,
brokers, persistence, scheduler behavior, runtime orchestration, provider
adapters, UI visualization, Result/Error contracts, Artifact/Evidence/
Verification reference contracts, WorkItem, AgentDefinition/Instance,
Capability, ProviderDescriptor, PolicyDecision, API behavior, or TypeScript
contracts.
