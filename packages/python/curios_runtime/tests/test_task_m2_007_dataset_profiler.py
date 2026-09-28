from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pytest
from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    DataLabAnalysisId,
    DataLabResultId,
    DataLabRunId,
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
    WorkItem,
)
from curios_runtime import (
    DATALAB_DATASET_MEDIA_TYPE,
    DATALAB_DATASET_PROFILE_WORK_TYPE,
    DataLabDatasetIntakeResult,
    DataLabDatasetProfilerCleanupStatus,
    DataLabDatasetProfilerError,
    DataLabDatasetProfilerErrorCode,
    DataLabDatasetProfilerOutcome,
    DataLabDatasetProfilerRequest,
    DataLabDatasetProfilerStatus,
    DataLabProfilerOutcome,
    DataLabProfilerOutcomeStatus,
    DataLabProfilerRequest,
    DataLabProfilerStagedInput,
    DeterministicDataLabProfiler,
    InProcessDataLabDatasetProfiler,
    LocalDataLabDatasetStagingStore,
    datalab_staged_locator_for_artifact_id,
)

UTC_NOW = UtcTimestamp.parse("2026-09-28T10:00:00Z")
ARTIFACT_ID = ArtifactId("art_0123456789ABCDEFGHJKMNPQRS")
ARTIFACT_ID_B = ArtifactId("art_1123456789ABCDEFGHJKMNPQRS")


class _CountingProfiler(DeterministicDataLabProfiler):
    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[object] = []

    def profile(self, request: object) -> DataLabProfilerOutcome:  # type: ignore[override]
        self.calls += 1
        self.requests.append(request)
        return super().profile(request)  # type: ignore[arg-type]


class _ExplodingAuthority:
    handle_id = "looks_bounded"

    def __init__(self) -> None:
        self.callback_invoked = False

    def read_authorized_bytes(self) -> bytes:
        self.callback_invoked = True
        return b"name\nsecret-token=do-not-print\n"


class _SpyStagingStore(LocalDataLabDatasetStagingStore):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.read_count = 0
        self.cleanup_count = 0

    def read_staged_bytes(self, locator: str) -> bytes:
        self.read_count += 1
        return super().read_staged_bytes(locator)

    def cleanup_staged_bytes(self, locator: str) -> None:
        self.cleanup_count += 1
        return super().cleanup_staged_bytes(locator)


def _producer_ref() -> ObjectReference:
    return ObjectReference.from_id(ProjectId("prj_0123456789ABCDEFGHJKMNPQRS"))


def _store(tmp_path: Path) -> LocalDataLabDatasetStagingStore:
    return LocalDataLabDatasetStagingStore(tmp_path / "stage")


def _spy_store(tmp_path: Path) -> _SpyStagingStore:
    return _SpyStagingStore(tmp_path / "stage")


def _accept(
    store: LocalDataLabDatasetStagingStore,
    content: bytes,
    *,
    artifact_id: ArtifactId = ARTIFACT_ID,
) -> DataLabDatasetIntakeResult:
    return store.accept_dataset(
        content=content,
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        client_filename="dataset.csv",
        producer_ref=_producer_ref(),
        artifact_id=artifact_id,
        created_at=UTC_NOW,
    )


def _hybrid_dataset(
    source: DataLabDatasetIntakeResult,
    *,
    artifact_id: ArtifactId,
    locator: str,
    digest: str | None = None,
) -> DataLabDatasetIntakeResult:
    selected_digest = digest or source.dataset_integrity_sha256
    return DataLabDatasetIntakeResult(
        artifact_ref=ArtifactReference(
            artifact_id=artifact_id,
            kind=ArtifactKind.DATASET,
            locator=locator,
            media_type=DATALAB_DATASET_MEDIA_TYPE,
            integrity=IntegrityDescriptor(
                algorithm=IntegrityAlgorithm.SHA256,
                value=selected_digest,
            ),
            producer_ref=_producer_ref(),
            created_at=UTC_NOW,
        ),
        normalized_filename="forged.csv",
        size_bytes=source.size_bytes,
        data_row_count=source.data_row_count,
        column_count=source.column_count,
        dataset_integrity_sha256=selected_digest,
    )


