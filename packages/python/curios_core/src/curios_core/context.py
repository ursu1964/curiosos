"""Core application context composed from frozen contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from curios_contracts import Authority, ObservabilityContext


@dataclass(frozen=True, slots=True)
class CoreContext:
    """Context passed through core application boundaries.

    Core owns this composition point, but the correlated runtime facts and
    authority grant remain the frozen contract objects.
    """

    observability: ObservabilityContext = field(default_factory=ObservabilityContext)
    authority: Authority | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.observability, ObservabilityContext):
            msg = "observability must be an ObservabilityContext"
            raise TypeError(msg)
        if self.authority is not None and not isinstance(self.authority, Authority):
            msg = "authority must be an Authority when provided"
            raise TypeError(msg)
