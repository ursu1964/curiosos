---
id: CONTRACT-BOOT-010-RESULT-EVIDENCE
title: Result, Error, Artifact, Evidence, and Verification Contracts
lifecycle: IMPLEMENTED
artifact_type: contract
authority: authoritative
task: TASK-BOOT-010
---

# Result, Error, Artifact, Evidence, and Verification Contracts

TASK-BOOT-010 defines portable CuriosOS M0 semantic structures for structured
errors, result envelopes, artifact references, evidence references, and
verification references. These contracts compose the frozen TASK-BOOT-009
primitive IDs and UTC timestamp rules.

This task does not define storage, providers, verification engines, testing
engines, runtime orchestration, EventEnvelope, or ObservabilityContext.

## CONTRACT-BOOT-010-REF-001 ObjectReference

`ObjectReference` is the smallest provider-neutral reference primitive used by
TASK-BOOT-010 for `subject_ref`, `producer_ref`, `verifier_ref`, and storage
provider references.

Fields:

| Field | Semantics |
| --- | --- |
| `kind` | Stable lower-snake namespace derived from a frozen Curios runtime ID type. |
| `ref_id` | Canonical TASK-BOOT-009 runtime ID string with a prefix matching `kind`. |

Supported kinds are `project`, `application`, `milestone`, `workstream`, `work`,
`execution`, `agent_definition`, `agent_instance`, `capability`, `provider`,
`artifact`, `evidence`, `verification`, and `trace`.

The reference preserves namespace meaning without implementing the full object
hierarchy for the referenced object.

## CONTRACT-BOOT-010-ERR-001 ContractError

`ContractError` is a safe, provider-neutral error structure for cross-boundary
translation.

Fields:

| Field | Semantics |
| --- | --- |
| `error_code` | Stable 3-64 character uppercase machine code. |
| `message` | Safe human-readable message, bounded to 1024 characters. |
| `category` | One of `validation`, `authorization`, `not_found`, `conflict`, `rate_limit`, `timeout`, `dependency`, `internal`. |
| `severity` | One of `info`, `warning`, `error`, `critical`. |
| `retryable` | Explicit boolean retry hint after translation. |
| `subject_ref` | Optional `ObjectReference` for the object the error concerns. |
| `trace_id` | Optional TASK-BOOT-009 `TraceId` for narrow traceability. |
| `details` | Optional bounded JSON-compatible safe details. |

Security constraints:

- no exception objects;
- no stack traces;
- no provider-native exception structures;
- no credentials or secrets;
- no arbitrary environment state;
- detail keys and values are bounded and JSON-compatible.

`ResultWarning` is a separate structured warning contract. Warnings are not
encoded as `ContractError` values.

## CONTRACT-BOOT-010-RES-001 Result

`Result[T]` is a bounded generic envelope for useful operation boundaries. It is
not required for every internal domain method.

Fields:

| Field | Semantics |
| --- | --- |
| `status` | `success` or `failure`. |
| `value` | Optional JSON-compatible result value. |
| `evidence_refs` | Zero or more `EvidenceReference` or `EvidenceId` values. |
| `warnings` | Zero or more `ResultWarning` values. |
| `errors` | Zero or more `ContractError` values. |

Invariants:

- `success` results must not contain errors;
- `failure` results must contain at least one error;
- `failure` results must not contain a value;
- warnings remain structurally distinct from errors.

## CONTRACT-BOOT-010-ART-001 ArtifactReference

`ArtifactReference` identifies an artifact without granting access to it.

Fields:

| Field | Semantics |
| --- | --- |
| `artifact_id` | TASK-BOOT-009 `ArtifactId`. |
| `kind` | One of `document`, `dataset`, `image`, `audio`, `video`, `model_output`, `log`, `binary`, `other`. |
| `locator` | Provider-neutral locator string. |
| `storage_provider_ref` | Optional `ObjectReference` whose kind is `provider`. |
| `media_type` | Optional type/subtype media type. |
| `integrity` | Optional algorithm/value `IntegrityDescriptor`. |
| `created_at` | Canonical UTC timestamp. |
| `producer_ref` | Optional `ObjectReference`. |

Locator rules:

- a locator does not grant permission;
- a locator is not assumed to be a filesystem path;
- a locator is not assumed to be an object-store key;
- a locator is not assumed to be a network URI;
- access authorization is outside this contract;
- locators must not contain secret-shaped key/value material.

Portable integrity algorithms are `sha256`, `sha512`, and `blake3`.

## CONTRACT-BOOT-010-EVD-001 EvidenceReference

`EvidenceReference` references evidence without becoming the complete evidence
record or provenance model.

Fields:

| Field | Semantics |
| --- | --- |
| `evidence_id` | TASK-BOOT-009 `EvidenceId`. |
| `kind` | One of `test_result`, `inspection`, `log_excerpt`, `human_attestation`, `provider_report`, `artifact`, `other`. |
| `subject_ref` | Required `ObjectReference`. |
| `artifact_refs` | Zero or more `ArtifactReference` or `ArtifactId` values. |
| `collected_at` | Canonical UTC timestamp. |
| `summary` | Optional bounded human-readable summary. |
| `trace_id` | Optional TASK-BOOT-009 `TraceId`. |

## CONTRACT-BOOT-010-VER-001 VerificationReference

`VerificationReference` references a verification result without implementing a
verification engine. Implementation success is not validation.

Fields:

| Field | Semantics |
| --- | --- |
| `verification_id` | TASK-BOOT-009 `VerificationId`. |
| `subject_ref` | Required `ObjectReference`. |
| `outcome` | One of `passed`, `failed`, `inconclusive`, `not_evaluated`. |
| `evidence_refs` | Zero or more relevant `EvidenceReference` or `EvidenceId` values. |
| `verifier_ref` | Optional `ObjectReference` for the verifier. |
| `verified_at` | Canonical UTC timestamp. |

## Serialization

All TASK-BOOT-010 contracts serialize to JSON-compatible objects using:

- snake_case field names;
- stable string enums;
- canonical TASK-BOOT-009 ID strings;
- canonical UTC timestamp strings;
- explicit `null` for absent optional object fields;
- arrays for repeated references.

## Explicitly Deferred

TASK-BOOT-010 does not implement WorkItem, ExecutionRecord, Capability,
ProviderDescriptor, AgentDefinition, AgentInstance, EventEnvelope,
ObservabilityContext, PolicyDecision, effects/permissions, providers, storage,
APIs, database models, or validation/freeze authority.
