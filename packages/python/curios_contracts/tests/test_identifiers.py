from __future__ import annotations

import json

import pytest
from curios_contracts import (
    ID_TYPES,
    ApplicationId,
    ProjectId,
    ensure_id_type,
    to_json_compatible,
)


def test_all_id_types_generate_valid_prefixed_strings() -> None:
    for id_type in ID_TYPES:
        generated = id_type.generate()

        assert isinstance(generated, id_type)
        assert str(generated).startswith(f"{id_type.prefix}_")
        assert len(generated.ulid_value) == 26
        assert json.dumps({"id": generated}) == json.dumps({"id": str(generated)})


def test_generated_ids_are_unique_across_generation() -> None:
    generated = {ProjectId.generate() for _ in range(100)}

    assert len(generated) == 100


def test_invalid_prefix_is_rejected() -> None:
    valid_application_id = ApplicationId.generate()

    with pytest.raises(ValueError, match="must start"):
        ProjectId(str(valid_application_id))


@pytest.mark.parametrize(
    "value",
    [
        "prj_",
        "prj_not-a-ulid",
        "prj_01ARZ3NDEKTSV4RRFFQ69G5FA",
        "prj_01ARZ3NDEKTSV4RRFFQ69G5FAL",
        "prj_01ARZ3NDEKTSV4RRFFQ69G5FA!",
    ],
)
def test_malformed_values_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="ULID-style"):
        ProjectId(value)


def test_typed_ids_do_not_silently_interchange_at_runtime_validation() -> None:
    project_id = ProjectId.generate()

    assert ensure_id_type(project_id, ProjectId) is project_id
    with pytest.raises(TypeError, match="expected ApplicationId"):
        ensure_id_type(project_id, ApplicationId)


def test_id_to_json_compatible_representation_is_string() -> None:
    project_id = ProjectId.generate()

    assert to_json_compatible(project_id) == str(project_id)
