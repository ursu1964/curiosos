"""Provider-facing ports owned by core."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from curios_contracts import ProviderDescriptor, Result

from curios_core.context import CoreContext

type ProviderDescriptorsResult = Result[tuple[ProviderDescriptor, ...]]


@runtime_checkable
class ProviderCatalog(Protocol):
    """Read-only inventory of provider descriptors.

    Implementations live outside core and translate implementation-specific
    failures into frozen ``ContractError`` values inside the returned
    ``Result``.
    """

    def list_provider_descriptors(self, context: CoreContext) -> ProviderDescriptorsResult:
        """Return declared provider descriptors without selecting or executing one."""
