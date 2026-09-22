"""Shared validation helpers for immutable contract value objects."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from types import MappingProxyType

_SAFE_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MEDIA_TYPE_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}$"
)
_SECRET_KEY_PARTS = frozenset(
    {
        "api_key",
        "auth",
        "authorization",
        "cookie",
        "credential",
        "key",
        "password",
        "secret",
        "session",
        "token",
    }
)
_SECRET_VALUE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|credential|password|secret|token)\s*[:=]"
)

_MAX_DETAIL_KEYS = 16
_MAX_DETAIL_SEQUENCE_ITEMS = 16
_MAX_DETAIL_DEPTH = 3
_MAX_DETAIL_STRING_LENGTH = 512


def validate_safe_token(value: str, field_name: str) -> str:
    """Return a bounded lower-snake token or raise a contract validation error."""
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    if _SAFE_TOKEN_RE.fullmatch(value) is None:
        msg = f"{field_name} must be a lower-snake token up to 64 characters"
        raise ValueError(msg)
    return value


def validate_safe_text(
    value: str,
    field_name: str,
    *,
    max_length: int,
    allow_empty: bool = False,
) -> str:
    """Return a bounded human-readable string without control characters."""
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    if not allow_empty and value == "":
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
    if len(value) > max_length:
        msg = f"{field_name} must be at most {max_length} characters"
        raise ValueError(msg)
    if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
        msg = f"{field_name} must not contain control characters"
        raise ValueError(msg)
    return value


def validate_media_type(value: str) -> str:
    """Return a portable media type token."""
    if not isinstance(value, str):
        msg = "media_type must be a string"
        raise TypeError(msg)
    if _MEDIA_TYPE_RE.fullmatch(value) is None:
        msg = "media_type must be a type/subtype media type"
        raise ValueError(msg)
    return value


def reject_secret_shaped_text(value: str, field_name: str) -> None:
    """Reject text that visibly embeds credential-like key/value material."""
    if _SECRET_VALUE_RE.search(value) is not None:
        msg = f"{field_name} must not contain secret-shaped key/value material"
        raise ValueError(msg)


def normalize_details(details: Mapping[str, object] | None) -> Mapping[str, object] | None:
    """Normalize bounded JSON-compatible structured details into immutable values."""
    if details is None:
        return None
    if not isinstance(details, Mapping):
        msg = "details must be a mapping when provided"
        raise TypeError(msg)
    normalized = _normalize_detail_mapping(details, depth=_MAX_DETAIL_DEPTH, field_name="details")
    return MappingProxyType(normalized)


def _normalize_detail_mapping(
    value: Mapping[str, object],
    *,
    depth: int,
    field_name: str,
) -> dict[str, object]:
    if len(value) > _MAX_DETAIL_KEYS:
        msg = f"{field_name} must contain at most {_MAX_DETAIL_KEYS} keys"
        raise ValueError(msg)

    normalized: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        key = validate_safe_token(raw_key, f"{field_name} key")
        _reject_secret_key(key, field_name)
        normalized[key] = _normalize_detail_value(raw_value, depth=depth - 1, field_name=key)
    return normalized


def _normalize_detail_value(value: object, *, depth: int, field_name: str) -> object:
    if depth < 0:
        msg = "details nesting is too deep"
        raise ValueError(msg)

    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        validate_safe_text(
            value,
            field_name,
            max_length=_MAX_DETAIL_STRING_LENGTH,
            allow_empty=True,
        )
        reject_secret_shaped_text(value, field_name)
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            msg = f"{field_name} must be a finite number"
            raise ValueError(msg)
        return value
    if isinstance(value, Mapping):
        return MappingProxyType(
            _normalize_detail_mapping(value, depth=depth, field_name=field_name)
        )
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        if len(value) > _MAX_DETAIL_SEQUENCE_ITEMS:
            msg = f"{field_name} must contain at most {_MAX_DETAIL_SEQUENCE_ITEMS} items"
            raise ValueError(msg)
        return tuple(
            _normalize_detail_value(item, depth=depth - 1, field_name=field_name) for item in value
        )

    msg = f"{field_name} must be JSON-compatible safe detail data"
    raise TypeError(msg)


def _reject_secret_key(key: str, field_name: str) -> None:
    key_parts = set(key.split("_"))
    if key in _SECRET_KEY_PARTS or key_parts.intersection(_SECRET_KEY_PARTS):
        msg = f"{field_name} must not include secret-shaped key {key!r}"
        raise ValueError(msg)
