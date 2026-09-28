"""Canonical M2 DataLab analysis contracts."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import (
    reject_secret_shaped_text,
    validate_safe_text,
    validate_safe_token,
)
from curios_contracts.artifacts import (
    ArtifactKind,
    ArtifactReference,
    IntegrityAlgorithm,
)
from curios_contracts.evidence import EvidenceReference
from curios_contracts.identifiers import (
    CorrelationId,
    DataLabAnalysisId,
    DataLabResultId,
    DataLabRunId,
    EvidenceId,
    TraceId,
)
from curios_contracts.references import ObjectReference, ReferenceKind
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp
from curios_contracts.verification import VerificationReference

_MAX_DATALAB_OBJECTIVE_LENGTH = 1000
_MAX_DATALAB_CONSTRAINTS = 10
_MAX_DATALAB_CONSTRAINT_KEY_LENGTH = 128
_MAX_DATALAB_CONSTRAINT_VALUE_LENGTH = 128
_MAX_DATALAB_PROFILE_COLUMNS = 100
_MAX_DATALAB_WARNINGS = 100
_MAX_DATALAB_FINDINGS = 50
_MAX_DATALAB_FINDING_SUMMARY_LENGTH = 500
_MAX_DATALAB_FINDING_EVIDENCE_REFS = 5
_MAX_DATALAB_RESULT_EVIDENCE_REFS = 20
_MAX_DATALAB_PROVENANCE_PATH_LENGTH = 256
_MAX_DATALAB_WARNING_MESSAGE_LENGTH = 500

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class DataLabAnalysisKind(StrEnum):
    """Frozen M2 DataLab analysis intent."""

    PROFILE_DATASET = "PROFILE_DATASET"


class DatasetPrimitiveType(StrEnum):
    """Deterministic primitive type labels emitted by the future M2 profiler."""

    STRING = "STRING"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    EMPTY = "EMPTY"
    MIXED = "MIXED"


class DataLabFindingCategory(StrEnum):
    """Frozen M2 finding categories."""

    SCHEMA = "SCHEMA"
    COMPLETENESS = "COMPLETENESS"
    TYPE_MIX = "TYPE_MIX"
    DISTRIBUTION = "DISTRIBUTION"
    QUALITY = "QUALITY"


class DataLabFindingSeverity(StrEnum):
    """Frozen M2 finding severities."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class DatasetColumnProfile:
    """Ordered per-column profile data within a DatasetProfile."""

    name: str
    index: int
    inferred_type: DatasetPrimitiveType
    missing_count: int
    non_missing_count: int
    distinct_count: int
    minimum: int | float | None = None
    maximum: int | float | None = None
    mean: int | float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "name", validate_safe_text(self.name, "column name", max_length=256)
        )
        object.__setattr__(self, "index", _require_non_negative_int(self.index, "column index"))
        object.__setattr__(self, "inferred_type", DatasetPrimitiveType(self.inferred_type))
        object.__setattr__(
            self,
            "missing_count",
            _require_non_negative_int(self.missing_count, "missing_count"),
        )
        object.__setattr__(
            self,
            "non_missing_count",
            _require_non_negative_int(self.non_missing_count, "non_missing_count"),
        )
        object.__setattr__(
            self,
            "distinct_count",
            _require_non_negative_int(self.distinct_count, "distinct_count"),
        )

        numeric_type = self.inferred_type in {
            DatasetPrimitiveType.INTEGER,
            DatasetPrimitiveType.DECIMAL,
        }
        for field_name in ("minimum", "maximum", "mean"):
            value = getattr(self, field_name)
            if value is None:
                continue
            if not numeric_type:
                msg = f"{field_name} is only valid for numeric column profiles"
                raise ValueError(msg)
            object.__setattr__(self, field_name, _require_finite_number(value, field_name))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse a canonical JSON-compatible column profile."""
        if not isinstance(value, dict):
            msg = "column profile JSON must be an object"
            raise TypeError(msg)
        return cls(
            name=_require_str(value["name"], "name"),
            index=_require_int(value["index"], "index"),
            inferred_type=DatasetPrimitiveType(value["inferred_type"]),
            missing_count=_require_int(value["missing_count"], "missing_count"),
            non_missing_count=_require_int(value["non_missing_count"], "non_missing_count"),
            distinct_count=_require_int(value["distinct_count"], "distinct_count"),
            minimum=_parse_optional_number(value.get("minimum"), "minimum"),
            maximum=_parse_optional_number(value.get("maximum"), "maximum"),
            mean=_parse_optional_number(value.get("mean"), "mean"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible column profile."""
        return {
            "name": self.name,
            "index": self.index,
            "inferred_type": self.inferred_type.value,
            "missing_count": self.missing_count,
            "non_missing_count": self.non_missing_count,
            "distinct_count": self.distinct_count,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "mean": self.mean,
        }


