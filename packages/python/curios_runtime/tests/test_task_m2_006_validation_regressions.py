from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    DataLabAnalysisId,
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
    DATALAB_MAX_UPLOAD_BYTES,
    DataLabProfilerErrorCode,
    DataLabProfilerOutcomeStatus,
    DataLabProfilerRequest,
    DataLabProfilerStagedInput,
    DeterministicDataLabProfiler,
)

UTC_NOW = UtcTimestamp.parse("2026-09-28T10:00:00Z")


def _producer_ref() -> ObjectReference:
    return ObjectReference.from_id(ProjectId("prj_0123456789ABCDEFGHJKMNPQRS"))


def _work_ref() -> ObjectReference:
    return ObjectReference.from_id(WorkId("wrk_0123456789ABCDEFGHJKMNPQRS"))


def _dataset_ref(
    content: bytes,
    *,
    kind: ArtifactKind = ArtifactKind.DATASET,
    media_type: str = DATALAB_DATASET_MEDIA_TYPE,
    integrity_algorithm: IntegrityAlgorithm = IntegrityAlgorithm.SHA256,
    sha256: str | None = None,
) -> ArtifactReference:
    digest = sha256 or hashlib.sha256(content).hexdigest()
    return ArtifactReference(
        artifact_id=ArtifactId("art_0123456789ABCDEFGHJKMNPQRS"),
        kind=kind,
        locator="curios-datalab-staged:art_0123456789ABCDEFGHJKMNPQRS",
        media_type=media_type,
        integrity=IntegrityDescriptor(algorithm=integrity_algorithm, value=digest),
        producer_ref=_producer_ref(),
        created_at=UTC_NOW,
    )


def _request(
    content: bytes,
    *,
    staged_content: bytes | None = None,
    staged_input: object | None = None,
    dataset_ref: ArtifactReference | None = None,
    expected_sha256: str | None = None,
) -> DataLabProfilerRequest:
    return DataLabProfilerRequest(
        dataset_ref=dataset_ref or _dataset_ref(content),
        staged_input=staged_input
        if staged_input is not None
        else DataLabProfilerStagedInput(
            handle_id="authorized_dataset",
            content=content if staged_content is None else staged_content,
        ),  # type: ignore[arg-type]
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
    )


class _EvilInput:
    handle_id = "bounded-looking"

    def __init__(self) -> None:
        self.callback_invoked = False

    def read_authorized_bytes(self) -> bytes:
        self.callback_invoked = True
        return b"a\n1\n"


@dataclass(slots=True)
class _SpyAuthority:
    method_name: str
    invocation_count: int = 0

    @property
    def handle_id(self) -> str:
        return "spy_authority"

    def read_authorized_bytes(self) -> bytes:
        self.invocation_count += 1
        return b"a\n1\n"

    def read(self) -> bytes:
        self.invocation_count += 1
        return b"a\n1\n"

    def read_bytes(self) -> bytes:
        self.invocation_count += 1
        return b"a\n1\n"

    def open(self) -> bytes:
        self.invocation_count += 1
        return b"a\n1\n"


class _SubclassedAuthority(DataLabProfilerStagedInput):  # type: ignore[misc]
    def read_authorized_bytes(self) -> bytes:
        raise AssertionError("subclass byte authority should not execute")


def test_validation_regression_original_duck_typed_authority_is_rejected_before_access() -> None:
    evil = _EvilInput()
    accepted_request = False
    profile_emitted = False
    result_emitted = False
    evidence_emitted = False
    event_emitted = False

    try:
        request = _request(b"a\n1\n", staged_input=evil)
        accepted_request = True
        outcome = DeterministicDataLabProfiler().profile(request)
        profile_emitted = outcome.profile is not None
        result_emitted = outcome.result.value is not None
        evidence_emitted = bool(outcome.evidence_refs)
        event_emitted = bool(outcome.events)
    except TypeError:
        pass

    assert accepted_request is False
    assert evil.callback_invoked is False
    assert profile_emitted is False
    assert result_emitted is False
    assert evidence_emitted is False
    assert event_emitted is False


