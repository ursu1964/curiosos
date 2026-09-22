"""Curios-owned domain and application logic package boundary."""

from curios_core.application import CoreServices
from curios_core.context import CoreContext
from curios_core.ports import ProviderCatalog, ProviderDescriptorsResult

__version__ = "0.0.0"

__all__ = (
    "CoreContext",
    "CoreServices",
    "ProviderCatalog",
    "ProviderDescriptorsResult",
    "__version__",
)
