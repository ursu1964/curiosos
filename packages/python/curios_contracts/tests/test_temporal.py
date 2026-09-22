from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from curios_contracts import DurationMilliseconds, UtcTimestamp, to_json_compatible


def test_timestamp_requires_timezone_aware_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        UtcTimestamp.from_datetime(datetime(2026, 9, 22, 10, 15, 30))


def test_timestamp_accepts_utc_and_serializes_with_z() -> None:
    timestamp = UtcTimestamp.from_datetime(datetime(2026, 9, 22, 8, 15, 30, tzinfo=UTC))

    assert str(timestamp) == "2026-09-22T08:15:30Z"
    assert json.dumps({"created_at": timestamp}) == '{"created_at": "2026-09-22T08:15:30Z"}'


def test_timestamp_normalizes_non_utc_input_to_canonical_utc() -> None:
    prague = timezone(timedelta(hours=2))
    timestamp = UtcTimestamp.from_datetime(datetime(2026, 9, 22, 10, 15, 30, tzinfo=prague))

    assert str(timestamp) == "2026-09-22T08:15:30Z"
    assert timestamp.to_datetime() == datetime(2026, 9, 22, 8, 15, 30, tzinfo=UTC)


def test_timestamp_parse_rejects_naive_string() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        UtcTimestamp.parse("2026-09-22T08:15:30")


def test_timestamp_preserves_microsecond_precision_when_present() -> None:
    timestamp = UtcTimestamp.parse("2026-09-22T08:15:30.123456+00:00")

    assert str(timestamp) == "2026-09-22T08:15:30.123456Z"


def test_duration_milliseconds_is_canonical_integer_duration() -> None:
    duration = DurationMilliseconds(2500)

    assert int(duration) == 2500
    assert to_json_compatible(duration) == 2500
    with pytest.raises(ValueError, match="non-negative"):
        DurationMilliseconds(-1)
