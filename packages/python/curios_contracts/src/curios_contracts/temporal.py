"""Canonical temporal primitives for Curios contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Self


class UtcTimestamp(str):
    """Canonical UTC timestamp serialized as RFC3339 with a ``Z`` suffix."""

    def __new__(cls, value: datetime | str) -> Self:
        canonical = _format_utc(_coerce_datetime(value))
        return str.__new__(cls, canonical)

    @classmethod
    def now(cls) -> Self:
        """Return the current wall-clock timestamp in canonical UTC form."""
        return cls(datetime.now(UTC))

    @classmethod
    def from_datetime(cls, value: datetime) -> Self:
        """Create a canonical timestamp from a timezone-aware datetime."""
        return cls(value)

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse an RFC3339/ISO-8601 timestamp into canonical UTC form."""
        return cls(value)

    def to_datetime(self) -> datetime:
        """Return the timestamp as a timezone-aware UTC ``datetime``."""
        return _parse_datetime(str(self))

    def to_json_primitive(self) -> str:
        """Return the canonical JSON-compatible string representation."""
        return str(self)


class DurationMilliseconds(int):
    """Canonical non-negative duration serialized as integer milliseconds."""

    def __new__(cls, value: int) -> Self:
        if isinstance(value, bool) or not isinstance(value, int):
            msg = "duration milliseconds must be an integer"
            raise TypeError(msg)
        if value < 0:
            msg = "duration milliseconds must be non-negative"
            raise ValueError(msg)
        return int.__new__(cls, value)

    def to_json_primitive(self) -> int:
        """Return the canonical JSON-compatible integer representation."""
        return int(self)


def _coerce_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return _require_aware(value).astimezone(UTC)
    if isinstance(value, str):
        return _parse_datetime(value)

    msg = "timestamp requires a datetime or string value"
    raise TypeError(msg)


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        msg = "timestamp must be an RFC3339/ISO-8601 datetime"
        raise ValueError(msg) from exc
    return _require_aware(parsed).astimezone(UTC)


def _require_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = "timestamp must be timezone-aware"
        raise ValueError(msg)
    return value


def _format_utc(value: datetime) -> str:
    utc_value = value.astimezone(UTC)
    if utc_value.microsecond == 0:
        return utc_value.isoformat(timespec="seconds").replace("+00:00", "Z")
    return utc_value.isoformat(timespec="microseconds").replace("+00:00", "Z")
