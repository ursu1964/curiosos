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
WORK_ROUTES = (
    "/work/provider-inventory",
    "/work/{work_id}",
    "/work/{work_id}/run",
    "/work/{work_id}/executions/{execution_id}",
    "/work/{work_id}/events",
    "/work/{work_id}/evidence",
)

pytestmark = pytest.mark.acceptance


def test_m0_acceptance_provider_inventory_policy_and_recovery_slice() -> None:
    _require_docker()
    _run_compose("config", "--quiet")
    _run_compose("up", "-d", "postgres")

    schema = f"m0_012_{uuid4().hex}"
    config = PersistenceConfig(sqlalchemy_url=_postgres_url(), schema=schema)
    store = PersistenceStore(config)
    descriptors = (_descriptor("model", ordinal=2), _descriptor("database", ordinal=1))
    catalog = _Catalog(Result.success(descriptors))

    try:
        _wait_for_store_initialization(store)
        app = _app(store, catalog)

        with TestClient(app) as client:
            work_a = _create_work(client, title="M0 acceptance inventory A")
            run_a = _run_work(client, work_a["work_id"])
            work_b = _create_work(client, title="M0 acceptance inventory B")
            run_b = _run_work(client, work_b["work_id"])

            unknown = _create_work(client, title="M0 acceptance unknown policy")
            unknown_response = client.post(
                f"/work/{unknown['work_id']}/run",
                json={"policy_state_known": False},
            )

            unsupported = _create_work(client, title="M0 acceptance unsupported effect")
            unsupported_response = client.post(
                f"/work/{unsupported['work_id']}/run",
                json={"requested_effects": ["EXTERNAL_READ"]},
            )

            work_a_response = client.get(f"/work/{work_a['work_id']}")
            execution_a_response = client.get(
                f"/work/{work_a['work_id']}/executions/{run_a['execution_id']}"
            )
            events_a_response = client.get(f"/work/{work_a['work_id']}/events")
            evidence_a_response = client.get(f"/work/{work_a['work_id']}/evidence")
            cross_execution = client.get(
                f"/work/{work_b['work_id']}/executions/{run_a['execution_id']}"
            )

        assert catalog.calls == 2
        assert run_a["status"] == "COMPLETED"
        assert run_a["work"]["state"] == "COMPLETED"
        assert run_a["execution"]["state"] == "SUCCEEDED"
        assert run_a["executor_result"]["status"] == "success"
        assert run_a["executor_result"]["value"] == {
            "work_type": "provider_inventory",
            "provider_count": 2,
            "providers": [
                _descriptor("database", ordinal=1).to_json_compatible(),
                _descriptor("model", ordinal=2).to_json_compatible(),
            ],
        }
        assert work_a_response.json()["work"] == run_a["work"]
        assert execution_a_response.json()["execution"] == run_a["execution"]
        assert _event_types(events_a_response) == (
            "policy.evaluated",
            "execution.started",
            "evidence.produced",
            "execution.completed",
        )
        assert _event_subject_ids(events_a_response) == (work_a["work_id"],) * 4
        assert _evidence_subject_ids(evidence_a_response) == (work_a["work_id"],)
        assert evidence_a_response.json()["evidence"][0]["kind"] == "provider_report"
        assert cross_execution.status_code == 404
        assert run_a["work"]["work_id"] != run_b["work"]["work_id"]
        assert run_a["execution"]["execution_id"] != run_b["execution"]["execution_id"]

        assert unknown_response.status_code == 403
        assert unknown_response.json()["detail"]["status"] == "BLOCKED"
        assert unknown_response.json()["detail"]["policy_decision"]["outcome"] == "UNKNOWN"
        assert unsupported_response.status_code == 403
        assert unsupported_response.json()["detail"]["status"] == "BLOCKED"
        assert unsupported_response.json()["detail"]["policy_decision"]["outcome"] == "DENY"
        assert catalog.calls == 2

        failure_store = PersistenceStore(config)
        try:
            failure_app = _app(failure_store, _Catalog(Result.failure((_provider_failure(),))))
            with TestClient(failure_app) as client:
                failing = _create_work(client, title="M0 acceptance provider failure")
                failure_response = client.post(f"/work/{failing['work_id']}/run")
                failed_work = client.get(f"/work/{failing['work_id']}")
                failed_events = client.get(f"/work/{failing['work_id']}/events")
        finally:
            failure_store.dispose()

        failure_detail = failure_response.json()["detail"]
        assert failure_response.status_code == 502
        assert failure_detail["status"] == "FAILED"
        assert failure_detail["executor_result"]["status"] == "failure"
        assert failed_work.json()["work"]["state"] == "FAILED"
        assert _event_types(failed_events) == (
            "policy.evaluated",
            "execution.started",
            "execution.failed",
        )
        serialized_failure = json.dumps(failure_detail).lower()
        assert "sqlalchemy" not in serialized_failure
        assert "psycopg" not in serialized_failure
        assert "traceback" not in serialized_failure

        _assert_persisted_record_counts(
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
                recovered_work = client.get(f"/work/{work_a['work_id']}")
                recovered_execution = client.get(
                    f"/work/{work_a['work_id']}/executions/{run_a['execution_id']}"
                )
                recovered_events = client.get(f"/work/{work_a['work_id']}/events")
                recovered_evidence = client.get(f"/work/{work_a['work_id']}/evidence")
        finally:
            recovered_store.dispose()

        assert recovered_work.json()["work"] == run_a["work"]
        assert recovered_execution.json()["execution"] == run_a["execution"]
        assert recovered_events.json() == events_a_response.json()
        assert recovered_evidence.json() == evidence_a_response.json()
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


def test_m0_acceptance_api_web_ci_security_and_architecture_boundaries() -> None:
    api_service = (REPO_ROOT / "apps/api/src/curios_api/service.py").read_text(encoding="utf-8")
    api_composition = (REPO_ROOT / "apps/api/src/curios_api/composition.py").read_text(
        encoding="utf-8"
    )
    web_app = (REPO_ROOT / "apps/web/src/App.tsx").read_text(encoding="utf-8")
    web_boundary = (REPO_ROOT / "apps/web/src/apiBoundary.ts").read_text(encoding="utf-8")
    web_tests = (REPO_ROOT / "apps/web/src/App.test.tsx").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github/workflows/quality-gates.yml").read_text(encoding="utf-8")
    security = (REPO_ROOT / "tests/security/test_security_baseline.py").read_text(encoding="utf-8")
    architecture = (REPO_ROOT / "tests/architecture/test_architecture_conformance.py").read_text(
        encoding="utf-8"
    )

    for route in WORK_ROUTES:
        assert route in web_boundary
    assert '@app.post("/work/provider-inventory"' in api_service
    assert '@app.get("/work/{work_id}"' in api_service
    assert '@app.post("/work/{work_id}/run")' in api_service
    assert '@app.get("/work/{work_id}/events")' in api_service
    assert '@app.get("/work/{work_id}/evidence")' in api_service

    assert "SingleStepRuntimeService(" in api_composition
    assert "ProviderInventoryExecutor(" in api_composition
    assert "MinimalM0PolicyEvaluator()" in api_composition
    assert "M0WorkRepository(" in api_composition
    assert "EventEvidenceRuntimeStore(" in api_composition
    assert "from sqlalchemy" not in api_service
    assert "from psycopg" not in api_service

    assert "createProviderInventoryWork" in web_app
    assert "runProviderInventoryWork" in web_app
    assert "listWorkEvents" in web_app
    assert "listWorkEvidence" in web_app
    assert "activeWorkId" in web_app
    assert "isCurrentWork" in web_app
    assert "policy_state_known" not in web_app
    assert "requested_effects" not in web_app
    assert "WebSocket" not in web_app + web_boundary
    assert "EventSource" not in web_app + web_boundary
    assert "setInterval" not in web_app + web_boundary
    assert "does not let stale observation responses overwrite newly selected work" in web_tests
    assert "stale evidence" in web_tests

    assert "uv run pytest tests/acceptance -q" in workflow
    assert "uv run pytest tests/integration/test_m0_vertical_slice_integration.py -q" in workflow
    assert "uv run pytest tests/security -q" in workflow
    assert "uv run pytest tests/architecture -q" in workflow
    assert "uv run pytest -q" in workflow
    assert "pnpm --dir apps/web build" in workflow
    assert "git diff --check" in workflow
    assert "docker compose up -d ollama" not in workflow
    assert "down -v" not in workflow

    assert '"tests/acceptance/test_boot_acceptance.py"' in security
    assert '"tests/acceptance/test_m0_acceptance.py"' in security
    assert "AUTHORIZED_M0_ACCEPTANCE_TESTS_BY_TASK" in security
    assert "test_m0_acceptance_topology_rejects_unvalidated_future_acceptance_surfaces" in security
    assert "M1_PLUS_EXAMPLE_PACKAGE_ROOTS" in security
    assert "curios_contracts" in architecture
    assert "curios_core" in architecture
    for deferred in (
        "scheduler",
        "agent",
        "model_router",
        "DataLab",
        "secret_resolver",
        "knowledge",
        "memory",
        "iam",
    ):
        assert deferred.lower() not in web_boundary.lower()


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
    work = response.json()["work"]
    assert work["work_type"] == "provider_inventory"
    assert work["state"] == "CREATED"
    return work


def _run_work(client: TestClient, work_id: str) -> dict[str, object]:
    response = client.post(f"/work/{work_id}/run")
    assert response.status_code == 200
    payload = response.json()
    assert payload["work"]["work_id"] == work_id
    assert payload["execution"]["work_id"] == work_id
    payload["execution_id"] = payload["execution"]["execution_id"]
    return payload


def _event_types(response) -> tuple[str, ...]:
    assert response.status_code == 200
    return tuple(event["event_type"] for event in response.json()["events"])


def _event_subject_ids(response) -> tuple[str, ...]:
    assert response.status_code == 200
    return tuple(
        event["subject_ref"]["ref_id"].removeprefix("work:") for event in response.json()["events"]
    )


def _evidence_subject_ids(response) -> tuple[str, ...]:
    assert response.status_code == 200
    return tuple(
        evidence["subject_ref"]["ref_id"].removeprefix("work:")
        for evidence in response.json()["evidence"]
    )


def _assert_persisted_record_counts(
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


def _descriptor(provider_type: str, *, ordinal: int) -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=fixed_id(ProviderId, ordinal=ordinal),
        provider_type=ProviderType(provider_type),
        version=SchemaVersion(1, 0, ordinal),
        declared_capability_ids=(),
        status=ProviderStatus.AVAILABLE,
    )


def _provider_failure() -> ContractError:
    return ContractError(
        error_code=ErrorCode("M0_ACCEPTANCE_PROVIDER_FAILURE"),
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
    pytest.fail(f"PostgreSQL M0 acceptance schema did not initialize: {last_error!r}")


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
