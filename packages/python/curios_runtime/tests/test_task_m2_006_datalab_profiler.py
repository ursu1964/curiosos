from __future__ import annotations

import hashlib
import json

import pytest
from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    DataLabAnalysisId,
    DataLabFindingCategory,
    DataLabFindingSeverity,
    DataLabResultId,
    DataLabRunId,
    DatasetPrimitiveType,
    ErrorCategory,
    EventId,
    EvidenceId,
    IntegrityAlgorithm,
    IntegrityDescriptor,
    ObjectReference,
    ObservabilityContext,
    ProjectId,
    ReferenceKind,
    ResultStatus,
    UtcTimestamp,
    WorkId,
)
from curios_runtime import (
    DATALAB_DATASET_MEDIA_TYPE,
    DATALAB_MAX_CELL_BYTES,
    DATALAB_MAX_COLUMNS,
    DATALAB_MAX_DATA_ROWS,
    DataLabProfilerErrorCode,
    DataLabProfilerOutcome,
    DataLabProfilerOutcomeStatus,
    DataLabProfilerRequest,
    DataLabProfilerResourceBounds,
    DeterministicDataLabProfiler,
    InMemoryDataLabStagedInput,
)

UTC_NOW = UtcTimestamp.parse("2026-09-28T10:00:00Z")


def _producer_ref() -> ObjectReference:
    return ObjectReference.from_id(ProjectId("prj_0123456789ABCDEFGHJKMNPQRS"))


def _work_ref() -> ObjectReference:
    return ObjectReference.from_id(WorkId("wrk_0123456789ABCDEFGHJKMNPQRS"))


def _dataset_ref(content: bytes, *, kind: ArtifactKind = ArtifactKind.DATASET) -> ArtifactReference:
    return ArtifactReference(
        artifact_id=ArtifactId("art_0123456789ABCDEFGHJKMNPQRS"),
        kind=kind,
        locator="curios-datalab-staged:art_0123456789ABCDEFGHJKMNPQRS",
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        integrity=IntegrityDescriptor(
            algorithm=IntegrityAlgorithm.SHA256,
            value=hashlib.sha256(content).hexdigest(),
        ),
        producer_ref=_producer_ref(),
        created_at=UTC_NOW,
    )


def _request(
    content: bytes,
    *,
    staged_content: bytes | None = None,
    dataset_ref: ArtifactReference | None = None,
    expected_sha256: str | None = None,
    bounds: DataLabProfilerResourceBounds | None = None,
    constraints: tuple[tuple[str, str], ...] = (),
) -> DataLabProfilerRequest:
    selected_ref = dataset_ref or _dataset_ref(content)
    return DataLabProfilerRequest(
        dataset_ref=selected_ref,
        staged_input=InMemoryDataLabStagedInput(
            handle_id="staged_dataset",
            content=content if staged_content is None else staged_content,
        ),
        expected_sha256=expected_sha256 or hashlib.sha256(content).hexdigest(),
        run_id=DataLabRunId("dlr_0123456789ABCDEFGHJKMNPQRS"),
        analysis_id=DataLabAnalysisId("dla_0123456789ABCDEFGHJKMNPQRS"),
        result_id=DataLabResultId("dlt_0123456789ABCDEFGHJKMNPQRS"),
        work_ref=_work_ref(),
        producer_ref=_producer_ref(),
        evidence_id=EvidenceId("evd_0123456789ABCDEFGHJKMNPQRS"),
        started_event_id=EventId("evt_0123456789ABCDEFGHJKMNPQRS"),
        completed_event_id=EventId("evt_1123456789ABCDEFGHJKMNPQRS"),
        occurred_at=UTC_NOW,
        observability_context=ObservabilityContext(
            work_id=WorkId("wrk_0123456789ABCDEFGHJKMNPQRS")
        ),
        resource_bounds=bounds or DataLabProfilerResourceBounds(),
        constraints=constraints,
    )


def _profile(content: bytes) -> DataLabProfilerOutcome:
    outcome = DeterministicDataLabProfiler().profile(_request(content))
    assert outcome.status is DataLabProfilerOutcomeStatus.COMPLETED
    assert outcome.profile is not None
    assert outcome.result.status is ResultStatus.SUCCESS
    return outcome


