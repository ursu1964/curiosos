"""Engineering/build lifecycle vocabulary."""

from __future__ import annotations

from enum import StrEnum


class EngineeringLifecycle(StrEnum):
    """Frozen engineering/build lifecycle values, distinct from runtime state."""

    DEFINED = "DEFINED"
    SPECIFIED = "SPECIFIED"
    IMPLEMENTING = "IMPLEMENTING"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    VALIDATED = "VALIDATED"
    FROZEN = "FROZEN"


ENGINEERING_LIFECYCLE_VALUES: tuple[str, ...] = tuple(
    member.value for member in EngineeringLifecycle
)