@pytest.mark.parametrize(
    "staged_input",
    (
        _EvilInput(),
        _SpyAuthority("read_authorized_bytes"),
        _SpyAuthority("read"),
        _SpyAuthority("read_bytes"),
        _SpyAuthority("open"),
        lambda: b"a\n1\n",
        Path("dataset.csv"),
        "dataset.csv",
        "file:///tmp/dataset.csv",
        "http://example.test/dataset.csv",
        "https://example.test/dataset.csv",
        io.BytesIO(b"a\n1\n"),
        object(),
        _SubclassedAuthority(handle_id="subclassed_authority", content=b"a\n1\n"),
    ),
)
def test_validation_regression_invalid_authority_matrix_rejects_without_invocation(
    staged_input: object,
) -> None:
    with pytest.raises(TypeError, match="DataLabProfilerStagedInput"):
        _request(b"a\n1\n", staged_input=staged_input)

    if isinstance(staged_input, _SpyAuthority):
        assert staged_input.invocation_count == 0
    if isinstance(staged_input, _EvilInput):
        assert staged_input.callback_invoked is False


def test_validation_regression_controlled_escape_wrappers_do_not_execute(tmp_path: Path) -> None:
    external_file = tmp_path / "external.csv"
    external_file.write_bytes(b"a\n1\n")
    path_reader = _SpyAuthority("Path.read_bytes")
    open_reader = _SpyAuthority("builtins.open")
    network_reader = _SpyAuthority("network")
    subprocess_reader = _SpyAuthority("subprocess")

    for staged_input in (path_reader, open_reader, network_reader, subprocess_reader):
        with pytest.raises(TypeError, match="DataLabProfilerStagedInput"):
            _request(b"a\n1\n", staged_input=staged_input)
        assert staged_input.invocation_count == 0


def test_validation_regression_explicit_authority_handle_is_opaque_and_non_authoritative() -> None:
    content = b"a\n1\n"
    for bad_handle in ("../dataset", "/tmp/dataset", "file://dataset", "http://dataset"):
        with pytest.raises(ValueError, match="opaque"):
            DataLabProfilerStagedInput(handle_id=bad_handle, content=content)

    first = DataLabProfilerStagedInput(handle_id="first_dataset", content=b"a\n1\n")
    second = DataLabProfilerStagedInput(handle_id="second_dataset", content=b"a\n2\n")

    first_outcome = DeterministicDataLabProfiler().profile(_request(b"a\n1\n", staged_input=first))
    second_outcome = DeterministicDataLabProfiler().profile(
        _request(b"a\n2\n", staged_input=second)
    )

    assert first_outcome.status is DataLabProfilerOutcomeStatus.COMPLETED
    assert second_outcome.status is DataLabProfilerOutcomeStatus.COMPLETED
    assert first_outcome.profile is not None
    assert second_outcome.profile is not None
    assert first_outcome.profile.dataset_integrity_sha256 != (
        second_outcome.profile.dataset_integrity_sha256
    )


def test_validation_regression_m2_003_future_bridge_uses_already_authorized_bytes_only() -> None:
    content = b"\xef\xbb\xbfa,b\n1,true\n2,false\n"
    staged_bytes_from_m2_003 = bytes(content)
    authority = DataLabProfilerStagedInput(
        handle_id="m2_007_bridge",
        content=staged_bytes_from_m2_003,
    )

    outcome = DeterministicDataLabProfiler().profile(_request(content, staged_input=authority))

    assert outcome.status is DataLabProfilerOutcomeStatus.COMPLETED
    assert outcome.profile is not None
    assert outcome.profile.row_count == 2
    assert [column.name for column in outcome.profile.columns] == ["a", "b"]


def test_validation_regression_integrity_gate_permutations() -> None:
    content = b"a\n1\n"
    other = b"a\n2\n"

    success = DeterministicDataLabProfiler().profile(_request(content))
    assert success.status is DataLabProfilerOutcomeStatus.COMPLETED

    staged_mismatch = DeterministicDataLabProfiler().profile(
        _request(content, staged_content=other)
    )
    assert staged_mismatch.status is DataLabProfilerOutcomeStatus.FAILED
    assert staged_mismatch.profile is None
    assert staged_mismatch.result.value is None
    assert (
        str(staged_mismatch.result.errors[0].error_code)
        == DataLabProfilerErrorCode.DATASET_INTEGRITY_MISMATCH.value
    )

    with pytest.raises(ValueError, match="integrity must match"):
        _request(
            content,
            dataset_ref=_dataset_ref(content, sha256=hashlib.sha256(other).hexdigest()),
        )
    with pytest.raises(ValueError, match="integrity algorithm"):
        _request(
            content,
            dataset_ref=_dataset_ref(
                content,
                integrity_algorithm=IntegrityAlgorithm.SHA512,
                sha256="b" * 128,
            ),
        )


