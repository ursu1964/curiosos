from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest
from curios_contracts import (
    ArtifactId,
    CorrelationId,
    DataLabAnalysisId,
    DataLabAnalysisKind,
    DataLabAnalysisRequest,
    DatasetColumnProfile,
    DatasetPrimitiveType,
    DatasetProfile,
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
    DATALAB_MAX_FILENAME_CHARS,
    DATALAB_MAX_UPLOAD_BYTES,
    DataLabDatasetIntakeError,
    DataLabDatasetIntakeErrorCode,
    DataLabDatasetIntakeResult,
    LocalDataLabDatasetStagingStore,
)

UTC_NOW = UtcTimestamp.parse("2026-09-28T10:00:00Z")
FIXED_ARTIFACT_ID = ArtifactId("art_0123456789ABCDEFGHJKMNPQRS")


def _producer_ref() -> ObjectReference:
    return ObjectReference.from_id(ProjectId.generate())


def _artifact(suffix: str) -> ArtifactId:
    return ArtifactId(f"art_0123456789ABCDEFGHJKMNPQ{suffix}")


def _store(tmp_path: Path) -> LocalDataLabDatasetStagingStore:
    return LocalDataLabDatasetStagingStore(tmp_path / "stage")


def _accept(
    tmp_path: Path,
    content: bytes,
    *,
    filename: str = "dataset.csv",
    artifact_id: ArtifactId = FIXED_ARTIFACT_ID,
) -> DataLabDatasetIntakeResult:
    return _store(tmp_path).accept_dataset(
        content=content,
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        client_filename=filename,
        producer_ref=_producer_ref(),
        artifact_id=artifact_id,
        created_at=UTC_NOW,
    )


def _expect_code(
    tmp_path: Path,
    content: bytes,
    code: DataLabDatasetIntakeErrorCode,
    *,
    filename: str = "dataset.csv",
) -> None:
    with pytest.raises(DataLabDatasetIntakeError) as exc_info:
        _accept(tmp_path, content, filename=filename)
    assert exc_info.value.code is code


def _exact_upload_size_csv(size: int) -> bytes:
    content = bytearray(b"c\n")
    remaining = size - len(content)
    while remaining > DATALAB_MAX_CELL_BYTES + 1:
        content.extend(b"x" * DATALAB_MAX_CELL_BYTES + b"\n")
        remaining -= DATALAB_MAX_CELL_BYTES + 1
    content.extend(b"y" * (remaining - 1) + b"\n")
    assert len(content) == size
    return bytes(content)


def test_validation_regression_exact_upload_bounds_and_sha(tmp_path: Path) -> None:
    below = _exact_upload_size_csv(DATALAB_MAX_UPLOAD_BYTES - 1)
    exact = _exact_upload_size_csv(DATALAB_MAX_UPLOAD_BYTES)

    assert _accept(tmp_path, below).size_bytes == DATALAB_MAX_UPLOAD_BYTES - 1
    exact_result = _accept(tmp_path, exact)
    assert exact_result.size_bytes == DATALAB_MAX_UPLOAD_BYTES
    assert exact_result.dataset_integrity_sha256 == hashlib.sha256(exact).hexdigest()
    assert exact_result.artifact_ref.integrity is not None
    assert exact_result.artifact_ref.integrity.algorithm is IntegrityAlgorithm.SHA256
    _expect_code(
        tmp_path,
        exact + b"x",
        DataLabDatasetIntakeErrorCode.UPLOAD_TOO_LARGE,
    )


def test_validation_regression_utf8_bom_and_logical_csv_rows(tmp_path: Path) -> None:
    bom_payload = b'\xef\xbb\xbfname,note\nAlice,"line 1\nline 2"\n'
    result = _accept(tmp_path, bom_payload)

    assert result.data_row_count == 1
    assert result.column_count == 2
    assert result.dataset_integrity_sha256 == hashlib.sha256(bom_payload).hexdigest()
    _expect_code(
        tmp_path,
        b"name\n\xe2\x82\n",
        DataLabDatasetIntakeErrorCode.INVALID_ENCODING,
    )
    _expect_code(
        tmp_path,
        b'name\n"unterminated\n',
        DataLabDatasetIntakeErrorCode.MALFORMED_CSV,
    )