def test_profiles_minimal_dataset_into_canonical_result_profile_events_and_evidence() -> None:
    content = b"name,amount\nalice,2\nbob,3\n"
    outcome = _profile(content)

    assert outcome.profile is not None
    assert outcome.profile.dataset_ref == _dataset_ref(content)
    assert outcome.profile.dataset_integrity_sha256 == hashlib.sha256(content).hexdigest()
    assert outcome.profile.row_count == 2
    assert outcome.profile.column_count == 2
    assert [column.name for column in outcome.profile.columns] == ["name", "amount"]
    assert outcome.profile.columns[0].inferred_type is DatasetPrimitiveType.STRING
    assert outcome.profile.columns[1].inferred_type is DatasetPrimitiveType.INTEGER
    assert outcome.profile.columns[1].minimum == 2
    assert outcome.profile.columns[1].maximum == 3
    assert outcome.profile.columns[1].mean == 2.5
    assert outcome.result.value is not None
    assert outcome.result.value.profile == outcome.profile
    assert outcome.result.value.evidence_refs == outcome.evidence_refs
    assert [str(event.event_type) for event in outcome.events] == [
        "datalab.profiler.started",
        "datalab.profiler.completed",
    ]
    assert outcome.evidence_refs[0].subject_ref.kind is ReferenceKind.WORK


def test_profiler_infers_frozen_primitive_types_and_missing_counts() -> None:
    outcome = _profile(
        b"integer,decimal,boolean,empty,mixed,string\n2,1.5,true,,2,hello\n3,2.5,false,,text,NaN\n"
    )
    assert outcome.profile is not None

    by_name = {column.name: column for column in outcome.profile.columns}
    assert by_name["integer"].inferred_type is DatasetPrimitiveType.INTEGER
    assert by_name["decimal"].inferred_type is DatasetPrimitiveType.DECIMAL
    assert by_name["boolean"].inferred_type is DatasetPrimitiveType.BOOLEAN
    assert by_name["empty"].inferred_type is DatasetPrimitiveType.EMPTY
    assert by_name["empty"].missing_count == 2
    assert by_name["empty"].non_missing_count == 0
    assert by_name["mixed"].inferred_type is DatasetPrimitiveType.MIXED
    assert by_name["string"].inferred_type is DatasetPrimitiveType.STRING
    assert {warning.warning_code for warning in outcome.profile.warnings} == {
        "empty_column",
        "high_missingness",
        "mixed_types",
    }
    assert {finding.category for finding in outcome.findings} == {
        DataLabFindingCategory.COMPLETENESS,
        DataLabFindingCategory.TYPE_MIX,
    }
    assert DataLabFindingSeverity.WARNING in {finding.severity for finding in outcome.findings}


def test_profiler_is_deterministic_for_same_request_and_bytes() -> None:
    content = b"flag,text\nYES, a \nno,b\n"
    request = _request(content)
    profiler = DeterministicDataLabProfiler()

    first = profiler.profile(request).to_json_compatible()
    second = profiler.profile(request).to_json_compatible()

    assert json.loads(json.dumps(first, sort_keys=True)) == json.loads(
        json.dumps(second, sort_keys=True)
    )


def test_profiler_accepts_utf8_bom_and_hashes_exact_uploaded_bytes() -> None:
    content = b"\xef\xbb\xbfname\nalice\n"
    outcome = _profile(content)

    assert outcome.profile is not None
    assert outcome.profile.dataset_integrity_sha256 == hashlib.sha256(content).hexdigest()
    assert outcome.profile.columns[0].name == "name"


def test_profiler_rejects_wrong_dataset_kind_and_non_seam_staged_input() -> None:
    content = b"name\nalice\n"
    with pytest.raises(ValueError, match="kind=dataset"):
        _request(content, dataset_ref=_dataset_ref(content, kind=ArtifactKind.DOCUMENT))

    with pytest.raises(TypeError, match="authorized staged-input seam"):
        DataLabProfilerRequest(
            dataset_ref=_dataset_ref(content),
            staged_input="curios-datalab-staged:art_0123456789ABCDEFGHJKMNPQRS",  # type: ignore[arg-type]
            expected_sha256=hashlib.sha256(content).hexdigest(),
            run_id=DataLabRunId("dlr_0123456789ABCDEFGHJKMNPQRS"),
            analysis_id=DataLabAnalysisId("dla_0123456789ABCDEFGHJKMNPQRS"),
            result_id=DataLabResultId("dlt_0123456789ABCDEFGHJKMNPQRS"),
            work_ref=_work_ref(),
            producer_ref=_producer_ref(),
            evidence_id=EvidenceId("evd_0123456789ABCDEFGHJKMNPQRS"),
            started_event_id=EventId("evt_0123456789ABCDEFGHJKMNPQRS"),
            completed_event_id=EventId("evt_1123456789ABCDEFGHJKMNPQRS"),
            occurred_at=UTC_NOW,
            observability_context=ObservabilityContext(),
        )


