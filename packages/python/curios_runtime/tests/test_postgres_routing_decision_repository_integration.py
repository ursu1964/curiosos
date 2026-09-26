from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import DecisionId, ObservabilityContext, ProviderId, WorkId, WorkItem
from curios_persistence import PersistenceConfig, PersistenceError, PersistenceStore
from curios_runtime import (
    M1RoutingDecisionRepository,
    RoutingCandidate,
    select_m1_route,
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


def test_task_m1_010_routing_decision_repository_against_local_docker() -> None:
    from curios_runtime import RoutingDecisionRequest

    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m1_010_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    repository = M1RoutingDecisionRepository(store)

    try:
        _wait_for_store_initialization(store)
        _assert_routing_table_exists(config)

        work = WorkItem(
            work_id=fixed_id(WorkId),
            work_type="inspect_current_state",
            title="Inspect current state",
            objective="Inspect current state without execution.",
            created_at=UTC_NOW,
            updated_at=UTC_NOW,
        )
        request = RoutingDecisionRequest(
            decision_id=fixed_id(DecisionId),
            work=work,
            candidates=(
                RoutingCandidate.deterministic_executor(
                    work_id=work.work_id,
                    executor_name="deterministic_m1",
                    supported_work_types=("inspect_current_state",),
                ),
            ),
            requested_at=UTC_LATER,
            producer_ref=ref_for(ProviderId),
            observability_context=ObservabilityContext(work_id=work.work_id),
            resource_constraints={"local_only": True},
        )
        decision = select_m1_route(request)
        stored = repository.create_decision(decision)

        assert repository.read_decision(decision.decision_id) == stored
        assert repository.list_decisions(limit=10) == (stored,)

        store.dispose()
        restarted = PersistenceStore(config)
        try:
            recovered = M1RoutingDecisionRepository(restarted)
            assert recovered.read_decision(decision.decision_id) == stored
        finally:
            restarted.dispose()

        _assert_downgrade_minus_one_removes_only_routing_table(config)
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


def _assert_routing_table_exists(config: PersistenceConfig) -> None:
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = set(inspector.get_table_names(schema=config.schema))
        assert "curios_m1_routing_decision_records" in tables
    finally:
        engine.dispose()


def _assert_downgrade_minus_one_removes_only_routing_table(config: PersistenceConfig) -> None:
    from curios_persistence import apply_schema_migrations

    apply_schema_migrations(config, revision="-1")
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = set(inspector.get_table_names(schema=config.schema))
        assert "curios_m1_routing_decision_records" not in tables
        assert "curios_m1_agent_instance_records" in tables
        assert "curios_m1_work_dag_records" in tables
    finally:
        engine.dispose()
    apply_schema_migrations(config, revision="head")
    _assert_routing_table_exists(config)


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