@dataclass(frozen=True, slots=True)
class DatasetProfileWarning:
    """Bounded profile warning ordered by stable code and optional column index."""

    warning_code: str
    message: str
    column_index: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "warning_code",
            validate_safe_token(self.warning_code, "warning_code"),
        )
        message = validate_safe_text(
            self.message,
            "warning message",
            max_length=_MAX_DATALAB_WARNING_MESSAGE_LENGTH,
        )
        reject_secret_shaped_text(message, "warning message")
        object.__setattr__(self, "message", message)
        if self.column_index is not None:
            object.__setattr__(
                self,
                "column_index",
                _require_non_negative_int(self.column_index, "column_index"),
            )

    @property
    def ordering_key(self) -> tuple[str, int]:
        """Return the deterministic DatasetProfile warning ordering key."""
        return (self.warning_code, self.column_index if self.column_index is not None else -1)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse a canonical JSON-compatible profile warning."""
        if not isinstance(value, dict):
            msg = "profile warning JSON must be an object"
            raise TypeError(msg)
        column_index = value.get("column_index")
        return cls(
            warning_code=_require_str(value["warning_code"], "warning_code"),
            message=_require_str(value["message"], "message"),
            column_index=(
                _require_int(column_index, "column_index") if column_index is not None else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible profile warning."""
        return {
            "warning_code": self.warning_code,
            "message": self.message,
            "column_index": self.column_index,
        }


