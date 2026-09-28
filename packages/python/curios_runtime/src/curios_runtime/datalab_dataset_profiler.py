"""In-process M2 DataLab dataset profiler bridge."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from curios_contracts import (
    DataLabAnalysisId,
    DataLabResultId,
    DataLabRunId,
    EventId,
    EvidenceId,
    ObjectReference,
    ObservabilityContext,
    UtcTimestamp,
    WorkItem,
)

from curios_runtime.datalab_dataset_intake import (
    DataLabDatasetIntakeError,
    DataLabDatasetIntakeErrorCode,
    DataLabDatasetIntakeResult,
    LocalDataLabDatasetStagingStore,
)
from curios_runtime.datalab_profiler import (
    DataLabProfilerOutcome,
    DataLabProfilerOutcomeStatus,
    DataLabProfilerRequest,
    DataLabProfilerResourceBounds,
    DataLabProfilerStagedInput,
    DeterministicDataLabProfiler,
)

DATALAB_DATASET_PROFILE_WORK_TYPE: Final = "dataset_profile"


class DataLabDatasetProfilerStatus(StrEnum):
    """Bounded M2-007 bridge outcome classes."""

    COMPLETED = "completed"
    FAILED = "failed"


class DataLabDatasetProfilerCleanupStatus(StrEnum):
    """Bounded cleanup state for an M2-007 profiler execution."""

    CLEANED = "cleaned"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"
    SKIPPED = "skipped"


class DataLabDatasetProfilerErrorCode(StrEnum):
    """Bounded M2-007 bridge failure codes."""

    INVALID_REQUEST = "DATALAB_DATASET_PROFILER_INVALID_REQUEST"
    DATASET_UNAVAILABLE = "DATALAB_DATASET_PROFILER_DATASET_UNAVAILABLE"
    DATASET_INTEGRITY_MISMATCH = "DATALAB_DATASET_PROFILER_INTEGRITY_MISMATCH"
    PROFILER_FAILURE = "DATALAB_DATASET_PROFILER_FAILURE"
    CLEANUP_FAILURE = "DATALAB_DATASET_PROFILER_CLEANUP_FAILURE"


_ERROR_MESSAGES: Final[dict[DataLabDatasetProfilerErrorCode, str]] = {
    DataLabDatasetProfilerErrorCode.INVALID_REQUEST: "invalid dataset profiler request",
    DataLabDatasetProfilerErrorCode.DATASET_UNAVAILABLE: "dataset unavailable",
    DataLabDatasetProfilerErrorCode.DATASET_INTEGRITY_MISMATCH: "dataset integrity mismatch",
    DataLabDatasetProfilerErrorCode.PROFILER_FAILURE: "bounded profiler failure",
    DataLabDatasetProfilerErrorCode.CLEANUP_FAILURE: "bounded cleanup failure",
}


class DataLabDatasetProfilerError(Exception):
    """Bounded bridge error that does not echo staged bytes, paths, or locators."""

    def __init__(self, code: DataLabDatasetProfilerErrorCode) -> None:
        self.code = DataLabDatasetProfilerErrorCode(code)
        super().__init__(_ERROR_MESSAGES[self.code])

    def to_json_compatible(self) -> dict[str, object]:
        """Return bounded JSON-compatible error details."""

        return {"code": self.code.value, "message": _ERROR_MESSAGES[self.code]}


@dataclass(frozen=True, slots=True)
class DataLabDatasetProfilerRequest:
    """Bridge request from an accepted staged dataset to the deterministic profiler."""

    dataset: DataLabDatasetIntakeResult
    work: WorkItem
    run_id: DataLabRunId
    analysis_id: DataLabAnalysisId
    result_id: DataLabResultId
    producer_ref: ObjectReference
    evidence_id: EvidenceId
    started_event_id: EventId
    completed_event_id: EventId
    occurred_at: UtcTimestamp
    observability_context: ObservabilityContext
    resource_bounds: DataLabProfilerResourceBounds = field(
        default_factory=DataLabProfilerResourceBounds
    )
    constraints: tuple[tuple[str, str], ...] = ()
    cleanup_staged_bytes: bool = True

    def __post_init__(self) -> None:
        _require_type(self.dataset, DataLabDatasetIntakeResult, "dataset")
        _require_type(self.work, WorkItem, "work")
        if self.work.work_type != DATALAB_DATASET_PROFILE_WORK_TYPE:
            raise DataLabDatasetProfilerError(DataLabDatasetProfilerErrorCode.INVALID_REQUEST)
        _require_type(self.run_id, DataLabRunId, "run_id")
        _require_type(self.analysis_id, DataLabAnalysisId, "analysis_id")
        _require_type(self.result_id, DataLabResultId, "result_id")
        _require_type(self.producer_ref, ObjectReference, "producer_ref")
        _require_type(self.evidence_id, EvidenceId, "evidence_id")
        _require_type(self.started_event_id, EventId, "started_event_id")
        _require_type(self.completed_event_id, EventId, "completed_event_id")
        object.__setattr__(self, "occurred_at", UtcTimestamp(self.occurred_at))
        _require_type(
            self.observability_context,
            ObservabilityContext,
            "observability_context",
        )
        _require_type(self.resource_bounds, DataLabProfilerResourceBounds, "resource_bounds")
        object.__setattr__(self, "constraints", _normalize_constraints(self.constraints))
        if not isinstance(self.cleanup_staged_bytes, bool):
            msg = "cleanup_staged_bytes must be a bool"
            raise TypeError(msg)
        integrity = self.dataset.artifact_ref.integrity
        if integrity is None or integrity.value != self.dataset.dataset_integrity_sha256:
            raise DataLabDatasetProfilerError(
                DataLabDatasetProfilerErrorCode.DATASET_INTEGRITY_MISMATCH
            )


@dataclass(frozen=True, slots=True)
class DataLabDatasetProfilerOutcome:
    """M2-007 bridge outcome that propagates the canonical M2-006 profiler output."""

    status: DataLabDatasetProfilerStatus
    cleanup_status: DataLabDatasetProfilerCleanupStatus
    profiler_outcome: DataLabProfilerOutcome | None = None
    error_code: DataLabDatasetProfilerErrorCode | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", DataLabDatasetProfilerStatus(self.status))
        object.__setattr__(
            self,
            "cleanup_status",
            DataLabDatasetProfilerCleanupStatus(self.cleanup_status),
        )
        if self.profiler_outcome is not None:
            _require_type(self.profiler_outcome, DataLabProfilerOutcome, "profiler_outcome")
        if self.error_code is not None:
            object.__setattr__(
                self,
                "error_code",
                DataLabDatasetProfilerErrorCode(self.error_code),
            )
        if self.status is DataLabDatasetProfilerStatus.COMPLETED:
            if self.profiler_outcome is None:
                msg = "completed dataset profiler outcomes require a profiler outcome"
                raise ValueError(msg)
            if self.profiler_outcome.status is not DataLabProfilerOutcomeStatus.COMPLETED:
                msg = "completed dataset profiler outcomes require completed profiler output"
                raise ValueError(msg)
        elif self.profiler_outcome is None and self.error_code is None:
            msg = "failed dataset profiler outcomes require an error code or profiler outcome"
            raise ValueError(msg)

    @property
    def profile(self) -> object | None:
        """Return the propagated DatasetProfile, if profiling completed."""

        if self.profiler_outcome is None:
            return None
        return self.profiler_outcome.profile

    @property
    def events(self) -> tuple[object, ...]:
        """Return propagated profiler events."""

        if self.profiler_outcome is None:
            return ()
        return self.profiler_outcome.events

    @property
    def evidence_refs(self) -> tuple[object, ...]:
        """Return propagated profiler evidence references."""

        if self.profiler_outcome is None:
            return ()
        return self.profiler_outcome.evidence_refs


class InProcessDataLabDatasetProfiler:
    """Bounded bridge from M2-003 staged datasets into the M2-006 profiler seam."""

    def __init__(
        self,
        *,
        staging_store: LocalDataLabDatasetStagingStore,
        profiler: DeterministicDataLabProfiler | None = None,
    ) -> None:
        _require_type(staging_store, LocalDataLabDatasetStagingStore, "staging_store")
        self._staging_store = staging_store
        self._profiler = profiler or DeterministicDataLabProfiler()
        if not isinstance(self._profiler, DeterministicDataLabProfiler):
            msg = "profiler must be a DeterministicDataLabProfiler"
            raise TypeError(msg)

    def profile(self, request: DataLabDatasetProfilerRequest) -> DataLabDatasetProfilerOutcome:
        """Read one authorized staged dataset, profile it once, and clean it up if requested."""

        _require_type(request, DataLabDatasetProfilerRequest, "request")
        content = self._read_authorized_staged_bytes(request)
        if content is None:
            return DataLabDatasetProfilerOutcome(
                status=DataLabDatasetProfilerStatus.FAILED,
                cleanup_status=DataLabDatasetProfilerCleanupStatus.NOT_ATTEMPTED,
                error_code=DataLabDatasetProfilerErrorCode.DATASET_UNAVAILABLE,
            )

        if hashlib.sha256(content).hexdigest() != request.dataset.dataset_integrity_sha256:
            cleanup_status, cleanup_error = self._cleanup(request)
            return DataLabDatasetProfilerOutcome(
                status=DataLabDatasetProfilerStatus.FAILED,
                cleanup_status=cleanup_status,
                error_code=cleanup_error
                or DataLabDatasetProfilerErrorCode.DATASET_INTEGRITY_MISMATCH,
            )

        profiler_request = DataLabProfilerRequest(
            dataset_ref=request.dataset.artifact_ref,
            staged_input=DataLabProfilerStagedInput(
                handle_id=_handle_id_for_dataset(request.dataset),
                content=content,
            ),
            expected_sha256=request.dataset.dataset_integrity_sha256,
            run_id=request.run_id,
            analysis_id=request.analysis_id,
            result_id=request.result_id,
            work_ref=ObjectReference.from_id(request.work.work_id),
            producer_ref=request.producer_ref,
            evidence_id=request.evidence_id,
            started_event_id=request.started_event_id,
            completed_event_id=request.completed_event_id,
            occurred_at=request.occurred_at,
            observability_context=request.observability_context,
            resource_bounds=request.resource_bounds,
            constraints=request.constraints,
        )

        try:
            profiler_outcome = self._profiler.profile(profiler_request)
        except Exception:
            cleanup_status, cleanup_error = self._cleanup(request)
            return DataLabDatasetProfilerOutcome(
                status=DataLabDatasetProfilerStatus.FAILED,
                cleanup_status=cleanup_status,
                error_code=cleanup_error or DataLabDatasetProfilerErrorCode.PROFILER_FAILURE,
            )

        cleanup_status, cleanup_error = self._cleanup(request)
        bridge_status = (
            DataLabDatasetProfilerStatus.COMPLETED
            if profiler_outcome.status is DataLabProfilerOutcomeStatus.COMPLETED
            else DataLabDatasetProfilerStatus.FAILED
        )
        return DataLabDatasetProfilerOutcome(
            status=bridge_status,
            cleanup_status=cleanup_status,
            profiler_outcome=profiler_outcome,
            error_code=cleanup_error,
        )

    def _read_authorized_staged_bytes(
        self,
        request: DataLabDatasetProfilerRequest,
    ) -> bytes | None:
        try:
            return self._staging_store.read_staged_bytes(request.dataset.staged_locator)
        except DataLabDatasetIntakeError as exc:
            if exc.code is DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE:
                return None
            return None

    def _cleanup(
        self,
        request: DataLabDatasetProfilerRequest,
    ) -> tuple[DataLabDatasetProfilerCleanupStatus, DataLabDatasetProfilerErrorCode | None]:
        if not request.cleanup_staged_bytes:
            return DataLabDatasetProfilerCleanupStatus.SKIPPED, None
        try:
            self._staging_store.cleanup_staged_bytes(request.dataset.staged_locator)
        except DataLabDatasetIntakeError:
            return (
                DataLabDatasetProfilerCleanupStatus.FAILED,
                DataLabDatasetProfilerErrorCode.CLEANUP_FAILURE,
            )
        return DataLabDatasetProfilerCleanupStatus.CLEANED, None


def _handle_id_for_dataset(dataset: DataLabDatasetIntakeResult) -> str:
    digest_prefix = dataset.dataset_integrity_sha256[:24]
    return f"dataset_{digest_prefix}"


def _normalize_constraints(constraints: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    if not isinstance(constraints, tuple):
        msg = "constraints must be a tuple"
        raise TypeError(msg)
    normalized: list[tuple[str, str]] = []
    for item in constraints:
        if not isinstance(item, tuple) or len(item) != 2:
            msg = "constraints must contain key/value pairs"
            raise TypeError(msg)
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            msg = "constraints must contain string key/value pairs"
            raise TypeError(msg)
        normalized.append((key, value))
    return tuple(sorted(normalized, key=lambda pair: pair[0]))


def _require_type[ValueT](value: object, expected_type: type[ValueT], field_name: str) -> None:
    if not isinstance(value, expected_type):
        msg = f"{field_name} must be {expected_type.__name__}"
        raise TypeError(msg)
