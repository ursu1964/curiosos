from __future__ import annotations

import hashlib
import json
from pathlib import Path

import curios_runtime.datalab_dataset_profiler as bridge_module
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
    UtcTimestamp,
    WorkId,
    WorkItem,
)
from curios_runtime import (
    DATALAB_DATASET_MEDIA_TYPE,
    DataLabDatasetIntakeResult,
    DataLabDatasetProfilerCleanupStatus,
    DataLabDatasetProfilerErrorCode,
    DataLabDatasetProfilerRequest,
    DataLabDatasetProfilerStatus,
    DataLabProfilerOutcome,
    DataLabProfilerRequest,
    DeterministicDataLabProfiler,
    InProcessDataLabDatasetProfiler,
    LocalDataLabDatasetStagingStore,
    datalab_staged_locator_for_artifact_id,
)

UTC_NOW = UtcTimestamp.parse("2026-09-28T10:00:00Z")
ARTIFACT_A = ArtifactId("art_0123456789ABCDEFGHJKMNPQRS")
ARTIFACT_B = ArtifactId("art_1123456789ABCDEFGHJKMNPQRS")


class _SpyStore(LocalDataLabDatasetStagingStore):
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


class _SpyProfiler(DeterministicDataLabProfiler):
    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[DataLabProfilerRequest] = []

    def profile(self, request: DataLabProfilerRequest) -> DataLabProfilerOutcome:
        self.calls += 1
        self.requests.append(request)
        return super().profile(request)


class _EvilAuthority:
    handle_id = "bounded_looking"

    def __init__(self) -> None:
        self.invoked = False

    def read_authorized_bytes(self) -> bytes:
        self.invoked = True
        return b"name\napi_key=do-not-print\n"


def _producer_ref() -> ObjectReference:
    return ObjectReference.from_id(ProjectId("prj_0123456789ABCDEFGHJKMNPQRS"))


def _work(*, work_type: str = "dataset_profile") -> WorkItem:
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


def _accept(
    store: LocalDataLabDatasetStagingStore,
    content: bytes,
    *,
    artifact_id: ArtifactId,
) -> DataLabDatasetIntakeResult:
    return store.accept_dataset(
        content=content,
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        client_filename="dataset.csv",
        producer_ref=_producer_ref(),
        artifact_id=artifact_id,
        created_at=UTC_NOW,
    )


def _hybrid(
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


def test_original_hybrid_exploit_rejected_before_any_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _SpyStore(tmp_path / "stage")
    dataset_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_A)
    hybrid = _hybrid(dataset_a, artifact_id=ARTIFACT_B, locator=dataset_a.staged_locator)
    profiler = _SpyProfiler()
    hash_count = 0
    staged_input_count = 0

    real_sha256 = bridge_module.hashlib.sha256
    real_staged_input = bridge_module.DataLabProfilerStagedInput

    def counting_sha256(content: bytes = b"") -> object:
        nonlocal hash_count
        hash_count += 1
        return real_sha256(content)

    def counting_staged_input(*args: object, **kwargs: object) -> object:
        nonlocal staged_input_count
        staged_input_count += 1
        return real_staged_input(*args, **kwargs)

    monkeypatch.setattr(bridge_module.hashlib, "sha256", counting_sha256)
    monkeypatch.setattr(bridge_module, "DataLabProfilerStagedInput", counting_staged_input)

    outcome = InProcessDataLabDatasetProfiler(
        staging_store=store,
        profiler=profiler,
    ).profile(_request(hybrid))

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    assert outcome.profiler_outcome is None
    assert outcome.events == ()
    assert outcome.evidence_refs == ()
    assert store.read_count == 0
    assert store.cleanup_count == 0
    assert profiler.calls == 0
    assert hash_count == 0
    assert staged_input_count == 0
    assert store.read_staged_bytes(dataset_a.staged_locator) == b"name\nalice\n"


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
def test_correction1_rejects_noncanonical_locator_lookalikes(
    tmp_path: Path,
    locator: str,
) -> None:
    store = _SpyStore(tmp_path / "stage")
    dataset_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_A)
    forged = _hybrid(dataset_a, artifact_id=ARTIFACT_A, locator=locator)

    outcome = InProcessDataLabDatasetProfiler(staging_store=store).profile(_request(forged))

    assert outcome.status is DataLabDatasetProfilerStatus.FAILED
    assert outcome.error_code is DataLabDatasetProfilerErrorCode.INVALID_REQUEST
    assert store.read_count == 0
    assert store.cleanup_count == 0


def test_sha_second_defense_and_exact_byte_identity_are_preserved(tmp_path: Path) -> None:
    store = _SpyStore(tmp_path / "stage")
    content = b"\xef\xbb\xbfname,value\r\nalice,1\r\n"
    dataset_a = _accept(store, content, artifact_id=ARTIFACT_A)
    dataset_b = _accept(store, b"name,value\nbob,2\n", artifact_id=ARTIFACT_B)
    profiler = _SpyProfiler()

    valid = InProcessDataLabDatasetProfiler(staging_store=store, profiler=profiler).profile(
        _request(dataset_a, cleanup_staged_bytes=False)
    )

    assert valid.status is DataLabDatasetProfilerStatus.COMPLETED
    assert profiler.calls == 1
    assert profiler.requests[0].staged_input.read_authorized_bytes() == content
    assert profiler.requests[0].expected_sha256 == hashlib.sha256(content).hexdigest()

    wrong_digest = _hybrid(
        dataset_a,
        artifact_id=ARTIFACT_A,
        locator=dataset_a.staged_locator,
        digest=dataset_b.dataset_integrity_sha256,
    )
    mismatch = InProcessDataLabDatasetProfiler(staging_store=store).profile(_request(wrong_digest))
    assert mismatch.status is DataLabDatasetProfilerStatus.FAILED
    assert mismatch.error_code is DataLabDatasetProfilerErrorCode.DATASET_INTEGRITY_MISMATCH