def test_validation_regression_column_row_and_cell_edges(tmp_path: Path) -> None:
    hundred_columns = (
        ",".join(f"c{index}" for index in range(DATALAB_MAX_COLUMNS))
        + "\n"
        + ",".join("x" for _ in range(DATALAB_MAX_COLUMNS))
        + "\n"
    ).encode()
    hundred_one_columns = hundred_columns.replace(b"c99\n", b"c99,c100\n").replace(
        b"x\n",
        b"x,x\n",
    )
    assert _accept(tmp_path, hundred_columns).column_count == DATALAB_MAX_COLUMNS
    _expect_code(
        tmp_path,
        hundred_one_columns,
        DataLabDatasetIntakeErrorCode.TOO_MANY_COLUMNS,
    )

    max_rows = ("c\n" + "1\n" * DATALAB_MAX_DATA_ROWS).encode()
    assert _accept(tmp_path, max_rows).data_row_count == DATALAB_MAX_DATA_ROWS
    _expect_code(
        tmp_path,
        max_rows + b"1\n",
        DataLabDatasetIntakeErrorCode.TOO_MANY_ROWS,
    )

    max_multibyte_cell = ("c\n" + ("é" * (DATALAB_MAX_CELL_BYTES // 2)) + "\n").encode()
    over_multibyte_cell = ("c\n" + ("é" * (DATALAB_MAX_CELL_BYTES // 2 + 1)) + "\n").encode()
    assert _accept(tmp_path, max_multibyte_cell).data_row_count == 1
    _expect_code(
        tmp_path,
        over_multibyte_cell,
        DataLabDatasetIntakeErrorCode.CELL_TOO_LARGE,
    )


def test_validation_regression_filename_path_forms_and_non_authority(
    tmp_path: Path,
) -> None:
    exact_name = "x" * DATALAB_MAX_FILENAME_CHARS
    accepted = _accept(tmp_path, b"c\n1\n", filename=exact_name)
    assert accepted.normalized_filename == exact_name

    for filename in (
        "",
        "x" * (DATALAB_MAX_FILENAME_CHARS + 1),
        "bad\x00.csv",
        "bad\n.csv",
        "/etc/passwd",
        "C:\\dataset.csv",
        "\\\\server\\share.csv",
        "../x",
        "..\\x",
    ):
        with pytest.raises(DataLabDatasetIntakeError) as exc_info:
            _accept(tmp_path, b"c\n1\n", filename=filename)
        assert exc_info.value.code is DataLabDatasetIntakeErrorCode.INVALID_FILENAME
        if filename:
            assert filename not in str(exc_info.value)

    client_a = _accept(
        tmp_path,
        b"c\n1\n",
        filename="ordinary.csv",
        artifact_id=_artifact("RT"),
    )
    client_b = _accept(
        tmp_path,
        b"c\n1\n",
        filename="unicode 名.csv",
        artifact_id=_artifact("RV"),
    )
    assert "ordinary.csv" not in client_a.staged_locator
    assert "unicode" not in client_b.staged_locator
    assert (tmp_path / "stage" / f"{client_a.artifact_ref.artifact_id}.csv").exists()
    assert not (tmp_path / "stage" / client_a.normalized_filename).exists()


def test_validation_regression_staging_containment_cleanup_and_replay(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    outside = tmp_path / "outside.csv"
    outside.write_text("outside", encoding="utf-8")
    first = store.accept_dataset(
        content=b"c\n1\n",
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        client_filename="first.csv",
        producer_ref=_producer_ref(),
        artifact_id=_artifact("RT"),
        created_at=UTC_NOW,
    )
    second = store.accept_dataset(
        content=b"c\n2\n",
        media_type=DATALAB_DATASET_MEDIA_TYPE,
        client_filename="second.csv",
        producer_ref=_producer_ref(),
        artifact_id=_artifact("RV"),
        created_at=UTC_NOW,
    )

    assert store.read_staged_bytes(first.staged_locator) == b"c\n1\n"
    assert store.read_staged_bytes(second.staged_locator) == b"c\n2\n"

    store.cleanup_staged_bytes(first.staged_locator)
    store.cleanup_staged_bytes(first.staged_locator)

    with pytest.raises(DataLabDatasetIntakeError) as exc_info:
        store.read_staged_bytes(first.staged_locator)
    assert exc_info.value.code is DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE
    assert store.read_staged_bytes(second.staged_locator) == b"c\n2\n"

    with pytest.raises(DataLabDatasetIntakeError) as bad_locator:
        store.cleanup_staged_bytes("../outside.csv")
    assert bad_locator.value.code is DataLabDatasetIntakeErrorCode.DATASET_UNAVAILABLE
    assert outside.read_text(encoding="utf-8") == "outside"

    restarted_store = LocalDataLabDatasetStagingStore(tmp_path / "stage")
    assert restarted_store.read_staged_bytes(second.staged_locator) == b"c\n2\n"


def test_validation_regression_m2_002_contract_compatibility(tmp_path: Path) -> None:
    result = _accept(tmp_path, b"c\n1\n")
    request = DataLabAnalysisRequest(
        analysis_id=DataLabAnalysisId.generate(),
        dataset_ref=result.artifact_ref,
        dataset_integrity_sha256=result.dataset_integrity_sha256,
        objective="PROFILE_DATASET",
        analysis_kind=DataLabAnalysisKind.PROFILE_DATASET,
        created_at=UTC_NOW,
        correlation_id=CorrelationId.generate(),
    )
    profile = DatasetProfile(
        dataset_ref=result.artifact_ref,
        dataset_integrity_sha256=result.dataset_integrity_sha256,
        row_count=1,
        column_count=1,
        columns=(
            DatasetColumnProfile(
                name="c",
                index=0,
                inferred_type=DatasetPrimitiveType.STRING,
                missing_count=0,
                non_missing_count=1,
                distinct_count=1,
            ),
        ),
    )

    assert request.dataset_ref == result.artifact_ref
    assert profile.dataset_ref == result.artifact_ref


def test_validation_regression_errors_do_not_echo_unsafe_input(tmp_path: Path) -> None:
    unsafe_value = "api" + "_key" + "=" + "super-secret-value"

    with pytest.raises(DataLabDatasetIntakeError) as csv_error:
        _accept(tmp_path, f"c\n{unsafe_value},extra\n".encode())
    assert csv_error.value.code is DataLabDatasetIntakeErrorCode.MALFORMED_CSV
    assert unsafe_value not in str(csv_error.value)
    assert unsafe_value not in str(csv_error.value.to_json_compatible())

    unsafe_filename = "../" + "password" + "=" + "super-secret-value.csv"
    with pytest.raises(DataLabDatasetIntakeError) as filename_error:
        _accept(tmp_path, b"c\n1\n", filename=unsafe_filename)
    assert filename_error.value.code is DataLabDatasetIntakeErrorCode.INVALID_FILENAME
    assert unsafe_filename not in str(filename_error.value)


def test_validation_regression_runtime_intake_has_no_forbidden_authority_imports() -> None:
    source = Path("packages/python/curios_runtime/src/curios_runtime/datalab_dataset_intake.py")
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            match node.func:
                case ast.Name(id=name):
                    call_names.add(name)
                case ast.Attribute(attr=attr):
                    call_names.add(attr)

    assert imported_modules.isdisjoint(
        {
            "aiohttp",
            "boto3",
            "httpx",
            "importlib",
            "ollama",
            "openai",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
    )
    assert call_names.isdisjoint({"eval", "exec", "__import__", "system", "popen", "run"})
