from __future__ import annotations

import pytest
from curios_contracts import (
    DataLabAnalysisId,
    DataLabResultId,
    DataLabRunId,
    EventId,
    ObjectReference,
    ProjectId,
    ProviderId,
    ReferenceKind,
    WorkId,
)


def test_object_reference_preserves_id_namespace_meaning() -> None:
    project_id = ProjectId.generate()

    reference = ObjectReference.from_id(project_id)

    assert reference.kind is ReferenceKind.PROJECT
    assert reference.ref_id == project_id
    assert ObjectReference.from_json_compatible(reference.to_json_compatible()) == reference


def test_object_reference_rejects_kind_id_mismatch() -> None:
    with pytest.raises(TypeError, match="provider references require ProviderId"):
        ObjectReference(kind=ReferenceKind.PROVIDER, ref_id=ProjectId.generate())


def test_object_reference_accepts_provider_references() -> None:
    provider_reference = ObjectReference.from_id(ProviderId.generate())

    assert provider_reference.kind is ReferenceKind.PROVIDER


def test_object_reference_accepts_event_references_for_causation() -> None:
    event_reference = ObjectReference.from_id(EventId.generate())

    assert event_reference.kind is ReferenceKind.EVENT


@pytest.mark.parametrize(
    ("id_type", "expected_kind"),
    (
        (DataLabAnalysisId, ReferenceKind.DATALAB_ANALYSIS),
        (DataLabRunId, ReferenceKind.DATALAB_RUN),
        (DataLabResultId, ReferenceKind.DATALAB_RESULT),
    ),
)
def test_object_reference_accepts_datalab_typed_ids(
    id_type: type[DataLabAnalysisId] | type[DataLabRunId] | type[DataLabResultId],
    expected_kind: ReferenceKind,
) -> None:
    typed_id = id_type.generate()

    reference = ObjectReference.from_id(typed_id)
    decoded = ObjectReference.from_json_compatible(reference.to_json_compatible())

    assert reference.kind is expected_kind
    assert reference.ref_id == typed_id
    assert type(reference.ref_id) is id_type
    assert decoded == reference
    assert decoded.kind is expected_kind
    assert type(decoded.ref_id) is id_type


@pytest.mark.parametrize(
    ("kind", "ref_id", "expected_error"),
    (
        (
            ReferenceKind.DATALAB_RUN,
            DataLabAnalysisId.generate(),
            "datalab_run references require DataLabRunId",
        ),
        (
            ReferenceKind.DATALAB_RESULT,
            DataLabAnalysisId.generate(),
            "datalab_result references require DataLabResultId",
        ),
        (
            ReferenceKind.DATALAB_ANALYSIS,
            DataLabRunId.generate(),
            "datalab_analysis references require DataLabAnalysisId",
        ),
        (
            ReferenceKind.DATALAB_RESULT,
            DataLabRunId.generate(),
            "datalab_result references require DataLabResultId",
        ),
        (
            ReferenceKind.DATALAB_ANALYSIS,
            DataLabResultId.generate(),
            "datalab_analysis references require DataLabAnalysisId",
        ),
        (
            ReferenceKind.DATALAB_RUN,
            DataLabResultId.generate(),
            "datalab_run references require DataLabRunId",
        ),
        (
            ReferenceKind.WORK,
            DataLabRunId.generate(),
            "work references require WorkId",
        ),
    ),
)
def test_object_reference_rejects_datalab_wrong_kind_combinations(
    kind: ReferenceKind,
    ref_id: DataLabAnalysisId | DataLabRunId | DataLabResultId,
    expected_error: str,
) -> None:
    with pytest.raises(TypeError, match=expected_error):
        ObjectReference(kind=kind, ref_id=ref_id)


def test_object_reference_rejects_malformed_datalab_json_payloads() -> None:
    with pytest.raises(ValueError, match="DataLabRunId must start"):
        ObjectReference.from_json_compatible(
            {"kind": "datalab_run", "ref_id": str(DataLabAnalysisId.generate())}
        )

    with pytest.raises(ValueError, match="DataLabResultId must end"):
        ObjectReference.from_json_compatible({"kind": "datalab_result", "ref_id": "dlt_not-a-ulid"})

    with pytest.raises(ValueError, match="'datalab_unknown' is not a valid ReferenceKind"):
        ObjectReference.from_json_compatible(
            {"kind": "datalab_unknown", "ref_id": str(DataLabRunId.generate())}
        )


def test_datalab_downstream_reference_vocabulary_is_complete_without_runtime_records() -> None:
    analysis_ref = ObjectReference.from_id(DataLabAnalysisId.generate())
    run_ref = ObjectReference.from_id(DataLabRunId.generate())
    result_ref = ObjectReference.from_id(DataLabResultId.generate())
    work_ref = ObjectReference.from_id(WorkId.generate())

    synthetic_relationships = {
        "analysis_ref": analysis_ref.to_json_compatible(),
        "run_ref": run_ref.to_json_compatible(),
        "result_ref": result_ref.to_json_compatible(),
        "work_ref": work_ref.to_json_compatible(),
    }

    assert synthetic_relationships["analysis_ref"]["kind"] == "datalab_analysis"
    assert synthetic_relationships["run_ref"]["kind"] == "datalab_run"
    assert synthetic_relationships["result_ref"]["kind"] == "datalab_result"
    assert synthetic_relationships["work_ref"]["kind"] == "work"
