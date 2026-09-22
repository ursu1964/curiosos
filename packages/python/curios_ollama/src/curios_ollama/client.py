"""Ollama client boundary types."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class OllamaModelSummary:
    """Adapter-owned normalized summary of an Ollama model entry."""

    name: str
    modified_at: str | None = None
    size_bytes: int | None = None
    digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _require_nonempty_string(self.name, "name"))
        if self.modified_at is not None:
            object.__setattr__(
                self,
                "modified_at",
                _require_nonempty_string(self.modified_at, "modified_at"),
            )
        if self.size_bytes is not None and (
            isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int)
        ):
            msg = "size_bytes must be an integer when provided"
            raise TypeError(msg)
        if self.size_bytes is not None and self.size_bytes < 0:
            msg = "size_bytes must be non-negative"
            raise ValueError(msg)
        if self.digest is not None:
            object.__setattr__(self, "digest", _require_nonempty_string(self.digest, "digest"))


@runtime_checkable
class OllamaModelClient(Protocol):
    """Small testable boundary over Ollama model inventory."""

    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        """Return local model summaries without downloading or invoking a model."""


@dataclass(frozen=True, slots=True)
class OllamaHttpClient:
    """Minimal stdlib HTTP client for Ollama's local tags endpoint."""

    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", _require_nonempty_string(self.base_url, "base_url"))
        if isinstance(self.timeout_seconds, bool) or not isinstance(
            self.timeout_seconds,
            int | float,
        ):
            msg = "timeout_seconds must be numeric"
            raise TypeError(msg)
        if self.timeout_seconds <= 0:
            msg = "timeout_seconds must be positive"
            raise ValueError(msg)

    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        """Read `/api/tags` and normalize the response behind the adapter boundary."""
        request = Request(urljoin(f"{self.base_url.rstrip('/')}/", "api/tags"), method="GET")
        with urlopen(request, timeout=float(self.timeout_seconds)) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return parse_tags_response(payload)


def parse_tags_response(payload: object) -> tuple[OllamaModelSummary, ...]:
    """Normalize the Ollama `/api/tags` response without exposing provider JSON."""
    if not isinstance(payload, Mapping):
        msg = "Ollama tags response must be an object"
        raise ValueError(msg)
    raw_models = payload.get("models", ())
    if not isinstance(raw_models, list | tuple):
        msg = "Ollama tags response models must be a list"
        raise ValueError(msg)

    models: list[OllamaModelSummary] = []
    for raw_model in raw_models:
        if not isinstance(raw_model, Mapping):
            msg = "Ollama model entry must be an object"
            raise ValueError(msg)
        models.append(_parse_model(raw_model))
    return tuple(models)


def _parse_model(raw_model: Mapping[str, object]) -> OllamaModelSummary:
    raw_name = raw_model.get("name")
    raw_modified_at = raw_model.get("modified_at")
    raw_size = raw_model.get("size")
    raw_digest = raw_model.get("digest")
    return OllamaModelSummary(
        name=_require_nonempty_string(raw_name, "name"),
        modified_at=(
            _require_nonempty_string(raw_modified_at, "modified_at")
            if raw_modified_at is not None
            else None
        ),
        size_bytes=_optional_int(raw_size, "size"),
        digest=_require_nonempty_string(raw_digest, "digest") if raw_digest is not None else None,
    )


def _optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be an integer when provided"
        raise ValueError(msg)
    return value


def _require_nonempty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise ValueError(msg)
    stripped = value.strip()
    if stripped == "":
        msg = f"{field_name} must be non-empty"
        raise ValueError(msg)
    return stripped
