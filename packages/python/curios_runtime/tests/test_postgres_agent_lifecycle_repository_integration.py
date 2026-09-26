from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id
from curios_contracts import (
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    CapabilityId,
    EventId,
    ExecutionId,
    SchemaVersion,
    WorkId,
)
from curios_persistence import PersistenceConfig, PersistenceError, PersistenceStore
from curios_runtime import (
    EventEvidenceRuntimeStore,
    M1AgentLifecycleRepository,
    M1AgentRepository,
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


def test_task_m1_007_agent_lifecycle_repository_against_local_docker() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m1_007_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    agents = M1AgentRepository(store)
    lifecycle = M1AgentLifecycleRepository(store)
    events = EventEvidenceRuntimeStore(store)

    try:
        _wait_for_store_initialization(store)
        agents.create_definition(_definition())
        agents.create_instance(_instance())

        ready = lifecycle.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
        )
        active = lifecycle.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.ACTIVE,
            event_id=fixed_id(EventId, ordinal=1),
            occurred_at=UTC_LATER,
        )

        persisted = agents.read_instance(fixed_id(AgentInstanceId))
        assert persisted is not None
        assert persisted.instance == active.instance
        assert active.instance.state is AgentInstanceState.ACTIVE
        assert active.instance.started_at == UTC_LATER
        assert active.instance.execution_id == fixed_id(ExecutionId)

        assert ready.event is not None
        assert active.event is not None
        assert events.get_event(ready.event.event_id) == ready.event
        assert events.get_event(active.event.event_id) == active.event
        assert tuple(event.event_type for event in events.list_events(limit=10)) == (
            "agent.lifecycle.transitioned",
            "agent.lifecycle.transitioned",
        )

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            recovered_agents = M1AgentRepository(restarted)
            recovered_events = EventEvidenceRuntimeStore(restarted)
            recovered = recovered_agents.read_instance(fixed_id(AgentInstanceId))
            assert recovered is not None
            assert recovered.instance == active.instance
            assert recovered_events.get_event(active.event.event_id) == active.event
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


def _definition() -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId),
        name="local_agent",
        version=SchemaVersion(1, 0, 0),
        purpose="Handle deterministic local assignment.",
        allowed_capability_ids=(fixed_id(CapabilityId),),
    )


def _instance() -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=fixed_id(WorkId),
        execution_id=fixed_id(ExecutionId),
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
