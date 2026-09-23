"""Outer application composition for the Curios API service."""

from __future__ import annotations

from dataclasses import dataclass, field

from curios_config import ConfigurationProvider, local_docker_configuration_provider
from curios_contracts import (
    ContractError,
    ObjectReference,
    Principal,
    ProviderDescriptor,
    Result,
    ResultStatus,
)
from curios_core import CoreContext, CoreServices, ProviderCatalog
from curios_observability import NoopTelemetryProvider, TelemetryProvider
from curios_ollama import OllamaModelClient, OllamaProviderCatalog
from curios_persistence import PersistenceStore
from curios_policy import MinimalM0PolicyEvaluator
from curios_postgres_provider import PostgresProvider
from curios_runtime import (
    EventEvidenceRuntimeStore,
    M0WorkRepository,
    ProviderInventoryExecutor,
    SingleStepRuntimeService,
)


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
    m0_work: M0WorkApiComposition | None = None

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
        if self.m0_work is not None and not isinstance(self.m0_work, M0WorkApiComposition):
            msg = "m0_work must be M0WorkApiComposition when provided"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class M0WorkApiComposition:
    """API-owned composition for the frozen M0 work/runtime boundaries."""

    work_repository: M0WorkRepository
    event_store: EventEvidenceRuntimeStore
    runtime_service: SingleStepRuntimeService
    principal: Principal
    producer_ref: ObjectReference
    executor_ref: ObjectReference
    scope: str = "project sandbox"
    resource_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.work_repository, M0WorkRepository):
            msg = "work_repository must be M0WorkRepository"
            raise TypeError(msg)
        if not isinstance(self.event_store, EventEvidenceRuntimeStore):
            msg = "event_store must be EventEvidenceRuntimeStore"
            raise TypeError(msg)
        if not isinstance(self.runtime_service, SingleStepRuntimeService):
            msg = "runtime_service must be SingleStepRuntimeService"
            raise TypeError(msg)
        if not isinstance(self.principal, Principal):
            msg = "principal must be Principal"
            raise TypeError(msg)
        if not isinstance(self.producer_ref, ObjectReference):
            msg = "producer_ref must be ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.executor_ref, ObjectReference):
            msg = "executor_ref must be ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.scope, str):
            msg = "scope must be a string"
            raise TypeError(msg)
        for resource_ref in self.resource_refs:
            if not isinstance(resource_ref, ObjectReference):
                msg = "resource_refs must contain ObjectReference values"
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
    m0_work: M0WorkApiComposition | None = None,
) -> ApiComposition:
    """Create deterministic API composition from Curios-owned boundaries."""
    return ApiComposition(
        configuration_provider=configuration_provider or local_docker_configuration_provider(),
        core_services=CoreServices(provider_catalog=provider_catalog),
        telemetry_provider=telemetry_provider or NoopTelemetryProvider(),
        context=context or CoreContext(),
        m0_work=m0_work,
    )


def create_m0_work_api_composition(
    *,
    persistence_store: PersistenceStore,
    provider_catalog: ProviderCatalog,
    principal: Principal,
    producer_ref: ObjectReference,
    executor_ref: ObjectReference,
    scope: str = "project sandbox",
    resource_refs: tuple[ObjectReference, ...] = (),
) -> M0WorkApiComposition:
    """Wire the frozen M0 runtime stack for explicit API work composition."""
    repository = M0WorkRepository(persistence_store)
    event_store = EventEvidenceRuntimeStore(persistence_store)
    runtime_service = SingleStepRuntimeService(
        work_repository=repository,
        event_store=event_store,
        policy_evaluator=MinimalM0PolicyEvaluator(),
        executor=ProviderInventoryExecutor((provider_catalog,)),
    )
    return M0WorkApiComposition(
        work_repository=repository,
        event_store=event_store,
        runtime_service=runtime_service,
        principal=principal,
        producer_ref=producer_ref,
        executor_ref=executor_ref,
        scope=scope,
        resource_refs=resource_refs,
    )
