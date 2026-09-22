"""FastAPI service composition boundary for Curios."""

from curios_api.composition import (
    ApiComposition,
    CompositeProviderCatalog,
    create_api_composition,
    create_provider_catalog,
)
from curios_api.service import create_application

__version__ = "0.0.0"

__all__ = (
    "ApiComposition",
    "CompositeProviderCatalog",
    "__version__",
    "create_api_composition",
    "create_application",
    "create_provider_catalog",
)