def _work(*, work_type: str = DATALAB_DATASET_PROFILE_WORK_TYPE) -> WorkItem:
    return WorkItem(
        work_id=WorkId("wrk_0123456789ABCDEFGHJKMNPQRS"),
        work_type=work_type,
        title="Profile staged dataset",
        objective="Create bounded deterministic dataset profile.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
    )


def _request(
    dataset: DataLabDatasetIntakeResult,
    *,
    work: WorkItem | None = None,
    cleanup_staged_bytes: bool = True,
) -> DataLabDatasetProfilerRequest:
    selected_work = work or _work()
    return DataLabDatasetProfilerRequest(
        dataset=dataset,
        work=selected_work,
        run_id=DataLabRunId("dlr_0123456789ABCDEFGHJKMNPQRS"),
        analysis_id=DataLabAnalysisId("dla_0123456789ABCDEFGHJKMNPQRS"),
        result_id=DataLabResultId("dlt_0123456789ABCDEFGHJKMNPQRS"),
        producer_ref=_producer_ref(),
        evidence_id=EvidenceId("evd_0123456789ABCDEFGHJKMNPQRS"),
        started_event_id=EventId("evt_0123456789ABCDEFGHJKMNPQRS"),
        completed_event_id=EventId("evt_1123456789ABCDEFGHJKMNPQRS"),
        occurred_at=UTC_NOW,
        observability_context=ObservabilityContext(work_id=selected_work.work_id),
        cleanup_staged_bytes=cleanup_staged_bytes,
    )


