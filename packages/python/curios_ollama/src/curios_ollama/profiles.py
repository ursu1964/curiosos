"""Local model/profile discovery records for the Ollama provider boundary."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from curios_contracts import (
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    ObjectReference,
    ProviderId,
    ReferenceKind,
    Result,
    SchemaVersion,
    to_json_compatible,
)
from curios_core import CoreContext

from curios_ollama.catalog import DEFAULT_OLLAMA_PROVIDER_ID
from curios_ollama.client import OllamaModelClient, OllamaModelSummary

_PROFILE_SCHEMA_VERSION = SchemaVersion.parse("0.0.0")
_MAX_MODEL_NAME_LENGTH = 128
_MAX_METADATA_KEYS = 16
_MAX_METADATA_SEQUENCE_ITEMS = 16
_MAX_METADATA_DEPTH = 3
_MAX_METADATA_STRING_LENGTH = 512
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
_SAFE_METADATA_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_INVALID_INVENTORY_MESSAGE = (
    "Ollama model profile discovery received invalid local inventory metadata."
)


class ModelProfileStatus(StrEnum):
    """Provider-local model/profile availability without execution authority."""

    AVAILABLE = "available"


@dataclass(frozen=True, slots=True)
class LocalModelProfile:
    """Non-invoked local model candidate metadata."""

    provider_ref: ObjectReference
    model_name: str
    schema_version: SchemaVersion = _PROFILE_SCHEMA_VERSION
    status: ModelProfileStatus = ModelProfileStatus.AVAILABLE
    context_window_tokens: int | None = None
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provider_ref, ObjectReference):
            msg = "provider_ref must be an ObjectReference"
            raise TypeError(msg)
        if self.provider_ref.kind is not ReferenceKind.PROVIDER:
            msg = "provider_ref must reference a provider"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "model_name",
            _normalize_model_name(self.model_name),
        )
        if not isinstance(self.schema_version, SchemaVersion):
            msg = "schema_version must be a SchemaVersion"
            raise TypeError(msg)
        object.__setattr__(self, "status", ModelProfileStatus(self.status))
        if self.context_window_tokens is not None:
            if isinstance(self.context_window_tokens, bool) or not isinstance(
                self.context_window_tokens,
                int,
            ):
                msg = "context_window_tokens must be an integer when provided"
                raise TypeError(msg)
            if self.context_window_tokens <= 0:
                msg = "context_window_tokens must be positive when provided"
                raise ValueError(msg)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @classmethod
    def from_json_compatible(cls, value: object) -> LocalModelProfile:
        """Parse the JSON-compatible provider-local representation."""
        if not isinstance(value, dict):
            msg = "model profile JSON must be an object"
            raise TypeError(msg)
        return cls(
            provider_ref=ObjectReference.from_json_compatible(value["provider_ref"]),
            model_name=_require_str(value["model_name"], "model_name"),
            schema_version=SchemaVersion.parse(
                _require_str(value["schema_version"], "schema_version")
            ),
            status=ModelProfileStatus(value["status"]),
            context_window_tokens=_optional_positive_int(
                value.get("context_window_tokens"),
                "context_window_tokens",
            ),
            metadata=_optional_mapping(value.get("metadata"), "metadata"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return deterministic JSON-compatible profile metadata."""
        return {
            "provider_ref": to_json_compatible(self.provider_ref),
            "model_name": self.model_name,
            "schema_version": to_json_compatible(self.schema_version),
            "status": self.status.value,
            "context_window_tokens": self.context_window_tokens,
            "metadata": to_json_compatible(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class OllamaModelProfileDiscovery:
    """Discover local Ollama model candidates without invoking a model."""

    client: OllamaModelClient
    provider_id: ProviderId = DEFAULT_OLLAMA_PROVIDER_ID
    schema_version: SchemaVersion = _PROFILE_SCHEMA_VERSION
    base_metadata: Mapping[str, object] | None = field(
        default_factory=lambda: {"provider_family": "ollama"}
    )

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, ProviderId):
            msg = "provider_id must be a ProviderId"
            raise TypeError(msg)
        if not isinstance(self.schema_version, SchemaVersion):
            msg = "schema_version must be a SchemaVersion"
            raise TypeError(msg)
        object.__setattr__(self, "base_metadata", _normalize_metadata(self.base_metadata))

    def discover_model_profiles(
        self,
        context: CoreContext,
    ) -> Result[tuple[LocalModelProfile, ...]]:
        """Return local candidate profiles without generation, routing, or persistence."""
        if not isinstance(context, CoreContext):
            msg = "context must be a CoreContext"
            raise TypeError(msg)

        try:
            summaries = self.client.list_models()
            profiles = tuple(
                _profile_from_summary(
                    summary,
                    provider_id=self.provider_id,
                    schema_version=self.schema_version,
                    base_metadata=self.base_metadata,
                )
                for summary in summaries
            )
        except TimeoutError:
            return Result.failure((_profile_error(category=ErrorCategory.TIMEOUT),))
        except OSError:
            return Result.failure((_profile_error(),))
        except TypeError, ValueError:
            return Result.failure(
                (
                    _profile_error(
                        code="OLLAMA_MODEL_PROFILE_INVALID",
                        message=_INVALID_INVENTORY_MESSAGE,
                        retryable=False,
                    ),
                )
            )

        duplicate_name = _first_duplicate_model_name(profiles)
        if duplicate_name is not None:
            return Result.failure(
                (
                    _profile_error(
                        code="OLLAMA_MODEL_PROFILE_DUPLICATE",
                        message=f"duplicate Ollama model profile {duplicate_name!r}",
                        retryable=False,
                    ),
                )
            )
        return Result.success(tuple(sorted(profiles, key=lambda profile: profile.model_name)))


def _profile_from_summary(
    summary: OllamaModelSummary,
    *,
    provider_id: ProviderId,
    schema_version: SchemaVersion,
    base_metadata: Mapping[str, object] | None,
) -> LocalModelProfile:
    if not isinstance(summary, OllamaModelSummary):
        msg = "model summaries must be OllamaModelSummary values"
        raise TypeError(msg)
    metadata: dict[str, object] = dict(base_metadata or {})
    if summary.modified_at is not None:
        metadata["modified_at"] = summary.modified_at
    if summary.size_bytes is not None:
        metadata["size_bytes"] = summary.size_bytes
    if summary.digest is not None:
        metadata["digest"] = summary.digest
    return LocalModelProfile(
        provider_ref=ObjectReference.from_id(provider_id),
        model_name=summary.name,
        schema_version=schema_version,
        status=ModelProfileStatus.AVAILABLE,
        metadata=metadata,
    )


def _profile_error(
    *,
    code: str = "OLLAMA_MODEL_PROFILE_DISCOVERY_UNAVAILABLE",
    category: ErrorCategory = ErrorCategory.DEPENDENCY,
    message: str = "Ollama model profile discovery could not list local models",
    retryable: bool = True,
) -> ContractError:
    return ContractError(
        error_code=ErrorCode(code),
        message=message,
        category=category,
        severity=ErrorSeverity.ERROR,
        retryable=retryable,
    )


def _first_duplicate_model_name(profiles: tuple[LocalModelProfile, ...]) -> str | None:
    seen: set[str] = set()
    for profile in profiles:
        if profile.model_name in seen:
            return profile.model_name
        seen.add(profile.model_name)
    return None


def _normalize_model_name(value: object) -> str:
    model_name = _require_str(value, "model_name").strip()
    _validate_safe_text(model_name, "model_name", max_length=_MAX_MODEL_NAME_LENGTH)
    _reject_secret_shaped_text(model_name, "model_name")
    return model_name


def _normalize_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if metadata is None:
        return None
    if not isinstance(metadata, Mapping):
        msg = "metadata must be a mapping when provided"
        raise TypeError(msg)
    return MappingProxyType(
        _normalize_metadata_mapping(
            metadata,
            depth=_MAX_METADATA_DEPTH,
            field_name="metadata",
        )
    )


def _normalize_metadata_mapping(
    value: Mapping[str, object],
    *,
    depth: int,
    field_name: str,
) -> dict[str, object]:
    if len(value) > _MAX_METADATA_KEYS:
        msg = f"{field_name} must contain at most {_MAX_METADATA_KEYS} keys"
        raise ValueError(msg)

    normalized: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        key = _validate_metadata_key(raw_key, f"{field_name} key")
        _reject_secret_key(key, field_name)
        normalized[key] = _normalize_metadata_value(raw_value, depth=depth - 1, field_name=key)
    return normalized


def _normalize_metadata_value(value: object, *, depth: int, field_name: str) -> object:
    if depth < 0:
        msg = "metadata nesting is too deep"
        raise ValueError(msg)

    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        _validate_safe_text(
            value,
            field_name,
            max_length=_MAX_METADATA_STRING_LENGTH,
            allow_empty=True,
        )
        _reject_secret_shaped_text(value, field_name)
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
            _normalize_metadata_mapping(value, depth=depth, field_name=field_name)
        )
    if isinstance(value, tuple | list):
        if len(value) > _MAX_METADATA_SEQUENCE_ITEMS:
            msg = f"{field_name} must contain at most {_MAX_METADATA_SEQUENCE_ITEMS} items"
            raise ValueError(msg)
        return tuple(
            _normalize_metadata_value(item, depth=depth - 1, field_name=field_name)
            for item in value
        )

    msg = f"{field_name} must be JSON-compatible safe metadata"
    raise TypeError(msg)


