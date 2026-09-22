from __future__ import annotations

import pytest
from curios_contracts import EventId, ObjectReference, ProjectId, ProviderId, ReferenceKind


def test_object_reference_preserves_id_namespace_meaning() -> None:
    project_id = ProjectId.generate()

    reference = ObjectReference.from_id(project_id)

    assert reference.kind is ReferenceKind.PROJECT
    assert reference.ref_id == project_id
    assert ObjectReference.from_json_compatible(reference.to_json_compatible()) == reference


def test_object_reference_rejects_kind_id_mismatch() -> None:
    with pytest.raises(TypeError, match="provider references require ProviderId"):
        ObjectReference(kind=ReferenceKind.PROVIDER, ref_id=ProjectId.generate())


def test_object_reference_accepts_provider_references() -> None:
    provider_reference = ObjectReference.from_id(ProviderId.generate())

    assert provider_reference.kind is ReferenceKind.PROVIDER


def test_object_reference_accepts_event_references_for_causation() -> None:
    event_reference = ObjectReference.from_id(EventId.generate())

    assert event_reference.kind is ReferenceKind.EVENT
