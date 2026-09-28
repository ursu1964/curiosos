"""Deterministic M2 DataLab profiler seam."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Final, Protocol

from curios_contracts import (
    ArtifactKind,
    ArtifactReference,
    ContractError,
    DataLabAnalysisId,
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
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    EventEnvelope,
    EventId,
    EventType,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    IntegrityAlgorithm,
    ObjectReference,
    ObservabilityContext,
    ReferenceKind,
    Result,
    ResultStatus,
    SchemaVersion,
    UtcTimestamp,
    to_json_compatible,
)

from curios_runtime.datalab_dataset_intake import (
    DATALAB_DATASET_MEDIA_TYPE,
    DATALAB_MAX_CELL_BYTES,
    DATALAB_MAX_COLUMNS,
    DATALAB_MAX_DATA_ROWS,
    DATALAB_MAX_UPLOAD_BYTES,
)

DATALAB_PROFILER_TIMEOUT_SECONDS: Final = 5.0
DATALAB_PROFILER_MAX_EVENT_PAYLOAD_BYTES: Final = 16 * 1024
DATALAB_PROFILER_MAX_WARNINGS: Final = 100
DATALAB_PROFILER_MAX_FINDINGS: Final = 50
DATALAB_PROFILER_SCHEMA_VERSION: Final = SchemaVersion.parse("1.0.0")
DATALAB_PROFILER_STARTED_EVENT_TYPE: Final = EventType("datalab.profiler.started")
DATALAB_PROFILER_COMPLETED_EVENT_TYPE: Final = EventType("datalab.profiler.completed")
DATALAB_PROFILER_FAILED_EVENT_TYPE: Final = EventType("datalab.profiler.failed")
DATALAB_PROFILER_TIMEOUT_EVENT_TYPE: Final = EventType("datalab.profiler.timeout")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HANDLE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
_INTEGER_RE = re.compile(r"^[+-]?[0-9]+$")
_DECIMAL_RE = re.compile(r"^[+-]?(?:[0-9]+\.[0-9]+|[0-9]+\.|\.[0-9]+)$")
_BOOLEAN_VALUES = frozenset({"true", "false", "yes", "no", "1", "0"})
_NONFINITE_VALUES = frozenset({"nan", "+nan", "-nan", "infinity", "+infinity", "-infinity"})


class DataLabProfilerOutcomeStatus(StrEnum):
    """Frozen bounded profiler outcome classes."""

    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class DataLabProfilerErrorCode(StrEnum):
    """Bounded M2 profiler failure codes."""

    INVALID_REQUEST = "DATALAB_PROFILER_INVALID_REQUEST"
    DATASET_UNAVAILABLE = "DATALAB_PROFILER_DATASET_UNAVAILABLE"
    DATASET_INTEGRITY_MISMATCH = "DATALAB_PROFILER_DATASET_INTEGRITY_MISMATCH"
    MALFORMED_CSV = "DATALAB_PROFILER_MALFORMED_CSV"
    RESOURCE_LIMIT_EXCEEDED = "DATALAB_PROFILER_RESOURCE_LIMIT_EXCEEDED"
    PROFILER_TIMEOUT = "DATALAB_PROFILER_TIMEOUT"
    INTERNAL_FAILURE = "DATALAB_PROFILER_FAILURE"


class DataLabStagedInput(Protocol):
    """Bounded authority to bytes that were staged by a Curios-owned boundary."""

    @property
    def handle_id(self) -> str:
        """Return an opaque staged-input handle identifier, not a path."""

    def read_authorized_bytes(self) -> bytes:
        """Return authorized staged bytes for deterministic profiling."""


@dataclass(frozen=True, slots=True)
class InMemoryDataLabStagedInput:
    """Synthetic staged-input seam for contract tests and in-process composition."""

    handle_id: str
    content: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.handle_id, str) or _HANDLE_RE.fullmatch(self.handle_id) is None:
            msg = "handle_id must be a bounded opaque staged-input token"
            raise ValueError(msg)
        if not isinstance(self.content, bytes):
            msg = "content must be bytes"
            raise TypeError(msg)

    def read_authorized_bytes(self) -> bytes:
        """Return an immutable copy of the supplied staged bytes."""

        return bytes(self.content)


@dataclass(frozen=True, slots=True)
class DataLabProfilerResourceBounds:
    """Explicit frozen bounds for one deterministic profiler invocation."""

    timeout_seconds: float = DATALAB_PROFILER_TIMEOUT_SECONDS
    max_rows: int = DATALAB_MAX_DATA_ROWS
    max_columns: int = DATALAB_MAX_COLUMNS
    max_cell_bytes: int = DATALAB_MAX_CELL_BYTES
    max_upload_bytes: int = DATALAB_MAX_UPLOAD_BYTES
    max_warnings: int = DATALAB_PROFILER_MAX_WARNINGS
    max_findings: int = DATALAB_PROFILER_MAX_FINDINGS
    max_event_payload_bytes: int = DATALAB_PROFILER_MAX_EVENT_PAYLOAD_BYTES

    def __post_init__(self) -> None:
        _require_positive_float_at_most(
            self.timeout_seconds,
            "timeout_seconds",
            maximum=DATALAB_PROFILER_TIMEOUT_SECONDS,
        )
        _require_int_between(self.max_rows, "max_rows", minimum=1, maximum=DATALAB_MAX_DATA_ROWS)
        _require_int_between(
            self.max_columns,
            "max_columns",
            minimum=1,
            maximum=DATALAB_MAX_COLUMNS,
        )
        _require_int_between(
            self.max_cell_bytes,
            "max_cell_bytes",
            minimum=1,
            maximum=DATALAB_MAX_CELL_BYTES,
        )
        _require_int_between(
            self.max_upload_bytes,
            "max_upload_bytes",
            minimum=1,
            maximum=DATALAB_MAX_UPLOAD_BYTES,
        )
        _require_int_between(
            self.max_warnings,
            "max_warnings",
            minimum=0,
            maximum=DATALAB_PROFILER_MAX_WARNINGS,
        )
        _require_int_between(
            self.max_findings,
            "max_findings",
            minimum=0,
            maximum=DATALAB_PROFILER_MAX_FINDINGS,
        )
        _require_int_between(
            self.max_event_payload_bytes,
            "max_event_payload_bytes",
            minimum=1,
            maximum=DATALAB_PROFILER_MAX_EVENT_PAYLOAD_BYTES,
        )


@dataclass(frozen=True, slots=True)
class DataLabProfilerRequest:
    """Canonical profiler seam request for already-authorized staged dataset bytes."""

    dataset_ref: ArtifactReference
    staged_input: DataLabStagedInput
    expected_sha256: str
    run_id: DataLabRunId
    analysis_id: DataLabAnalysisId
    result_id: DataLabResultId
    work_ref: ObjectReference
    producer_ref: ObjectReference
    evidence_id: EvidenceId
    started_event_id: EventId
    completed_event_id: EventId
    occurred_at: UtcTimestamp
    observability_context: ObservabilityContext
    resource_bounds: DataLabProfilerResourceBounds = field(
        default_factory=DataLabProfilerResourceBounds
    )
    constraints: Mapping[str, str] | Sequence[tuple[str, str]] = ()

    def __post_init__(self) -> None:
        sha256 = _require_sha256(self.expected_sha256, "expected_sha256")
        _require_dataset_artifact(self.dataset_ref, sha256)
        object.__setattr__(self, "expected_sha256", sha256)
        _require_staged_input(self.staged_input)
        _require_type(self.run_id, DataLabRunId, "run_id")
        _require_type(self.analysis_id, DataLabAnalysisId, "analysis_id")
        _require_type(self.result_id, DataLabResultId, "result_id")
        _require_reference_kind(self.work_ref, ReferenceKind.WORK, "work_ref")
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
        _require_type(
            self.resource_bounds,
            DataLabProfilerResourceBounds,
            "resource_bounds",
        )
        object.__setattr__(self, "constraints", _normalize_constraints(self.constraints))


@dataclass(frozen=True, slots=True)
class DataLabProfilerOutcome:
    """Bounded profiler outcome containing result, events, evidence, and profile facts."""

    status: DataLabProfilerOutcomeStatus
    result: Result[DataLabAnalysisResult]
    events: tuple[EventEnvelope, ...]
    evidence_refs: tuple[EvidenceReference, ...]
    profile: DatasetProfile | None = None
    findings: tuple[DataLabFinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", DataLabProfilerOutcomeStatus(self.status))
        _require_type(self.result, Result, "result")
        events = tuple(self.events)
        for event in events:
            _require_type(event, EventEnvelope, "events item")
        object.__setattr__(self, "events", events)
        evidence_refs = tuple(self.evidence_refs)
        for evidence_ref in evidence_refs:
            _require_type(evidence_ref, EvidenceReference, "evidence_refs item")
        object.__setattr__(self, "evidence_refs", evidence_refs)
        if self.profile is not None:
            _require_type(self.profile, DatasetProfile, "profile")
        findings = tuple(self.findings)
        for finding in findings:
            _require_type(finding, DataLabFinding, "findings item")
        object.__setattr__(self, "findings", findings)
        if self.status is DataLabProfilerOutcomeStatus.COMPLETED:
            if self.result.status is not ResultStatus.SUCCESS or self.profile is None:
                msg = "completed profiler outcomes require successful result and profile"
                raise ValueError(msg)
        elif self.result.status is not ResultStatus.FAILURE:
            msg = "failed profiler outcomes require failure result"
            raise ValueError(msg)

    def to_json_compatible(self) -> dict[str, object]:
        """Return a canonical JSON-compatible profiler outcome."""

        return {
            "status": self.status.value,
            "result": to_json_compatible(self.result),
            "events": to_json_compatible(self.events),
            "evidence_refs": to_json_compatible(self.evidence_refs),
            "profile": to_json_compatible(self.profile),
            "findings": to_json_compatible(self.findings),
        }


class DeterministicDataLabProfiler:
    """Bounded in-process profiler over authorized staged CSV bytes."""

    def profile(self, request: DataLabProfilerRequest) -> DataLabProfilerOutcome:
        """Profile one authorized staged dataset request."""

        _require_type(request, DataLabProfilerRequest, "request")
        started = _event(
            request,
            event_id=request.started_event_id,
            event_type=DATALAB_PROFILER_STARTED_EVENT_TYPE,
            payload={
                "status": "started",
                "run_id": str(request.run_id),
                "work_id": str(request.work_ref.ref_id),
                "dataset_artifact_id": str(request.dataset_ref.artifact_id),
                "expected_sha256": request.expected_sha256,
            },
        )
        started_at = time.monotonic()

        if request.constraints:
            return _failure_outcome(
                request,
                started,
                DataLabProfilerOutcomeStatus.FAILED,
                DataLabProfilerErrorCode.INVALID_REQUEST,
                ErrorCategory.VALIDATION,
                "unsupported profiler constraint",
            )

        try:
            content = request.staged_input.read_authorized_bytes()
        except Exception:
            return _failure_outcome(
                request,
                started,
                DataLabProfilerOutcomeStatus.FAILED,
                DataLabProfilerErrorCode.DATASET_UNAVAILABLE,
                ErrorCategory.NOT_FOUND,
                "dataset unavailable",
            )
        if not isinstance(content, bytes):
            return _failure_outcome(
                request,
                started,
                DataLabProfilerOutcomeStatus.FAILED,
                DataLabProfilerErrorCode.DATASET_UNAVAILABLE,
                ErrorCategory.NOT_FOUND,
                "dataset unavailable",
            )
        if len(content) > request.resource_bounds.max_upload_bytes:
            return _failure_outcome(
                request,
                started,
                DataLabProfilerOutcomeStatus.FAILED,
                DataLabProfilerErrorCode.RESOURCE_LIMIT_EXCEEDED,
                ErrorCategory.VALIDATION,
                "resource limit exceeded",
                details={"limit": "upload"},
            )

        observed_sha256 = hashlib.sha256(content).hexdigest()
        if observed_sha256 != request.expected_sha256:
            return _failure_outcome(
                request,
                started,
                DataLabProfilerOutcomeStatus.FAILED,
                DataLabProfilerErrorCode.DATASET_INTEGRITY_MISMATCH,
                ErrorCategory.CONFLICT,
                "dataset integrity mismatch",
            )

        try:
            profile = _profile_csv_content(request, content, started_at=started_at)
        except _ProfilerTimeout:
            return _failure_outcome(
                request,
                started,
                DataLabProfilerOutcomeStatus.TIMED_OUT,
                DataLabProfilerErrorCode.PROFILER_TIMEOUT,
                ErrorCategory.TIMEOUT,
                "profiler timeout",
            )
        except _ProfilerFailure as exc:
            return _failure_outcome(
                request,
                started,
                DataLabProfilerOutcomeStatus.FAILED,
                exc.code,
                exc.category,
                exc.message,
                details=exc.details,
            )

        evidence = _evidence(request, summary="DataLab profiler produced a bounded profile.")
        findings = _findings_for_profile(request, profile, evidence)
        analysis_result = DataLabAnalysisResult(
            result_id=request.result_id,
            run_id=request.run_id,
            analysis_id=request.analysis_id,
            work_ref=request.work_ref,
            dataset_ref=request.dataset_ref,
            dataset_integrity_sha256=request.expected_sha256,
            profile=profile,
            findings=findings,
            warnings=profile.warnings,
            evidence_refs=(evidence,),
            created_at=request.occurred_at,
        )
        completed = _event(
            request,
            event_id=request.completed_event_id,
            event_type=DATALAB_PROFILER_COMPLETED_EVENT_TYPE,
            payload={
                "status": "completed",
                "run_id": str(request.run_id),
                "work_id": str(request.work_ref.ref_id),
                "result_id": str(request.result_id),
                "dataset_artifact_id": str(request.dataset_ref.artifact_id),
                "expected_sha256": request.expected_sha256,
                "row_count": profile.row_count,
                "column_count": profile.column_count,
                "warning_count": len(profile.warnings),
                "finding_count": len(analysis_result.findings),
            },
        )
        return DataLabProfilerOutcome(
            status=DataLabProfilerOutcomeStatus.COMPLETED,
            result=Result.success(analysis_result, evidence_refs=(evidence,)),
            events=(started, completed),
            evidence_refs=(evidence,),
            profile=profile,
            findings=analysis_result.findings,
        )


@dataclass(frozen=True, slots=True)
class _ColumnAccumulator:
    name: str
    index: int
    missing_count: int = 0
    values: tuple[str, ...] = ()
    classes: tuple[DatasetPrimitiveType, ...] = ()
    integers: tuple[int, ...] = ()
    decimals: tuple[Decimal, ...] = ()

    def add(self, value: str) -> _ColumnAccumulator:
        trimmed = value.strip()
        if trimmed == "":
            return _ColumnAccumulator(
                name=self.name,
                index=self.index,
                missing_count=self.missing_count + 1,
                values=self.values,
                classes=self.classes,
                integers=self.integers,
                decimals=self.decimals,
            )
        value_class = _classify_value(trimmed)
        return _ColumnAccumulator(
            name=self.name,
            index=self.index,
            missing_count=self.missing_count,
            values=(*self.values, trimmed),
            classes=(*self.classes, value_class),
            integers=(
                (*self.integers, int(trimmed))
                if value_class is DatasetPrimitiveType.INTEGER
                else self.integers
            ),
            decimals=(
                (*self.decimals, Decimal(trimmed))
                if value_class is DatasetPrimitiveType.DECIMAL
                else self.decimals
            ),
        )


class _ProfilerTimeout(Exception):
    pass


@dataclass(frozen=True, slots=True)
class _ProfilerFailure(Exception):
    code: DataLabProfilerErrorCode
    category: ErrorCategory
    message: str
    details: Mapping[str, object] | None = None


def _profile_csv_content(
    request: DataLabProfilerRequest,
    content: bytes,
    *,
    started_at: float,
) -> DatasetProfile:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
            {"reason": "encoding"},
        ) from exc

    reader = csv.reader(io.StringIO(text), delimiter=",", strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
            {"reason": "empty"},
        ) from exc
    except csv.Error as exc:
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
        ) from exc

    _check_timeout(request, started_at)
    if not header:
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
            {"reason": "empty"},
        )
    if any(name == "" for name in header):
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
            {"reason": "empty_header"},
        )
    if len(header) > request.resource_bounds.max_columns:
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.RESOURCE_LIMIT_EXCEEDED,
            ErrorCategory.VALIDATION,
            "resource limit exceeded",
            {"limit": "columns"},
        )
    if len(set(header)) != len(header):
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
            {"reason": "duplicate_columns"},
        )
    _validate_cell_bounds(header, request)

    accumulators = tuple(
        _ColumnAccumulator(name=name, index=index) for index, name in enumerate(header)
    )
    row_count = 0
    try:
        for row in reader:
            _check_timeout(request, started_at)
            if len(row) != len(header):
                raise _ProfilerFailure(
                    DataLabProfilerErrorCode.MALFORMED_CSV,
                    ErrorCategory.VALIDATION,
                    "malformed csv",
                    {"reason": "row_shape"},
                )
            _validate_cell_bounds(row, request)
            row_count += 1
            if row_count > request.resource_bounds.max_rows:
                raise _ProfilerFailure(
                    DataLabProfilerErrorCode.RESOURCE_LIMIT_EXCEEDED,
                    ErrorCategory.VALIDATION,
                    "resource limit exceeded",
                    {"limit": "rows"},
                )
            accumulators = tuple(
                accumulator.add(value) for accumulator, value in zip(accumulators, row, strict=True)
            )
    except csv.Error as exc:
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
        ) from exc

    if row_count == 0:
        raise _ProfilerFailure(
            DataLabProfilerErrorCode.MALFORMED_CSV,
            ErrorCategory.VALIDATION,
            "malformed csv",
            {"reason": "empty"},
        )

    columns = tuple(_column_profile(accumulator, row_count) for accumulator in accumulators)
    warnings = _warnings_for_columns(columns, request.resource_bounds.max_warnings)
    return DatasetProfile(
        dataset_ref=request.dataset_ref,
        dataset_integrity_sha256=request.expected_sha256,
        row_count=row_count,
        column_count=len(columns),
        columns=columns,
        warnings=warnings,
    )


def _column_profile(accumulator: _ColumnAccumulator, row_count: int) -> DatasetColumnProfile:
    non_missing_count = len(accumulator.values)
    inferred_type = _infer_column_type(accumulator.classes)
    numeric_values: tuple[int | Decimal, ...]
    if inferred_type is DatasetPrimitiveType.INTEGER:
        numeric_values = accumulator.integers
    elif inferred_type is DatasetPrimitiveType.DECIMAL:
        numeric_values = accumulator.decimals
    else:
        numeric_values = ()

    minimum: int | float | None = None
    maximum: int | float | None = None
    mean: int | float | None = None
    if numeric_values:
        minimum = _json_number(min(numeric_values))
        maximum = _json_number(max(numeric_values))
        mean = _json_number(sum(numeric_values) / Decimal(len(numeric_values)))

    return DatasetColumnProfile(
        name=accumulator.name,
        index=accumulator.index,
        inferred_type=inferred_type,
        missing_count=accumulator.missing_count,
        non_missing_count=non_missing_count,
        distinct_count=len(frozenset(accumulator.values)),
        minimum=minimum,
        maximum=maximum,
        mean=mean,
    )


def _classify_value(value: str) -> DatasetPrimitiveType:
    lowered = value.lower()
    if lowered in _BOOLEAN_VALUES:
        return DatasetPrimitiveType.BOOLEAN
    if lowered in _NONFINITE_VALUES:
        return DatasetPrimitiveType.STRING
    if _INTEGER_RE.fullmatch(value) is not None:
        return DatasetPrimitiveType.INTEGER
    if _DECIMAL_RE.fullmatch(value) is not None:
        return DatasetPrimitiveType.DECIMAL
    return DatasetPrimitiveType.STRING


def _infer_column_type(classes: tuple[DatasetPrimitiveType, ...]) -> DatasetPrimitiveType:
    if not classes:
        return DatasetPrimitiveType.EMPTY
    distinct_classes = frozenset(classes)
    if len(distinct_classes) == 1:
        return next(iter(distinct_classes))
    return DatasetPrimitiveType.MIXED


def _warnings_for_columns(
    columns: tuple[DatasetColumnProfile, ...],
    max_warnings: int,
) -> tuple[DatasetProfileWarning, ...]:
    warnings: list[DatasetProfileWarning] = []
    for column in columns:
        if column.inferred_type is DatasetPrimitiveType.EMPTY:
            _append_warning(
                warnings,
                max_warnings,
                "empty_column",
                "Column contains only missing values.",
                column.index,
            )
        if column.inferred_type is DatasetPrimitiveType.MIXED:
            _append_warning(
                warnings,
                max_warnings,
                "mixed_types",
                "Column contains mixed primitive types.",
                column.index,
            )
        if column.missing_count > column.non_missing_count:
            _append_warning(
                warnings,
                max_warnings,
                "high_missingness",
                "Column contains more missing than non-missing values.",
                column.index,
            )
    return tuple(warnings)


def _findings_for_profile(
    request: DataLabProfilerRequest,
    profile: DatasetProfile,
    evidence: EvidenceReference,
) -> tuple[DataLabFinding, ...]:
    findings: list[DataLabFinding] = []
    for warning in profile.warnings:
        if len(findings) >= request.resource_bounds.max_findings:
            break
        if warning.column_index is None:
            continue
        if warning.warning_code == "empty_column":
            category = DataLabFindingCategory.COMPLETENESS
            severity = DataLabFindingSeverity.INFO
            summary = "Column contains only missing values."
        elif warning.warning_code == "high_missingness":
            category = DataLabFindingCategory.COMPLETENESS
            severity = DataLabFindingSeverity.WARNING
            summary = "Column contains high missingness."
        elif warning.warning_code == "mixed_types":
            category = DataLabFindingCategory.TYPE_MIX
            severity = DataLabFindingSeverity.WARNING
            summary = "Column contains mixed primitive types."
        else:
            continue
        findings.append(
            DataLabFinding(
                finding_key=f"{warning.warning_code}_{warning.column_index}",
                category=category,
                severity=severity,
                summary=summary,
                dataset_ref=request.dataset_ref,
                dataset_integrity_sha256=request.expected_sha256,
                provenance_path=f"profile.columns[{warning.column_index}]",
                evidence_refs=(evidence,),
            )
        )
    return tuple(findings)


def _append_warning(
    warnings: list[DatasetProfileWarning],
    max_warnings: int,
    warning_code: str,
    message: str,
    column_index: int,
) -> None:
    if len(warnings) >= max_warnings:
        return
    warnings.append(
        DatasetProfileWarning(
            warning_code=warning_code,
            message=message,
            column_index=column_index,
        )
    )


def _failure_outcome(
    request: DataLabProfilerRequest,
    started_event: EventEnvelope,
    status: DataLabProfilerOutcomeStatus,
    code: DataLabProfilerErrorCode,
    category: ErrorCategory,
    message: str,
    *,
    details: Mapping[str, object] | None = None,
) -> DataLabProfilerOutcome:
    evidence = _evidence(request, summary="DataLab profiler produced a bounded failure.")
    event_type = (
        DATALAB_PROFILER_TIMEOUT_EVENT_TYPE
        if status is DataLabProfilerOutcomeStatus.TIMED_OUT
        else DATALAB_PROFILER_FAILED_EVENT_TYPE
    )
    completed = _event(
        request,
        event_id=request.completed_event_id,
        event_type=event_type,
        payload={
            "status": status.value,
            "run_id": str(request.run_id),
            "work_id": str(request.work_ref.ref_id),
            "dataset_artifact_id": str(request.dataset_ref.artifact_id),
            "expected_sha256": request.expected_sha256,
            "reason": code.value,
        },
    )
    error = ContractError(
        error_code=ErrorCode(code.value),
        message=message,
        category=category,
        severity=ErrorSeverity.ERROR,
        retryable=category in {ErrorCategory.NOT_FOUND, ErrorCategory.TIMEOUT},
        subject_ref=request.work_ref,
        trace_id=request.observability_context.trace_id,
        details=details,
    )
    return DataLabProfilerOutcome(
        status=status,
        result=Result.failure((error,), evidence_refs=(evidence,)),
        events=(started_event, completed),
        evidence_refs=(evidence,),
    )


def _event(
    request: DataLabProfilerRequest,
    *,
    event_id: EventId,
    event_type: EventType,
    payload: dict[str, object],
) -> EventEnvelope:
    compatible_payload = to_json_compatible(payload)
    if not isinstance(compatible_payload, dict):
        msg = "profiler event payload must be an object"
        raise TypeError(msg)
    encoded = json.dumps(compatible_payload, allow_nan=False, sort_keys=True).encode("utf-8")
    if len(encoded) > request.resource_bounds.max_event_payload_bytes:
        compatible_payload = {
            "status": str(payload["status"]),
            "run_id": str(request.run_id),
            "work_id": str(request.work_ref.ref_id),
            "reason": "payload_summarized",
        }
    return EventEnvelope(
        event_id=event_id,
        event_type=event_type,
        schema_version=DATALAB_PROFILER_SCHEMA_VERSION,
        occurred_at=request.occurred_at,
        producer=request.producer_ref,
        subject_ref=request.work_ref,
        observability_context=request.observability_context,
        payload=compatible_payload,
    )


def _evidence(request: DataLabProfilerRequest, *, summary: str) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=request.evidence_id,
        kind=EvidenceKind.INSPECTION,
        subject_ref=request.work_ref,
        collected_at=request.occurred_at,
        artifact_refs=(request.dataset_ref.artifact_id,),
        summary=summary,
        trace_id=request.observability_context.trace_id,
    )


def _validate_cell_bounds(row: Sequence[str], request: DataLabProfilerRequest) -> None:
    for cell in row:
        if len(cell.encode("utf-8")) > request.resource_bounds.max_cell_bytes:
            raise _ProfilerFailure(
                DataLabProfilerErrorCode.RESOURCE_LIMIT_EXCEEDED,
                ErrorCategory.VALIDATION,
                "resource limit exceeded",
                {"limit": "cell"},
            )


def _check_timeout(request: DataLabProfilerRequest, started_at: float) -> None:
    if time.monotonic() - started_at > request.resource_bounds.timeout_seconds:
        raise _ProfilerTimeout


def _json_number(value: int | Decimal) -> int | float:
    if isinstance(value, int):
        return value
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _require_dataset_artifact(dataset_ref: ArtifactReference, sha256: str) -> None:
    _require_type(dataset_ref, ArtifactReference, "dataset_ref")
    if dataset_ref.kind is not ArtifactKind.DATASET:
        msg = "dataset_ref must have kind=dataset"
        raise ValueError(msg)
    if dataset_ref.media_type != DATALAB_DATASET_MEDIA_TYPE:
        msg = "dataset_ref media_type must be text/csv"
        raise ValueError(msg)
    if dataset_ref.integrity is None:
        msg = "dataset_ref integrity must be present"
        raise ValueError(msg)
    if dataset_ref.integrity.algorithm is not IntegrityAlgorithm.SHA256:
        msg = "dataset_ref integrity algorithm must be sha256"
        raise ValueError(msg)
    if dataset_ref.integrity.value != sha256:
        msg = "dataset_ref integrity must match expected_sha256"
        raise ValueError(msg)
    if dataset_ref.producer_ref is None:
        msg = "dataset_ref producer_ref must be present"
        raise ValueError(msg)


def _require_staged_input(staged_input: DataLabStagedInput) -> None:
    if isinstance(staged_input, str | bytes | bytearray):
        msg = "staged_input must be an authorized staged-input seam"
        raise TypeError(msg)
    read = getattr(staged_input, "read_authorized_bytes", None)
    handle_id = getattr(staged_input, "handle_id", None)
    if not callable(read) or not isinstance(handle_id, str):
        msg = "staged_input must be an authorized staged-input seam"
        raise TypeError(msg)


def _normalize_constraints(
    constraints: Mapping[str, str] | Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    if isinstance(constraints, Mapping):
        items = tuple(constraints.items())
    elif isinstance(constraints, Sequence) and not isinstance(constraints, str | bytes | bytearray):
        items = tuple(constraints)
    else:
        msg = "constraints must be a mapping or key/value sequence"
        raise TypeError(msg)
    normalized: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, tuple) or len(item) != 2:
            msg = "constraints must contain key/value pairs"
            raise TypeError(msg)
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            msg = "constraints must contain string key/value pairs"
            raise TypeError(msg)
        if len(key) > 128 or len(value) > 128:
            msg = "constraints must be bounded"
            raise ValueError(msg)
        normalized.append((key, value))
    return tuple(sorted(normalized, key=lambda pair: pair[0]))


def _require_sha256(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    if _SHA256_RE.fullmatch(value) is None:
        msg = f"{field_name} must be a lowercase sha256 hex digest"
        raise ValueError(msg)
    return value


def _require_reference_kind(
    reference: ObjectReference,
    expected_kind: ReferenceKind,
    field_name: str,
) -> None:
    _require_type(reference, ObjectReference, field_name)
    if reference.kind is not expected_kind:
        msg = f"{field_name} must reference {expected_kind.value}"
        raise ValueError(msg)


def _require_type[ValueT](value: object, expected_type: type[ValueT], field_name: str) -> None:
    if not isinstance(value, expected_type):
        msg = f"{field_name} must be {expected_type.__name__}"
        raise TypeError(msg)


def _require_int_between(value: int, field_name: str, *, minimum: int, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be an integer"
        raise TypeError(msg)
    if value < minimum or value > maximum:
        msg = f"{field_name} must be between {minimum} and {maximum}"
        raise ValueError(msg)


def _require_positive_float_at_most(value: float, field_name: str, *, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{field_name} must be numeric"
        raise TypeError(msg)
    if value <= 0 or value > maximum:
        msg = f"{field_name} must be greater than 0 and at most {maximum}"
        raise ValueError(msg)
