"""Lightweight verification-reference contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts.evidence import EvidenceReference
from curios_contracts.identifiers import EvidenceId, VerificationId
from curios_contracts.references import ObjectReference
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp


class VerificationOutcome(StrEnum):
    """M0 verification-reference outcomes."""

    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True, slots=True)
class VerificationReference:
    """Lightweight reference to a verification result, not a verification engine."""

    verification_id: VerificationId
    subject_ref: ObjectReference
    outcome: VerificationOutcome
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...]
    verified_at: UtcTimestamp
    verifier_ref: ObjectReference | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.verification_id, VerificationId):
            msg = "verification_id must be a VerificationId"
            raise TypeError(msg)
        if not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference"
            raise TypeError(msg)
        object.__setattr__(self, "outcome", VerificationOutcome(self.outcome))

        evidence_refs = tuple(self.evidence_refs)
        for evidence_ref in evidence_refs:
            if not isinstance(evidence_ref, EvidenceReference | EvidenceId):
                msg = "evidence_refs must contain EvidenceReference or EvidenceId values"
                raise TypeError(msg)
        object.__setattr__(self, "evidence_refs", evidence_refs)
        object.__setattr__(self, "verified_at", UtcTimestamp(self.verified_at))

        if self.verifier_ref is not None and not isinstance(self.verifier_ref, ObjectReference):
            msg = "verifier_ref must be an ObjectReference when provided"
            raise TypeError(msg)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "verification reference JSON must be an object"
            raise TypeError(msg)
        evidence_refs_value = value["evidence_refs"]
        if not isinstance(evidence_refs_value, list | tuple):
            msg = "evidence_refs must be a list"
            raise TypeError(msg)
        verifier_ref = value.get("verifier_ref")
        return cls(
            verification_id=VerificationId(
                _require_str(value["verification_id"], "verification_id")
            ),
            subject_ref=ObjectReference.from_json_compatible(value["subject_ref"]),
            outcome=VerificationOutcome(value["outcome"]),
            evidence_refs=tuple(_parse_evidence_ref(item) for item in evidence_refs_value),
            verified_at=UtcTimestamp(_require_str(value["verified_at"], "verified_at")),
            verifier_ref=(
                ObjectReference.from_json_compatible(verifier_ref)
                if verifier_ref is not None
                else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "verification_id": str(self.verification_id),
            "subject_ref": to_json_compatible(self.subject_ref),
            "outcome": self.outcome.value,
            "evidence_refs": to_json_compatible(self.evidence_refs),
            "verifier_ref": to_json_compatible(self.verifier_ref),
            "verified_at": to_json_compatible(self.verified_at),
        }


def _parse_evidence_ref(value: object) -> EvidenceReference | EvidenceId:
    if isinstance(value, str):
        return EvidenceId(value)
    return EvidenceReference.from_json_compatible(value)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


VERIFICATION_OUTCOME_VALUES: tuple[str, ...] = tuple(member.value for member in VerificationOutcome)
