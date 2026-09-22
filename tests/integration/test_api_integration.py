from __future__ import annotations

from collections.abc import Awaitable, Callable

import pytest
from curios_api import CompositeProviderCatalog, create_api_composition, create_application
from curios_config import local_docker_configuration_profile
from curios_contracts import (
    ConfigurationProfile,
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
from curios_ollama import OllamaModelSummary, OllamaProviderCatalog
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class CountingConfigurationProvider:
    def __init__(self) -> None:
        self.calls = 0

    def load_configuration_profile(self) -> Result[ConfigurationProfile]:
        self.calls += 1
        return Result.success(local_docker_configuration_profile())


class FailingConfigurationProvider:
    def load_configuration_profile(self) -> Result[ConfigurationProfile]:
        return Result.failure((_error("API_CONFIGURATION_UNAVAILABLE"),))


class DescriptorCatalog:
    def __init__(self, descriptors: tuple[ProviderDescriptor, ...]) -> None:
        self.descriptors = descriptors
        self.calls = 0

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context, CoreContext)
        self.calls += 1
        return Result.success(self.descriptors)


class FailingCatalog:
    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context, CoreContext)
        return Result.failure((_error("API_PROVIDER_UNAVAILABLE"),))


class FakeModelClient:
    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        return (OllamaModelSummary(name="llama-local:latest"),)


def test_application_constructs_as_asgi_app_and_liveness_stays_provider_independent() -> None:
    configuration_provider = CountingConfigurationProvider()
    provider_catalog = DescriptorCatalog((_descriptor(ProviderType.DATABASE, suffix="01"),))
    app = create_application(
        create_api_composition(
            configuration_provider=configuration_provider,
            provider_catalog=provider_catalog,
        )
    )

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"service": "curios-api", "status": "ok"}
    assert configuration_provider.calls == 0
    assert provider_catalog.calls == 0
    assert {getattr(route, "path", "") for route in app.routes} >= {
        "/health/live",
        "/health/ready",
        "/providers",
    }


def test_readiness_serializes_configuration_and_composed_providers_over_http() -> None:
    configuration_provider = CountingConfigurationProvider()
    database_descriptor = _descriptor(ProviderType.DATABASE, suffix="02")
    catalog = CompositeProviderCatalog(
        (
            DescriptorCatalog((database_descriptor,)),
            OllamaProviderCatalog(client=FakeModelClient()),
        )
    )
    app = create_application(
        create_api_composition(
            configuration_provider=configuration_provider,
            provider_catalog=catalog,
        )
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["configuration_profile"]["profile"] == "LOCAL_DOCKER"
    assert configuration_provider.calls == 1
    provider_payloads = payload["providers"]
    assert [provider["provider_type"] for provider in provider_payloads] == [
        "database",
        "model",
    ]
    assert provider_payloads[0]["provider_id"] == str(database_descriptor.provider_id)
    assert provider_payloads[1]["implementation_metadata"] == {
        "model_count": 1,
        "provider_family": "ollama",
    }


def test_providers_endpoint_returns_catalog_descriptors_through_fastapi_boundary() -> None:
    database_descriptor = _descriptor(ProviderType.DATABASE, suffix="03")
    model_descriptor = _descriptor(ProviderType.MODEL, suffix="04")
    provider_catalog = DescriptorCatalog((database_descriptor, model_descriptor))
    app = create_application(create_api_composition(provider_catalog=provider_catalog))

    with TestClient(app) as client:
        response = client.get("/providers")

    assert response.status_code == 200
    providers = response.json()["providers"]
    assert len(providers) == 2
    assert providers[0] == _expected_provider_payload(database_descriptor)
    assert providers[1] == _expected_provider_payload(model_descriptor)
    assert provider_catalog.calls == 1


def test_provider_result_failure_translates_to_canonical_http_503_detail() -> None:
    app = create_application(create_api_composition(provider_catalog=FailingCatalog()))

    with TestClient(app) as client:
        response = client.get("/providers")

    assert response.status_code == 503
    assert response.json()["detail"] == _expected_failure_detail("API_PROVIDER_UNAVAILABLE")


def test_readiness_configuration_failure_translates_to_canonical_http_503_detail() -> None:
    app = create_application(
        create_api_composition(configuration_provider=FailingConfigurationProvider())
    )

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == _expected_failure_detail("API_CONFIGURATION_UNAVAILABLE")


def test_application_lifespan_runs_startup_and_shutdown_around_client_context() -> None:
    events: list[str] = []
    app = create_application()

    async def startup() -> None:
        events.append("startup")

    async def shutdown() -> None:
        events.append("shutdown")

    app.router.on_startup.append(_lifespan_handler(startup))
    app.router.on_shutdown.append(_lifespan_handler(shutdown))

    assert events == []
    with TestClient(app) as client:
        assert events == ["startup"]
        assert client.get("/health/live").status_code == 200

    assert events == ["startup", "shutdown"]


def _descriptor(provider_type: ProviderType, *, suffix: str) -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=ProviderId(f"prv_000000000000000000000023{suffix}"),
        provider_type=provider_type,
        version=SchemaVersion(0, 0, 0),
        declared_capability_ids=(),
        status=ProviderStatus.AVAILABLE,
    )


def _error(error_code: str) -> ContractError:
    return ContractError(
        error_code=ErrorCode(error_code),
        message=f"{error_code} from integration fixture",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.ERROR,
        retryable=True,
    )


def _expected_failure_detail(error_code: str) -> dict[str, object]:
    return {
        "errors": [
            {
                "category": "dependency",
                "details": None,
                "error_code": error_code,
                "message": f"{error_code} from integration fixture",
                "retryable": True,
                "severity": "error",
                "subject_ref": None,
                "trace_id": None,
            }
        ],
        "evidence_refs": [],
        "status": "failure",
        "value": None,
        "warnings": [],
    }


def _expected_provider_payload(descriptor: ProviderDescriptor) -> dict[str, object]:
    return {
        "configuration_requirement_refs": [],
        "declared_capability_ids": [],
        "implementation_metadata": None,
        "provider_id": str(descriptor.provider_id),
        "provider_type": descriptor.provider_type.value,
        "status": "available",
        "version": "0.0.0",
    }


def _lifespan_handler(
    handler: Callable[[], Awaitable[None]],
) -> Callable[[], Awaitable[None]]:
    return handler