def test_validation_regression_profiler_semantics_profiles_counts_and_findings() -> None:
    outcome = DeterministicDataLabProfiler().profile(
        _request(b"integer,decimal,boolean,empty,mixed,text\n2,1.5,YES,,2,NaN\n3,2.5,no,,x,hello\n")
    )

    assert outcome.status is DataLabProfilerOutcomeStatus.COMPLETED
    assert outcome.profile is not None
    profile = outcome.profile
    assert profile.row_count == 2
    assert profile.column_count == 6
    assert [column.name for column in profile.columns] == [
        "integer",
        "decimal",
        "boolean",
        "empty",
        "mixed",
        "text",
    ]
    by_name = {column.name: column for column in profile.columns}
    assert by_name["integer"].inferred_type is DatasetPrimitiveType.INTEGER
    assert by_name["decimal"].inferred_type is DatasetPrimitiveType.DECIMAL
    assert by_name["boolean"].inferred_type is DatasetPrimitiveType.BOOLEAN
    assert by_name["empty"].inferred_type is DatasetPrimitiveType.EMPTY
    assert by_name["mixed"].inferred_type is DatasetPrimitiveType.MIXED
    assert by_name["text"].inferred_type is DatasetPrimitiveType.STRING
    for column in profile.columns:
        assert column.missing_count + column.non_missing_count == profile.row_count

    assert {warning.warning_code for warning in profile.warnings} == {
        "empty_column",
        "high_missingness",
        "mixed_types",
    }
    assert {finding.finding_key for finding in outcome.findings} == {
        "empty_column_3",
        "high_missingness_3",
        "mixed_types_4",
    }


def test_validation_regression_result_evidence_events_and_determinism() -> None:
    content = b"name,amount\nalice,1\nbob,2\n"
    request = _request(content)
    profiler = DeterministicDataLabProfiler()

    first = profiler.profile(request)
    second = profiler.profile(request)

    assert first.to_json_compatible() == second.to_json_compatible()
    assert first.result.status is ResultStatus.SUCCESS
    assert first.result.value is not None
    assert first.result.value.profile == first.profile
    assert first.result.value.dataset_ref == request.dataset_ref
    assert first.result.value.dataset_integrity_sha256 == request.expected_sha256
    assert first.evidence_refs[0].subject_ref.kind is ReferenceKind.WORK
    assert first.evidence_refs[0].artifact_refs == (request.dataset_ref.artifact_id,)
    assert [str(event.event_type) for event in first.events] == [
        "datalab.profiler.started",
        "datalab.profiler.completed",
    ]
    assert all(event.subject_ref == request.work_ref for event in first.events)


def test_validation_regression_safe_errors_do_not_reflect_authority_or_data() -> None:
    secret_value = "api" + "_key" + "=" + "super-secret-value"
    outcome = DeterministicDataLabProfiler().profile(
        _request(f"name\n{secret_value},extra\n".encode())
    )
    serialized = json.dumps(outcome.to_json_compatible(), sort_keys=True)

    assert outcome.status is DataLabProfilerOutcomeStatus.FAILED
    assert secret_value not in serialized
    assert "authorized_dataset" not in serialized
    assert "curios-datalab-staged:" not in serialized

    with pytest.raises(TypeError) as exc_info:
        _request(b"a\n1\n", staged_input=_EvilInput())
    assert "EvilInput" not in str(exc_info.value)
    assert "read_authorized_bytes" not in str(exc_info.value)


def test_validation_regression_resource_bound_and_no_m2_007_orchestration() -> None:
    oversized = b"a\n" + b"1" * DATALAB_MAX_UPLOAD_BYTES + b"\n"
    outcome = DeterministicDataLabProfiler().profile(_request(oversized))

    assert outcome.status is DataLabProfilerOutcomeStatus.FAILED
    assert outcome.result.errors[0].category is ErrorCategory.VALIDATION
    assert outcome.result.errors[0].details == {"limit": "upload"}

    source = Path(
        "packages/python/curios_runtime/src/curios_runtime/datalab_profiler.py"
    ).read_text(encoding="utf-8")
    assert "LocalDataLabDatasetStagingStore" not in source
    assert "BoundedM1DagRunner" not in source
    assert "cleanup_staged_bytes" not in source
    assert "read_staged_bytes" not in source
    assert "transition" not in source
