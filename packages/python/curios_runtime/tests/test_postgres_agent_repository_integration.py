from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import UTC_NOW, fixed_id
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    CapabilityId,
    ExecutionId,
    SchemaVersion,
    WorkId,
)
from curios_persistence import PersistenceConfig, PersistenceError, PersistenceStore
from curios_runtime import AgentRepositoryError, AgentRepositoryErrorCode, M1AgentRepository
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


def test_task_m1_006_agent_repository_against_local_docker() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m1_006_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    repository = M1AgentRepository(store)

    try:
        _wait_for_store_initialization(store)
        _assert_agent_tables_exist(config)

        definition = _definition()
        assert repository.read_definition(definition.agent_definition_id) is None
        stored_definition = repository.create_definition(definition)
        assert repository.read_definition(definition.agent_definition_id) == stored_definition
        assert repository.list_definitions(limit=10) == (stored_definition,)

        with pytest.raises(AgentRepositoryError) as duplicate_definition:
            repository.create_definition(definition)
        assert duplicate_definition.value.code is AgentRepositoryErrorCode.CONFLICT

        unknown_instance = _instance(definition_ordinal=1)
        with pytest.raises(AgentRepositoryError) as missing_definition:
            repository.create_instance(unknown_instance)
        assert missing_definition.value.code is AgentRepositoryErrorCode.NOT_FOUND

        instance = _instance()
        stored_instance = repository.create_instance(instance)
        assert repository.read_instance(instance.agent_instance_id) == stored_instance
        assert repository.list_instances(limit=10) == (stored_instance,)
        assert stored_instance.instance.work_id == fixed_id(WorkId)
        assert stored_instance.instance.execution_id == fixed_id(ExecutionId)
        assert stored_instance.instance.state is AgentInstanceState.CREATED

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            recovered = M1AgentRepository(restarted)
            assert recovered.read_definition(definition.agent_definition_id) == stored_definition
            assert recovered.read_instance(instance.agent_instance_id) == stored_instance
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


def _definition(ordinal: int = 0) -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId, ordinal=ordinal),
        name=f"local_agent_{ordinal}",
        version=SchemaVersion(1, 0, 0),
        purpose="Handle deterministic local assignment.",
        allowed_capability_ids=(fixed_id(CapabilityId, ordinal=ordinal),),
    )


def _instance(ordinal: int = 0, *, definition_ordinal: int = 0) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId, ordinal=ordinal),
        agent_definition_id=fixed_id(AgentDefinitionId, ordinal=definition_ordinal),
        work_id=fixed_id(WorkId, ordinal=ordinal),
        execution_id=fixed_id(ExecutionId, ordinal=ordinal),
        state=AgentInstanceState.CREATED,
        created_at=UTC_NOW,
    )


def _wait_for_store_initialization(store: PersistenceStore) -> None:
    last_error: PersistenceError | None = None
    for _ in range(30):
        try:
            store.initialize()
            return
        except PersistenceError as exc:
            last_error = exc
            time.sleep(1)
    assert last_error is not None
    raise last_error


def _assert_agent_tables_exist(config: PersistenceConfig) -> None:
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = set(inspector.get_table_names(schema=config.schema))
        assert {
            "curios_m1_agent_definition_records",
            "curios_m1_agent_instance_records",
        }.issubset(tables)
    finally:
        engine.dispose()


def _drop_schema(config: PersistenceConfig) -> None:
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{config.schema}" CASCADE'))
    finally:
        engine.dispose()


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


def _require_docker() -> None:
    result = subprocess.run(
        ("docker", "info"),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Docker is unavailable: {result.stderr.strip() or result.stdout.strip()}")


def _run_compose(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (*COMPOSE, *args),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
