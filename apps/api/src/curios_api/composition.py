"""Outer application composition for the Curios API service."""

from __future__ import annotations

from dataclasses import dataclass, field

from curios_config import ConfigurationProvider, local_docker_configuration_provider
from curios_contracts import ContractError, ProviderDescriptor, Result, ResultStatus
from curios_core import CoreContext, CoreServices, ProviderCatalog
from curios_observability import NoopTelemetryProvider, TelemetryProvider
from curios_ollama import OllamaModelClient, OllamaProviderCatalog
from curios_postgres_provider import PostgresProvider


@dataclass(frozen=True, slots=True)
class CompositeProviderCatalog:
    """Outer composition adapter that joins already-authorized provider catalogs."""

    catalogs: tuple[ProviderCatalog, ...] = ()

    def __post_init__(self) -> None:
        for catalog in self.catalogs:
            if not isinstance(catalog, ProviderCatalog):
                msg = "catalogs must contain ProviderCatalog implementations"
                raise TypeError(msg)

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        """List provider descriptors without selecting or executing providers."""
        if not isinstance(context, CoreContext):
            msg = "context must be a CoreContext"
            raise TypeError(msg)

        descriptors: list[ProviderDescriptor] = []
        errors: list[ContractError] = []
        for catalog in self.catalogs:
            result = catalog.list_provider_descriptors(context)
            if result.status is ResultStatus.FAILURE:
                errors.extend(result.errors)
                continue
            if result.value is not None:
                descriptors.extend(result.value)

        if errors:
            return Result.failure(tuple(errors))
        return Result.success(tuple(descriptors))


@dataclass(frozen=True, slots=True)
class ApiComposition:
    """FastAPI-owned wiring of frozen Curios boundaries."""

    configuration_provider: ConfigurationProvider = field(
        default_factory=local_docker_configuration_provider
    )
    core_services: CoreServices = field(default_factory=CoreServices)
    telemetry_provider: TelemetryProvider = field(default_factory=NoopTelemetryProvider)
    context: CoreContext = field(default_factory=CoreContext)

    def __post_init__(self) -> None:
        if not isinstance(self.configuration_provider, ConfigurationProvider):
            msg = "configuration_provider must implement ConfigurationProvider"
            raise TypeError(msg)
        if not isinstance(self.core_services, CoreServices):
            msg = "core_services must be CoreServices"
            raise TypeError(msg)
        if not isinstance(self.telemetry_provider, TelemetryProvider):
            msg = "telemetry_provider must implement TelemetryProvider"
            raise TypeError(msg)
        if not isinstance(self.context, CoreContext):
            msg = "context must be CoreContext"
            raise TypeError(msg)


def create_provider_catalog(
    *,
    ollama_client: OllamaModelClient | None = None,
    postgres_sqlalchemy_url: str | None = None,
) -> CompositeProviderCatalog:
    """Create the explicit provider catalog wiring authorized for TASK-BOOT-022.

    Live providers are only constructed when explicit provider-local inputs are
    supplied by the outer application layer.
    """
    catalogs: list[ProviderCatalog] = []
    if ollama_client is not None:
        catalogs.append(OllamaProviderCatalog(client=ollama_client))
    if postgres_sqlalchemy_url is not None:
        catalogs.append(PostgresProvider.from_sqlalchemy_url(postgres_sqlalchemy_url))
    return CompositeProviderCatalog(tuple(catalogs))


def create_api_composition(
    *,
    configuration_provider: ConfigurationProvider | None = None,
    provider_catalog: ProviderCatalog | None = None,
    telemetry_provider: TelemetryProvider | None = None,
    context: CoreContext | None = None,
) -> ApiComposition:
    """Create deterministic API composition from Curios-owned boundaries."""
    return ApiComposition(
        configuration_provider=configuration_provider or local_docker_configuration_provider(),
        core_services=CoreServices(provider_catalog=provider_catalog),
        telemetry_provider=telemetry_provider or NoopTelemetryProvider(),
        context=context or CoreContext(),
    )
