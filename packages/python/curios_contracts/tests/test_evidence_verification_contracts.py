from __future__ import annotations

import json

from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ObjectReference,
    ProjectId,
    TraceId,
    UtcTimestamp,
    VerificationId,
    VerificationOutcome,
    VerificationReference,
    WorkId,
    to_json_compatible,
)


def test_evidence_reference_subject_artifact_timestamps_and_serialization() -> None:
    subject_ref = ObjectReference.from_id(ProjectId.generate())
    trace_id = TraceId.generate()
    artifact_ref = ArtifactReference(
        artifact_id=ArtifactId.generate(),
        kind=ArtifactKind.LOG,
        locator="task-output-log",
        created_at=UtcTimestamp.parse("2026-09-22T09:00:00Z"),
    )
    evidence = EvidenceReference(
        evidence_id=EvidenceId.generate(),
        kind=EvidenceKind.TEST_RESULT,
        subject_ref=subject_ref,
        artifact_refs=(artifact_ref,),
        collected_at=UtcTimestamp.parse("2026-09-22T10:00:00+02:00"),
        summary="Package-local tests passed.",
        trace_id=trace_id,
    )

    decoded = json.loads(json.dumps(to_json_compatible(evidence), sort_keys=True))

    assert decoded["subject_ref"] == subject_ref.to_json_compatible()
    assert decoded["artifact_refs"] == [artifact_ref.to_json_compatible()]
    assert decoded["collected_at"] == "2026-09-22T08:00:00Z"
    assert decoded["trace_id"] == str(trace_id)
    assert EvidenceReference.from_json_compatible(decoded) == evidence


def test_evidence_reference_can_link_artifact_ids_without_embedding_records() -> None:
    artifact_id = ArtifactId.generate()
    evidence = EvidenceReference(
        evidence_id=EvidenceId.generate(),
        kind=EvidenceKind.INSPECTION,
        subject_ref=ObjectReference.from_id(WorkId.generate()),
        artifact_refs=(artifact_id,),
        collected_at=UtcTimestamp.parse("2026-09-22T10:00:00Z"),
    )

    assert evidence.to_json_compatible()["artifact_refs"] == [str(artifact_id)]


def test_verification_reference_core_fields_outcome_and_serialization() -> None:
    evidence_id = EvidenceId.generate()
    verifier_ref = ObjectReference.from_id(ProjectId.generate())
    verification = VerificationReference(
        verification_id=VerificationId.generate(),
        subject_ref=ObjectReference.from_id(WorkId.generate()),
        outcome=VerificationOutcome.PASSED,
        evidence_refs=(evidence_id,),
        verifier_ref=verifier_ref,
        verified_at=UtcTimestamp.parse("2026-09-22T11:30:00+02:00"),
    )

    decoded = json.loads(json.dumps(to_json_compatible(verification), sort_keys=True))

    assert decoded["verification_id"] == str(verification.verification_id)
    assert decoded["evidence_refs"] == [str(evidence_id)]
    assert decoded["verifier_ref"] == verifier_ref.to_json_compatible()
    assert decoded["outcome"] == "passed"
    assert decoded["verified_at"] == "2026-09-22T09:30:00Z"
    assert VerificationReference.from_json_compatible(decoded) == verification
