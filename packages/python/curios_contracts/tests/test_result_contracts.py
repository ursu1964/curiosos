from __future__ import annotations

import json
from typing import cast

import pytest
from curios_contracts import (
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    EvidenceId,
    Result,
    ResultStatus,
    ResultWarning,
    to_json_compatible,
)


def _error() -> ContractError:
    return ContractError(
        error_code=ErrorCode("EXECUTION_FAILED"),
        message="Execution failed.",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        retryable=False,
    )


def test_result_success_with_value_and_evidence() -> None:
    evidence_id = EvidenceId.generate()

    result = Result.success(value={"answer": 42}, evidence_refs=(evidence_id,))

    assert result.status is ResultStatus.SUCCESS
    assert result.value == {"answer": 42}
    assert result.errors == ()
    assert result.to_json_compatible()["evidence_refs"] == [str(evidence_id)]


def test_result_failure_requires_meaningful_error_information() -> None:
    error = _error()

    result: Result[object] = Result.failure(errors=(error,))

    assert result.status is ResultStatus.FAILURE
    assert result.value is None
    assert result.errors == (error,)


def test_result_warnings_remain_distinct_from_errors() -> None:
    warning = ResultWarning(
        warning_code=ErrorCode("NON_FATAL_LIMIT"),
        message="A non-fatal limit was reached.",
    )

    result = Result.success(value="ok", warnings=(warning,))
    compatible = result.to_json_compatible()
    warnings = cast(list[dict[str, object]], compatible["warnings"])

    assert result.warnings == (warning,)
    assert result.errors == ()
    assert warnings[0]["warning_code"] == "NON_FATAL_LIMIT"


def test_result_rejects_contradictory_invalid_state() -> None:
    with pytest.raises(ValueError, match="successful results must not contain errors"):
        Result(status=ResultStatus.SUCCESS, value="ok", errors=(_error(),))

    with pytest.raises(ValueError, match="failure results must contain"):
        Result(status=ResultStatus.FAILURE)

    with pytest.raises(ValueError, match="failure results must not contain a value"):
        Result(status=ResultStatus.FAILURE, value="bad", errors=(_error(),))


def test_result_serialization_round_trip() -> None:
    evidence_id = EvidenceId.generate()
    warning = ResultWarning(
        warning_code=ErrorCode("PARTIAL_CONTEXT"),
        message="Some optional context was unavailable.",
    )
    result = Result.success(
        value={"ok": True},
        evidence_refs=(evidence_id,),
        warnings=(warning,),
    )

    decoded = json.loads(json.dumps(to_json_compatible(result), sort_keys=True))
    parsed: Result[object] = Result.from_json_compatible(decoded)

    assert parsed == result
