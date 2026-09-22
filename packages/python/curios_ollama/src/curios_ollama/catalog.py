"""Provider catalog adapter for Ollama."""

from __future__ import annotations

from dataclasses import dataclass, field

from curios_contracts import (
    CapabilityId,
    ContractError,
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    ObjectReference,
    ProviderDescriptor,
    ProviderId,
    ProviderStatus,
    ProviderType,
    Result,
    SchemaVersion,
)
from curios_core import CoreContext

from curios_ollama.client import OllamaModelClient

DEFAULT_OLLAMA_PROVIDER_ID = ProviderId("prv_00000000000000000000000000")
DEFAULT_OLLAMA_CAPABILITY_IDS = (CapabilityId("cap_00000000000000000000000000"),)
_DESCRIPTOR_VERSION = SchemaVersion.parse("0.0.0")


@dataclass(frozen=True, slots=True)
class OllamaProviderCatalog:
    """Translate Ollama boundary observations into Curios provider descriptors."""

    client: OllamaModelClient
    provider_id: ProviderId = DEFAULT_OLLAMA_PROVIDER_ID
    declared_capability_ids: tuple[CapabilityId, ...] = DEFAULT_OLLAMA_CAPABILITY_IDS
    configuration_requirement_refs: tuple[ObjectReference, ...] = ()
    version: SchemaVersion = _DESCRIPTOR_VERSION
    implementation_metadata: dict[str, object] = field(
        default_factory=lambda: {"provider_family": "ollama"}
    )

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, ProviderId):
            msg = "provider_id must be a ProviderId"
            raise TypeError(msg)
        for capability_id in self.declared_capability_ids:
            if not isinstance(capability_id, CapabilityId):
                msg = "declared_capability_ids must contain CapabilityId values"
                raise TypeError(msg)
        for reference in self.configuration_requirement_refs:
            if not isinstance(reference, ObjectReference):
                msg = "configuration_requirement_refs must contain ObjectReference values"
                raise TypeError(msg)
        if not isinstance(self.version, SchemaVersion):
            msg = "version must be a SchemaVersion"
            raise TypeError(msg)

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        """Return the Ollama provider descriptor without selecting or invoking a model."""
        if not isinstance(context, CoreContext):
            msg = "context must be a CoreContext"
            raise TypeError(msg)

        try:
            models = self.client.list_models()
        except TimeoutError:
            return Result.failure((_provider_error(category=ErrorCategory.TIMEOUT),))
        except OSError:
            return Result.failure((_provider_error(),))
        except ValueError as error:
            return Result.failure((_provider_error(message=str(error), retryable=False),))

        descriptor = ProviderDescriptor(
            provider_id=self.provider_id,
            provider_type=ProviderType.MODEL,
            version=self.version,
            declared_capability_ids=self.declared_capability_ids,
            configuration_requirement_refs=self.configuration_requirement_refs,
            status=ProviderStatus.AVAILABLE,
            implementation_metadata={
                **self.implementation_metadata,
                "model_count": len(models),
            },
        )
        return Result.success((descriptor,))


def _provider_error(
    *,
    category: ErrorCategory = ErrorCategory.DEPENDENCY,
    message: str = "Ollama provider boundary could not list local models",
    retryable: bool = True,
) -> ContractError:
    return ContractError(
        error_code=ErrorCode("OLLAMA_PROVIDER_UNAVAILABLE"),
        message=message,
        category=category,
        severity=ErrorSeverity.ERROR,
        retryable=retryable,
    )