def test_profiler_integrity_gate_fails_before_successful_profile() -> None:
    content = b"name\nalice\n"
    request = _request(content, staged_content=b"name\nmallory\n")
    outcome = DeterministicDataLabProfiler().profile(request)

    assert outcome.status is DataLabProfilerOutcomeStatus.FAILED
    assert outcome.result.status is ResultStatus.FAILURE
    assert (
        str(outcome.result.errors[0].error_code)
        == DataLabProfilerErrorCode.DATASET_INTEGRITY_MISMATCH.value
    )
    assert outcome.profile is None


@pytest.mark.parametrize(
    ("content", "code"),
    (
        (b"\xff\n", DataLabProfilerErrorCode.MALFORMED_CSV),
        (b"name\n", DataLabProfilerErrorCode.MALFORMED_CSV),
        (b"name,amount\nalice\n", DataLabProfilerErrorCode.MALFORMED_CSV),
        (b'name\n"unterminated\n', DataLabProfilerErrorCode.MALFORMED_CSV),
        (b"name,name\nalice,bob\n", DataLabProfilerErrorCode.MALFORMED_CSV),
    ),
)
def test_profiler_malformed_input_fails_boundedly(
    content: bytes,
    code: DataLabProfilerErrorCode,
) -> None:
    outcome = DeterministicDataLabProfiler().profile(_request(content))

    assert outcome.status is DataLabProfilerOutcomeStatus.FAILED
    assert str(outcome.result.errors[0].error_code) == code.value
    assert outcome.result.errors[0].message == "malformed csv"


def test_profiler_enforces_resource_bounds() -> None:
    max_rows = b"c\n" + b"1\n" * DATALAB_MAX_DATA_ROWS
    assert _profile(max_rows).profile is not None

    too_many_rows = max_rows + b"1\n"
    outcome = DeterministicDataLabProfiler().profile(_request(too_many_rows))
    assert outcome.result.errors[0].details == {"limit": "rows"}

    header = ",".join(f"c{index}" for index in range(DATALAB_MAX_COLUMNS + 1))
    row = ",".join("x" for _ in range(DATALAB_MAX_COLUMNS + 1))
    outcome = DeterministicDataLabProfiler().profile(_request(f"{header}\n{row}\n".encode()))
    assert outcome.result.errors[0].details == {"limit": "columns"}

    oversized_cell = b"c\n" + b"x" * (DATALAB_MAX_CELL_BYTES + 1) + b"\n"
    outcome = DeterministicDataLabProfiler().profile(_request(oversized_cell))
    assert outcome.result.errors[0].details == {"limit": "cell"}


def test_profiler_rejects_unsupported_constraints_without_tool_authority() -> None:
    outcome = DeterministicDataLabProfiler().profile(
        _request(b"name\nalice\n", constraints=(("mode", "profile"),))
    )

    assert outcome.status is DataLabProfilerOutcomeStatus.FAILED
    assert (
        str(outcome.result.errors[0].error_code) == DataLabProfilerErrorCode.INVALID_REQUEST.value
    )
    assert outcome.result.errors[0].category is ErrorCategory.VALIDATION


def test_profiler_safe_errors_do_not_echo_csv_or_secret_shaped_values() -> None:
    sensitive_text = "api" + "_key" + "=" + "super-secret-value"
    outcome = DeterministicDataLabProfiler().profile(
        _request(f"name\n{sensitive_text},extra\n".encode())
    )

    serialized = json.dumps(outcome.to_json_compatible(), sort_keys=True)
    assert outcome.status is DataLabProfilerOutcomeStatus.FAILED
    assert sensitive_text not in serialized
    assert "staged_dataset" not in serialized
    assert "curios-datalab-staged:" not in serialized


def test_profiler_output_does_not_depend_on_staged_handle_metadata() -> None:
    content = b"name,amount\nalice,2\n"
    base = _request(content)
    alternate = DataLabProfilerRequest(
        dataset_ref=base.dataset_ref,
        staged_input=InMemoryDataLabStagedInput(handle_id="other_handle", content=content),
        expected_sha256=base.expected_sha256,
        run_id=base.run_id,
        analysis_id=base.analysis_id,
        result_id=base.result_id,
        work_ref=base.work_ref,
        producer_ref=base.producer_ref,
        evidence_id=base.evidence_id,
        started_event_id=base.started_event_id,
        completed_event_id=base.completed_event_id,
        occurred_at=base.occurred_at,
        observability_context=base.observability_context,
    )

    base_result = DeterministicDataLabProfiler().profile(base).to_json_compatible()
    alternate_result = DeterministicDataLabProfiler().profile(alternate).to_json_compatible()
    assert base_result == alternate_result
