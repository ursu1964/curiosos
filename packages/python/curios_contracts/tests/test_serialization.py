from __future__ import annotations

import json

from curios_contracts import (
    EngineeringLifecycle,
    ProjectId,
    SchemaVersion,
    UtcTimestamp,
    to_json_compatible,
)


def test_json_compatible_primitive_representation_and_round_trip() -> None:
    project_id = ProjectId.generate()
    timestamp = UtcTimestamp.parse("2026-09-22T10:15:30+02:00")
    payload = {
        "project_id": project_id,
        "created_at": timestamp,
        "schema_version": SchemaVersion.parse("1.0.0"),
        "lifecycle": EngineeringLifecycle.IMPLEMENTED,
        "optional_note": None,
    }

    compatible = to_json_compatible(payload)
    encoded = json.dumps(compatible, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded == {
        "created_at": "2026-09-22T08:15:30Z",
        "lifecycle": "IMPLEMENTED",
        "optional_note": None,
        "project_id": str(project_id),
        "schema_version": "1.0.0",
    }
    assert ProjectId(decoded["project_id"]) == project_id
    assert UtcTimestamp.parse(decoded["created_at"]) == timestamp
    assert SchemaVersion.parse(decoded["schema_version"]) == SchemaVersion(1, 0, 0)
