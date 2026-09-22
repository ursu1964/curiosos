from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from contract_fixtures import UTC_NOW, fixed_id, human_principal
from curios_api import CompositeProviderCatalog, create_api_composition, create_application
from curios_contracts import (
    EffectClassification,
    EventEnvelope,
    EventId,
    EventType,
    ObjectReference,
    ObservabilityContext,
    PolicyDecision,
    PolicyDecisionOutcome,
    ProviderDescriptor,
    ProviderId,
    ProviderType,
    Result,
    ResultStatus,
    SchemaVersion,
    TraceId,
    WorkId,
)
from curios_observability import NoopTelemetryProvider, event_attributes
from curios_ollama import OllamaModelSummary, OllamaProviderCatalog
from curios_postgres_provider import PostgresProvider
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/quality-gates.yml"
WEB_API_BOUNDARY_PATH = REPO_ROOT / "apps/web/src/apiBoundary.ts"
POSTGRES_INTEGRATION_PATH = REPO_ROOT / "tests/integration/test_postgres_provider_integration.py"
SECURITY_BASELINE_PATH = REPO_ROOT / "tests/security/test_security_baseline.py"

pytestmark = pytest.mark.acceptance


class FakeOllamaClient:
    def __init__(self) -> None:
        self.calls = 0

    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        self.calls += 1
        return (
            OllamaModelSummary(name="llama-local:latest"),
            OllamaModelSummary(name="embedding-local:latest"),
        )


class UnavailableOllamaClient:
    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        raise OSError("ollama is intentionally unavailable in acceptance")


def test_boot_composition_serves_canonical_configuration_and_provider_catalogs_over_api() -> None:
    ollama_client = FakeOllamaClient()
    catalog = CompositeProviderCatalog(
        (
            PostgresProvider(),
            OllamaProviderCatalog(client=ollama_client),
        )
    )
    app = create_application(create_api_composition(provider_catalog=catalog))

    with TestClient(app) as client:
        ready_response = client.get("/health/ready")
        providers_response = client.get("/providers")

    assert ready_response.status_code == 200
    ready_payload = ready_response.json()
    assert ready_payload["status"] == "ready"
    assert ready_payload["configuration_profile"]["profile"] == "LOCAL_DOCKER"

    ready_providers = _provider_descriptors_from_payload(ready_payload["providers"])
    provider_response_descriptors = _provider_descriptors_from_payload(
        providers_response.json()["providers"]
    )
    assert providers_response.status_code == 200
    assert provider_response_descriptors == ready_providers
    assert [descriptor.provider_type for descriptor in ready_providers] == [
        ProviderType.DATABASE,
        ProviderType.MODEL,
    ]
    assert ready_payload["providers"][0]["implementation_metadata"] == {
        "database": "postgresql",
        "driver": "psycopg",
        "sqlalchemy": "2.x",
    }
    assert ready_payload["providers"][1]["implementation_metadata"] == {
        "model_count": 2,
        "provider_family": "ollama",
    }
    assert ollama_client.calls == 2
    assert _web_boundary_paths() == _api_route_paths(app)


def test_ollama_provider_failure_remains_deterministic_and_translates_canonically() -> None:
    catalog = CompositeProviderCatalog(
        (
            PostgresProvider(),
            OllamaProviderCatalog(client=UnavailableOllamaClient()),
        )
    )
    app = create_application(create_api_composition(provider_catalog=catalog))

    with TestClient(app) as client:
        response = client.get("/providers")

    assert response.status_code == 503
    result = Result.from_json_compatible(response.json()["detail"])
    assert result.status is ResultStatus.FAILURE
    assert result.errors[0].error_code == "OLLAMA_PROVIDER_UNAVAILABLE"
    assert result.errors[0].retryable is True


