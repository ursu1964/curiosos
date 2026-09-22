from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import SCHEMA_V1, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    CorrelationId,
    EventEnvelope,
    EventId,
    EvidenceId,
    EvidenceKind,
    EvidenceReference,
    ExecutionId,
    ObservabilityContext,
    ProjectId,
    RuntimeEventType,
    TraceId,
    WorkId,
)
from curios_persistence import (
    PersistenceConfig,
    PersistenceError,
    PersistenceErrorCode,
    PersistenceStore,
)
from curios_runtime import EventEvidenceRuntimeStore, RuntimeStoreError, RuntimeStoreErrorCode
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


def test_task_m0_004_event_evidence_store_against_local_docker() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m0_004_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    persistence = PersistenceStore(config)
    store = EventEvidenceRuntimeStore(persistence)
    event = _event()
    evidence = _evidence()

    try:
        _wait_for_store_initialization(persistence)

        assert store.append_event(event) == event
        assert store.append_evidence(evidence) == evidence
        assert store.require_event(event.event_id) == event
        assert store.require_evidence(evidence.evidence_id) == evidence
        assert store.list_events(limit=10) == (event,)
        assert store.list_evidence(limit=10) == (evidence,)

        stored_hash = _single_value(
            config,
            """
            SELECT payload_sha256
            FROM curios_m0_event_records
            WHERE canonical_id = :canonical_id
            """,
            {"canonical_id": str(event.event_id)},
        )
        assert isinstance(stored_hash, str)
        assert len(stored_hash) == 64

        persistence.dispose()
        restarted_persistence = PersistenceStore(config)
        restarted = EventEvidenceRuntimeStore(restarted_persistence)
        try:
            assert restarted.require_event(event.event_id) == event
            assert restarted.require_evidence(evidence.evidence_id) == evidence
        finally:
            restarted_persistence.dispose()

        _single_value(
            config,
            """
            UPDATE curios_m0_event_records
            SET payload = jsonb_set(
                payload,
                '{payload,evidence_id}',
                '"evd_0000000000000000000000001"'
            )
            WHERE canonical_id = :canonical_id
            RETURNING canonical_id
            """,
            {"canonical_id": str(event.event_id)},
        )

        corrupted_persistence = PersistenceStore(config)
        corrupted_store = EventEvidenceRuntimeStore(corrupted_persistence)
        try:
            with pytest.raises(RuntimeStoreError) as corrupt:
                corrupted_store.require_event(event.event_id)
            assert corrupt.value.code is RuntimeStoreErrorCode.CORRUPT_RECORD
            assert corrupt.value.__cause__ is None
        finally:
            corrupted_persistence.dispose()
    finally:
        persistence.dispose()
        _drop_schema(config)
        _run_compose("stop", "postgres")

    subprocess.run(
        ("docker", "volume", "inspect", POSTGRES_VOLUME),
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _event() -> EventEnvelope:
    return EventEnvelope(
        event_id=fixed_id(EventId),
        event_type=RuntimeEventType.EVIDENCE_PRODUCED.value,
        schema_version=SCHEMA_V1,
        occurred_at=UTC_NOW,
        producer=ref_for(ProjectId),
        subject_ref=ref_for(WorkId),
        observability_context=ObservabilityContext(
            project_id=fixed_id(ProjectId),
            work_id=fixed_id(WorkId),
            execution_id=fixed_id(ExecutionId),
            trace_id=fixed_id(TraceId),
            correlation_id=fixed_id(CorrelationId),
        ),
        payload={"evidence_id": str(fixed_id(EvidenceId))},
        metadata={"source": "runtime-store-postgres"},
    )


def _evidence() -> EvidenceReference:
    return EvidenceReference(
        evidence_id=fixed_id(EvidenceId),
        kind=EvidenceKind.INSPECTION,
        subject_ref=ref_for(WorkId),
        collected_at=UTC_NOW,
        summary="Runtime store PostgreSQL evidence.",
        trace_id=fixed_id(TraceId),
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


def _single_value(
    config: PersistenceConfig,
    statement: str,
    parameters: dict[str, object],
) -> object:
    engine = create_engine(config.sqlalchemy_url, future=True)
    try:
        with engine.begin() as connection:
            if config.schema is not None:
                connection.execute(text(f'SET search_path TO "{config.schema}"'))
            result = connection.execute(text(statement), parameters)
            return result.scalar_one()
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
