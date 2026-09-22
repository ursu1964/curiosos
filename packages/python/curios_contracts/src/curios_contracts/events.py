"""Canonical transport-neutral event contracts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Self

from curios_contracts.identifiers import EventId
from curios_contracts.observability import ObservabilityContext
from curios_contracts.references import Reference
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp

_EVENT_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_MAX_METADATA_ENTRIES = 16
_MAX_METADATA_KEY_LENGTH = 64


class EventType(str):
    """Stable, serializable event type string independent from schema version."""

    def __new__(cls, value: str) -> Self:
        if not isinstance(value, str):
            msg = "event type requires a string value"
            raise TypeError(msg)
        if _EVENT_TYPE_RE.fullmatch(value) is None:
            msg = "event type must be a non-empty lower-case dotted string"
            raise ValueError(msg)
        if re.fullmatch(r"v[0-9]+", value.rsplit(".", maxsplit=1)[-1]) is not None:
            msg = "event type must not encode schema version"
            raise ValueError(msg)
        return str.__new__(cls, value)

    def to_json_primitive(self) -> str:
        """Return the canonical JSON-compatible string representation."""
        return str(self)


class RuntimeEventType(Enum):
    """Minimal M0/M1-facing runtime event vocabulary."""

    WORK_CREATED = EventType("work.created")
    EXECUTION_STARTED = EventType("execution.started")
    EXECUTION_COMPLETED = EventType("execution.completed")
    EXECUTION_FAILED = EventType("execution.failed")
    PROVIDER_INVOKED = EventType("provider.invoked")
    POLICY_EVALUATED = EventType("policy.evaluated")
    APPROVAL_REQUESTED = EventType("approval.requested")
    APPROVAL_RESOLVED = EventType("approval.resolved")
    EVIDENCE_PRODUCED = EventType("evidence.produced")
    VERIFICATION_COMPLETED = EventType("verification.completed")


RUNTIME_EVENT_TYPES: tuple[EventType, ...] = tuple(
    event_type.value for event_type in RuntimeEventType
)


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """Canonical event fact envelope without broker or telemetry coupling."""

    event_id: EventId
    event_type: EventType
    schema_version: SchemaVersion
    occurred_at: UtcTimestamp
    producer: Reference
    subject_ref: Reference
    observability_context: ObservabilityContext
    payload: object = field(default_factory=dict)
    metadata: object = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_type(self.event_id, EventId, "event_id")
        _require_type(self.event_type, EventType, "event_type")
        _require_type(self.schema_version, SchemaVersion, "schema_version")
        _require_type(self.occurred_at, UtcTimestamp, "occurred_at")
        _require_type(self.producer, Reference, "producer")
        _require_type(self.subject_ref, Reference, "subject_ref")
        _require_type(
            self.observability_context,
            ObservabilityContext,
            "observability_context",
        )
        _ensure_json_object(self.payload, "payload")
        _ensure_metadata(self.metadata)

    @classmethod
    def from_json(cls, value: object) -> Self:
        """Parse an event envelope from canonical JSON object form."""
        if not isinstance(value, dict):
            msg = "event envelope JSON value must be an object"
            raise TypeError(msg)

        try:
            event_id = value["event_id"]
            event_type = value["event_type"]
            schema_version = value["schema_version"]
            occurred_at = value["occurred_at"]
            producer = value["producer"]
            subject_ref = value["subject_ref"]
            observability_context = value["observability_context"]
            payload = value["payload"]
        except KeyError as exc:
            msg = "event envelope JSON value is missing a required field"
            raise ValueError(msg) from exc

        if not all(
            isinstance(item, str) for item in (event_id, event_type, schema_version, occurred_at)
        ):
            msg = "event_id, event_type, schema_version, and occurred_at must be strings"
            raise TypeError(msg)

        return cls(
            event_id=EventId(event_id),
            event_type=EventType(event_type),
            schema_version=SchemaVersion.parse(schema_version),
            occurred_at=UtcTimestamp.parse(occurred_at),
            producer=Reference.from_json(producer),
            subject_ref=Reference.from_json(subject_ref),
            observability_context=ObservabilityContext.from_json(observability_context),
            payload=payload,
            metadata=value.get("metadata", {}),
        )

    def to_json(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        serialized: dict[str, object] = {
            "event_id": str(self.event_id),
            "event_type": str(self.event_type),
            "schema_version": str(self.schema_version),
            "occurred_at": str(self.occurred_at),
            "producer": self.producer.to_json(),
            "subject_ref": self.subject_ref.to_json(),
            "observability_context": self.observability_context.to_json(),
            "payload": _ensure_json_object(self.payload, "payload"),
        }
        metadata = _ensure_metadata(self.metadata)
        if metadata:
            serialized["metadata"] = metadata
        return serialized


def _require_type[ValueT](value: object, expected_type: type[ValueT], field_name: str) -> None:
    if not isinstance(value, expected_type):
        msg = f"{field_name} must be {expected_type.__name__}"
        raise TypeError(msg)


def _ensure_json_object(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        msg = f"{field_name} must be a JSON-compatible object"
        raise TypeError(msg)
    if any(not isinstance(key, str) for key in value):
        msg = f"{field_name} keys must be strings"
        raise TypeError(msg)
    try:
        compatible = to_json_compatible(value)
    except TypeError as exc:
        msg = f"{field_name} contains a non-JSON-compatible value"
        raise TypeError(msg) from exc
    if not isinstance(compatible, dict):
        msg = f"{field_name} must serialize to a JSON object"
        raise TypeError(msg)
    try:
        json.dumps(compatible, allow_nan=False, sort_keys=True)
    except TypeError as exc:
        msg = f"{field_name} contains a non-JSON-compatible value"
        raise TypeError(msg) from exc
    except ValueError as exc:
        msg = f"{field_name} contains a non-finite numeric value"
        raise ValueError(msg) from exc
    return compatible


def _ensure_metadata(value: object) -> dict[str, object]:
    metadata = _ensure_json_object(value, "metadata")
    if len(metadata) > _MAX_METADATA_ENTRIES:
        msg = "metadata must not contain more than 16 top-level entries"
        raise ValueError(msg)
    for key in metadata:
        if key == "" or len(key) > _MAX_METADATA_KEY_LENGTH:
            msg = "metadata keys must be 1 to 64 characters"
            raise ValueError(msg)
    return metadata
