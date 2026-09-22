"""Provider-neutral typed references for canonical Curios contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self

from curios_contracts.identifiers import CuriosId

_REFERENCE_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")


@dataclass(frozen=True, slots=True)
class Reference:
    """A small typed reference to a Curios or external subject.

    ``ref_type`` is a stable Curios-owned type string such as ``work``,
    ``execution``, ``agent_instance``, or ``runtime.system``. ``ref_id`` is the
    canonical identifier string in the referenced namespace.
    """

    ref_type: str
    ref_id: str | CuriosId

    def __post_init__(self) -> None:
        if not isinstance(self.ref_type, str):
            msg = "reference ref_type must be a string"
            raise TypeError(msg)
        if _REFERENCE_TYPE_RE.fullmatch(self.ref_type) is None:
            msg = "reference ref_type must be a stable lower-case type string"
            raise ValueError(msg)
        if not isinstance(self.ref_id, str):
            msg = "reference ref_id must be a string or CuriosId"
            raise TypeError(msg)
        if self.ref_id == "":
            msg = "reference ref_id must not be empty"
            raise ValueError(msg)

    @classmethod
    def from_json(cls, value: object) -> Self:
        """Parse a reference from its canonical JSON object form."""
        if not isinstance(value, dict):
            msg = "reference JSON value must be an object"
            raise TypeError(msg)
        try:
            ref_type = value["ref_type"]
            ref_id = value["ref_id"]
        except KeyError as exc:
            msg = "reference JSON value requires ref_type and ref_id"
            raise ValueError(msg) from exc
        if not isinstance(ref_type, str) or not isinstance(ref_id, str):
            msg = "reference JSON ref_type and ref_id must be strings"
            raise TypeError(msg)
        return cls(ref_type=ref_type, ref_id=ref_id)

    def to_json(self) -> dict[str, str]:
        """Return the canonical JSON-compatible object representation."""
        return {"ref_type": self.ref_type, "ref_id": str(self.ref_id)}
