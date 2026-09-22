"""Canonical structured error and warning contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import normalize_details, validate_safe_text
from curios_contracts.identifiers import TraceId
from curios_contracts.references import ObjectReference
from curios_contracts.serialization import to_json_compatible

_ERROR_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


class ErrorCode(str):
    """Stable bounded machine-readable error code."""

    def __new__(cls, value: str) -> Self:
        if not isinstance(value, str):
            msg = "error_code must be a string"
            raise TypeError(msg)
        if _ERROR_CODE_RE.fullmatch(value) is None:
            msg = "error_code must be 3-64 uppercase letters, digits, or underscores"
            raise ValueError(msg)
        return str.__new__(cls, value)

    def to_json_primitive(self) -> str:
        """Return the canonical JSON-compatible string representation."""
        return str(self)


class ErrorCategory(StrEnum):
    """M0 bounded categories for provider-neutral error translation."""

    VALIDATION = "validation"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    DEPENDENCY = "dependency"
    INTERNAL = "internal"


class ErrorSeverity(StrEnum):
    """M0 bounded severities for structured errors."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class ContractError:
    """Safe cross-boundary error structure.

    This contract intentionally stores translated error facts, not provider
    exception objects, stack traces, or arbitrary environment state.
    """

    error_code: ErrorCode
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    retryable: bool
    subject_ref: ObjectReference | None = None
    trace_id: TraceId | None = None
    details: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "error_code", ErrorCode(self.error_code))
        object.__setattr__(
            self,
            "message",
            validate_safe_text(self.message, "message", max_length=1024),
        )
        object.__setattr__(self, "category", ErrorCategory(self.category))
        object.__setattr__(self, "severity", ErrorSeverity(self.severity))
        if not isinstance(self.retryable, bool):
            msg = "retryable must be a bool"
            raise TypeError(msg)
        if self.subject_ref is not None and not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        if self.trace_id is not None and not isinstance(self.trace_id, TraceId):
            msg = "trace_id must be a TraceId when provided"
            raise TypeError(msg)
        object.__setattr__(self, "details", normalize_details(self.details))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "contract error JSON must be an object"
            raise TypeError(msg)
        subject_ref = value.get("subject_ref")
        trace_id = value.get("trace_id")
        if trace_id is not None and not isinstance(trace_id, str):
            msg = "trace_id must be a string when provided"
            raise TypeError(msg)
        return cls(
            error_code=ErrorCode(_require_str(value["error_code"], "error_code")),
            message=_require_str(value["message"], "message"),
            category=ErrorCategory(value["category"]),
            severity=ErrorSeverity(value["severity"]),
            retryable=_require_bool(value["retryable"], "retryable"),
            subject_ref=(
                ObjectReference.from_json_compatible(subject_ref)
                if subject_ref is not None
                else None
            ),
            trace_id=TraceId(trace_id) if trace_id is not None else None,
            details=_optional_mapping(value.get("details"), "details"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "error_code": str(self.error_code),
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "retryable": self.retryable,
            "subject_ref": to_json_compatible(self.subject_ref),
            "trace_id": to_json_compatible(self.trace_id),
            "details": to_json_compatible(self.details),
        }


@dataclass(frozen=True, slots=True)
class ResultWarning:
    """Structured non-fatal warning kept distinct from ``ContractError``."""

    warning_code: ErrorCode
    message: str
    subject_ref: ObjectReference | None = None
    trace_id: TraceId | None = None
    details: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "warning_code", ErrorCode(self.warning_code))
        object.__setattr__(
            self,
            "message",
            validate_safe_text(self.message, "message", max_length=1024),
        )
        if self.subject_ref is not None and not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        if self.trace_id is not None and not isinstance(self.trace_id, TraceId):
            msg = "trace_id must be a TraceId when provided"
            raise TypeError(msg)
        object.__setattr__(self, "details", normalize_details(self.details))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "result warning JSON must be an object"
            raise TypeError(msg)
        subject_ref = value.get("subject_ref")
        trace_id = value.get("trace_id")
        if trace_id is not None and not isinstance(trace_id, str):
            msg = "trace_id must be a string when provided"
            raise TypeError(msg)
        return cls(
            warning_code=ErrorCode(_require_str(value["warning_code"], "warning_code")),
            message=_require_str(value["message"], "message"),
            subject_ref=(
                ObjectReference.from_json_compatible(subject_ref)
                if subject_ref is not None
                else None
            ),
            trace_id=TraceId(trace_id) if trace_id is not None else None,
            details=_optional_mapping(value.get("details"), "details"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "warning_code": str(self.warning_code),
            "message": self.message,
            "subject_ref": to_json_compatible(self.subject_ref),
            "trace_id": to_json_compatible(self.trace_id),
            "details": to_json_compatible(self.details),
        }


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a bool"
        raise TypeError(msg)
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


ERROR_CATEGORY_VALUES: tuple[str, ...] = tuple(member.value for member in ErrorCategory)
ERROR_SEVERITY_VALUES: tuple[str, ...] = tuple(member.value for member in ErrorSeverity)
