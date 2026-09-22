from __future__ import annotations

import json

from curios_contracts import ENGINEERING_LIFECYCLE_VALUES, EngineeringLifecycle, to_json_compatible


def test_engineering_lifecycle_has_complete_frozen_values() -> None:
    assert ENGINEERING_LIFECYCLE_VALUES == (
        "DEFINED",
        "SPECIFIED",
        "IMPLEMENTING",
        "IMPLEMENTED",
        "TESTED",
        "VALIDATED",
        "FROZEN",
    )


def test_engineering_lifecycle_serializes_as_stable_string() -> None:
    assert EngineeringLifecycle.TESTED.value == "TESTED"
    assert json.dumps({"lifecycle": EngineeringLifecycle.TESTED}) == '{"lifecycle": "TESTED"}'
    assert to_json_compatible(EngineeringLifecycle.TESTED) == "TESTED"


def test_runtime_specific_states_are_not_engineering_lifecycle_values() -> None:
    runtime_states = {"PENDING", "RUNNING", "FAILED", "SUCCEEDED", "CANCELLED", "APPROVED"}

    assert runtime_states.isdisjoint(ENGINEERING_LIFECYCLE_VALUES)
