"""Ollama provider boundary for Curios."""

from curios_ollama.catalog import (
    DEFAULT_OLLAMA_CAPABILITY_IDS,
    DEFAULT_OLLAMA_PROVIDER_ID,
    OllamaProviderCatalog,
)
from curios_ollama.client import OllamaHttpClient, OllamaModelClient, OllamaModelSummary

__version__ = "0.0.0"

__all__ = (
    "DEFAULT_OLLAMA_CAPABILITY_IDS",
    "DEFAULT_OLLAMA_PROVIDER_ID",
    "OllamaHttpClient",
    "OllamaModelClient",
    "OllamaModelSummary",
    "OllamaProviderCatalog",
    "__version__",
)
