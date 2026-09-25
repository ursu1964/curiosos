from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import UTC_NOW, fixed_id
from curios_contracts import WorkId, WorkItem
from curios_dag import M1WorkDagRepository, WorkDag, WorkDagError, WorkDagErrorCode, WorkDagId
from curios_persistence import (
    PersistenceConfig,
    PersistenceError,
    PersistenceErrorCode,
    PersistenceStore,
)
from sqlalchemy import create_engine, text

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


def test_task_m1_004_work_dag_repository_against_local_docker() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m1_004_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    repository = M1WorkDagRepository(store)

    try:
        _wait_for_store_initialization(store)

        assert repository.read_dag(_dag_id()) is None

        dag = WorkDag.from_work_items(
            _dag_id(),
            (_work(0), _work(1, dependencies=(fixed_id(WorkId),))),
            created_at=UTC_NOW,
        )
        created = repository.create_dag(dag)
        assert created.dag == dag

        with pytest.raises(WorkDagError) as duplicate:
            repository.create_dag(dag)
        assert duplicate.value.code is WorkDagErrorCode.CONFLICT

        assert repository.read_dag(_dag_id()) == created
        assert repository.list_dags(limit=10) == (created,)

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            recovered = M1WorkDagRepository(restarted)
            assert recovered.read_dag(_dag_id()) == created
            assert recovered.list_dags(limit=10) == (created,)
        finally:
            restarted.dispose()
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


def _dag_id() -> WorkDagId:
    return fixed_id(WorkDagId)


def _work(ordinal: int, *, dependencies: tuple[WorkId, ...] = ()) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal),
        work_type="m1_dag_test",
        title=f"M1 DAG test work {ordinal}",
        objective="Exercise bounded M1 work DAG persistence.",
        dependencies=dependencies,
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
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
    pytest.fail(f"PostgreSQL work DAG repository did not initialize: {last_error!r}")


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
