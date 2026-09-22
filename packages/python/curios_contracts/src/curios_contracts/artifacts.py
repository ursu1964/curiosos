"""Provider-neutral artifact reference contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import (
    reject_secret_shaped_text,
    validate_media_type,
    validate_safe_text,
)
from curios_contracts.identifiers import ArtifactId
from curios_contracts.references import ObjectReference, ReferenceKind
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp


class ArtifactKind(StrEnum):
    """M0 provider-neutral artifact kinds."""

    DOCUMENT = "document"
    DATASET = "dataset"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MODEL_OUTPUT = "model_output"
    LOG = "log"
    BINARY = "binary"
    OTHER = "other"


class IntegrityAlgorithm(StrEnum):
    """Portable content-integrity algorithms."""

    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE3 = "blake3"


@dataclass(frozen=True, slots=True)
class IntegrityDescriptor:
    """Portable algorithm/value content-integrity descriptor."""

    algorithm: IntegrityAlgorithm
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "algorithm", IntegrityAlgorithm(self.algorithm))
        value = validate_safe_text(self.value, "integrity value", max_length=256)
        if any(character.isspace() for character in value):
            msg = "integrity value must not contain whitespace"
            raise ValueError(msg)
        object.__setattr__(self, "value", value)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "integrity JSON must be an object"
            raise TypeError(msg)
        algorithm = value["algorithm"]
        integrity_value = value["value"]
        if not isinstance(integrity_value, str):
            msg = "integrity value must be a string"
            raise TypeError(msg)
        return cls(algorithm=IntegrityAlgorithm(algorithm), value=integrity_value)

    def to_json_compatible(self) -> dict[str, str]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "algorithm": self.algorithm.value,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Provider-neutral pointer to an artifact, not an authorization grant."""

    artifact_id: ArtifactId
    kind: ArtifactKind
    locator: str
    created_at: UtcTimestamp
    storage_provider_ref: ObjectReference | None = None
    media_type: str | None = None
    integrity: IntegrityDescriptor | None = None
    producer_ref: ObjectReference | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, ArtifactId):
            msg = "artifact_id must be an ArtifactId"
            raise TypeError(msg)
        object.__setattr__(self, "kind", ArtifactKind(self.kind))

        locator = validate_safe_text(self.locator, "locator", max_length=2048)
        reject_secret_shaped_text(locator, "locator")
        object.__setattr__(self, "locator", locator)

        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))

        if self.storage_provider_ref is not None:
            _require_reference_kind(
                self.storage_provider_ref,
                ReferenceKind.PROVIDER,
                "storage_provider_ref",
            )
        if self.media_type is not None:
            object.__setattr__(self, "media_type", validate_media_type(self.media_type))
        if self.integrity is not None and not isinstance(self.integrity, IntegrityDescriptor):
            msg = "integrity must be an IntegrityDescriptor when provided"
            raise TypeError(msg)
        if self.producer_ref is not None and not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be an ObjectReference when provided"
            raise TypeError(msg)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "artifact reference JSON must be an object"
            raise TypeError(msg)
        storage_provider_ref = value.get("storage_provider_ref")
        integrity = value.get("integrity")
        producer_ref = value.get("producer_ref")
        return cls(
            artifact_id=ArtifactId(_require_str(value["artifact_id"], "artifact_id")),
            kind=ArtifactKind(value["kind"]),
            locator=_require_str(value["locator"], "locator"),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            storage_provider_ref=(
                ObjectReference.from_json_compatible(storage_provider_ref)
                if storage_provider_ref is not None
                else None
            ),
            media_type=(
                _require_str(value["media_type"], "media_type")
                if value.get("media_type") is not None
                else None
            ),
            integrity=(
                IntegrityDescriptor.from_json_compatible(integrity)
                if integrity is not None
                else None
            ),
            producer_ref=(
                ObjectReference.from_json_compatible(producer_ref)
                if producer_ref is not None
                else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "artifact_id": str(self.artifact_id),
            "kind": self.kind.value,
            "locator": self.locator,
            "storage_provider_ref": to_json_compatible(self.storage_provider_ref),
            "media_type": self.media_type,
            "integrity": to_json_compatible(self.integrity),
            "created_at": to_json_compatible(self.created_at),
            "producer_ref": to_json_compatible(self.producer_ref),
        }


def _require_reference_kind(
    reference: ObjectReference,
    expected_kind: ReferenceKind,
    field_name: str,
) -> None:
    if not isinstance(reference, ObjectReference):
        msg = f"{field_name} must be an ObjectReference when provided"
        raise TypeError(msg)
    if reference.kind is not expected_kind:
        msg = f"{field_name} must reference {expected_kind.value}"
        raise ValueError(msg)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


ARTIFACT_KIND_VALUES: tuple[str, ...] = tuple(member.value for member in ArtifactKind)
INTEGRITY_ALGORITHM_VALUES: tuple[str, ...] = tuple(member.value for member in IntegrityAlgorithm)
