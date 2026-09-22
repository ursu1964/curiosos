from __future__ import annotations

import json

import pytest
from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    IntegrityAlgorithm,
    IntegrityDescriptor,
    ObjectReference,
    ProjectId,
    ProviderId,
    UtcTimestamp,
    to_json_compatible,
)


def test_artifact_reference_provider_neutral_locator_and_serialization() -> None:
    artifact_id = ArtifactId.generate()
    provider_ref = ObjectReference.from_id(ProviderId.generate())
    producer_ref = ObjectReference.from_id(ProjectId.generate())
    created_at = UtcTimestamp.parse("2026-09-22T12:00:00+02:00")
    integrity = IntegrityDescriptor(
        algorithm=IntegrityAlgorithm.SHA256,
        value="a" * 64,
    )

    reference = ArtifactReference(
        artifact_id=artifact_id,
        kind=ArtifactKind.DOCUMENT,
        locator="provider-neutral:artifact/primary-report",
        storage_provider_ref=provider_ref,
        media_type="application/json",
        integrity=integrity,
        created_at=created_at,
        producer_ref=producer_ref,
    )

    decoded = json.loads(json.dumps(to_json_compatible(reference), sort_keys=True))

    assert decoded == {
        "artifact_id": str(artifact_id),
        "kind": "document",
        "locator": "provider-neutral:artifact/primary-report",
        "storage_provider_ref": provider_ref.to_json_compatible(),
        "media_type": "application/json",
        "integrity": {"algorithm": "sha256", "value": "a" * 64},
        "created_at": "2026-09-22T10:00:00Z",
        "producer_ref": producer_ref.to_json_compatible(),
    }
    assert ArtifactReference.from_json_compatible(decoded) == reference


def test_artifact_locator_does_not_imply_local_path_semantics() -> None:
    reference = ArtifactReference(
        artifact_id=ArtifactId.generate(),
        kind=ArtifactKind.BINARY,
        locator="opaque-locator-value-without-uri-or-path-contract",
        created_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
    )

    assert "/" not in reference.locator
    assert ":" not in reference.locator
    assert reference.storage_provider_ref is None


def test_artifact_storage_provider_must_be_provider_reference() -> None:
    with pytest.raises(ValueError, match="storage_provider_ref must reference provider"):
        ArtifactReference(
            artifact_id=ArtifactId.generate(),
            kind=ArtifactKind.DATASET,
            locator="dataset:one",
            storage_provider_ref=ObjectReference.from_id(ProjectId.generate()),
            created_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
        )


def test_artifact_locator_rejects_secret_shaped_values() -> None:
    with pytest.raises(ValueError, match="secret-shaped"):
        ArtifactReference(
            artifact_id=ArtifactId.generate(),
            kind=ArtifactKind.LOG,
            locator="https://example.invalid/object?token=secret",
            created_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
        )
