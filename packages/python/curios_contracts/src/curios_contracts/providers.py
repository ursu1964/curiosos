"""Replaceable provider descriptor contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import normalize_details
from curios_contracts.identifiers import CapabilityId, ProviderId
from curios_contracts.references import ObjectReference
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.serialization import to_json_compatible


class ProviderType(StrEnum):
    """Provider implementation categories without execution semantics."""

    MODEL = "model"
    STORAGE = "storage"
    DATABASE = "database"
    TOOL = "tool"
    RUNTIME = "runtime"
    OTHER = "other"


class ProviderStatus(StrEnum):
    """Descriptor-level provider availability status."""

    UNKNOWN = "unknown"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    """Descriptor for a replaceable implementation provider.

    This describes declared capability support. It is not an authority grant and
    does not define a universal provider execution method.
    """

    provider_id: ProviderId
    provider_type: ProviderType
    version: SchemaVersion
    declared_capability_ids: tuple[CapabilityId, ...]
    configuration_requirement_refs: tuple[ObjectReference, ...] = ()
    status: ProviderStatus = ProviderStatus.UNKNOWN
    implementation_metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, ProviderId):
            msg = "provider_id must be a ProviderId"
            raise TypeError(msg)
        object.__setattr__(self, "provider_type", ProviderType(self.provider_type))
        if not isinstance(self.version, SchemaVersion):
            msg = "version must be a SchemaVersion"
            raise TypeError(msg)
        declared_capability_ids = tuple(self.declared_capability_ids)
        for capability_id in declared_capability_ids:
            if not isinstance(capability_id, CapabilityId):
                msg = "declared_capability_ids must contain CapabilityId values"
                raise TypeError(msg)
        object.__setattr__(self, "declared_capability_ids", declared_capability_ids)
        object.__setattr__(
            self,
            "configuration_requirement_refs",
            _normalize_references(
                self.configuration_requirement_refs,
                "configuration_requirement_refs",
            ),
        )
        object.__setattr__(self, "status", ProviderStatus(self.status))
        object.__setattr__(
            self,
            "implementation_metadata",
            normalize_details(self.implementation_metadata),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "provider descriptor JSON must be an object"
            raise TypeError(msg)
        capability_ids = value.get("declared_capability_ids", ())
        configuration_refs = value.get("configuration_requirement_refs", ())
        if not isinstance(capability_ids, list | tuple):
            msg = "declared_capability_ids must be a list"
            raise TypeError(msg)
        if not isinstance(configuration_refs, list | tuple):
            msg = "configuration_requirement_refs must be a list"
            raise TypeError(msg)
        return cls(
            provider_id=ProviderId(_require_str(value["provider_id"], "provider_id")),
            provider_type=ProviderType(value["provider_type"]),
            version=SchemaVersion.parse(_require_str(value["version"], "version")),
            declared_capability_ids=tuple(
                CapabilityId(_require_str(item, "declared_capability_ids item"))
                for item in capability_ids
            ),
            configuration_requirement_refs=tuple(
                ObjectReference.from_json_compatible(item) for item in configuration_refs
            ),
            status=ProviderStatus(value["status"]),
            implementation_metadata=_optional_mapping(
                value.get("implementation_metadata"),
                "implementation_metadata",
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "provider_id": str(self.provider_id),
            "provider_type": self.provider_type.value,
            "version": to_json_compatible(self.version),
            "declared_capability_ids": to_json_compatible(self.declared_capability_ids),
            "configuration_requirement_refs": to_json_compatible(
                self.configuration_requirement_refs
            ),
            "status": self.status.value,
            "implementation_metadata": to_json_compatible(self.implementation_metadata),
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


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


PROVIDER_TYPE_VALUES: tuple[str, ...] = tuple(member.value for member in ProviderType)
PROVIDER_STATUS_VALUES: tuple[str, ...] = tuple(member.value for member in ProviderStatus)
