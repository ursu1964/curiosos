from __future__ import annotations

import json
from typing import cast

import pytest
from curios_contracts import (
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    ObjectReference,
    ProjectId,
    ResultWarning,
    TraceId,
    to_json_compatible,
)


def test_error_valid_construction_and_stable_serialization() -> None:
    subject_ref = ObjectReference.from_id(ProjectId.generate())
    trace_id = TraceId.generate()

    error = ContractError(
        error_code=ErrorCode("VALIDATION_FAILED"),
        message="Input did not satisfy the contract.",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        retryable=False,
        subject_ref=subject_ref,
        trace_id=trace_id,
        details={"field": "locator", "attempt": 1},
    )

    encoded = json.dumps(to_json_compatible(error), sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded == {
        "category": "validation",
        "details": {"attempt": 1, "field": "locator"},
        "error_code": "VALIDATION_FAILED",
        "message": "Input did not satisfy the contract.",
        "retryable": False,
        "severity": "error",
        "subject_ref": subject_ref.to_json_compatible(),
        "trace_id": str(trace_id),
    }
    assert ContractError.from_json_compatible(decoded) == error


def test_error_retryable_semantics_are_explicit_bool() -> None:
    retryable_error = ContractError(
        error_code=ErrorCode("DEPENDENCY_TIMEOUT"),
        message="Dependency timed out.",
        category=ErrorCategory.TIMEOUT,
        severity=ErrorSeverity.ERROR,
        retryable=True,
    )

    assert retryable_error.retryable is True
    assert retryable_error.to_json_compatible()["retryable"] is True


def test_error_category_and_severity_validation() -> None:
    with pytest.raises(ValueError, match="not a valid"):
        ContractError(
            error_code=ErrorCode("BAD_CATEGORY"),
            message="Bad category.",
            category=cast(ErrorCategory, "provider_native"),
            severity=ErrorSeverity.ERROR,
            retryable=False,
        )

    with pytest.raises(ValueError, match="not a valid"):
        ContractError(
            error_code=ErrorCode("BAD_SEVERITY"),
            message="Bad severity.",
            category=ErrorCategory.INTERNAL,
            severity=cast(ErrorSeverity, "panic"),
            retryable=False,
        )


def test_secret_shaped_arbitrary_details_are_not_implicitly_accepted() -> None:
    with pytest.raises(ValueError, match="secret-shaped key"):
        ContractError(
            error_code=ErrorCode("UNSAFE_DETAILS"),
            message="Unsafe details.",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.ERROR,
            retryable=False,
            details={"api_token": "abc123"},
        )


def test_provider_native_exception_objects_are_not_serialized() -> None:
    with pytest.raises(TypeError, match="JSON-compatible safe detail data"):
        ContractError(
            error_code=ErrorCode("PROVIDER_ERROR"),
            message="Provider error was translated unsafely.",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.ERROR,
            retryable=True,
            details={"provider_exception": ValueError("native exception")},
        )


def test_warning_contract_is_distinct_from_error_contract() -> None:
    warning = ResultWarning(
        warning_code=ErrorCode("PARTIAL_CONTEXT"),
        message="Some optional context was unavailable.",
        details={"source_count": 2},
    )

    assert not isinstance(warning, ContractError)
    assert warning.to_json_compatible() == {
        "warning_code": "PARTIAL_CONTEXT",
        "message": "Some optional context was unavailable.",
        "subject_ref": None,
        "trace_id": None,
        "details": {"source_count": 2},
    }
