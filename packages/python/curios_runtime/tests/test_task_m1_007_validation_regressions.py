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
    AgentDefinition,
    AgentDefinitionId,
    AgentInstance,
    AgentInstanceId,
    AgentInstanceState,
    ApplicationId,
    CapabilityId,
    EventId,
    ExecutionId,
    ObjectReference,
    ProjectId,
    SchemaVersion,
    UtcTimestamp,
    WorkId,
)
from curios_persistence import PersistenceConfig, PersistenceError, PersistenceStore
from curios_runtime import (
    AGENT_INSTANCE_TRANSITIONS,
    AgentLifecycleError,
    AgentLifecycleErrorCode,
    EventEvidenceRuntimeStore,
    M1AgentLifecycleRepository,
    M1AgentRepository,
    agent_lifecycle_event,
    transition_agent_instance,
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

pytestmark = pytest.mark.integration


def test_task_m1_007_validation_exhaustive_state_pair_semantics() -> None:
    all_states = tuple(AgentInstanceState)

    for source in all_states:
        for target in all_states:
            instance = _instance(state=source)
            if source is target:
                assert (
                    transition_agent_instance(
                        instance,
                        target,
                        occurred_at=UTC_LATER,
                    )
                    is instance
                )
            elif target in AGENT_INSTANCE_TRANSITIONS[source]:
                transitioned = transition_agent_instance(
                    instance,
                    target,
                    occurred_at=UTC_LATER,
                )
                assert transitioned.state is target
                assert transitioned.agent_instance_id == instance.agent_instance_id
                assert transitioned.agent_definition_id == instance.agent_definition_id
                assert transitioned.work_id == instance.work_id
                assert transitioned.execution_id == instance.execution_id
            else:
                with pytest.raises(AgentLifecycleError) as exc:
                    transition_agent_instance(
                        instance,
                        target,
                        occurred_at=UTC_LATER,
                    )
                assert exc.value.code is AgentLifecycleErrorCode.ILLEGAL_TRANSITION


def test_task_m1_007_validation_event_shape_and_two_agent_identity() -> None:
    first = _instance(ordinal=0, state=AgentInstanceState.CREATED)
    first_ready = _instance(ordinal=0, state=AgentInstanceState.READY)
    second = _instance(ordinal=1, state=AgentInstanceState.CREATED)
    second_ready = _instance(ordinal=1, state=AgentInstanceState.READY)

    first_event = agent_lifecycle_event(
        first,
        first_ready,
        event_id=fixed_id(EventId),
        occurred_at=UTC_NOW,
        causation_ref=ref_for(EventId, 2),
    )
    second_event = agent_lifecycle_event(
        second,
        second_ready,
        event_id=fixed_id(EventId, 1),
        occurred_at=UTC_NOW,
    )

    assert first_event.event_type == "agent.lifecycle.transitioned"
    assert first_event.subject_ref == ObjectReference.from_id(first.agent_instance_id)
    assert first_event.producer == ObjectReference.from_id(first.agent_instance_id)
    assert first_event.observability_context.agent_instance_id == first.agent_instance_id
    assert first_event.observability_context.work_id == first.work_id
    assert first_event.observability_context.execution_id == first.execution_id
    assert first_event.observability_context.causation_ref == ref_for(EventId, 2)
    assert first_event.payload["source_state"] == "CREATED"
    assert first_event.payload["target_state"] == "READY"
    assert {"work_type", "dependencies", "executor_ref", "provider_refs"}.isdisjoint(
        first_event.payload
    )
    assert second_event.subject_ref == ObjectReference.from_id(second.agent_instance_id)
    assert first_event.subject_ref != second_event.subject_ref


def test_task_m1_007_validation_postgres_event_conflict_rolls_back_and_retry_succeeds() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m1_007_validation_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    agents = M1AgentRepository(store)
    lifecycle = M1AgentLifecycleRepository(store)
    events = EventEvidenceRuntimeStore(store)

    try:
        _wait_for_store_initialization(store)
        agents.create_definition(_definition())
        agents.create_instance(_instance(state=AgentInstanceState.CREATED))

        duplicate_event = agent_lifecycle_event(
            _instance(state=AgentInstanceState.CREATED),
            _instance(state=AgentInstanceState.READY),
            event_id=fixed_id(EventId),
            occurred_at=UTC_NOW,
        )
        events.append_event(duplicate_event)

        with pytest.raises(AgentLifecycleError) as conflict:
            lifecycle.transition_instance(
                fixed_id(AgentInstanceId),
                AgentInstanceState.READY,
                event_id=fixed_id(EventId),
                occurred_at=UTC_LATER,
            )

        assert conflict.value.code is AgentLifecycleErrorCode.CONFLICT
        unchanged = agents.read_instance(fixed_id(AgentInstanceId))
        assert unchanged is not None
        assert unchanged.instance.state is AgentInstanceState.CREATED
        assert tuple(event.event_id for event in events.list_events(limit=10)) == (
            fixed_id(EventId),
        )

        retried = lifecycle.transition_instance(
            fixed_id(AgentInstanceId),
            AgentInstanceState.READY,
            event_id=fixed_id(EventId, 1),
            occurred_at=UTC_LATER,
        )

        assert retried.changed is True
        assert retried.instance.state is AgentInstanceState.READY
        assert retried.event is not None
        assert tuple(event.event_id for event in events.list_events(limit=10)) == (
            fixed_id(EventId),
            fixed_id(EventId, 1),
        )
    finally:
        store.dispose()
        _drop_schema(config)
        _run_compose("stop", "postgres")


def _definition() -> AgentDefinition:
    return AgentDefinition(
        agent_definition_id=fixed_id(AgentDefinitionId),
        name="validation_agent",
        version=SchemaVersion(1, 0, 0),
        purpose="Validate deterministic M1 agent lifecycle behavior.",
        allowed_capability_ids=(fixed_id(CapabilityId),),
    )


def _instance(
    *,
    ordinal: int = 0,
    state: AgentInstanceState = AgentInstanceState.CREATED,
    execution: bool = True,
    started_at: UtcTimestamp | None = None,
    ended_at: UtcTimestamp | None = None,
) -> AgentInstance:
    return AgentInstance(
        agent_instance_id=fixed_id(AgentInstanceId, ordinal),
        agent_definition_id=fixed_id(AgentDefinitionId),
        work_id=fixed_id(WorkId, ordinal),
        execution_id=fixed_id(ExecutionId, ordinal) if execution else None,
        state=state,
        created_at=UTC_NOW,
        started_at=started_at,
        ended_at=ended_at,
        authority_ref=ref_for(ProjectId),
        principal_ref=ref_for(ApplicationId),
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
