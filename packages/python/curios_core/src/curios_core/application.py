"""Minimal Curios core application service boundary."""

from __future__ import annotations

from dataclasses import dataclass

from curios_contracts import ProviderDescriptor, Result

from curios_core.context import CoreContext
from curios_core.ports import ProviderCatalog


@dataclass(frozen=True, slots=True)
class CoreServices:
    """Composition root for the current core application boundary."""

    provider_catalog: ProviderCatalog | None = None

    def list_provider_descriptors(
        self,
        context: CoreContext,
    ) -> Result[tuple[ProviderDescriptor, ...]]:
        """List declared provider descriptors through the provider catalog port."""
        if not isinstance(context, CoreContext):
            msg = "context must be a CoreContext"
            raise TypeError(msg)
        if self.provider_catalog is None:
            return Result.success(())
        return self.provider_catalog.list_provider_descriptors(context)
