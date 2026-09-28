from __future__ import annotations

import json

import pytest
from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    CorrelationId,
    DataLabAnalysisId,
    DataLabAnalysisKind,
    DataLabAnalysisRequest,
    DataLabAnalysisResult,
    DataLabFinding,
    DataLabFindingCategory,
    DataLabFindingSeverity,
    DataLabResultId,
    DataLabRunId,
    DatasetColumnProfile,
    DatasetPrimitiveType,
    DatasetProfile,
    DatasetProfileWarning,
    EvidenceId,
    IntegrityAlgorithm,
    IntegrityDescriptor,
    ObjectReference,
    ProjectId,
    UtcTimestamp,
    WorkId,
    to_json_compatible,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
UTC_NOW = UtcTimestamp.parse("2026-09-22T10:00:00Z")


def _dataset_ref(
    *, sha256: str = SHA_A, kind: ArtifactKind = ArtifactKind.DATASET
) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=ArtifactId.generate(),
        kind=kind,
        locator="curios-staged-dataset",
        media_type="text/csv",
        integrity=IntegrityDescriptor(
            algorithm=IntegrityAlgorithm.SHA256,
            value=sha256,
        ),
        created_at=UTC_NOW,
        producer_ref=ObjectReference.from_id(ProjectId.generate()),
    )


def _columns() -> tuple[DatasetColumnProfile, DatasetColumnProfile]:
    return (
        DatasetColumnProfile(
            name="amount",
            index=1,
            inferred_type=DatasetPrimitiveType.DECIMAL,
            missing_count=1,
            non_missing_count=9,
            distinct_count=7,
            minimum=1.5,
            maximum=9.5,
            mean=4.5,
        ),
        DatasetColumnProfile(
            name="name",
            index=0,
            inferred_type=DatasetPrimitiveType.STRING,
            missing_count=0,
            non_missing_count=10,
            distinct_count=10,
        ),
    )


def _profile(
    dataset_ref: ArtifactReference | None = None, *, sha256: str = SHA_A
) -> DatasetProfile:
    return DatasetProfile(
        dataset_ref=dataset_ref or _dataset_ref(sha256=sha256),
        dataset_integrity_sha256=sha256,
        row_count=10,
        column_count=2,
        columns=_columns(),
        warnings=(
            DatasetProfileWarning(
                warning_code="mixed_values",
                message="Column contains mixed values.",
                column_index=1,
            ),
            DatasetProfileWarning(
                warning_code="empty_values",
                message="Column contains empty values.",
                column_index=0,
            ),
        ),
    )


def _finding(
    dataset_ref: ArtifactReference,
    *,
    sha256: str = SHA_A,
    key: str = "schema_warning",
    severity: DataLabFindingSeverity = DataLabFindingSeverity.WARNING,
) -> DataLabFinding:
    return DataLabFinding(
        finding_key=key,
        category=DataLabFindingCategory.SCHEMA,
        severity=severity,
        summary="Column shape requires attention.",
        dataset_ref=dataset_ref,
        dataset_integrity_sha256=sha256,
        provenance_path="profile.columns[0]",
        evidence_refs=(EvidenceId.generate(),),
    )


def _analysis_request(dataset_ref: ArtifactReference) -> DataLabAnalysisRequest:
    return DataLabAnalysisRequest(
        analysis_id=DataLabAnalysisId.generate(),
        dataset_ref=dataset_ref,
        dataset_integrity_sha256=SHA_A,
        objective="PROFILE_DATASET",
        analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
        created_at=UTC_NOW,
        correlation_id=CorrelationId.generate(),
        principal_ref=ObjectReference.from_id(ProjectId.generate()),
        constraints={"max_rows": "10000", "mode": "profile"},
    )


def _analysis_result(dataset_ref: ArtifactReference) -> DataLabAnalysisResult:
    profile = _profile(dataset_ref)
    return DataLabAnalysisResult(
        result_id=DataLabResultId.generate(),
        run_id=DataLabRunId.generate(),
        analysis_id=DataLabAnalysisId.generate(),
        work_ref=ObjectReference.from_id(WorkId.generate()),
        dataset_ref=dataset_ref,
        dataset_integrity_sha256=SHA_A,
        profile=profile,
        findings=(
            _finding(dataset_ref, key="info_notice", severity=DataLabFindingSeverity.INFO),
            _finding(dataset_ref, key="error_notice", severity=DataLabFindingSeverity.ERROR),
        ),
        warnings=profile.warnings,
        evidence_refs=(EvidenceId.generate(),),
        created_at=UTC_NOW,
    )


def test_datalab_analysis_request_reuses_dataset_artifact_reference_and_serializes() -> None:
    request = _analysis_request(_dataset_ref())
    decoded = json.loads(json.dumps(to_json_compatible(request), sort_keys=True))

    assert decoded["analysis_kind"] == "PROFILE_DATASET"
    assert decoded["dataset_ref"]["kind"] == "dataset"
    assert decoded["dataset_ref"]["media_type"] == "text/csv"
    assert decoded["dataset_integrity_sha256"] == SHA_A
    assert list(decoded["constraints"]) == ["max_rows", "mode"]
    assert DataLabAnalysisRequest.from_json_compatible(decoded) == request


