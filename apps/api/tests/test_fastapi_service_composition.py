from __future__ import annotations

import ast
import asyncio
import tomllib
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast

import pytest
from curios_api import (
    ApiComposition,
    CompositeProviderCatalog,
    create_api_composition,
    create_application,
    create_provider_catalog,
)
from curios_config import local_docker_configuration_profile
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
    ResultStatus,
    SchemaVersion,
)
from curios_core import CoreContext, ProviderCatalog
from curios_observability import NoopTelemetryProvider
from curios_ollama import OllamaModelSummary
from fastapi import FastAPI, HTTPException

PACKAGE_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src" / "curios_api"
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"

FORBIDDEN_DIRECT_PROVIDER_NATIVE_IMPORTS = {
    "alembic",
    "asyncpg",
    "ollama",
    "opentelemetry",
    "psycopg",
    "psycopg2",
    "sqlalchemy",
    "sqlmodel",
}
FORBIDDEN_RUNTIME_NAMES = {
    "AgentRuntime",
    "AuthorityEngine",
    "DagEngine",
    "ModelRouter",
    "PolicyEngine",
    "Repository",
    "Scheduler",
    "SecretResolver",
}
type Endpoint = Callable[[], Awaitable[dict[str, object]]]


class DescriptorCatalog:
    def __init__(self, descriptors: tuple[ProviderDescriptor, ...]) -> None:
        self.descriptors = descriptors

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context, CoreContext)
        return Result.success(self.descriptors)


class FailingCatalog:
    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        assert isinstance(context, CoreContext)
        return Result.failure(
            (
                ContractError(
                    error_code=ErrorCode("API_PROVIDER_UNAVAILABLE"),
                    message="provider catalog failed",
                    category=ErrorCategory.DEPENDENCY,
                    severity=ErrorSeverity.ERROR,
                    retryable=True,
                ),
            )
        )


class FakeModelClient:
    def list_models(self) -> tuple[OllamaModelSummary, ...]:
        return (OllamaModelSummary(name="llama-local:latest"),)


def _descriptor() -> ProviderDescriptor:
    return ProviderDescriptor(
        provider_id=ProviderId("prv_00000000000000000000002201"),
        provider_type=ProviderType.MODEL,
        version=SchemaVersion(0, 0, 0),
        declared_capability_ids=(),
        status=ProviderStatus.AVAILABLE,
    )


def _source_trees() -> tuple[ast.AST, ...]:
    return tuple(
        ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        for path in SOURCE_ROOT.rglob("*.py")
    )


def _import_roots() -> set[str]:
    roots: set[str] = set()
    for tree in _source_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def _declared_class_names() -> set[str]:
    names: set[str] = set()
    for tree in _source_trees():
        names.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    return names


def _endpoint(app: FastAPI, path: str) -> Endpoint:
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return cast(Endpoint, route.endpoint)
    msg = f"route not found: {path}"
    raise AssertionError(msg)


def test_create_api_composition_wires_deterministic_curios_boundaries() -> None:
    composition = create_api_composition()

    assert isinstance(composition, ApiComposition)
    assert composition.configuration_provider.load_configuration_profile().value == (
        local_docker_configuration_profile()
    )
    assert isinstance(composition.core_services.list_provider_descriptors(CoreContext()), Result)
    assert isinstance(composition.telemetry_provider, NoopTelemetryProvider)


def test_provider_catalog_composes_authorized_provider_catalogs_without_routing() -> None:
    descriptor = _descriptor()
    catalog = CompositeProviderCatalog((DescriptorCatalog((descriptor,)),))

    result = catalog.list_provider_descriptors(CoreContext())

    assert isinstance(catalog, ProviderCatalog)
    assert result.status is ResultStatus.SUCCESS
    assert result.value == (descriptor,)


def test_provider_catalog_preserves_canonical_failures() -> None:
    result = CompositeProviderCatalog((FailingCatalog(),)).list_provider_descriptors(CoreContext())

    assert result.status is ResultStatus.FAILURE
    assert result.errors[0].error_code == "API_PROVIDER_UNAVAILABLE"
    assert result.errors[0].category is ErrorCategory.DEPENDENCY


def test_explicit_provider_catalog_factory_does_not_create_live_providers_by_default() -> None:
    empty = create_provider_catalog()
    ollama = create_provider_catalog(ollama_client=FakeModelClient())

    assert empty.list_provider_descriptors(CoreContext()).value == ()
    result = ollama.list_provider_descriptors(CoreContext())
    assert result.status is ResultStatus.SUCCESS
    assert result.value is not None
    assert result.value[0].provider_type is ProviderType.MODEL


def test_fastapi_liveness_endpoint_is_transport_only() -> None:
    app = create_application()

    response = asyncio.run(_endpoint(app, "/health/live")())

    assert response == {"service": "curios-api", "status": "ok"}


def test_fastapi_readiness_reports_configuration_and_provider_descriptors() -> None:
    descriptor = _descriptor()
    composition = create_api_composition(provider_catalog=DescriptorCatalog((descriptor,)))
    app = create_application(composition)

    payload = asyncio.run(_endpoint(app, "/health/ready")())

    assert payload["status"] == "ready"
    assert payload["configuration_profile"]["profile"] == "LOCAL_DOCKER"
    assert payload["providers"][0]["provider_id"] == str(descriptor.provider_id)


def test_fastapi_provider_endpoint_translates_contract_failures_to_http_boundary() -> None:
    composition = create_api_composition(provider_catalog=FailingCatalog())
    app = create_application(composition)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(_endpoint(app, "/providers")())

    assert raised.value.status_code == 503
    detail = raised.value.detail
    assert detail["status"] == "failure"
    assert detail["errors"][0]["error_code"] == "API_PROVIDER_UNAVAILABLE"


def test_application_package_keeps_fastapi_out_of_contracts_and_core() -> None:
    imports = _import_roots()

    assert "fastapi" in imports
    assert imports.isdisjoint(FORBIDDEN_DIRECT_PROVIDER_NATIVE_IMPORTS)
    assert _declared_class_names().isdisjoint(FORBIDDEN_RUNTIME_NAMES)


def test_application_package_dependencies_remain_outer_boundary_dependencies() -> None:
    dependencies = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["dependencies"]

    assert "fastapi>=0.118.0" in dependencies
    assert "curios-contracts" in dependencies
    assert "curios-core" in dependencies
    assert "curios-config" in dependencies
    assert "curios-postgres-provider" in dependencies
    assert "curios-ollama" in dependencies
    assert "curios-observability" in dependencies
