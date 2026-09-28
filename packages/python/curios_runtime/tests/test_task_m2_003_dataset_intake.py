from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from curios_contracts import (
    ArtifactId,
    ArtifactKind,
    IntegrityAlgorithm,
    ObjectReference,
    ProjectId,
    UtcTimestamp,
)
from curios_runtime import (
    DATALAB_DATASET_MEDIA_TYPE,
    DATALAB_MAX_CELL_BYTES,
    DATALAB_MAX_COLUMNS,
    DATALAB_MAX_DATA_ROWS,
    DATALAB_MAX_UPLOAD_BYTES,
    DataLabDatasetIntakeError,
    DataLabDatasetIntakeErrorCode,
    DataLabDatasetIntakeResult,
    LocalDataLabDatasetStagingStore,
    normalize_datalab_dataset_filename,
)

UTC_NOW = UtcTimestamp.parse("2026-09-28T10:00:00Z")
ARTIFACT_ID = ArtifactId("art_0123456789ABCDEFGHJKMNPQRS")


def _producer_ref() -> ObjectReference:
    return ObjectReference.from_id(ProjectId.generate())


def _store(tmp_path: Path) -> LocalDataLabDatasetStagingStore:
    return LocalDataLabDatasetStagingStore(tmp_path / "stage")


def _accept(
    tmp_path: Path,
    content: bytes = b"name,amount\nalice,10\n",
    *,
    filename: str = "dataset.csv",
) -> DataLabDatasetIntakeResult:
    return _store(tmp_path).accept_dataset(
        content=content,
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        client_filename=filename,
        producer_ref=_producer_ref(),
        artifact_id=ARTIFACT_ID,
        created_at=UTC_NOW,
    )


def _assert_error(
    tmp_path: Path,
    code: DataLabDatasetIntakeErrorCode,
    content: bytes,
    *,
    filename: str = "dataset.csv",
    media_type: str = DATALAB_DATASET_MEDIA_TYPE,
) -> None:
    with pytest.raises(DataLabDatasetIntakeError) as exc_info:
        _store(tmp_path).accept_dataset(
            content=content,
            media_type=media_type,
            client_filename=filename,
            producer_ref=_producer_ref(),
            artifact_id=ARTIFACT_ID,
            created_at=UTC_NOW,
        )
    assert exc_info.value.code is code
    assert exc_info.value.to_json_compatible()["message"] == str(exc_info.value)


def _csv_with_columns(count: int) -> bytes:
    header = ",".join(f"c{index}" for index in range(count))
    row = ",".join(str(index) for index in range(count))
    return f"{header}\n{row}\n".encode()


def _exact_upload_size_csv(size: int) -> bytes:
    content = bytearray(b"c\n")
    remaining = size - len(content)
    while remaining > DATALAB_MAX_CELL_BYTES + 1:
        content.extend(b"x" * DATALAB_MAX_CELL_BYTES + b"\n")
        remaining -= DATALAB_MAX_CELL_BYTES + 1
    assert 1 <= remaining <= DATALAB_MAX_CELL_BYTES + 1
    content.extend(b"y" * (remaining - 1) + b"\n")
    assert len(content) == size
    return bytes(content)


def test_accepts_minimal_csv_and_returns_canonical_dataset_artifact(tmp_path: Path) -> None:
    result = _accept(tmp_path)

    assert result.artifact_ref.artifact_id == ARTIFACT_ID
    assert result.artifact_ref.kind is ArtifactKind.DATASET
    assert result.artifact_ref.media_type == "text/csv"
    assert result.artifact_ref.integrity is not None
    assert result.artifact_ref.integrity.algorithm is IntegrityAlgorithm.SHA256
    assert (
        result.artifact_ref.integrity.value
        == hashlib.sha256(b"name,amount\nalice,10\n").hexdigest()
    )
    assert result.artifact_ref.producer_ref is not None
    assert result.normalized_filename == "dataset.csv"
    assert result.size_bytes == 21
    assert result.data_row_count == 1
    assert result.column_count == 2


def test_accepts_utf8_bom_and_hashes_exact_uploaded_bytes(tmp_path: Path) -> None:
    content = b"\xef\xbb\xbfname\nalice\n"
    result = _accept(tmp_path, content)

    assert result.dataset_integrity_sha256 == hashlib.sha256(content).hexdigest()
    assert result.data_row_count == 1
    assert result.column_count == 1


def test_enforces_exact_upload_size_bound_before_parsing(tmp_path: Path) -> None:
    exact = _exact_upload_size_csv(DATALAB_MAX_UPLOAD_BYTES)

    result = _accept(tmp_path, exact)
    assert result.size_bytes == DATALAB_MAX_UPLOAD_BYTES

    _assert_error(
        tmp_path,
        DataLabDatasetIntakeErrorCode.UPLOAD_TOO_LARGE,
        exact + b"x",
    )


