"""Runtime identifier primitives for canonical Curios contracts."""

from __future__ import annotations

import re
import secrets
import time
from typing import ClassVar, Self

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_VALUE_RE = re.compile(rf"^[{_ULID_ALPHABET}]{{26}}$")


def _generate_ulid_style_value() -> str:
    """Return a 26-character ULID-style value without exposing a ULID object."""
    timestamp_ms = time.time_ns() // 1_000_000
    if timestamp_ms >= 1 << 48:
        msg = "current timestamp exceeds the 48-bit ULID timestamp range"
        raise OverflowError(msg)

    random_bits = secrets.randbits(80)
    value = (timestamp_ms << 80) | random_bits
    return "".join(_ULID_ALPHABET[(value >> shift) & 0b11111] for shift in range(125, -1, -5))


class CuriosId(str):
    """Opaque runtime identifier serialized as ``<prefix>_<ULID-style-value>``."""

    prefix: ClassVar[str]

    def __new__(cls, value: str) -> Self:
        if cls is CuriosId:
            msg = "CuriosId is an abstract primitive; use a concrete typed ID"
            raise TypeError(msg)
        if not isinstance(value, str):
            msg = f"{cls.__name__} requires a string value"
            raise TypeError(msg)

        expected_prefix = f"{cls.prefix}_"
        if not value.startswith(expected_prefix):
            msg = f"{cls.__name__} must start with {expected_prefix!r}"
            raise ValueError(msg)

        ulid_value = value.removeprefix(expected_prefix)
        if not _ULID_VALUE_RE.fullmatch(ulid_value):
            msg = f"{cls.__name__} must end with a 26-character ULID-style value"
            raise ValueError(msg)

        return str.__new__(cls, value)

    @classmethod
    def generate(cls) -> Self:
        """Generate a new globally unique opaque identifier for this ID type."""
        return cls(f"{cls.prefix}_{_generate_ulid_style_value()}")

    @property
    def ulid_value(self) -> str:
        """Return the provider-neutral ULID-style suffix."""
        return self.removeprefix(f"{self.prefix}_")

    def to_json_primitive(self) -> str:
        """Return the canonical JSON-compatible string representation."""
        return str(self)


class ProjectId(CuriosId):
    prefix = "prj"


class ApplicationId(CuriosId):
    prefix = "app"


class MilestoneId(CuriosId):
    prefix = "mls"


class WorkstreamId(CuriosId):
    prefix = "wst"


class WorkId(CuriosId):
    prefix = "wrk"


class ExecutionId(CuriosId):
    prefix = "exe"


class AgentDefinitionId(CuriosId):
    prefix = "agd"


class AgentInstanceId(CuriosId):
    prefix = "agi"


class CapabilityId(CuriosId):
    prefix = "cap"


class ProviderId(CuriosId):
    prefix = "prv"


class ArtifactId(CuriosId):
    prefix = "art"


class EvidenceId(CuriosId):
    prefix = "evd"


class VerificationId(CuriosId):
    prefix = "ver"


class EventId(CuriosId):
    prefix = "evt"


class TraceId(CuriosId):
    prefix = "trc"


def ensure_id_type[IdT: CuriosId](value: CuriosId, expected_type: type[IdT]) -> IdT:
    """Return ``value`` only when it already has the expected concrete ID type."""
    if not isinstance(value, expected_type):
        msg = f"expected {expected_type.__name__}, got {type(value).__name__}"
        raise TypeError(msg)
    return value


ID_TYPES: tuple[type[CuriosId], ...] = (
    ProjectId,
    ApplicationId,
    MilestoneId,
    WorkstreamId,
    WorkId,
    ExecutionId,
    AgentDefinitionId,
    AgentInstanceId,
    CapabilityId,
    ProviderId,
    ArtifactId,
    EvidenceId,
    VerificationId,
    EventId,
    TraceId,
)

ID_PREFIXES: dict[str, str] = {id_type.__name__: id_type.prefix for id_type in ID_TYPES}