def test_observability_and_policy_contracts_survive_provider_boundary_projection() -> None:
    provider_ref = ObjectReference.from_id(ProviderId("prv_00000000000000000000002601"))
    work_ref = ObjectReference.from_id(fixed_id(WorkId))
    context = ObservabilityContext(
        trace_id=TraceId("trc_00000000000000000000002601"),
        principal_ref=human_principal().principal_ref,
    )
    event = EventEnvelope(
        event_id=EventId("evt_00000000000000000000002601"),
        event_type=EventType("provider.invoked"),
        schema_version=SchemaVersion(1, 0, 0),
        occurred_at=UTC_NOW,
        producer=provider_ref,
        subject_ref=work_ref,
        observability_context=context,
        payload={"provider_type": "model"},
    )

    NoopTelemetryProvider().record_event(event)
    attributes = event_attributes(event)
    assert attributes == {
        "curios.event_id": "evt_00000000000000000000002601",
        "curios.event_type": "provider.invoked",
        "curios.occurred_at": str(UTC_NOW),
        "curios.principal_ref.kind": "project",
        "curios.principal_ref.ref_id": str(human_principal().principal_ref.ref_id),
        "curios.producer.kind": "provider",
        "curios.producer.ref_id": "prv_00000000000000000000002601",
        "curios.schema_version": "1.0.0",
        "curios.subject_ref.kind": "work",
        "curios.subject_ref.ref_id": str(fixed_id(WorkId)),
        "curios.trace_id": "trc_00000000000000000000002601",
    }

    decision = PolicyDecision(
        subject_ref=work_ref,
        principal=human_principal(),
        requested_effects=tuple(EffectClassification),
        resource_refs=(provider_ref,),
        scope="BOOT acceptance",
        outcome=PolicyDecisionOutcome.UNKNOWN,
        reason="policy evaluator is intentionally not implemented in BOOT",
        decided_at=UTC_NOW,
        observability_context=context,
    )
    parsed = PolicyDecision.from_json_compatible(decision.to_json_compatible())
    assert parsed.outcome is PolicyDecisionOutcome.UNKNOWN
    assert parsed.is_authorizing is False


def test_ci_quality_gates_include_boot_acceptance_without_live_ollama_requirement() -> None:
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    expected_commands = (
        "uv lock --check",
        "uv sync --locked --all-groups --all-packages",
        "docker compose",
        "uv run ruff check .",
        "uv run ruff format --check .",
        "uv run mypy apps/api/src packages/python/*/src",
        "uv run pytest tests/contract tests/schema -q",
        "uv run pytest tests/architecture -q",
        "uv run pytest tests/security -q",
        "uv run pytest tests/integration/test_api_integration.py -q",
        "uv run pytest tests/integration/test_postgres_provider_integration.py -q",
        "uv run pytest tests/acceptance -q",
        "uv run pytest -q",
        "pnpm install --frozen-lockfile",
        "pnpm check",
        "pnpm --dir apps/web test",
        "pnpm --dir apps/web typecheck",
        "pnpm --dir apps/web build",
        "git diff --check",
    )
    normalized_workflow = _normalize_workflow_text(workflow_text)
    for command in expected_commands:
        assert command in normalized_workflow

    assert normalized_workflow.index("uv run pytest tests/integration/test_api_integration.py -q")
    assert normalized_workflow.index(
        "uv run pytest tests/integration/test_postgres_provider_integration.py -q"
    ) < normalized_workflow.index("uv run pytest tests/acceptance -q")
    assert normalized_workflow.index(
        "uv run pytest tests/acceptance -q"
    ) < normalized_workflow.index("uv run pytest -q")
    assert "ollama serve" not in normalized_workflow
    assert "docker compose up -d ollama" not in normalized_workflow
    assert "gpu" not in normalized_workflow.lower()


def test_postgresql_acceptance_uses_authorized_local_docker_readiness_behavior() -> None:
    source = POSTGRES_INTEGRATION_PATH.read_text(encoding="utf-8")

    assert '"up", "-d", "postgres"' in source
    assert '"stop", "postgres"' in source
    assert "down" not in source
    assert 'POSTGRES_VOLUME = "curios-local-docker_postgres_data"' in source
    assert "accepts_writes is True" in source
    assert "_READINESS_SQL" not in source
    assert "check_readiness(CoreContext())" in source
    assert '"docker", "volume", "inspect", POSTGRES_VOLUME' in source


def test_acceptance_test_surface_is_narrowly_authorized_by_security_topology() -> None:
    acceptance_paths = frozenset(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "tests/acceptance").rglob("*.py")
    )

    assert acceptance_paths == {"tests/acceptance/test_boot_acceptance.py"}
    security_text = SECURITY_BASELINE_PATH.read_text(encoding="utf-8")
    assert '"tests/acceptance/test_boot_acceptance.py"' in security_text
    assert '"tests/acceptance"' in security_text


def _provider_descriptors_from_payload(payload: object) -> tuple[ProviderDescriptor, ...]:
    assert isinstance(payload, list)
    return tuple(ProviderDescriptor.from_json_compatible(item) for item in payload)


def _api_route_paths(app: Any) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for route in app.routes
            if isinstance(path := getattr(route, "path", None), str)
            and (path.startswith("/health/") or path == "/providers")
        )
    )


def _web_boundary_paths() -> tuple[str, ...]:
    source = WEB_API_BOUNDARY_PATH.read_text(encoding="utf-8")
    return tuple(sorted(re.findall(r'"(/(?:health/(?:live|ready)|providers))"', source)))


def _normalize_workflow_text(text: str) -> str:
    return re.sub(r"\s+", " ", text)
