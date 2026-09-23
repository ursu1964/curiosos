from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import pytest
from contract_fixtures import fixed_id, human_principal, ref_for
from curios_api import create_api_composition, create_application, create_m0_work_api_composition
from curios_contracts import (
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    Result,
    SchemaVersion,
)
from curios_core import CoreContext
from curios_persistence import (
    PersistenceConfig,
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecordKind,
    PersistenceStore,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[2]
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


def test_m0_provider_inventory_slice_persists_and_recovers_runtime_truth() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m0_010_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    descriptors = (_descriptor(ordinal=2), _descriptor(ordinal=1))
    success_catalog = _Catalog(Result.success(descriptors))

    try:
        _wait_for_store_initialization(store)

        app = _app(store, success_catalog)
        with TestClient(app) as client:
            first = _create_and_run_provider_inventory(client, title="Inventory providers A")
            second = _create_and_run_provider_inventory(client, title="Inventory providers B")

            unknown = _create_work(client, title="Blocked unknown policy")
            unknown_response = client.post(
                f"/work/{unknown['work_id']}/run",
                json={"policy_state_known": False},
            )

            unsupported = _create_work(client, title="Blocked unsupported effect")
            unsupported_response = client.post(
                f"/work/{unsupported['work_id']}/run",
                json={"requested_effects": ["EXTERNAL_READ"]},
            )

            first_work = client.get(f"/work/{first['work_id']}")
            first_execution = client.get(
                f"/work/{first['work_id']}/executions/{first['execution_id']}"
            )
            first_events = client.get(f"/work/{first['work_id']}/events")
            first_evidence = client.get(f"/work/{first['work_id']}/evidence")
            second_events = client.get(f"/work/{second['work_id']}/events")
            second_evidence = client.get(f"/work/{second['work_id']}/evidence")
            cross_execution = client.get(
                f"/work/{second['work_id']}/executions/{first['execution_id']}"
            )

        assert success_catalog.calls == 2
        assert first["status"] == "COMPLETED"
        assert first["work"]["state"] == "COMPLETED"
        assert first["execution"]["state"] == "SUCCEEDED"
        assert first["executor_result"]["status"] == "success"
        assert first["executor_result"]["value"] == {
            "work_type": "provider_inventory",
            "provider_count": 2,
            "providers": [
                _descriptor(ordinal=1).to_json_compatible(),
                _descriptor(ordinal=2).to_json_compatible(),
            ],
        }
        assert first_work.json()["work"]["state"] == "COMPLETED"
        assert first_execution.json()["execution"]["state"] == "SUCCEEDED"
        assert _event_types(first_events) == (
            "policy.evaluated",
            "execution.started",
            "evidence.produced",
            "execution.completed",
        )
        assert first_evidence.json()["evidence"][0]["kind"] == "provider_report"
        assert _event_work_ids(first_events) == (first["work_id"],) * 4
        assert _event_work_ids(second_events) == (second["work_id"],) * 4
        assert _evidence_work_ids(first_evidence) == (first["work_id"],)
        assert _evidence_work_ids(second_evidence) == (second["work_id"],)
        assert cross_execution.status_code == 404

        assert unknown_response.status_code == 403
        assert unknown_response.json()["detail"]["status"] == "BLOCKED"
        assert unknown_response.json()["detail"]["policy_decision"]["outcome"] == "UNKNOWN"
        assert unsupported_response.status_code == 403
        assert unsupported_response.json()["detail"]["status"] == "BLOCKED"
        assert unsupported_response.json()["detail"]["policy_decision"]["outcome"] == "DENY"
        assert success_catalog.calls == 2

        failure_store = PersistenceStore(config)
        failure_catalog = _Catalog(Result.failure((_provider_failure(),)))
        try:
            failure_app = _app(failure_store, failure_catalog)
            with TestClient(failure_app) as client:
                failing_work = _create_work(client, title="Provider failure")
                failure_response = client.post(f"/work/{failing_work['work_id']}/run")
                failed_work = client.get(f"/work/{failing_work['work_id']}")
                failed_events = client.get(f"/work/{failing_work['work_id']}/events")
        finally:
            failure_store.dispose()

        assert failure_response.status_code == 502
        failure_detail = failure_response.json()["detail"]
        assert failure_detail["status"] == "FAILED"
        assert failure_detail["executor_result"]["status"] == "failure"
        assert failure_detail["executor_result"]["errors"][0]["error_code"] == (
            "PROVIDER_INVENTORY_CATALOG_FAILURE"
        )
        assert failed_work.json()["work"]["state"] == "FAILED"
        assert "sqlalchemy" not in json.dumps(failure_detail).lower()
        assert "psycopg" not in json.dumps(failure_detail).lower()
        assert "traceback" not in json.dumps(failure_detail).lower()
        assert _event_work_ids(failed_events) == (failing_work["work_id"],) * 3

        _assert_record_counts(
            store,
            expected_work=5,
            expected_execution=3,
            expected_evidence=2,
        )

        store.dispose()
        recovered_store = PersistenceStore(config)
        try:
            recovered_app = _app(recovered_store, _Catalog(Result.success(descriptors)))
            with TestClient(recovered_app) as client:
                recovered_work = client.get(f"/work/{first['work_id']}")
                recovered_execution = client.get(
                    f"/work/{first['work_id']}/executions/{first['execution_id']}"
                )
                recovered_events = client.get(f"/work/{first['work_id']}/events")
                recovered_evidence = client.get(f"/work/{first['work_id']}/evidence")

            assert recovered_work.status_code == 200
            assert recovered_work.json()["work"]["state"] == "COMPLETED"
            assert recovered_execution.json()["execution"]["state"] == "SUCCEEDED"
            assert _event_types(recovered_events) == _event_types(first_events)
            assert recovered_evidence.json() == first_evidence.json()
        finally:
            recovered_store.dispose()
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


def test_m0_web_api_boundary_matches_frozen_work_routes() -> None:
    app_routes = {
        (route.path, frozenset(route.methods or ()))
        for route in create_application(create_api_composition()).routes
    }
    assert ("/work/provider-inventory", frozenset({"POST"})) in app_routes
    assert ("/work/{work_id}", frozenset({"GET"})) in app_routes
    assert ("/work/{work_id}/run", frozenset({"POST"})) in app_routes
    assert ("/work/{work_id}/executions/{execution_id}", frozenset({"GET"})) in app_routes
    assert ("/work/{work_id}/events", frozenset({"GET"})) in app_routes
    assert ("/work/{work_id}/evidence", frozenset({"GET"})) in app_routes

    web_boundary = (REPO_ROOT / "apps/web/src/apiBoundary.ts").read_text(encoding="utf-8")
    for route in (
        "/work/provider-inventory",
        "/work/{work_id}",
        "/work/{work_id}/run",
        "/work/{work_id}/executions/{execution_id}",
        "/work/{work_id}/events",
        "/work/{work_id}/evidence",
    ):
        assert route in web_boundary


def _app(store: PersistenceStore, catalog: _Catalog):
    provider_ref = ref_for(ProviderId)
    m0_work = create_m0_work_api_composition(
        persistence_store=store,
        provider_catalog=catalog,
        principal=human_principal(),
        producer_ref=provider_ref,
        executor_ref=provider_ref,
        resource_refs=(provider_ref,),
    )
    return create_application(create_api_composition(provider_catalog=catalog, m0_work=m0_work))


def _create_work(client: TestClient, *, title: str) -> dict[str, object]:
    response = client.post(
        "/work/provider-inventory",
        json={"title": title, "objective": "Collect canonical provider descriptors."},
    )
    assert response.status_code == 201
    payload = response.json()
    work = payload["work"]
    assert isinstance(work, dict)
    assert work["work_type"] == "provider_inventory"
    assert work["state"] == "CREATED"
    return work


def _create_and_run_provider_inventory(client: TestClient, *, title: str) -> dict[str, object]:
    work = _create_work(client, title=title)
    response = client.post(f"/work/{work['work_id']}/run")
    assert response.status_code == 200
    payload = response.json()
    assert payload["work"]["work_id"] == work["work_id"]
    assert payload["execution"]["work_id"] == work["work_id"]
    payload["work_id"] = payload["work"]["work_id"]
    payload["execution_id"] = payload["execution"]["execution_id"]
    return payload


def _event_types(response) -> tuple[str, ...]:
    assert response.status_code == 200
    return tuple(event["event_type"] for event in response.json()["events"])


def _event_work_ids(response) -> tuple[str, ...]:
    assert response.status_code == 200
    return tuple(
        event["subject_ref"]["ref_id"].removeprefix("work:") for event in response.json()["events"]
    )


def _evidence_work_ids(response) -> tuple[str, ...]:
    assert response.status_code == 200
    return tuple(
        evidence["subject_ref"]["ref_id"].removeprefix("work:")
        for evidence in response.json()["evidence"]
    )


def _assert_record_counts(
    store: PersistenceStore,
    *,
    expected_work: int,
    expected_execution: int,
    expected_evidence: int,
) -> None:
    with store.transaction() as transaction:
        assert transaction.count_records(PersistenceRecordKind.WORK) == expected_work
        assert transaction.count_records(PersistenceRecordKind.EXECUTION) == expected_execution
        assert transaction.count_records(PersistenceRecordKind.EVIDENCE) == expected_evidence


def _descriptor(*, ordinal: int) -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=fixed_id(ProviderId, ordinal=ordinal),
        provider_type=ProviderType.MODEL if ordinal % 2 else ProviderType.DATABASE,
        version=SchemaVersion(1, 0, ordinal),
        declared_capability_ids=(),
        status=ProviderStatus.AVAILABLE,
    )


def _provider_failure() -> ContractError:
    return ContractError(
        error_code=ErrorCode("TEST_PROVIDER_INVENTORY_FAILURE"),
        message="bounded provider inventory failure",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.ERROR,
        retryable=False,
    )


class _Catalog:
    def __init__(self, result: Result[tuple[ProviderDescriptor, ...]]) -> None:
        self._result = result
        self.calls = 0

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context, CoreContext)
        self.calls += 1
        return self._result


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
    pytest.fail(f"PostgreSQL M0 integration schema did not initialize: {last_error!r}")


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