@dataclass(frozen=True, slots=True)
class DataLabAnalysisRequest:
    """Canonical bounded request for the M2 PROFILE_DATASET analysis."""

    analysis_id: DataLabAnalysisId
    dataset_ref: ArtifactReference
    dataset_integrity_sha256: str
    objective: str
    analysis_kind: DataLabAnalysisKind
    created_at: UtcTimestamp
    correlation_id: CorrelationId
    principal_ref: ObjectReference | None = None
    trace_id: TraceId | None = None
    constraints: Mapping[str, str] | Sequence[tuple[str, str]] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.analysis_id, DataLabAnalysisId):
            msg = "analysis_id must be a DataLabAnalysisId"
            raise TypeError(msg)
        sha256 = _require_sha256(self.dataset_integrity_sha256)
        _require_dataset_artifact(self.dataset_ref, sha256)
        object.__setattr__(self, "dataset_integrity_sha256", sha256)

        objective = validate_safe_text(
            self.objective,
            "objective",
            max_length=_MAX_DATALAB_OBJECTIVE_LENGTH,
        )
        reject_secret_shaped_text(objective, "objective")
        object.__setattr__(self, "objective", objective)
        object.__setattr__(self, "analysis_kind", DataLabAnalysisKind(self.analysis_kind))
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        if not isinstance(self.correlation_id, CorrelationId):
            msg = "correlation_id must be a CorrelationId"
            raise TypeError(msg)
        if self.trace_id is not None and not isinstance(self.trace_id, TraceId):
            msg = "trace_id must be a TraceId when provided"
            raise TypeError(msg)
        if self.principal_ref is not None and not isinstance(self.principal_ref, ObjectReference):
            msg = "principal_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        object.__setattr__(self, "constraints", _normalize_constraints(self.constraints))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse a canonical JSON-compatible analysis request."""
        if not isinstance(value, dict):
            msg = "DataLab analysis request JSON must be an object"
            raise TypeError(msg)
        principal_ref = value.get("principal_ref")
        trace_id = value.get("trace_id")
        return cls(
            analysis_id=DataLabAnalysisId(_require_str(value["analysis_id"], "analysis_id")),
            dataset_ref=ArtifactReference.from_json_compatible(value["dataset_ref"]),
            dataset_integrity_sha256=_require_str(
                value["dataset_integrity_sha256"],
                "dataset_integrity_sha256",
            ),
            objective=_require_str(value["objective"], "objective"),
            analysis_kind=DataLabAnalysisKind(value["analysis_kind"]),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            correlation_id=CorrelationId(_require_str(value["correlation_id"], "correlation_id")),
            principal_ref=(
                ObjectReference.from_json_compatible(principal_ref)
                if principal_ref is not None
                else None
            ),
            trace_id=TraceId(_require_str(trace_id, "trace_id")) if trace_id is not None else None,
            constraints=_require_mapping(value.get("constraints", {}), "constraints"),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible analysis request."""
        constraints = _normalize_constraints(self.constraints)
        return {
            "analysis_id": str(self.analysis_id),
            "dataset_ref": to_json_compatible(self.dataset_ref),
            "dataset_integrity_sha256": self.dataset_integrity_sha256,
            "objective": self.objective,
            "analysis_kind": self.analysis_kind.value,
            "created_at": to_json_compatible(self.created_at),
            "correlation_id": to_json_compatible(self.correlation_id),
            "principal_ref": to_json_compatible(self.principal_ref),
            "trace_id": to_json_compatible(self.trace_id),
            "constraints": {key: value for key, value in constraints},
        }


@dataclass(frozen=True, slots=True)
class DatasetProfile:
    """Canonical DatasetProfile bound to one accepted dataset artifact."""

    dataset_ref: ArtifactReference
    dataset_integrity_sha256: str
    row_count: int
    column_count: int
    columns: tuple[DatasetColumnProfile, ...]
    warnings: tuple[DatasetProfileWarning, ...] = ()

    def __post_init__(self) -> None:
        sha256 = _require_sha256(self.dataset_integrity_sha256)
        _require_dataset_artifact(self.dataset_ref, sha256)
        object.__setattr__(self, "dataset_integrity_sha256", sha256)
        row_count = _require_non_negative_int(self.row_count, "row_count")
        column_count = _require_non_negative_int(self.column_count, "column_count")
        if column_count > _MAX_DATALAB_PROFILE_COLUMNS:
            msg = f"column_count must be at most {_MAX_DATALAB_PROFILE_COLUMNS}"
            raise ValueError(msg)
        object.__setattr__(self, "row_count", row_count)
        object.__setattr__(self, "column_count", column_count)

        columns = _normalize_columns(self.columns, row_count=row_count, column_count=column_count)
        warnings = _normalize_warnings(self.warnings)
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "warnings", warnings)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse a canonical JSON-compatible dataset profile."""
        if not isinstance(value, dict):
            msg = "DatasetProfile JSON must be an object"
            raise TypeError(msg)
        columns_value = _require_sequence(value["columns"], "columns")
        warnings_value = _require_sequence(value.get("warnings", ()), "warnings")
        return cls(
            dataset_ref=ArtifactReference.from_json_compatible(value["dataset_ref"]),
            dataset_integrity_sha256=_require_str(
                value["dataset_integrity_sha256"],
                "dataset_integrity_sha256",
            ),
            row_count=_require_int(value["row_count"], "row_count"),
            column_count=_require_int(value["column_count"], "column_count"),
            columns=tuple(
                DatasetColumnProfile.from_json_compatible(item) for item in columns_value
            ),
            warnings=tuple(
                DatasetProfileWarning.from_json_compatible(item) for item in warnings_value
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible dataset profile."""
        return {
            "dataset_ref": to_json_compatible(self.dataset_ref),
            "dataset_integrity_sha256": self.dataset_integrity_sha256,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": to_json_compatible(self.columns),
            "warnings": to_json_compatible(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class DataLabFinding:
    """Canonical bounded DataLab finding with deterministic ordering."""

    finding_key: str
    category: DataLabFindingCategory
    severity: DataLabFindingSeverity
    summary: str
    dataset_ref: ArtifactReference
    dataset_integrity_sha256: str
    provenance_path: str
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "finding_key",
            validate_safe_token(self.finding_key, "finding_key"),
        )
        object.__setattr__(self, "category", DataLabFindingCategory(self.category))
        object.__setattr__(self, "severity", DataLabFindingSeverity(self.severity))
        summary = validate_safe_text(
            self.summary,
            "summary",
            max_length=_MAX_DATALAB_FINDING_SUMMARY_LENGTH,
        )
        reject_secret_shaped_text(summary, "summary")
        object.__setattr__(self, "summary", summary)
        sha256 = _require_sha256(self.dataset_integrity_sha256)
        _require_dataset_artifact(self.dataset_ref, sha256)
        object.__setattr__(self, "dataset_integrity_sha256", sha256)
        object.__setattr__(
            self,
            "provenance_path",
            validate_safe_text(
                self.provenance_path,
                "provenance_path",
                max_length=_MAX_DATALAB_PROVENANCE_PATH_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_evidence_refs(
                self.evidence_refs,
                max_count=_MAX_DATALAB_FINDING_EVIDENCE_REFS,
            ),
        )

    @property
    def ordering_key(self) -> tuple[int, str, str]:
        """Return the frozen deterministic finding ordering key."""
        return (_severity_rank(self.severity), self.category.value, self.finding_key)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse a canonical JSON-compatible finding."""
        if not isinstance(value, dict):
            msg = "DataLabFinding JSON must be an object"
            raise TypeError(msg)
        evidence_refs_value = _require_sequence(value.get("evidence_refs", ()), "evidence_refs")
        return cls(
            finding_key=_require_str(value["finding_key"], "finding_key"),
            category=DataLabFindingCategory(value["category"]),
            severity=DataLabFindingSeverity(value["severity"]),
            summary=_require_str(value["summary"], "summary"),
            dataset_ref=ArtifactReference.from_json_compatible(value["dataset_ref"]),
            dataset_integrity_sha256=_require_str(
                value["dataset_integrity_sha256"],
                "dataset_integrity_sha256",
            ),
            provenance_path=_require_str(value["provenance_path"], "provenance_path"),
            evidence_refs=tuple(_parse_evidence_ref(item) for item in evidence_refs_value),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible finding."""
        return {
            "finding_key": self.finding_key,
            "category": self.category.value,
            "severity": self.severity.value,
            "summary": self.summary,
            "dataset_ref": to_json_compatible(self.dataset_ref),
            "dataset_integrity_sha256": self.dataset_integrity_sha256,
            "provenance_path": self.provenance_path,
            "evidence_refs": to_json_compatible(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class DataLabAnalysisResult:
    """Canonical DataLab result binding request, work, dataset, profile, and evidence."""

    result_id: DataLabResultId
    run_id: DataLabRunId
    analysis_id: DataLabAnalysisId
    work_ref: ObjectReference
    dataset_ref: ArtifactReference
    dataset_integrity_sha256: str
    profile: DatasetProfile
    findings: tuple[DataLabFinding, ...]
    warnings: tuple[DatasetProfileWarning, ...]
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...]
    created_at: UtcTimestamp
    verification_ref: VerificationReference | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.result_id, DataLabResultId):
            msg = "result_id must be a DataLabResultId"
            raise TypeError(msg)
        if not isinstance(self.run_id, DataLabRunId):
            msg = "run_id must be a DataLabRunId"
            raise TypeError(msg)
        if not isinstance(self.analysis_id, DataLabAnalysisId):
            msg = "analysis_id must be a DataLabAnalysisId"
            raise TypeError(msg)
        _require_object_reference_kind(self.work_ref, ReferenceKind.WORK, "work_ref")
        sha256 = _require_sha256(self.dataset_integrity_sha256)
        _require_dataset_artifact(self.dataset_ref, sha256)
        object.__setattr__(self, "dataset_integrity_sha256", sha256)
        if self.profile.dataset_ref != self.dataset_ref:
            msg = "profile dataset_ref must match result dataset_ref"
            raise ValueError(msg)
        if self.profile.dataset_integrity_sha256 != sha256:
            msg = "profile dataset_integrity_sha256 must match result dataset_integrity_sha256"
            raise ValueError(msg)

        object.__setattr__(self, "findings", _normalize_findings(self.findings, self))
        object.__setattr__(self, "warnings", _normalize_warnings(self.warnings))
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_evidence_refs(
                self.evidence_refs,
                max_count=_MAX_DATALAB_RESULT_EVIDENCE_REFS,
            ),
        )
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        if self.verification_ref is not None and not isinstance(
            self.verification_ref,
            VerificationReference,
        ):
            msg = "verification_ref must be a VerificationReference when provided"
            raise TypeError(msg)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse a canonical JSON-compatible DataLab analysis result."""
        if not isinstance(value, dict):
            msg = "DataLabAnalysisResult JSON must be an object"
            raise TypeError(msg)
        findings_value = _require_sequence(value["findings"], "findings")
        warnings_value = _require_sequence(value.get("warnings", ()), "warnings")
        evidence_refs_value = _require_sequence(value.get("evidence_refs", ()), "evidence_refs")
        verification_ref = value.get("verification_ref")
        return cls(
            result_id=DataLabResultId(_require_str(value["result_id"], "result_id")),
            run_id=DataLabRunId(_require_str(value["run_id"], "run_id")),
            analysis_id=DataLabAnalysisId(_require_str(value["analysis_id"], "analysis_id")),
            work_ref=ObjectReference.from_json_compatible(value["work_ref"]),
            dataset_ref=ArtifactReference.from_json_compatible(value["dataset_ref"]),
            dataset_integrity_sha256=_require_str(
                value["dataset_integrity_sha256"],
                "dataset_integrity_sha256",
            ),
            profile=DatasetProfile.from_json_compatible(value["profile"]),
            findings=tuple(DataLabFinding.from_json_compatible(item) for item in findings_value),
            warnings=tuple(
                DatasetProfileWarning.from_json_compatible(item) for item in warnings_value
            ),
            evidence_refs=tuple(_parse_evidence_ref(item) for item in evidence_refs_value),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            verification_ref=(
                VerificationReference.from_json_compatible(verification_ref)
                if verification_ref is not None
                else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible DataLab analysis result."""
        return {
            "result_id": str(self.result_id),
            "run_id": str(self.run_id),
            "analysis_id": str(self.analysis_id),
            "work_ref": to_json_compatible(self.work_ref),
            "dataset_ref": to_json_compatible(self.dataset_ref),
            "dataset_integrity_sha256": self.dataset_integrity_sha256,
            "profile": to_json_compatible(self.profile),
            "findings": to_json_compatible(self.findings),
            "warnings": to_json_compatible(self.warnings),
            "evidence_refs": to_json_compatible(self.evidence_refs),
            "created_at": to_json_compatible(self.created_at),
            "verification_ref": to_json_compatible(self.verification_ref),
        }


def _require_dataset_artifact(dataset_ref: ArtifactReference, sha256: str) -> None:
    if not isinstance(dataset_ref, ArtifactReference):
        msg = "dataset_ref must be an ArtifactReference"
        raise TypeError(msg)
    if dataset_ref.kind is not ArtifactKind.DATASET:
        msg = "dataset_ref must have kind=dataset"
        raise ValueError(msg)
    if dataset_ref.media_type != "text/csv":
        msg = "dataset_ref media_type must be text/csv"
        raise ValueError(msg)
    if dataset_ref.integrity is None:
        msg = "dataset_ref integrity must be present"
        raise ValueError(msg)
    if dataset_ref.integrity.algorithm is not IntegrityAlgorithm.SHA256:
        msg = "dataset_ref integrity algorithm must be sha256"
        raise ValueError(msg)
    if dataset_ref.integrity.value != sha256:
        msg = "dataset_ref integrity must match dataset_integrity_sha256"
        raise ValueError(msg)
    if dataset_ref.producer_ref is None:
        msg = "dataset_ref producer_ref must be present"
        raise ValueError(msg)


def _require_sha256(value: str) -> str:
    if not isinstance(value, str):
        msg = "dataset_integrity_sha256 must be a string"
        raise TypeError(msg)
    if _SHA256_RE.fullmatch(value) is None:
        msg = "dataset_integrity_sha256 must be a lowercase sha256 hex digest"
        raise ValueError(msg)
    return value


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
    if len(items) > _MAX_DATALAB_CONSTRAINTS:
        msg = f"constraints must contain at most {_MAX_DATALAB_CONSTRAINTS} items"
        raise ValueError(msg)
    normalized: dict[str, str] = {}
    for key, value in items:
        normalized_key = validate_safe_text(
            key,
            "constraint key",
            max_length=_MAX_DATALAB_CONSTRAINT_KEY_LENGTH,
        )
        normalized_value = validate_safe_text(
            value,
            "constraint value",
            max_length=_MAX_DATALAB_CONSTRAINT_VALUE_LENGTH,
            allow_empty=True,
        )
        reject_secret_shaped_text(normalized_key, "constraint key")
        reject_secret_shaped_text(normalized_value, "constraint value")
        if normalized_key in normalized:
            msg = "constraints must not contain duplicate keys"
            raise ValueError(msg)
        normalized[normalized_key] = normalized_value
    return tuple(sorted(normalized.items(), key=lambda item: item[0]))


def _normalize_columns(
    columns: tuple[DatasetColumnProfile, ...],
    *,
    row_count: int,
    column_count: int,
) -> tuple[DatasetColumnProfile, ...]:
    normalized = tuple(columns)
    if len(normalized) != column_count:
        msg = "columns length must match column_count"
        raise ValueError(msg)
    if len(normalized) > _MAX_DATALAB_PROFILE_COLUMNS:
        msg = f"columns must contain at most {_MAX_DATALAB_PROFILE_COLUMNS} profiles"
        raise ValueError(msg)
    seen_indexes: set[int] = set()
    seen_names: set[str] = set()
    for column in normalized:
        if not isinstance(column, DatasetColumnProfile):
            msg = "columns must contain DatasetColumnProfile values"
            raise TypeError(msg)
        if column.index in seen_indexes:
            msg = "columns must not contain duplicate indexes"
            raise ValueError(msg)
        if column.name in seen_names:
            msg = "columns must not contain duplicate names"
            raise ValueError(msg)
        if column.missing_count + column.non_missing_count != row_count:
            msg = "column missing_count plus non_missing_count must equal row_count"
            raise ValueError(msg)
        seen_indexes.add(column.index)
        seen_names.add(column.name)
    return tuple(sorted(normalized, key=lambda column: column.index))


def _normalize_warnings(
    warnings: tuple[DatasetProfileWarning, ...],
) -> tuple[DatasetProfileWarning, ...]:
    normalized = tuple(warnings)
    if len(normalized) > _MAX_DATALAB_WARNINGS:
        msg = f"warnings must contain at most {_MAX_DATALAB_WARNINGS} items"
        raise ValueError(msg)
    for warning in normalized:
        if not isinstance(warning, DatasetProfileWarning):
            msg = "warnings must contain DatasetProfileWarning values"
            raise TypeError(msg)
    return tuple(sorted(normalized, key=lambda warning: warning.ordering_key))


def _normalize_findings(
    findings: tuple[DataLabFinding, ...],
    result: DataLabAnalysisResult,
) -> tuple[DataLabFinding, ...]:
    normalized = tuple(findings)
    if len(normalized) > _MAX_DATALAB_FINDINGS:
        msg = f"findings must contain at most {_MAX_DATALAB_FINDINGS} items"
        raise ValueError(msg)
    seen_keys: set[str] = set()
    for finding in normalized:
        if not isinstance(finding, DataLabFinding):
            msg = "findings must contain DataLabFinding values"
            raise TypeError(msg)
        if finding.finding_key in seen_keys:
            msg = "findings must not contain duplicate finding_key values"
            raise ValueError(msg)
        if finding.dataset_ref != result.dataset_ref:
            msg = "finding dataset_ref must match result dataset_ref"
            raise ValueError(msg)
        if finding.dataset_integrity_sha256 != result.dataset_integrity_sha256:
            msg = "finding dataset_integrity_sha256 must match result dataset_integrity_sha256"
            raise ValueError(msg)
        seen_keys.add(finding.finding_key)
    return tuple(sorted(normalized, key=lambda finding: finding.ordering_key))


def _normalize_evidence_refs(
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...],
    *,
    max_count: int,
) -> tuple[EvidenceReference | EvidenceId, ...]:
    normalized = tuple(evidence_refs)
    if len(normalized) > max_count:
        msg = f"evidence_refs must contain at most {max_count} items"
        raise ValueError(msg)
    seen_ids: set[str] = set()
    for evidence_ref in normalized:
        if not isinstance(evidence_ref, EvidenceReference | EvidenceId):
            msg = "evidence_refs must contain EvidenceReference or EvidenceId values"
            raise TypeError(msg)
        evidence_id = (
            evidence_ref.evidence_id
            if isinstance(evidence_ref, EvidenceReference)
            else evidence_ref
        )
        if str(evidence_id) in seen_ids:
            msg = "evidence_refs must not contain duplicate evidence IDs"
            raise ValueError(msg)
        seen_ids.add(str(evidence_id))
    return tuple(sorted(normalized, key=lambda evidence_ref: str(_evidence_id(evidence_ref))))


def _parse_evidence_ref(value: object) -> EvidenceReference | EvidenceId:
    if isinstance(value, str):
        return EvidenceId(value)
    return EvidenceReference.from_json_compatible(value)


def _evidence_id(evidence_ref: EvidenceReference | EvidenceId) -> EvidenceId:
    return evidence_ref.evidence_id if isinstance(evidence_ref, EvidenceReference) else evidence_ref


def _severity_rank(severity: DataLabFindingSeverity) -> int:
    return {
        DataLabFindingSeverity.ERROR: 0,
        DataLabFindingSeverity.WARNING: 1,
        DataLabFindingSeverity.INFO: 2,
    }[severity]


def _require_object_reference_kind(
    reference: ObjectReference,
    expected_kind: ReferenceKind,
    field_name: str,
) -> None:
    if not isinstance(reference, ObjectReference):
        msg = f"{field_name} must be an ObjectReference"
        raise TypeError(msg)
    if reference.kind is not expected_kind:
        msg = f"{field_name} must reference {expected_kind.value}"
        raise ValueError(msg)


def _require_non_negative_int(value: int, field_name: str) -> int:
    parsed = _require_int(value, field_name)
    if parsed < 0:
        msg = f"{field_name} must be non-negative"
        raise ValueError(msg)
    return parsed


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be an integer"
        raise TypeError(msg)
    return value


def _parse_optional_number(value: object, field_name: str) -> int | float | None:
    if value is None:
        return None
    return _require_finite_number(value, field_name)


def _require_finite_number(value: object, field_name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{field_name} must be a number"
        raise TypeError(msg)
    if isinstance(value, float) and not math.isfinite(value):
        msg = f"{field_name} must be finite"
        raise ValueError(msg)
    return value


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


def _require_sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    return value


def _require_mapping(value: object, field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be an object"
        raise TypeError(msg)
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            msg = f"{field_name} must contain string keys and values"
            raise TypeError(msg)
    return value


DATALAB_ANALYSIS_KIND_VALUES: tuple[str, ...] = tuple(
    member.value for member in DataLabAnalysisKind
)
DATASET_PRIMITIVE_TYPE_VALUES: tuple[str, ...] = tuple(
    member.value for member in DatasetPrimitiveType
)
DATALAB_FINDING_CATEGORY_VALUES: tuple[str, ...] = tuple(
    member.value for member in DataLabFindingCategory
)
DATALAB_FINDING_SEVERITY_VALUES: tuple[str, ...] = tuple(
    member.value for member in DataLabFindingSeverity
)
