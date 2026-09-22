"""Minimal deterministic M0 policy evaluator."""

from curios_policy.evaluator import (
    M0_PROVIDER_INVENTORY_WORK_TYPE,
    M0_SUPPORTED_AUTHORIZING_EFFECTS,
    M0_SUPPORTED_WORK_TYPES,
    M0PolicyEvaluationRequest,
    MinimalM0PolicyEvaluator,
    evaluate_m0_policy,
)

__version__ = "0.0.0"

__all__ = (
    "M0_PROVIDER_INVENTORY_WORK_TYPE",
    "M0_SUPPORTED_AUTHORIZING_EFFECTS",
    "M0_SUPPORTED_WORK_TYPES",
    "M0PolicyEvaluationRequest",
    "MinimalM0PolicyEvaluator",
    "__version__",
    "evaluate_m0_policy",
)
