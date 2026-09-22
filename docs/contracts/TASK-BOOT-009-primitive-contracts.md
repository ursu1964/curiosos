---
id: CONTRACT-BOOT-009-PRIMITIVES
title: Primitive Canonical Curios Contracts
lifecycle: IMPLEMENTED
artifact_type: contract
authority: authoritative
task: TASK-BOOT-009
---

# Primitive Canonical Curios Contracts

This contract defines the first primitive CuriosOS semantic layer required by
downstream M0 contracts. Curios contracts define the semantics. Python source,
tests, Pydantic, JSON Schema, TypeScript, database schemas, provider SDKs, and
frameworks are implementation representations only.

## CONTRACT-BOOT-009-ID-001 Runtime Identifiers

Runtime identifiers are opaque, immutable, globally unique values serialized as
strings in this form:

```text
<prefix>_<ULID-style-value>
```

The ULID-style value is a 26-character Crockford Base32 value containing a
48-bit millisecond timestamp component and 80 bits of cryptographic randomness.
The serialized contract does not expose any library-specific ULID object.

Runtime IDs are independent from database primary keys and from Build Pack
human-stable IDs. No frozen runtime prefix table existed before this task, so
TASK-BOOT-009 derives the minimum consistent runtime prefixes below:

| Primitive | Runtime prefix |
| --- | --- |
| `ProjectId` | `prj` |
| `ApplicationId` | `app` |
| `MilestoneId` | `mls` |
| `WorkstreamId` | `wst` |
| `WorkId` | `wrk` |
| `ExecutionId` | `exe` |
| `AgentDefinitionId` | `agd` |
| `AgentInstanceId` | `agi` |
| `CapabilityId` | `cap` |
| `ProviderId` | `prv` |
| `ArtifactId` | `art` |
| `EvidenceId` | `evd` |
| `VerificationId` | `ver` |
| `EventId` | `evt` |
| `TraceId` | `trc` |

Typed identifiers must not silently interchange where runtime validation applies.
The Python implementation maps each primitive to an immutable `str` subtype and
provides `ensure_id_type` for explicit runtime type checks.

## CONTRACT-BOOT-009-TIME-001 Timestamps

Canonical Curios timestamps are timezone-aware wall-clock timestamps serialized
as RFC3339/ISO-8601 strings with UTC `Z` boundaries.

The canonical rule is:

- naive datetimes or timestamp strings are rejected;
- timezone-aware non-UTC input is normalized to UTC;
- zero microseconds serialize with second precision;
- non-zero microseconds serialize with six fractional digits;
- local timezone is not canonical state.

Examples:

```text
2026-09-22T08:15:30Z
2026-09-22T08:15:30.123456Z
```

Monotonic elapsed-time measurement is separate from wall-clock timestamps and is
not modeled by `UtcTimestamp`.

## CONTRACT-BOOT-009-DURATION-001 Durations

The primitive duration convention is non-negative integer milliseconds. Greater
precision is deferred until a downstream contract explicitly requires it.

## CONTRACT-BOOT-009-SCHEMA-001 Schema Version

Canonical schema versions serialize as strings in this form:

```text
major.minor.patch
```

Each component is a non-negative integer with no leading zeros unless the
component is exactly `0`. Schema version is distinct from Python package version,
API version, entity revision, provider version, and Build Pack version. Semantic
ordering is not part of TASK-BOOT-009.

## CONTRACT-BOOT-009-LIFECYCLE-001 Engineering Lifecycle

The frozen engineering/build lifecycle vocabulary is:

```text
DEFINED
SPECIFIED
IMPLEMENTING
IMPLEMENTED
TESTED
VALIDATED
FROZEN
```

This vocabulary is not the runtime lifecycle for work items, agent instances,
execution records, or verification records. Runtime state machines are deferred.

## CONTRACT-BOOT-009-SER-001 Serialization Conventions

Primitive JSON serialization uses:

- snake_case field names;
- stable enum strings;
- canonical ID strings;
- canonical UTC timestamp strings;
- schema-version strings;
- duration integers in milliseconds;
- explicit `null` only when a caller includes an optional field.

TASK-BOOT-009 does not define a universal inherited base object. Downstream
contracts should compose these primitives rather than inherit arbitrary fields.

## Explicitly Deferred

TASK-BOOT-009 does not implement work contracts, agents, capabilities, providers,
events, security/policy, artifact/evidence/result objects, cognition, database
behavior, framework behavior, runtime scheduling, or TypeScript synchronization.