def test_enforces_column_row_and_cell_bounds(tmp_path: Path) -> None:
    assert _accept(tmp_path, _csv_with_columns(DATALAB_MAX_COLUMNS)).column_count == 100
    _assert_error(
        tmp_path,
        DataLabDatasetIntakeErrorCode.TOO_MANY_COLUMNS,
        _csv_with_columns(DATALAB_MAX_COLUMNS + 1),
    )

    max_rows = b"c\n" + b"1\n" * DATALAB_MAX_DATA_ROWS
    assert _accept(tmp_path, max_rows).data_row_count == DATALAB_MAX_DATA_ROWS
    _assert_error(
        tmp_path,
        DataLabDatasetIntakeErrorCode.TOO_MANY_ROWS,
        max_rows + b"1\n",
    )

    max_cell = b"c\n" + b"x" * DATALAB_MAX_CELL_BYTES + b"\n"
    assert _accept(tmp_path, max_cell).data_row_count == 1
    _assert_error(
        tmp_path,
        DataLabDatasetIntakeErrorCode.CELL_TOO_LARGE,
        b"c\n" + b"x" * (DATALAB_MAX_CELL_BYTES + 1) + b"\n",
    )


@pytest.mark.parametrize(
    ("content", "code"),
    (
        (b"", DataLabDatasetIntakeErrorCode.EMPTY_DATASET),
        (b"\xff\n", DataLabDatasetIntakeErrorCode.INVALID_ENCODING),
        (b"name\n", DataLabDatasetIntakeErrorCode.EMPTY_DATASET),
        (b"name,name\nalice,bob\n", DataLabDatasetIntakeErrorCode.DUPLICATE_COLUMNS),
        (b"name,amount\nalice\n", DataLabDatasetIntakeErrorCode.MALFORMED_CSV),
        (b'name\n"unterminated\n', DataLabDatasetIntakeErrorCode.MALFORMED_CSV),
    ),
)
def test_rejects_invalid_csv_shapes_boundedly(
    tmp_path: Path,
    content: bytes,
    code: DataLabDatasetIntakeErrorCode,
) -> None:
    _assert_error(tmp_path, code, content)


def test_rejects_unsupported_media_without_http_behavior(tmp_path: Path) -> None:
    _assert_error(
        tmp_path,
        DataLabDatasetIntakeErrorCode.UNSUPPORTED_MEDIA,
        b"name\nalice\n",
        media_type="application/json",
    )


@pytest.mark.parametrize(
    "filename",
    (
        "",
        ".",
        "..",
        "../secret.csv",
        "/etc/passwd",
        "C:\\temp\\dataset.csv",
        "folder/dataset.csv",
        "folder\\dataset.csv",
        "bad\x00name.csv",
        "bad\nname.csv",
        "x" * 129,
        "password=not-for-display.csv",
    ),
)
def test_rejects_unsafe_filename_metadata_without_path_authority(
    tmp_path: Path,
    filename: str,
) -> None:
    with pytest.raises(DataLabDatasetIntakeError) as exc_info:
        _accept(tmp_path, filename=filename)

    assert exc_info.value.code is DataLabDatasetIntakeErrorCode.INVALID_FILENAME
    if filename:
        assert filename not in str(exc_info.value)


def test_normalizes_filename_to_nfc_metadata_only(tmp_path: Path) -> None:
    decomposed = "Cafe\u0301.csv"

    assert normalize_datalab_dataset_filename(decomposed) == "Café.csv"
    result = _accept(tmp_path, filename=decomposed)

    assert result.normalized_filename == "Café.csv"
    assert not (tmp_path / "stage" / "Café.csv").exists()
    assert (tmp_path / "stage" / f"{ARTIFACT_ID}.csv").read_bytes() == b"name,amount\nalice,10\n"


def test_reads_and_cleans_staged_bytes_without_replay_after_cleanup(tmp_path: Path) -> None:
    store = _store(tmp_path)
    result = store.accept_dataset(
        content=b"name\nalice\n",
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        client_filename="dataset.csv",
        producer_ref=_producer_ref(),
        artifact_id=ARTIFACT_ID,
        created_at=UTC_NOW,
    )

    assert store.read_staged_bytes(result.staged_locator) == b"name\nalice\n"

    store.cleanup_staged_bytes(result.staged_locator)
    store.cleanup_staged_bytes(result.staged_locator)

    with pytest.raises(DataLabDatasetIntakeError) as exc_info:
        store.read_staged_bytes(result.staged_locator)
    assert exc_info.value.code is DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE


def test_rejects_staging_locator_misuse_without_deleting_outside_files(tmp_path: Path) -> None:
    store = _store(tmp_path)
    outside = tmp_path / "outside.csv"
    outside.write_text("keep me", encoding="utf-8")

    with pytest.raises(DataLabDatasetIntakeError) as exc_info:
        store.cleanup_staged_bytes("../outside.csv")

    assert exc_info.value.code is DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE
    assert outside.read_text(encoding="utf-8") == "keep me"


def test_secret_shaped_csv_values_do_not_leak_in_errors(tmp_path: Path) -> None:
    sensitive_text = "api" + "_key" + "=" + "super-secret-value"
    with pytest.raises(DataLabDatasetIntakeError) as exc_info:
        _accept(tmp_path, f"name\n{sensitive_text},extra\n".encode())

    assert exc_info.value.code is DataLabDatasetIntakeErrorCode.MALFORMED_CSV
    assert sensitive_text not in str(exc_info.value)
    assert sensitive_text not in str(exc_info.value.to_json_compatible())


def test_rejects_embedded_newline_shape_mismatch_boundedly(tmp_path: Path) -> None:
    _assert_error(
        tmp_path,
        DataLabDatasetIntakeErrorCode.MALFORMED_CSV,
        b'name,notes\nalice,"line one\nline two",extra\n',
    )