def test_profiles_m2_003_staged_dataset_through_m2_006_once_and_cleans(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    dataset = _accept(store, b"name,amount\nalice,2\nbob,3\n")
    profiler = _CountingProfiler()

    outcome = InProcessDataLabDatasetProfiler(
        staging_store=store,
        profiler=profiler,
    ).profile(_request(dataset))

    assert profiler.calls == 1
    assert outcome.status is DataLabDatasetProfilerStatus.COMPLETED
    assert outcome.cleanup_status is DataLabDatasetProfilerCleanupStatus.CLEANED
    assert outcome.profiler_outcome is not None
    assert outcome.profiler_outcome.status is DataLabProfilerOutcomeStatus.COMPLETED
    assert outcome.profiler_outcome.result.status is ResultStatus.SUCCESS
    assert outcome.profiler_outcome.profile is not None
    assert outcome.profiler_outcome.profile.dataset_ref == dataset.artifact_ref
    assert (
        outcome.profiler_outcome.profile.dataset_integrity_sha256
        == hashlib.sha256(b"name,amount\nalice,2\nbob,3\n").hexdigest()
    )
    assert [column.name for column in outcome.profiler_outcome.profile.columns] == [
        "name",
        "amount",
    ]
    assert outcome.profiler_outcome.evidence_refs[0].subject_ref.kind is ReferenceKind.WORK
    assert [str(event.event_type) for event in outcome.profiler_outcome.events] == [
        "datalab.profiler.started",
        "datalab.profiler.completed",
    ]


def test_bridge_uses_explicit_profiler_staged_input_and_preserves_sha(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    content = b"\xef\xbb\xbfname\nalice\n"
    dataset = _accept(store, content)
    profiler = _CountingProfiler()

    outcome = InProcessDataLabDatasetProfiler(
        staging_store=store,
        profiler=profiler,
    ).profile(_request(dataset))

    assert outcome.status is DataLabDatasetProfilerStatus.COMPLETED
    assert profiler.calls == 1
    profiler_request = profiler.requests[0]
    assert isinstance(profiler_request, DataLabProfilerRequest)
    assert profiler_request.staged_input.__class__ is DataLabProfilerStagedInput
    assert profiler_request.expected_sha256 == hashlib.sha256(content).hexdigest()


def test_repeated_execution_is_deterministic_when_cleanup_is_not_requested(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    dataset = _accept(store, b"flag,value\ntrue,1.5\nfalse,2.5\n")
    service = InProcessDataLabDatasetProfiler(staging_store=store)
    request = _request(dataset, cleanup_staged_bytes=False)

    first = service.profile(request)
    second = service.profile(request)

    assert first.cleanup_status is DataLabDatasetProfilerCleanupStatus.SKIPPED
    assert second.cleanup_status is DataLabDatasetProfilerCleanupStatus.SKIPPED
    assert first.profiler_outcome is not None
    assert second.profiler_outcome is not None
    assert json.loads(json.dumps(first.profiler_outcome.to_json_compatible(), sort_keys=True)) == (
        json.loads(json.dumps(second.profiler_outcome.to_json_compatible(), sort_keys=True))
    )


def test_cleanup_prevents_replay_and_does_not_touch_other_staged_datasets(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    first = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_ID)
    second = _accept(store, b"name\nbob\n", artifact_id=ARTIFACT_ID_B)
    service = InProcessDataLabDatasetProfiler(staging_store=store)

    first_outcome = service.profile(_request(first))
    replay_outcome = service.profile(_request(first))

    assert first_outcome.status is DataLabDatasetProfilerStatus.COMPLETED
    assert replay_outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert replay_outcome.error_code is DataLabDatasetProfilerErrorCode.DATASET_UNAVAILABLE
    assert store.read_staged_bytes(second.staged_locator) == b"name\nbob\n"


def test_foreign_staging_store_fails_before_profiler_invocation(tmp_path: Path) -> None:
    dataset = _accept(_store(tmp_path / "a"), b"name\nalice\n")
    profiler = _CountingProfiler()

    outcome = InProcessDataLabDatasetProfiler(
        staging_store=_store(tmp_path / "b"),
        profiler=profiler,
    ).profile(_request(dataset))

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert outcome.cleanup_status is DataLabDatasetProfilerCleanupStatus.NOT_ATTEMPTED
    assert outcome.error_code is DataLabDatasetProfilerErrorCode.DATASET_UNAVAILABLE
    assert profiler.calls == 0
    assert outcome.events == ()
    assert outcome.evidence_refs == ()


def test_staged_integrity_mismatch_fails_boundedly_before_profiler_success(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    dataset = _accept(store, b"name\nalice\n")
    staged_path = tmp_path / "stage" / f"{ARTIFACT_ID}.csv"
    staged_path.write_bytes(b"name\nmallory\n")
    profiler = _CountingProfiler()

    outcome = InProcessDataLabDatasetProfiler(
        staging_store=store,
        profiler=profiler,
    ).profile(_request(dataset))

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert outcome.cleanup_status is DataLabDatasetProfilerCleanupStatus.CLEANED
    assert outcome.error_code is DataLabDatasetProfilerErrorCode.DATASET_INTEGRITY_MISMATCH
    assert profiler.calls == 0
    assert not staged_path.exists()


def test_rejects_original_artifact_locator_hybrid_before_any_effect(tmp_path: Path) -> None:
    store = _spy_store(tmp_path)
    artifact_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_ID)
    forged_b = _hybrid_dataset(
        artifact_a,
        artifact_id=ARTIFACT_ID_B,
        locator=artifact_a.staged_locator,
    )
    profiler = _CountingProfiler()

    outcome = InProcessDataLabDatasetProfiler(
        staging_store=store,
        profiler=profiler,
    ).profile(_request(forged_b))

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    assert outcome.cleanup_status is DataLabDatasetProfilerCleanupStatus.NOT_ATTEMPTED
    assert store.read_count == 0
    assert store.cleanup_count == 0
    assert profiler.calls == 0
    assert outcome.profiler_outcome is None
    assert outcome.profile is None
    assert outcome.events == ()
    assert outcome.evidence_refs == ()
    assert store.read_staged_bytes(artifact_a.staged_locator) == b"name\nalice\n"


def test_artifact_locator_matrix_preserves_identity_and_sha_second_defense(
    tmp_path: Path,
) -> None:
    store = _spy_store(tmp_path)
    artifact_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_ID)
    artifact_b = _accept(store, b"name\nbob\n", artifact_id=ARTIFACT_ID_B)
    service = InProcessDataLabDatasetProfiler(staging_store=store)

    valid = service.profile(_request(artifact_a, cleanup_staged_bytes=False))
    assert valid.status is DataLabDatasetProfilerStatus.COMPLETED

    b_identity_a_locator = _hybrid_dataset(
        artifact_a,
        artifact_id=ARTIFACT_ID_B,
        locator=artifact_a.staged_locator,
    )
    b_identity_a_locator_outcome = service.profile(_request(b_identity_a_locator))
    assert b_identity_a_locator_outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert (
        b_identity_a_locator_outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    )

    a_identity_b_locator = _hybrid_dataset(
        artifact_b,
        artifact_id=ARTIFACT_ID,
        locator=artifact_b.staged_locator,
    )
    a_identity_b_locator_outcome = service.profile(_request(a_identity_b_locator))
    assert a_identity_b_locator_outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert (
        a_identity_b_locator_outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    )

    b_digest = artifact_b.dataset_integrity_sha256
    a_locator_b_digest = _hybrid_dataset(
        artifact_a,
        artifact_id=ARTIFACT_ID,
        locator=artifact_a.staged_locator,
        digest=b_digest,
    )
    sha_mismatch_outcome = service.profile(_request(a_locator_b_digest))
    assert sha_mismatch_outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert (
        sha_mismatch_outcome.error_code
        is DataLabDatasetProfilerErrorCode.DATASET_INTEGRITY_MISMATCH
    )

    unknown_with_foreign_locator = _hybrid_dataset(
        artifact_b,
        artifact_id=ArtifactId("art_2123456789ABCDEFGHJKMNPQRS"),
        locator=artifact_b.staged_locator,
    )
    unknown_outcome = service.profile(_request(unknown_with_foreign_locator))
    assert unknown_outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert unknown_outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST


@pytest.mark.parametrize(
    "locator",
    (
        "x-curios-datalab-staged:art_0123456789ABCDEFGHJKMNPQRS",
        "curios-datalab-staged:art_0123456789ABCDEFGHJKMNPQRS-extra",
        "prefix-art_0123456789ABCDEFGHJKMNPQRS",
        "curios-datalab-staged/art_0123456789ABCDEFGHJKMNPQRS",
        "curios-datalab-staged:art_0123456789ABCDEFGHJKMNPQRS:art_0123456789ABCDEFGHJKMNPQRS",
        "curios-datalab-staged:ART_0123456789ABCDEFGHJKMNPQRS",
        "curios-datalab-staged:%2Fart_0123456789ABCDEFGHJKMNPQRS",
    ),
)
def test_rejects_locator_lookalikes_before_read_cleanup_or_profile(
    tmp_path: Path,
    locator: str,
) -> None:
    store = _spy_store(tmp_path)
    artifact_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_ID)
    forged = _hybrid_dataset(artifact_a, artifact_id=ARTIFACT_ID, locator=locator)
    profiler = _CountingProfiler()

    outcome = InProcessDataLabDatasetProfiler(
        staging_store=store,
        profiler=profiler,
    ).profile(_request(forged))

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    assert store.read_count == 0
    assert store.cleanup_count == 0
    assert profiler.calls == 0


def test_invalid_hybrid_does_not_cleanup_either_staged_dataset(tmp_path: Path) -> None:
    store = _spy_store(tmp_path)
    artifact_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_ID)
    artifact_b = _accept(store, b"name\nbob\n", artifact_id=ARTIFACT_ID_B)
    forged = _hybrid_dataset(
        artifact_a,
        artifact_id=ARTIFACT_ID_B,
        locator=artifact_a.staged_locator,
    )

    outcome = InProcessDataLabDatasetProfiler(staging_store=store).profile(_request(forged))

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    assert store.cleanup_count == 0
    assert store.read_count == 0
    assert store.read_staged_bytes(artifact_a.staged_locator) == b"name\nalice\n"
    assert store.read_staged_bytes(artifact_b.staged_locator) == b"name\nbob\n"


