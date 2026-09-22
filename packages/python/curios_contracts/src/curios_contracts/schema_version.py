"""Canonical schema-version primitive."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self

_SCHEMA_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


@dataclass(frozen=True, slots=True)
class SchemaVersion:
    """Canonical ``major.minor.patch`` schema version value."""

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for name, value in (
            ("major", self.major),
            ("minor", self.minor),
            ("patch", self.patch),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                msg = f"schema version {name} must be an integer"
                raise TypeError(msg)
            if value < 0:
                msg = f"schema version {name} must be non-negative"
                raise ValueError(msg)

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse a canonical ``major.minor.patch`` schema version string."""
        if not isinstance(value, str):
            msg = "schema version requires a string value"
            raise TypeError(msg)
        match = _SCHEMA_VERSION_RE.fullmatch(value)
        if match is None:
            msg = "schema version must use canonical major.minor.patch integers"
            raise ValueError(msg)
        major, minor, patch = (int(part) for part in match.groups())
        return cls(major=major, minor=minor, patch=patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def to_json_primitive(self) -> str:
        """Return the canonical JSON-compatible string representation."""
        return str(self)
