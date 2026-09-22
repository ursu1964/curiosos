from __future__ import annotations

import pytest
from curios_contracts import SchemaVersion, to_json_compatible


def test_schema_version_accepts_canonical_semantic_version_string() -> None:
    schema_version = SchemaVersion.parse("1.2.3")

    assert schema_version.major == 1
    assert schema_version.minor == 2
    assert schema_version.patch == 3
    assert str(schema_version) == "1.2.3"


@pytest.mark.parametrize("value", ["", "1", "1.2", "1.2.3.4", "01.2.3", "1.-2.3", "v1.2.3"])
def test_schema_version_rejects_invalid_versions(value: str) -> None:
    with pytest.raises(ValueError, match="major.minor.patch"):
        SchemaVersion.parse(value)


def test_schema_version_rejects_invalid_constructor_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        SchemaVersion(major=1, minor=-1, patch=0)
    with pytest.raises(TypeError, match="integer"):
        SchemaVersion(major=True, minor=0, patch=0)


def test_schema_version_serializes_as_string_without_package_version_coupling() -> None:
    schema_version = SchemaVersion(major=0, minor=1, patch=0)

    assert to_json_compatible(schema_version) == "0.1.0"
