"""Minimal JSON-compatible serialization conventions for primitive contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from curios_contracts.identifiers import CuriosId
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.temporal import DurationMilliseconds, UtcTimestamp


@runtime_checkable
class SupportsToJson(Protocol):
    """Protocol for composed contracts with explicit JSON object rendering."""

    def to_json(self) -> object:
        """Return a JSON-compatible representation."""


def to_json_compatible(value: object) -> object:
    """Convert primitive contract values into JSON-compatible Python values.

    ``None`` is preserved as JSON ``null`` when a caller explicitly includes an
    optional field. This helper does not drop null fields or invent defaults.
    """
    if value is None:
        return None
    if isinstance(value, CuriosId | UtcTimestamp | DurationMilliseconds):
        return value.to_json_primitive()
    if isinstance(value, SchemaVersion):
        return value.to_json_primitive()
    if isinstance(value, SupportsToJson):
        return to_json_compatible(value.to_json())
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [to_json_compatible(item) for item in value]

    msg = f"value of type {type(value).__name__} is not a supported contract primitive"
    raise TypeError(msg)


JsonCompatible = Any