def test_canonical_locator_helper_matches_m2_003_generated_locator(tmp_path: Path) -> None:
    store = _store(tmp_path)
    artifact_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_ID)

    assert artifact_a.staged_locator == datalab_staged_locator_for_artifact_id(ARTIFACT_ID)


def test_wrong_work_type_rejected_before_byte_access(tmp_path: Path) -> None:
    store = _store(tmp_path)
    dataset = _accept(store, b"name\nalice\n")

    with pytest.raises(DataLabDatasetProfilerError) as exc_info:
        _request(dataset, work=_work(work_type="inspect_current_state"))

    assert exc_info.value.code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    assert store.read_staged_bytes(dataset.staged_locator) == b"name\nalice\n"


@pytest.mark.parametrize(
    "invalid_dataset",
    (
        "curios-datalab-staged:art_0123456789ABCDEFGHJKMNPQRS",
        Path("dataset.csv"),
        io.BytesIO(b"name\nalice\n"),
        lambda: b"name\nalice\n",
        object(),
    ),
)
def test_bridge_rejects_arbitrary_bytes_paths_files_and_callbacks_before_access(
    invalid_dataset: object,
) -> None:
    with pytest.raises(TypeError, match="DataLabDatasetIntakeResult"):
        DataLabDatasetProfilerRequest(
            dataset=invalid_dataset,  # type: ignore[arg-type]
            work=_work(),
            run_id=DataLabRunId("dlr_0123456789ABCDEFGHJKMNPQRS"),
            analysis_id=DataLabAnalysisId("dla_0123456789ABCDEFGHJKMNPQRS"),
            result_id=DataLabResultId("dlt_0123456789ABCDEFGHJKMNPQRS"),
            producer_ref=_producer_ref(),
            evidence_id=EvidenceId("evd_0123456789ABCDEFGHJKMNPQRS"),
            started_event_id=EventId("evt_0123456789ABCDEFGHJKMNPQRS"),
            completed_event_id=EventId("evt_1123456789ABCDEFGHJKMNPQRS"),
            occurred_at=UTC_NOW,
            observability_context=ObservabilityContext(),
        )


