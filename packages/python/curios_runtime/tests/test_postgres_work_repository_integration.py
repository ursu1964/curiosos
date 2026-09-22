from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    ExecutionId,
    ExecutionRecord,
    ExecutionState,
    ProviderId,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_persistence import (
    PersistenceConfig,
    PersistenceError,
    PersistenceErrorCode,
    PersistenceStore,
)
from curios_runtime import M0WorkRepository, RepositoryError, RepositoryErrorCode
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


def test_task_m0_005_work_repository_against_local_docker() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m0_005_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    repository = M0WorkRepository(store)

    try:
        _wait_for_store_initialization(store)

        assert repository.read_work(fixed_id(WorkId)) is None
        assert repository.read_execution(fixed_id(ExecutionId)) is None

        created_work = repository.create_work(_work())
        assert created_work.item.state is WorkItemState.CREATED

        duplicate_work = _work()
        with pytest.raises(RepositoryError) as duplicate:
            repository.create_work(duplicate_work)
        assert duplicate.value.code is RepositoryErrorCode.CONFLICT

        ready_work = repository.transition_work(
            created_work.item.work_id,
            WorkItemState.READY,
            occurred_at=UTC_LATER,
            expected_version=created_work.version,
        )
        assert ready_work.item.state is WorkItemState.READY
        assert ready_work.item.updated_at == UTC_LATER
        assert ready_work.version != created_work.version

        repeated_ready = repository.transition_work(
            ready_work.item.work_id,
            WorkItemState.READY,
            occurred_at=UTC_LATER,
            expected_version=ready_work.version,
        )
        assert repeated_ready == ready_work

        with pytest.raises(RepositoryError) as stale_transition:
            repository.transition_work(
                ready_work.item.work_id,
                WorkItemState.RUNNING,
                occurred_at=UTC_LATER,
                expected_version=created_work.version,
            )
        assert stale_transition.value.code is RepositoryErrorCode.CONFLICT

        running_work = repository.transition_work(
            ready_work.item.work_id,
            WorkItemState.RUNNING,
            occurred_at=UTC_LATER,
            expected_version=ready_work.version,
        )
        completed_work = repository.transition_work(
            running_work.item.work_id,
            WorkItemState.COMPLETED,
            occurred_at=UTC_LATER,
            expected_version=running_work.version,
        )
        assert completed_work.item.state is WorkItemState.COMPLETED

        with pytest.raises(RepositoryError) as illegal_work:
            repository.transition_work(
                completed_work.item.work_id,
                WorkItemState.RUNNING,
                occurred_at=UTC_LATER,
                expected_version=completed_work.version,
            )
        assert illegal_work.value.code is RepositoryErrorCode.ILLEGAL_TRANSITION

        created_execution = repository.create_execution(_execution())
        running_execution = repository.transition_execution(
            created_execution.record.execution_id,
            ExecutionState.RUNNING,
            occurred_at=UTC_LATER,
            expected_version=created_execution.version,
        )
        succeeded_execution = repository.transition_execution(
            running_execution.record.execution_id,
            ExecutionState.SUCCEEDED,
            occurred_at=UTC_LATER,
            expected_version=running_execution.version,
        )
        assert succeeded_execution.record.state is ExecutionState.SUCCEEDED
        assert succeeded_execution.record.ended_at == UTC_LATER

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            recovered = M0WorkRepository(restarted)
            assert recovered.read_work(fixed_id(WorkId)) == completed_work
            assert recovered.read_execution(fixed_id(ExecutionId)) == succeeded_execution
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


def _work() -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId),
        work_type="provider_inventory",
        title="Provider inventory",
        objective="Collect provider descriptors.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.CREATED,
    )


def _execution() -> ExecutionRecord:
    return ExecutionRecord(
        execution_id=fixed_id(ExecutionId),
        work_id=fixed_id(WorkId),
        executor_ref=ref_for(ProviderId),
        started_at=UTC_NOW,
        state=ExecutionState.CREATED,
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
    pytest.fail(f"PostgreSQL work repository did not initialize: {last_error!r}")


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