def test_dataset_profile_preserves_ordering_and_round_trips() -> None:
    profile = _profile()
    decoded = json.loads(json.dumps(to_json_compatible(profile), sort_keys=True))

    assert [column["name"] for column in decoded["columns"]] == ["name", "amount"]
    assert [warning["warning_code"] for warning in decoded["warnings"]] == [
        "empty_values",
        "mixed_values",
    ]
    assert DatasetProfile.from_json_compatible(decoded) == profile


def test_datalab_result_sorts_findings_and_binds_dataset_identity() -> None:
    result = _analysis_result(_dataset_ref())
    decoded = result.to_json_compatible()

    assert [finding["finding_key"] for finding in decoded["findings"]] == [
        "error_notice",
        "info_notice",
    ]
    assert DataLabAnalysisResult.from_json_compatible(decoded) == result


def test_contracts_reject_wrong_dataset_artifact_kind_or_missing_integrity() -> None:
    with pytest.raises(ValueError, match="kind=dataset"):
        _analysis_request(_dataset_ref(kind=ArtifactKind.DOCUMENT))

    dataset_ref = ArtifactReference(
        artifact_id=ArtifactId.generate(),
        kind=ArtifactKind.DATASET,
        locator="curios-staged-dataset",
        media_type="text/csv",
        created_at=UTC_NOW,
        producer_ref=ObjectReference.from_id(ProjectId.generate()),
    )
    with pytest.raises(ValueError, match="integrity must be present"):
        _analysis_request(dataset_ref)


def test_contracts_reject_hash_and_cross_record_mismatches() -> None:
    dataset_ref = _dataset_ref()
    with pytest.raises(ValueError, match="integrity must match"):
        DataLabAnalysisRequest(
            analysis_id=DataLabAnalysisId.generate(),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_B,
            objective="PROFILE_DATASET",
            analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
            created_at=UTC_NOW,
            correlation_id=CorrelationId.generate(),
        )

    wrong_profile = _profile(_dataset_ref(sha256=SHA_B), sha256=SHA_B)
    with pytest.raises(ValueError, match="profile dataset_ref must match"):
        DataLabAnalysisResult(
            result_id=DataLabResultId.generate(),
            run_id=DataLabRunId.generate(),
            analysis_id=DataLabAnalysisId.generate(),
            work_ref=ObjectReference.from_id(WorkId.generate()),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            profile=wrong_profile,
            findings=(),
            warnings=(),
            evidence_refs=(),
            created_at=UTC_NOW,
        )


def test_contracts_reject_bounds_duplicates_and_malformed_values() -> None:
    dataset_ref = _dataset_ref()
    with pytest.raises(ValueError, match="objective must be at most"):
        DataLabAnalysisRequest(
            analysis_id=DataLabAnalysisId.generate(),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            objective="x" * 1001,
            analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
            created_at=UTC_NOW,
            correlation_id=CorrelationId.generate(),
        )

    with pytest.raises(ValueError, match="columns length must match"):
        DatasetProfile(
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            row_count=10,
            column_count=2,
            columns=(_columns()[0],),
        )

    duplicate_finding = _finding(dataset_ref)
    with pytest.raises(ValueError, match="duplicate finding_key"):
        DataLabAnalysisResult(
            result_id=DataLabResultId.generate(),
            run_id=DataLabRunId.generate(),
            analysis_id=DataLabAnalysisId.generate(),
            work_ref=ObjectReference.from_id(WorkId.generate()),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            profile=_profile(dataset_ref),
            findings=(duplicate_finding, duplicate_finding),
            warnings=(),
            evidence_refs=(),
            created_at=UTC_NOW,
        )

    evidence_id = EvidenceId.generate()
    with pytest.raises(ValueError, match="duplicate evidence"):
        _finding(dataset_ref, key="duplicate_evidence", severity=DataLabFindingSeverity.ERROR)
        DataLabFinding(
            finding_key="duplicate_evidence",
            category=DataLabFindingCategory.QUALITY,
            severity=DataLabFindingSeverity.ERROR,
            summary="Duplicate evidence reference.",
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            provenance_path="profile",
            evidence_refs=(evidence_id, evidence_id),
        )


def test_contract_errors_are_bounded_and_reject_secret_shaped_text() -> None:
    dataset_ref = _dataset_ref()
    with pytest.raises(ValueError, match="secret-shaped") as exc_info:
        DataLabFinding(
            finding_key="unsafe_summary",
            category=DataLabFindingCategory.QUALITY,
            severity=DataLabFindingSeverity.ERROR,
            summary="password=super-secret-value",
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            provenance_path="profile",
        )

    assert "super-secret-value" not in str(exc_info.value)


def test_from_json_rejects_malformed_shapes_without_framework_models() -> None:
    with pytest.raises(TypeError, match="JSON must be an object"):
        DataLabAnalysisResult.from_json_compatible(["not", "an", "object"])

    payload = _analysis_result(_dataset_ref()).to_json_compatible()
    payload["work_ref"] = ObjectReference.from_id(ProjectId.generate()).to_json_compatible()
    with pytest.raises(ValueError, match="work_ref must reference work"):
        DataLabAnalysisResult.from_json_compatible(payload)