def _validate_metadata_key(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    if _SAFE_METADATA_KEY_RE.fullmatch(value) is None:
        msg = f"{field_name} must be a lower-snake token up to 64 characters"
        raise ValueError(msg)
    return value


def _validate_safe_text(
    value: str,
    field_name: str,
    *,
    max_length: int,
    allow_empty: bool = False,
) -> None:
    if not allow_empty and value == "":
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
    if len(value) > max_length:
        msg = f"{field_name} must be at most {max_length} characters"
        raise ValueError(msg)
    if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
        msg = f"{field_name} must not contain control characters"
        raise ValueError(msg)


def _reject_secret_key(key: str, field_name: str) -> None:
    key_parts = set(key.split("_"))
    if key in _SECRET_KEY_PARTS or key_parts.intersection(_SECRET_KEY_PARTS):
        msg = f"{field_name} must not include secret-shaped key {key!r}"
        raise ValueError(msg)


def _reject_secret_shaped_text(value: str, field_name: str) -> None:
    if _SECRET_VALUE_RE.search(value) is not None:
        msg = f"{field_name} must not contain secret-shaped key/value material"
        raise ValueError(msg)


def _optional_positive_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be an integer when provided"
        raise TypeError(msg)
    if value <= 0:
        msg = f"{field_name} must be positive when provided"
        raise ValueError(msg)
    return value


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


MODEL_PROFILE_STATUS_VALUES: tuple[str, ...] = tuple(member.value for member in ModelProfileStatus)
