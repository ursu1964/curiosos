"""Bounded generic result envelope contracts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Self, TypeVar, cast

from curios_contracts.errors import ContractError, ResultWarning
from curios_contracts.evidence import EvidenceReference
from curios_contracts.identifiers import EvidenceId
from curios_contracts.serialization import to_json_compatible

ResultValueT = TypeVar("ResultValueT")


class ResultStatus(StrEnum):
    """M0 result envelope statuses."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class Result[ResultValueT]:
    """Bounded cross-boundary result envelope for operation outcomes."""

    status: ResultStatus
    value: ResultValueT | None = None
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...] = ()
    warnings: tuple[ResultWarning, ...] = ()
    errors: tuple[ContractError, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", ResultStatus(self.status))

        evidence_refs = tuple(self.evidence_refs)
        for evidence_ref in evidence_refs:
            if not isinstance(evidence_ref, EvidenceReference | EvidenceId):
                msg = "evidence_refs must contain EvidenceReference or EvidenceId values"
                raise TypeError(msg)
        object.__setattr__(self, "evidence_refs", evidence_refs)

        warnings = tuple(self.warnings)
        for warning in warnings:
            if not isinstance(warning, ResultWarning):
                msg = "warnings must contain ResultWarning values"
                raise TypeError(msg)
        object.__setattr__(self, "warnings", warnings)

        errors = tuple(self.errors)
        for error in errors:
            if not isinstance(error, ContractError):
                msg = "errors must contain ContractError values"
                raise TypeError(msg)
        object.__setattr__(self, "errors", errors)

        if self.status is ResultStatus.SUCCESS and errors:
            msg = "successful results must not contain errors"
            raise ValueError(msg)
        if self.status is ResultStatus.FAILURE and not errors:
            msg = "failure results must contain at least one error"
            raise ValueError(msg)
        if self.status is ResultStatus.FAILURE and self.value is not None:
            msg = "failure results must not contain a value"
            raise ValueError(msg)

    @classmethod
    def success(
        cls,
        value: ResultValueT | None = None,
        *,
        evidence_refs: tuple[EvidenceReference | EvidenceId, ...] = (),
        warnings: tuple[ResultWarning, ...] = (),
    ) -> Self:
        """Create a successful result."""
        return cls(
            status=ResultStatus.SUCCESS,
            value=value,
            evidence_refs=evidence_refs,
            warnings=warnings,
        )

    @classmethod
    def failure(
        cls,
        errors: tuple[ContractError, ...],
        *,
        evidence_refs: tuple[EvidenceReference | EvidenceId, ...] = (),
        warnings: tuple[ResultWarning, ...] = (),
    ) -> Self:
        """Create a failed result."""
        return cls(
            status=ResultStatus.FAILURE,
            evidence_refs=evidence_refs,
            warnings=warnings,
            errors=errors,
        )

    @classmethod
    def from_json_compatible(
        cls,
        value: object,
        *,
        value_parser: Callable[[object], ResultValueT] | None = None,
    ) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "result JSON must be an object"
            raise TypeError(msg)
        raw_value = value.get("value")
        parsed_value: ResultValueT | None
        if raw_value is None:
            parsed_value = None
        elif value_parser is None:
            parsed_value = cast(ResultValueT, raw_value)
        else:
            parsed_value = value_parser(raw_value)

        evidence_refs_value = value.get("evidence_refs", ())
        warnings_value = value.get("warnings", ())
        errors_value = value.get("errors", ())
        if not isinstance(evidence_refs_value, list | tuple):
            msg = "evidence_refs must be a list"
            raise TypeError(msg)
        if not isinstance(warnings_value, list | tuple):
            msg = "warnings must be a list"
            raise TypeError(msg)
        if not isinstance(errors_value, list | tuple):
            msg = "errors must be a list"
            raise TypeError(msg)

        return cls(
            status=ResultStatus(value["status"]),
            value=parsed_value,
            evidence_refs=tuple(_parse_evidence_ref(item) for item in evidence_refs_value),
            warnings=tuple(ResultWarning.from_json_compatible(item) for item in warnings_value),
            errors=tuple(ContractError.from_json_compatible(item) for item in errors_value),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "status": self.status.value,
            "value": to_json_compatible(self.value),
            "evidence_refs": to_json_compatible(self.evidence_refs),
            "warnings": to_json_compatible(self.warnings),
            "errors": to_json_compatible(self.errors),
        }


def _parse_evidence_ref(value: object) -> EvidenceReference | EvidenceId:
    if isinstance(value, str):
        return EvidenceId(value)
    return EvidenceReference.from_json_compatible(value)


RESULT_STATUS_VALUES: tuple[str, ...] = tuple(member.value for member in ResultStatus)
