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
    ReferenceKind,
    UtcTimestamp,
    WorkId,
    to_json_compatible,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
UTC_NOW = UtcTimestamp.parse("2026-09-24T12:00:00Z")


def _dataset_ref(
    *,
    sha256: str = SHA_A,
    kind: ArtifactKind = ArtifactKind.DATASET,
    media_type: str = "text/csv",
    integrity_algorithm: IntegrityAlgorithm = IntegrityAlgorithm.SHA256,
    producer_ref: ObjectReference | None = None,
) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=ArtifactId.generate(),
        kind=kind,
        locator="curios-generated-staged-dataset",
        media_type=media_type,
        integrity=IntegrityDescriptor(algorithm=integrity_algorithm, value=sha256),
        created_at=UTC_NOW,
        producer_ref=producer_ref or ObjectReference.from_id(ProjectId.generate()),
    )


def _columns() -> tuple[DatasetColumnProfile, DatasetColumnProfile]:
    return (
        DatasetColumnProfile(
            name="amount",
            index=1,
            inferred_type=DatasetPrimitiveType.DECIMAL,
            missing_count=2,
            non_missing_count=8,
            distinct_count=6,
            minimum=1.0,
            maximum=9.0,
            mean=4.0,
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
    dataset_ref: ArtifactReference | None = None,
    *,
    sha256: str = SHA_A,
) -> DatasetProfile:
    return DatasetProfile(
        dataset_ref=dataset_ref or _dataset_ref(sha256=sha256),
        dataset_integrity_sha256=sha256,
        row_count=10,
        column_count=2,
        columns=_columns(),
        warnings=(
            DatasetProfileWarning("mixed_values", "Mixed values detected.", column_index=1),
            DatasetProfileWarning("empty_values", "Empty values detected.", column_index=0),
        ),
    )


def _finding(
    dataset_ref: ArtifactReference,
    *,
    sha256: str = SHA_A,
    key: str = "quality_warning",
    severity: DataLabFindingSeverity = DataLabFindingSeverity.WARNING,
    evidence_refs: tuple[EvidenceId, ...] | None = None,
) -> DataLabFinding:
    return DataLabFinding(
        finding_key=key,
        category=DataLabFindingCategory.QUALITY,
        severity=severity,
        summary="Profile requires review.",
        dataset_ref=dataset_ref,
        dataset_integrity_sha256=sha256,
        provenance_path="profile.columns[0]",
        evidence_refs=evidence_refs or (),
    )


def _result(dataset_ref: ArtifactReference) -> DataLabAnalysisResult:
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


@pytest.mark.parametrize(
    ("id_type", "expected_kind", "expected_token"),
    (
        (DataLabAnalysisId, ReferenceKind.DATALAB_ANALYSIS, "datalab_analysis"),
        (DataLabRunId, ReferenceKind.DATALAB_RUN, "datalab_run"),
        (DataLabResultId, ReferenceKind.DATALAB_RESULT, "datalab_result"),
    ),
)
def test_validation_regression_datalab_ids_round_trip_through_object_reference(
    id_type: type[DataLabAnalysisId] | type[DataLabRunId] | type[DataLabResultId],
    expected_kind: ReferenceKind,
    expected_token: str,
) -> None:
    typed_id = id_type.generate()

    reference = ObjectReference.from_id(typed_id)
    payload = reference.to_json_compatible()
    decoded = ObjectReference.from_json_compatible(payload)

    assert reference.kind is expected_kind
    assert payload == {"kind": expected_token, "ref_id": str(typed_id)}
    assert decoded == reference
    assert type(decoded.ref_id) is id_type


@pytest.mark.parametrize(
    ("kind", "ref_id"),
    (
        (ReferenceKind.DATALAB_RUN, DataLabAnalysisId.generate()),
        (ReferenceKind.DATALAB_RESULT, DataLabAnalysisId.generate()),
        (ReferenceKind.DATALAB_ANALYSIS, DataLabRunId.generate()),
        (ReferenceKind.DATALAB_RESULT, DataLabRunId.generate()),
        (ReferenceKind.DATALAB_ANALYSIS, DataLabResultId.generate()),
        (ReferenceKind.DATALAB_RUN, DataLabResultId.generate()),
        (ReferenceKind.WORK, DataLabResultId.generate()),
    ),
)
def test_validation_regression_datalab_references_reject_wrong_kinds(
    kind: ReferenceKind,
    ref_id: DataLabAnalysisId | DataLabRunId | DataLabResultId,
) -> None:
    with pytest.raises(TypeError):
        ObjectReference(kind=kind, ref_id=ref_id)


def test_validation_regression_dataset_artifact_requirements_are_enforced() -> None:
    with pytest.raises(ValueError, match="kind=dataset"):
        DataLabAnalysisRequest(
            analysis_id=DataLabAnalysisId.generate(),
            dataset_ref=_dataset_ref(kind=ArtifactKind.DOCUMENT),
            dataset_integrity_sha256=SHA_A,
            objective="PROFILE_DATASET",
            analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
            created_at=UTC_NOW,
            correlation_id=CorrelationId.generate(),
        )

    with pytest.raises(ValueError, match="media_type must be text/csv"):
        DataLabAnalysisRequest(
            analysis_id=DataLabAnalysisId.generate(),
            dataset_ref=_dataset_ref(media_type="application/json"),
            dataset_integrity_sha256=SHA_A,
            objective="PROFILE_DATASET",
            analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
            created_at=UTC_NOW,
            correlation_id=CorrelationId.generate(),
        )

    with pytest.raises(ValueError, match="integrity algorithm must be sha256"):
        DataLabAnalysisRequest(
            analysis_id=DataLabAnalysisId.generate(),
            dataset_ref=_dataset_ref(
                sha256="b" * 128,
                integrity_algorithm=IntegrityAlgorithm.SHA512,
            ),
            dataset_integrity_sha256=SHA_A,
            objective="PROFILE_DATASET",
            analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
            created_at=UTC_NOW,
            correlation_id=CorrelationId.generate(),
        )


def test_validation_regression_cross_record_dataset_and_integrity_mismatches_reject() -> None:
    dataset_ref = _dataset_ref()
    profile_b = _profile(_dataset_ref(sha256=SHA_B), sha256=SHA_B)

    with pytest.raises(ValueError, match="profile dataset_ref must match"):
        DataLabAnalysisResult(
            result_id=DataLabResultId.generate(),
            run_id=DataLabRunId.generate(),
            analysis_id=DataLabAnalysisId.generate(),
            work_ref=ObjectReference.from_id(WorkId.generate()),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            profile=profile_b,
            findings=(),
            warnings=(),
            evidence_refs=(),
            created_at=UTC_NOW,
        )

    with pytest.raises(ValueError, match="finding dataset_ref must match"):
        DataLabAnalysisResult(
            result_id=DataLabResultId.generate(),
            run_id=DataLabRunId.generate(),
            analysis_id=DataLabAnalysisId.generate(),
            work_ref=ObjectReference.from_id(WorkId.generate()),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            profile=_profile(dataset_ref),
            findings=(_finding(_dataset_ref(sha256=SHA_B), sha256=SHA_B),),
            warnings=(),
            evidence_refs=(),
            created_at=UTC_NOW,
        )


def test_validation_regression_duplicates_bounds_and_counts_reject() -> None:
    dataset_ref = _dataset_ref()
    evidence_id = EvidenceId.generate()

    with pytest.raises(ValueError, match="duplicate names"):
        DatasetProfile(
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            row_count=10,
            column_count=2,
            columns=(
                _columns()[0],
                DatasetColumnProfile(
                    name="amount",
                    index=0,
                    inferred_type=DatasetPrimitiveType.STRING,
                    missing_count=0,
                    non_missing_count=10,
                    distinct_count=10,
                ),
            ),
        )

    with pytest.raises(ValueError, match="must equal row_count"):
        DatasetProfile(
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            row_count=10,
            column_count=1,
            columns=(
                DatasetColumnProfile(
                    name="bad_count",
                    index=0,
                    inferred_type=DatasetPrimitiveType.STRING,
                    missing_count=1,
                    non_missing_count=1,
                    distinct_count=1,
                ),
            ),
        )

    with pytest.raises(ValueError, match="duplicate evidence"):
        _finding(dataset_ref, evidence_refs=(evidence_id, evidence_id))

    with pytest.raises(ValueError, match="at most 10"):
        DataLabAnalysisRequest(
            analysis_id=DataLabAnalysisId.generate(),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            objective="PROFILE_DATASET",
            analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
            created_at=UTC_NOW,
            correlation_id=CorrelationId.generate(),
            constraints=[(f"k{i}", "v") for i in range(11)],
        )


def test_validation_regression_ordering_and_immutability_are_canonical() -> None:
    dataset_ref = _dataset_ref()
    warnings = [
        DatasetProfileWarning("z_warning", "Later warning.", column_index=1),
        DatasetProfileWarning("a_warning", "Earlier warning.", column_index=0),
    ]
    profile = DatasetProfile(
        dataset_ref=dataset_ref,
        dataset_integrity_sha256=SHA_A,
        row_count=10,
        column_count=2,
        columns=list(_columns()),  # type: ignore[arg-type]
        warnings=warnings,  # type: ignore[arg-type]
    )
    warnings.append(DatasetProfileWarning("middle", "Mutated caller input.", column_index=0))

    payload = profile.to_json_compatible()

    assert [column["index"] for column in payload["columns"]] == [0, 1]
    assert [warning["warning_code"] for warning in payload["warnings"]] == [
        "a_warning",
        "z_warning",
    ]


def test_validation_regression_serialization_and_malformed_json_are_bounded() -> None:
    result = _result(_dataset_ref())
    payload = json.loads(json.dumps(to_json_compatible(result), sort_keys=True))

    assert DataLabAnalysisResult.from_json_compatible(payload) == result

    payload["work_ref"] = ObjectReference.from_id(ProjectId.generate()).to_json_compatible()
    with pytest.raises(ValueError, match="work_ref must reference work"):
        DataLabAnalysisResult.from_json_compatible(payload)

    with pytest.raises(TypeError, match="JSON must be an object"):
        DatasetProfile.from_json_compatible(None)


def test_validation_regression_safe_errors_do_not_echo_sensitive_values() -> None:
    dataset_ref = _dataset_ref()

    with pytest.raises(ValueError, match="secret-shaped") as exc_info:
        DataLabAnalysisRequest(
            analysis_id=DataLabAnalysisId.generate(),
            dataset_ref=dataset_ref,
            dataset_integrity_sha256=SHA_A,
            objective="api_key=abc123",
            analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
            created_at=UTC_NOW,
            correlation_id=CorrelationId.generate(),
        )

    assert "abc123" not in str(exc_info.value)
