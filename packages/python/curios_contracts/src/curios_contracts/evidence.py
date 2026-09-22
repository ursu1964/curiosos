"""Lightweight evidence-reference contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import validate_safe_text
from curios_contracts.artifacts import ArtifactReference
from curios_contracts.identifiers import ArtifactId, EvidenceId, TraceId
from curios_contracts.references import ObjectReference
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp


class EvidenceKind(StrEnum):
    """M0 evidence-reference kinds."""

    TEST_RESULT = "test_result"
    INSPECTION = "inspection"
    LOG_EXCERPT = "log_excerpt"
    HUMAN_ATTESTATION = "human_attestation"
    PROVIDER_REPORT = "provider_report"
    ARTIFACT = "artifact"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Lightweight reference to evidence, not a complete provenance record."""

    evidence_id: EvidenceId
    kind: EvidenceKind
    subject_ref: ObjectReference
    collected_at: UtcTimestamp
    artifact_refs: tuple[ArtifactReference | ArtifactId, ...] = ()
    summary: str | None = None
    trace_id: TraceId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, EvidenceId):
            msg = "evidence_id must be an EvidenceId"
            raise TypeError(msg)
        object.__setattr__(self, "kind", EvidenceKind(self.kind))
        if not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference"
            raise TypeError(msg)
        object.__setattr__(self, "collected_at", UtcTimestamp(self.collected_at))

        artifact_refs = tuple(self.artifact_refs)
        for artifact_ref in artifact_refs:
            if not isinstance(artifact_ref, ArtifactReference | ArtifactId):
                msg = "artifact_refs must contain ArtifactReference or ArtifactId values"
                raise TypeError(msg)
        object.__setattr__(self, "artifact_refs", artifact_refs)

        if self.summary is not None:
            object.__setattr__(
                self,
                "summary",
                validate_safe_text(self.summary, "summary", max_length=1024),
            )
        if self.trace_id is not None and not isinstance(self.trace_id, TraceId):
            msg = "trace_id must be a TraceId when provided"
            raise TypeError(msg)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "evidence reference JSON must be an object"
            raise TypeError(msg)
        artifact_refs_value = value.get("artifact_refs", ())
        if not isinstance(artifact_refs_value, list | tuple):
            msg = "artifact_refs must be a list"
            raise TypeError(msg)
        trace_id = value.get("trace_id")
        if trace_id is not None and not isinstance(trace_id, str):
            msg = "trace_id must be a string when provided"
            raise TypeError(msg)
        return cls(
            evidence_id=EvidenceId(_require_str(value["evidence_id"], "evidence_id")),
            kind=EvidenceKind(value["kind"]),
            subject_ref=ObjectReference.from_json_compatible(value["subject_ref"]),
            collected_at=UtcTimestamp(_require_str(value["collected_at"], "collected_at")),
            artifact_refs=tuple(_parse_artifact_ref(item) for item in artifact_refs_value),
            summary=(
                _require_str(value["summary"], "summary")
                if value.get("summary") is not None
                else None
            ),
            trace_id=TraceId(trace_id) if trace_id is not None else None,
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "evidence_id": str(self.evidence_id),
            "kind": self.kind.value,
            "subject_ref": to_json_compatible(self.subject_ref),
            "artifact_refs": to_json_compatible(self.artifact_refs),
            "collected_at": to_json_compatible(self.collected_at),
            "summary": self.summary,
            "trace_id": to_json_compatible(self.trace_id),
        }


def _parse_artifact_ref(value: object) -> ArtifactReference | ArtifactId:
    if isinstance(value, str):
        return ArtifactId(value)
    return ArtifactReference.from_json_compatible(value)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


EVIDENCE_KIND_VALUES: tuple[str, ...] = tuple(member.value for member in EvidenceKind)
