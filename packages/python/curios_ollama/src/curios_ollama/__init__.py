"""Ollama provider boundary for Curios."""

from curios_ollama.catalog import (
    DEFAULT_OLLAMA_CAPABILITY_IDS,
    DEFAULT_OLLAMA_PROVIDER_ID,
    OllamaProviderCatalog,
)
from curios_ollama.client import OllamaHttpClient, OllamaModelClient, OllamaModelSummary
from curios_ollama.profiles import (
    MODEL_PROFILE_STATUS_VALUES,
    LocalModelProfile,
    ModelProfileStatus,
    OllamaModelProfileDiscovery,
)

__version__ = "0.0.0"

__all__ = (
    "DEFAULT_OLLAMA_CAPABILITY_IDS",
    "DEFAULT_OLLAMA_PROVIDER_ID",
    "LocalModelProfile",
    "MODEL_PROFILE_STATUS_VALUES",
    "ModelProfileStatus",
    "OllamaHttpClient",
    "OllamaModelClient",
    "OllamaModelSummary",
    "OllamaModelProfileDiscovery",
    "OllamaProviderCatalog",
    "__version__",
)
