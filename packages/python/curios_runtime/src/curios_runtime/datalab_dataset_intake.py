"""Bounded M2 DataLab dataset intake and ephemeral staging."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    ArtifactReference,
    IntegrityAlgorithm,
    IntegrityDescriptor,
    ObjectReference,
    UtcTimestamp,
)

DATALAB_DATASET_MEDIA_TYPE: Final = "text/csv"
DATALAB_MAX_UPLOAD_BYTES: Final = 1024 * 1024
DATALAB_MAX_DATA_ROWS: Final = 10_000
DATALAB_MAX_COLUMNS: Final = 100
DATALAB_MAX_CELL_BYTES: Final = 16 * 1024
DATALAB_MAX_FILENAME_CHARS: Final = 128

_STAGED_LOCATOR_PREFIX: Final = "curios-datalab-staged:"
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_SECRET_SHAPED_METADATA_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|credential|password|secret|token)\s*[:=]"
)


class DataLabDatasetIntakeErrorCode(StrEnum):
    """Frozen M2 bounded dataset-intake failure classes."""

    UNSUPPORTED_MEDIA = "DATALAB_UNSUPPORTED_MEDIA"
    INVALID_FILENAME = "DATALAB_INVALID_FILENAME"
    EMPTY_DATASET = "DATALAB_EMPTY_DATASET"
    UPLOAD_TOO_LARGE = "DATALAB_UPLOAD_TOO_LARGE"
    INVALID_ENCODING = "DATALAB_INVALID_ENCODING"
    MALFORMED_CSV = "DATALAB_MALFORMED_CSV"
    DUPLICATE_COLUMNS = "DATALAB_DUPLICATE_COLUMNS"
    TOO_MANY_COLUMNS = "DATALAB_TOO_MANY_COLUMNS"
    TOO_MANY_ROWS = "DATALAB_TOO_MANY_ROWS"
    CELL_TOO_LARGE = "DATALAB_CELL_TOO_LARGE"
    INTEGRITY_FAILURE = "DATALAB_INTEGRITY_FAILURE"
    STAGING_FAILURE = "DATALAB_STAGING_FAILURE"
    DATASET_UNAVAILABLE = "DATALAB_DATASET_UNAVAILABLE"


_ERROR_MESSAGES: Final[dict[DataLabDatasetIntakeErrorCode, str]] = {
    DataLabDatasetIntakeErrorCode.UNSUPPORTED_MEDIA: "unsupported media",
    DataLabDatasetIntakeErrorCode.INVALID_FILENAME: "invalid filename",
    DataLabDatasetIntakeErrorCode.EMPTY_DATASET: "empty dataset",
    DataLabDatasetIntakeErrorCode.UPLOAD_TOO_LARGE: "upload too large",
    DataLabDatasetIntakeErrorCode.INVALID_ENCODING: "invalid encoding",
    DataLabDatasetIntakeErrorCode.MALFORMED_CSV: "malformed csv",
    DataLabDatasetIntakeErrorCode.DUPLICATE_COLUMNS: "duplicate columns",
    DataLabDatasetIntakeErrorCode.TOO_MANY_COLUMNS: "too many columns",
    DataLabDatasetIntakeErrorCode.TOO_MANY_ROWS: "too many rows",
    DataLabDatasetIntakeErrorCode.CELL_TOO_LARGE: "cell too large",
    DataLabDatasetIntakeErrorCode.INTEGRITY_FAILURE: "bounded integrity failure",
    DataLabDatasetIntakeErrorCode.STAGING_FAILURE: "bounded staging failure",
    DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE: "dataset unavailable",
}
_RETRYABLE_CODES: Final = frozenset(
    {
        DataLabDatasetIntakeErrorCode.INTEGRITY_FAILURE,
        DataLabDatasetIntakeErrorCode.STAGING_FAILURE,
        DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE,
    }
)


class DataLabDatasetIntakeError(Exception):
    """Bounded dataset-intake error that does not echo unsafe input."""

    def __init__(self, code: DataLabDatasetIntakeErrorCode) -> None:
        self.code = DataLabDatasetIntakeErrorCode(code)
        super().__init__(_ERROR_MESSAGES[self.code])

    @property
    def retryable(self) -> bool:
        """Return whether the frozen error class is retryable."""

        return self.code in _RETRYABLE_CODES

    def to_json_compatible(self) -> dict[str, object]:
        """Return bounded JSON-compatible error details."""

        return {
            "code": self.code.value,
            "message": _ERROR_MESSAGES[self.code],
            "retryable": self.retryable,
        }


@dataclass(frozen=True, slots=True)
class DataLabDatasetIntakeResult:
    """Accepted dataset metadata produced by the bounded intake boundary."""

    artifact_ref: ArtifactReference
    normalized_filename: str
    size_bytes: int
    data_row_count: int
    column_count: int
    dataset_integrity_sha256: str

    @property
    def staged_locator(self) -> str:
        """Return the generated opaque staged locator stored on the artifact."""

        return self.artifact_ref.locator


class LocalDataLabDatasetStagingStore:
    """Generated-locator local staging for accepted bounded DataLab datasets."""

    def __init__(self, root: Path) -> None:
        if not isinstance(root, Path):
            msg = "staging root must be a Path"
            raise TypeError(msg)
        self._root = root

    def accept_dataset(
        self,
        *,
        content: bytes,
        media_type: str,
        client_filename: str,
        producer_ref: ObjectReference,
        artifact_id: ArtifactId | None = None,
        created_at: UtcTimestamp | None = None,
    ) -> DataLabDatasetIntakeResult:
        """Validate, stage, and describe an authorized DataLab CSV upload."""

        if media_type != DATALAB_DATASET_MEDIA_TYPE:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.UNSUPPORTED_MEDIA)
        normalized_filename = normalize_datalab_dataset_filename(client_filename)
        _require_bytes(content)
        if len(content) == 0:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.EMPTY_DATASET)
        if len(content) > DATALAB_MAX_UPLOAD_BYTES:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.UPLOAD_TOO_LARGE)

        text = _decode_csv_text(content)
        csv_shape = _validate_csv_shape(text)
        digest = _sha256_hexdigest(content)
        selected_artifact_id = artifact_id or ArtifactId.generate()
        selected_created_at = created_at or UtcTimestamp.now()
        locator = datalab_staged_locator_for_artifact_id(selected_artifact_id)
        artifact_ref = ArtifactReference(
            artifact_id=selected_artifact_id,
            kind=ArtifactKind.DATASET,
            locator=locator,
            media_type=DATALAB_DATASET_MEDIA_TYPE,
            integrity=IntegrityDescriptor(
                algorithm=IntegrityAlgorithm.SHA256,
                value=digest,
            ),
            created_at=selected_created_at,
            producer_ref=producer_ref,
        )
        self._stage_bytes(locator=locator, content=content)
        return DataLabDatasetIntakeResult(
            artifact_ref=artifact_ref,
            normalized_filename=normalized_filename,
            size_bytes=len(content),
            data_row_count=csv_shape.data_row_count,
            column_count=csv_shape.column_count,
            dataset_integrity_sha256=digest,
        )

    def read_staged_bytes(self, locator: str) -> bytes:
        """Read bytes for a generated staged locator, if they are still available."""

        path = self._path_for_locator(locator)
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise DataLabDatasetIntakeError(
                DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE
            ) from exc
        except OSError as exc:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.STAGING_FAILURE) from exc

    def cleanup_staged_bytes(self, locator: str) -> None:
        """Idempotently remove bytes for a generated staged locator."""

        path = self._path_for_locator(locator)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.STAGING_FAILURE) from exc

    def _stage_bytes(self, *, locator: str, content: bytes) -> None:
        path = self._path_for_locator(locator)
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        except OSError as exc:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.STAGING_FAILURE) from exc

    def _path_for_locator(self, locator: str) -> Path:
        artifact_id = _artifact_id_from_locator(locator)
        path = self._root / f"{artifact_id}.csv"
        try:
            resolved_root = self._root.resolve(strict=False)
            resolved_path = path.resolve(strict=False)
            resolved_path.relative_to(resolved_root)
        except (OSError, ValueError) as exc:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.STAGING_FAILURE) from exc
        return path


@dataclass(frozen=True, slots=True)
class _CsvShape:
    data_row_count: int
    column_count: int


def normalize_datalab_dataset_filename(client_filename: str) -> str:
    """Return validated NFC filename metadata without granting path authority."""

    if not isinstance(client_filename, str):
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.INVALID_FILENAME)
    filename = unicodedata.normalize("NFC", client_filename)
    if (
        filename == ""
        or len(filename) > DATALAB_MAX_FILENAME_CHARS
        or filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
        or filename.startswith("/")
        or filename.startswith("\\")
        or _WINDOWS_DRIVE_RE.match(filename) is not None
        or _SECRET_SHAPED_METADATA_RE.search(filename) is not None
        or any(_is_control_character(character) for character in filename)
    ):
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.INVALID_FILENAME)
    return filename


def datalab_staged_locator_for_artifact_id(artifact_id: ArtifactId) -> str:
    """Return the canonical generated M2 DataLab staged locator for an artifact."""

    if not isinstance(artifact_id, ArtifactId):
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.STAGING_FAILURE)
    return f"{_STAGED_LOCATOR_PREFIX}{artifact_id}"


def _is_control_character(character: str) -> bool:
    codepoint = ord(character)
    return codepoint == 0 or codepoint < 32 or 127 <= codepoint <= 159


def _require_bytes(content: bytes) -> None:
    if not isinstance(content, bytes):
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.MALFORMED_CSV)


def _decode_csv_text(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.INVALID_ENCODING) from exc


def _validate_csv_shape(text: str) -> _CsvShape:
    reader = csv.reader(io.StringIO(text), delimiter=",", strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.EMPTY_DATASET) from exc
    except csv.Error as exc:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.MALFORMED_CSV) from exc

    if not header:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.EMPTY_DATASET)
    _validate_cells(header)
    column_count = len(header)
    if column_count > DATALAB_MAX_COLUMNS:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.TOO_MANY_COLUMNS)
    if len(set(header)) != column_count:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.DUPLICATE_COLUMNS)

    data_row_count = 0
    try:
        for row in reader:
            if len(row) != column_count:
                raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.MALFORMED_CSV)
            _validate_cells(row)
            data_row_count += 1
            if data_row_count > DATALAB_MAX_DATA_ROWS:
                raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.TOO_MANY_ROWS)
    except csv.Error as exc:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.MALFORMED_CSV) from exc

    if data_row_count == 0:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.EMPTY_DATASET)
    return _CsvShape(data_row_count=data_row_count, column_count=column_count)


def _validate_cells(cells: list[str]) -> None:
    for cell in cells:
        if len(cell.encode("utf-8")) > DATALAB_MAX_CELL_BYTES:
            raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.CELL_TOO_LARGE)


def _sha256_hexdigest(content: bytes) -> str:
    try:
        return hashlib.sha256(content).hexdigest()
    except Exception as exc:  # pragma: no cover - hashlib failure is defensive only.
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.INTEGRITY_FAILURE) from exc


def _locator_for_artifact_id(artifact_id: ArtifactId) -> str:
    return datalab_staged_locator_for_artifact_id(artifact_id)


def _artifact_id_from_locator(locator: str) -> ArtifactId:
    if not isinstance(locator, str) or not locator.startswith(_STAGED_LOCATOR_PREFIX):
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE)
    try:
        return ArtifactId(locator.removeprefix(_STAGED_LOCATOR_PREFIX))
    except (TypeError, ValueError) as exc:
        raise DataLabDatasetIntakeError(DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE) from exc