def test_duck_typed_callback_authority_is_not_invoked_by_bridge() -> None:
    evil = _ExplodingAuthority()

    with pytest.raises(TypeError, match="DataLabDatasetIntakeResult"):
        DataLabDatasetProfilerRequest(
            dataset=evil,  # type: ignore[arg-type]
            work=_work(),
            run_id=DataLabRunId("dlr_0123456789ABCDEFGHJKMNPQRS"),
            analysis_id=DataLabAnalysisId("dla_0123456789ABCDEFGHJKMNPQRS"),
            result_id=DataLabResultId("dlt_0123456789ABCDEFGHJKMNPQRS"),
            producer_ref=_producer_ref(),
            evidence_id=EvidenceId("evd_0123456789ABCDEFGHJKMNPQRS"),
            started_event_id=EventId("evt_0123456789ABCDEFGHJKMNPQRS"),
            completed_event_id=EventId("evt_1123456789ABCDEFGHJKMNPQRS"),
            occurred_at=UTC_NOW,
            observability_context=ObservabilityContext(),
        )

    assert evil.callback_invoked is False


def test_safe_errors_do_not_echo_secret_values_paths_or_locators(tmp_path: Path) -> None:
    store = _store(tmp_path)
    dataset = _accept(store, b"name\nsecret-token=do-not-print\n")
    store.cleanup_staged_bytes(dataset.staged_locator)

    outcome = InProcessDataLabDatasetProfiler(staging_store=store).profile(_request(dataset))
    error = DataLabDatasetProfilerError(outcome.error_code)  # type: ignore[arg-type]
    rendered = str(error.to_json_compatible())

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert "secret-token" not in rendered
    assert str(tmp_path) not in rendered
    assert dataset.staged_locator not in rendered


def test_outcome_requires_profile_for_completed_status() -> None:
    with pytest.raises(ValueError, match="require a profiler outcome"):
        DataLabDatasetProfilerOutcome(
            status=DataLabDatasetProfilerStatus.COMPLETED,
            cleanup_status=DataLabDatasetProfilerCleanupStatus.CLEANED,
        )
