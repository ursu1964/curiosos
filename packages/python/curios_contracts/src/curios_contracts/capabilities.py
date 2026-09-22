"""Provider-neutral capability contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import normalize_details, validate_safe_text, validate_safe_token
from curios_contracts.identifiers import CapabilityId
from curios_contracts.references import ObjectReference
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import DurationMilliseconds


class CapabilityCategory(StrEnum):
    """Small provider-neutral capability categories for M0 contracts."""

    COGNITIVE = "cognitive"
    DATA = "data"
    STORAGE = "storage"
    EXECUTION = "execution"
    INTEGRATION = "integration"
    OTHER = "other"


class CapabilityQuality(StrEnum):
    """Provider-neutral quality requirement hints."""

    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Capability:
    """Semantic statement of what can be done, independent of any provider."""

    capability_id: CapabilityId
    key: str
    version: SchemaVersion
    description: str
    category: CapabilityCategory = CapabilityCategory.OTHER
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, CapabilityId):
            msg = "capability_id must be a CapabilityId"
            raise TypeError(msg)
        object.__setattr__(self, "key", validate_safe_token(self.key, "key"))
        if not isinstance(self.version, SchemaVersion):
            msg = "version must be a SchemaVersion"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "description",
            validate_safe_text(self.description, "description", max_length=2048),
        )
        object.__setattr__(self, "category", CapabilityCategory(self.category))
        object.__setattr__(self, "metadata", normalize_details(self.metadata))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "capability JSON must be an object"
            raise TypeError(msg)
        return cls(
            capability_id=CapabilityId(_require_str(value["capability_id"], "capability_id")),
            key=_require_str(value["key"], "key"),
            version=SchemaVersion.parse(_require_str(value["version"], "version")),
            description=_require_str(value["description"], "description"),
            category=CapabilityCategory(value["category"]),
            metadata=_optional_mapping(value.get("metadata"), "metadata"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "capability_id": str(self.capability_id),
            "key": self.key,
            "version": to_json_compatible(self.version),
            "description": self.description,
            "category": self.category.value,
            "metadata": to_json_compatible(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    """Provider-neutral capability requirement for bounded work."""

    capability_id: CapabilityId
    quality: CapabilityQuality | None = None
    privacy_constraints: Mapping[str, object] | None = None
    latency_budget_ms: DurationMilliseconds | None = None
    cost_budget: Mapping[str, object] | None = None
    resource_constraints: Mapping[str, object] | None = None
    policy_constraint_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, CapabilityId):
            msg = "capability_id must be a CapabilityId"
            raise TypeError(msg)
        if self.quality is not None:
            object.__setattr__(self, "quality", CapabilityQuality(self.quality))
        if self.latency_budget_ms is not None:
            object.__setattr__(
                self,
                "latency_budget_ms",
                DurationMilliseconds(self.latency_budget_ms),
            )
        object.__setattr__(
            self,
            "privacy_constraints",
            normalize_details(self.privacy_constraints),
        )
        object.__setattr__(self, "cost_budget", normalize_details(self.cost_budget))
        object.__setattr__(
            self,
            "resource_constraints",
            normalize_details(self.resource_constraints),
        )
        object.__setattr__(
            self,
            "policy_constraint_refs",
            _normalize_references(self.policy_constraint_refs, "policy_constraint_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "capability requirement JSON must be an object"
            raise TypeError(msg)
        policy_constraint_refs = value.get("policy_constraint_refs", ())
        if not isinstance(policy_constraint_refs, list | tuple):
            msg = "policy_constraint_refs must be a list"
            raise TypeError(msg)
        quality = value.get("quality")
        latency_budget_ms = value.get("latency_budget_ms")
        return cls(
            capability_id=CapabilityId(_require_str(value["capability_id"], "capability_id")),
            quality=CapabilityQuality(quality) if quality is not None else None,
            privacy_constraints=_optional_mapping(
                value.get("privacy_constraints"),
                "privacy_constraints",
            ),
            latency_budget_ms=(
                DurationMilliseconds(_require_int(latency_budget_ms, "latency_budget_ms"))
                if latency_budget_ms is not None
                else None
            ),
            cost_budget=_optional_mapping(value.get("cost_budget"), "cost_budget"),
            resource_constraints=_optional_mapping(
                value.get("resource_constraints"),
                "resource_constraints",
            ),
            policy_constraint_refs=tuple(
                ObjectReference.from_json_compatible(item) for item in policy_constraint_refs
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "capability_id": str(self.capability_id),
            "quality": to_json_compatible(self.quality),
            "privacy_constraints": to_json_compatible(self.privacy_constraints),
            "latency_budget_ms": to_json_compatible(self.latency_budget_ms),
            "cost_budget": to_json_compatible(self.cost_budget),
            "resource_constraints": to_json_compatible(self.resource_constraints),
            "policy_constraint_refs": to_json_compatible(self.policy_constraint_refs),
        }


def _normalize_references(
    references: tuple[ObjectReference, ...],
    field_name: str,
) -> tuple[ObjectReference, ...]:
    normalized = tuple(references)
    for reference in normalized:
        if not isinstance(reference, ObjectReference):
            msg = f"{field_name} must contain ObjectReference values"
            raise TypeError(msg)
    return normalized


def _optional_mapping(value: object, field_name: str) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be an object when provided"
        raise TypeError(msg)
    for key in value:
        if not isinstance(key, str):
            msg = f"{field_name} keys must be strings"
            raise TypeError(msg)
    return value


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be an integer"
        raise TypeError(msg)
    return value


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


CAPABILITY_CATEGORY_VALUES: tuple[str, ...] = tuple(member.value for member in CapabilityCategory)
CAPABILITY_QUALITY_VALUES: tuple[str, ...] = tuple(member.value for member in CapabilityQuality)
