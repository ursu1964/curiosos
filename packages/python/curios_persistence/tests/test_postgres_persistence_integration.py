from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import UTC_NOW, fixed_id
from curios_contracts import WorkId, WorkItem, WorkItemState
from curios_persistence import (
    PersistenceConfig,
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
    canonical_to_record,
    record_to_canonical,
)
from sqlalchemy import create_engine, inspect, text

REPO_ROOT = Path(__file__).resolve().parents[4]
COMPOSE_FILE = REPO_ROOT / "infrastructure/local/docker/compose.yaml"
ENV_FILE = REPO_ROOT / "infrastructure/local/docker/.env.example"
COMPOSE = (
    "docker",
    "compose",
    "--env-file",
    ENV_FILE.as_posix(),
    "-f",
    COMPOSE_FILE.as_posix(),
)
POSTGRES_VOLUME = "curios-local-docker_postgres_data"

pytestmark = pytest.mark.integration


def test_task_m0_002_persistence_boundary_against_local_docker() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m0_002_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)

    try:
        _wait_for_store_initialization(store)
        readiness = store.check_readiness()
        assert readiness["ready"] is True
        assert readiness["schema"] == schema

        work = WorkItem(
            work_id=fixed_id(WorkId),
            work_type="provider_inventory",
            title="Provider inventory",
            objective="Collect provider descriptors.",
            created_at=UTC_NOW,
            updated_at=UTC_NOW,
            state=WorkItemState.CREATED,
        )
        work_record = canonical_to_record(work)

        with store.transaction() as transaction:
            transaction.insert_record(work_record)
            assert transaction.count_records(PersistenceRecordKind.WORK) == 1

        with store.transaction() as transaction:
            recovered = transaction.read_record(PersistenceRecordKind.WORK, str(work.work_id))
            assert recovered is not None
            assert record_to_canonical(recovered) == work

        with (
            pytest.raises(RuntimeError, match="force rollback"),
            store.transaction() as transaction,
        ):
            transaction.insert_record(
                canonical_to_record(
                    WorkItem(
                        work_id=fixed_id(WorkId, ordinal=1),
                        work_type="provider_inventory",
                        title="Rolled back inventory",
                        objective="This row should roll back.",
                        created_at=UTC_NOW,
                        updated_at=UTC_NOW,
                    )
                )
            )
            raise RuntimeError("force rollback")

        with store.transaction() as transaction:
            assert transaction.count_records(PersistenceRecordKind.WORK) == 1

        expected_event_order = (
            "z_second_by_sort",
            "a_first_by_sort",
            "m_third_across_transactions",
            "c_fourth_after_failed_insert",
        )
        with store.transaction() as transaction:
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    expected_event_order[0],
                    {"position": 1},
                )
            )
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    expected_event_order[1],
                    {"position": 2},
                )
            )
            assert (
                tuple(
                    record.record_id
                    for record in transaction.list_records(PersistenceRecordKind.EVENT, limit=10)
                )
                == expected_event_order[:2]
            )

        with store.transaction() as transaction:
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    expected_event_order[2],
                    {"position": 3},
                )
            )

        with (
            pytest.raises(RuntimeError, match="force rollback"),
            store.transaction() as transaction,
        ):
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    "b_rolled_back_between_successful_inserts",
                    {"position": "rolled_back"},
                )
            )
            raise RuntimeError("force rollback")

        with pytest.raises(PersistenceError) as duplicate_event, store.transaction() as transaction:
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    expected_event_order[0],
                    {"position": "duplicate"},
                )
            )
        assert duplicate_event.value.code is PersistenceErrorCode.CONFLICT

        with store.transaction() as transaction:
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    expected_event_order[3],
                    {"position": 4},
                )
            )
            assert (
                tuple(
                    record.record_id
                    for record in transaction.list_records(PersistenceRecordKind.EVENT, limit=10)
                )
                == expected_event_order
            )

        with pytest.raises(PersistenceError) as duplicate, store.transaction() as transaction:
            transaction.insert_record(work_record)
        assert duplicate.value.code is PersistenceErrorCode.CONFLICT
        assert duplicate.value.to_json_compatible()["cause_type"] == "IntegrityError"

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            with restarted.transaction() as transaction:
                recovered = transaction.read_record(PersistenceRecordKind.WORK, str(work.work_id))
                assert recovered is not None
                assert record_to_canonical(recovered) == work
                assert (
                    tuple(
                        record.record_id
                        for record in transaction.list_records(
                            PersistenceRecordKind.EVENT, limit=10
                        )
                    )
                    == expected_event_order
                )
        finally:
            restarted.dispose()

        _assert_migration_downgrade_removes_record_tables(config)
    finally:
        store.dispose()
        _drop_schema(config)
        _run_compose("stop", "postgres")

    subprocess.run(
        ("docker", "volume", "inspect", POSTGRES_VOLUME),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_append_ordinal_migration_upgrades_existing_m0_002_rows() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m0_004_upgrade_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    expected_event_order = ("z_before_upgrade", "a_before_upgrade")

    try:
        _wait_for_migration(config, revision="0001_m0_runtime_records")
        with store.transaction() as transaction:
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    expected_event_order[0],
                    {"position": 1},
                )
            )
            transaction.insert_record(
                PersistenceRecord(
                    PersistenceRecordKind.EVENT,
                    expected_event_order[1],
                    {"position": 2},
                )
            )

        store.dispose()
        _wait_for_migration(config)

        upgraded = PersistenceStore(config)
        try:
            with upgraded.transaction() as transaction:
                assert (
                    tuple(
                        record.record_id
                        for record in transaction.list_records(
                            PersistenceRecordKind.EVENT, limit=10
                        )
                    )
                    == expected_event_order
                )
        finally:
            upgraded.dispose()
    finally:
        store.dispose()
        _drop_schema(config)
        _run_compose("stop", "postgres")

    subprocess.run(
        ("docker", "volume", "inspect", POSTGRES_VOLUME),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _wait_for_store_initialization(store: PersistenceStore) -> None:
    deadline = time.monotonic() + 75
    last_error: object | None = None
    while time.monotonic() < deadline:
        try:
            store.initialize()
            return
        except PersistenceError as exc:
            last_error = exc.to_json_compatible()
            if exc.code is not PersistenceErrorCode.CONNECTIVITY:
                raise
            time.sleep(1)
    pytest.fail(f"PostgreSQL persistence did not initialize: {last_error!r}")


def _wait_for_migration(config: PersistenceConfig, *, revision: str = "head") -> None:
    from curios_persistence import apply_schema_migrations

    deadline = time.monotonic() + 75
    last_error: object | None = None
    while time.monotonic() < deadline:
        try:
            apply_schema_migrations(config, revision=revision)
            return
        except PersistenceError as exc:
            last_error = exc.to_json_compatible()
            if exc.code is not PersistenceErrorCode.CONNECTIVITY:
                raise
            time.sleep(1)
    pytest.fail(f"PostgreSQL persistence migration did not complete: {last_error!r}")


def _assert_migration_downgrade_removes_record_tables(config: PersistenceConfig) -> None:
    from curios_persistence import apply_schema_migrations

    apply_schema_migrations(config, revision="base")
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            assert not [
                table
                for table in inspector.get_table_names(schema=config.schema)
                if table.startswith(("curios_m0_", "curios_m1_"))
            ]
    finally:
        engine.dispose()


def _drop_schema(config: PersistenceConfig) -> None:
    if config.schema is None:
        return
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{config.schema}" CASCADE'))
    finally:
        engine.dispose()


def _require_docker() -> None:
    try:
        subprocess.run(
            ("docker", "info"),
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"Docker daemon is unavailable: {exc}")


def _run_compose(*args: str) -> None:
    subprocess.run(
        (*COMPOSE, *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _postgres_url() -> str:
    user = quote(_env_value("CURIOS_POSTGRES_USER"), safe="")
    credential = quote(_env_value("CURIOS_POSTGRES_PASSWORD"), safe="")
    host = os.environ.get("CURIOS_POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("CURIOS_POSTGRES_PORT", _env_value("CURIOS_POSTGRES_PORT"))
    database = quote(_env_value("CURIOS_POSTGRES_DB"), safe="")
    return f"postgresql+psycopg://{user}:{credential}@{host}:{port}/{database}"


def _env_value(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    prefix = f"{name}="
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    msg = f"missing {name}"
    raise RuntimeError(msg)
