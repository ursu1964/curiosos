"""Curios M1 deterministic capability resolver foundation."""

from curios_capability.resolver import (
    CapabilityResolution,
    CapabilityResolutionReason,
    CapabilityResolutionStatus,
    resolve_capability_requirement,
    resolve_capability_requirements,
)

__version__ = "0.0.0"

__all__ = (
    "CapabilityResolution",
    "CapabilityResolutionReason",
    "CapabilityResolutionStatus",
    "__version__",
    "resolve_capability_requirement",
    "resolve_capability_requirements",
)
