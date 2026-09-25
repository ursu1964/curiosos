"""Curios-owned deterministic cognitive decomposition implementation."""

from curios_cognitive.decomposition import (
    SUPPORTED_INTENT_CATEGORIES,
    DecompositionCategory,
    DecompositionProposal,
    DecompositionStatus,
    UnsupportedIntentReason,
    decompose_intent,
)

__version__ = "0.0.0"

__all__ = (
    "SUPPORTED_INTENT_CATEGORIES",
    "DecompositionCategory",
    "DecompositionProposal",
    "DecompositionStatus",
    "UnsupportedIntentReason",
    "__version__",
    "decompose_intent",
)