def test_foreign_store_and_cleaned_locator_fail_without_fallback(tmp_path: Path) -> None:
    store_a = _SpyStore(tmp_path / "a")
    store_b = _SpyStore(tmp_path / "b")
    dataset_a = _accept(store_a, b"name\nalice\n", artifact_id=ARTIFACT_A)

    foreign = InProcessDataLabDatasetProfiler(staging_store=store_b).profile(_request(dataset_a))

    assert foreign.status is DataLabDatasetProfilerStatus.FAILED
    assert foreign.error_code is DataLabDatasetProfilerErrorCode.DATASET_UNAVAILABLE
    assert store_b.read_count == 1
    assert store_b.cleanup_count == 0

    store_a.cleanup_staged_bytes(dataset_a.staged_locator)
    cleaned = InProcessDataLabDatasetProfiler(staging_store=store_a).profile(_request(dataset_a))
    assert cleaned.status is DataLabDatasetProfilerStatus.FAILED
    assert cleaned.error_code is DataLabDatasetProfilerErrorCode.DATASET_UNAVAILABLE


def test_invalid_hybrid_cleanup_non_effect_and_valid_cleanup_replay_isolation(
    tmp_path: Path,
) -> None:
    store = _SpyStore(tmp_path / "stage")
    dataset_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_A)
    dataset_b = _accept(store, b"name\nbob\n", artifact_id=ARTIFACT_B)
    hybrid = _hybrid(dataset_a, artifact_id=ARTIFACT_B, locator=dataset_a.staged_locator)
    service = InProcessDataLabDatasetProfiler(staging_store=store)

    invalid = service.profile(_request(hybrid))

    assert invalid.status is DataLabDatasetProfilerStatus.FAILED
    assert invalid.cleanup_status is DataLabDatasetProfilerCleanupStatus.NOT_ATTEMPTED
    assert store.read_count == 0
    assert store.cleanup_count == 0
    assert store.read_staged_bytes(dataset_a.staged_locator) == b"name\nalice\n"
    assert store.read_staged_bytes(dataset_b.staged_locator) == b"name\nbob\n"

    valid_a = service.profile(_request(dataset_a))
    assert valid_a.status is DataLabDatasetProfilerStatus.COMPLETED
    replay_a = service.profile(_request(dataset_a))
    assert replay_a.status is DataLabDatasetProfilerStatus.FAILED
    assert store.read_staged_bytes(dataset_b.staged_locator) == b"name\nbob\n"


def test_sealed_authority_non_bypass_and_safe_errors(tmp_path: Path) -> None:
    evil = _EvilAuthority()
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
    assert evil.invoked is False

    store = _SpyStore(tmp_path / "stage")
    dataset = _accept(store, b"name\napi_key=do-not-print\n", artifact_id=ARTIFACT_A)
    store.cleanup_staged_bytes(dataset.staged_locator)
    outcome = InProcessDataLabDatasetProfiler(staging_store=store).profile(_request(dataset))
    rendered = json.dumps(
        {
            "error": outcome.error_code.value if outcome.error_code else None,
            "status": outcome.status.value,
        },
        sort_keys=True,
    )
    assert "api_key=do-not-print" not in rendered
    assert dataset.staged_locator not in rendered
    assert str(tmp_path) not in rendered


def test_output_provenance_determinism_and_no_m2_009_authority(tmp_path: Path) -> None:
    store = _SpyStore(tmp_path / "stage")
    dataset_a = _accept(store, b"name,value\nalice,1\n", artifact_id=ARTIFACT_A)
    dataset_b = _accept(store, b"name,value\nbob,2\n", artifact_id=ARTIFACT_B)
    service = InProcessDataLabDatasetProfiler(staging_store=store)
    request_a = _request(dataset_a, cleanup_staged_bytes=False)

    first = service.profile(request_a)
    second = service.profile(request_a)
    b_outcome = service.profile(_request(dataset_b, cleanup_staged_bytes=False))

    assert first.profiler_outcome is not None
    assert second.profiler_outcome is not None
    assert b_outcome.profiler_outcome is not None
    assert json.loads(json.dumps(first.profiler_outcome.to_json_compatible(), sort_keys=True)) == (
        json.loads(json.dumps(second.profiler_outcome.to_json_compatible(), sort_keys=True))
    )
    assert first.profiler_outcome.profile is not None
    assert b_outcome.profiler_outcome.profile is not None
    assert first.profiler_outcome.profile.dataset_ref.artifact_id == ARTIFACT_A
    assert b_outcome.profiler_outcome.profile.dataset_ref.artifact_id == ARTIFACT_B
    assert first.profiler_outcome.evidence_refs[0].subject_ref.ref_id == request_a.work.work_id

    source = Path("packages/python/curios_runtime/src/curios_runtime/datalab_dataset_profiler.py")
    text = source.read_text(encoding="utf-8")
    assert "BoundedM1DagRunner" not in text
    assert "capability" not in text.lower()
    assert "DataLabRunRecord" not in text
    assert "curios_persistence" not in text


def test_canonical_locator_helper_matches_intake_generation(tmp_path: Path) -> None:
    store = _SpyStore(tmp_path / "stage")
    dataset_a = _accept(store, b"name\nalice\n", artifact_id=ARTIFACT_A)

    assert dataset_a.staged_locator == datalab_staged_locator_for_artifact_id(ARTIFACT_A)
