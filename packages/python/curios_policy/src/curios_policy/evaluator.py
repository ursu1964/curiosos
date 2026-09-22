"""Minimal deterministic M0 policy evaluator."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from curios_contracts import (
    EffectClassification,
    ObjectReference,
    ObservabilityContext,
    PolicyDecision,
    PolicyDecisionOutcome,
    Principal,
    UtcTimestamp,
)

M0_PROVIDER_INVENTORY_WORK_TYPE = "provider_inventory"
M0_SUPPORTED_WORK_TYPES: tuple[str, ...] = (M0_PROVIDER_INVENTORY_WORK_TYPE,)
M0_SUPPORTED_AUTHORIZING_EFFECTS: tuple[EffectClassification, ...] = (
    EffectClassification.READ_ONLY,
)

_READ_ONLY_PROVIDER_INVENTORY_REASON = (
    "M0 permits READ_ONLY provider_inventory work through the minimal policy evaluator."
)
_UNKNOWN_POLICY_STATE_REASON = (
    "M0 policy state is unknown or incomplete; governed execution is not authorized."
)
_UNSUPPORTED_WORK_TYPE_REASON = (
    "M0 policy supports only provider_inventory work; requested work is not authorized."
)
_UNSUPPORTED_EFFECT_REASON = (
    "M0 policy supports only READ_ONLY provider_inventory effects; requested effect is not "
    "authorized."
)


@dataclass(frozen=True, slots=True)
class M0PolicyEvaluationRequest:
    """Input for the minimal M0 policy evaluator.

    This is an evaluator input, not a canonical contract. Canonical vocabulary
    and decision records remain owned by ``curios_contracts``.
    """

    subject_ref: ObjectReference
    principal: Principal
    work_type: str | None
    requested_effects: Sequence[EffectClassification]
    resource_refs: Sequence[ObjectReference]
    scope: str
    decided_at: UtcTimestamp
    policy_refs: Sequence[ObjectReference] = ()
    observability_context: ObservabilityContext | None = None
    policy_state_known: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference"
            raise TypeError(msg)
        if not isinstance(self.principal, Principal):
            msg = "principal must be a Principal"
            raise TypeError(msg)
        if self.work_type is not None and not isinstance(self.work_type, str):
            msg = "work_type must be a string when provided"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "requested_effects",
            _normalize_effects(self.requested_effects, "requested_effects"),
        )
        object.__setattr__(
            self,
            "resource_refs",
            _normalize_object_refs(self.resource_refs, "resource_refs"),
        )
        if not isinstance(self.scope, str):
            msg = "scope must be a string"
            raise TypeError(msg)
        object.__setattr__(self, "decided_at", UtcTimestamp(self.decided_at))
        object.__setattr__(
            self,
            "policy_refs",
            _normalize_object_refs(self.policy_refs, "policy_refs"),
        )
        if self.observability_context is not None and not isinstance(
            self.observability_context,
            ObservabilityContext,
        ):
            msg = "observability_context must be an ObservabilityContext when provided"
            raise TypeError(msg)
        if not isinstance(self.policy_state_known, bool):
            msg = "policy_state_known must be a bool"
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class MinimalM0PolicyEvaluator:
    """Deterministic fail-safe evaluator for the authorized M0 work slice."""

    def evaluate(self, request: M0PolicyEvaluationRequest) -> PolicyDecision:
        """Return the canonical decision for a minimal M0 policy request."""
        if not isinstance(request, M0PolicyEvaluationRequest):
            msg = "request must be an M0PolicyEvaluationRequest"
            raise TypeError(msg)

        outcome, reason = _evaluate_outcome(request)
        return PolicyDecision(
            subject_ref=request.subject_ref,
            principal=request.principal,
            requested_effects=tuple(request.requested_effects),
            resource_refs=tuple(request.resource_refs),
            scope=request.scope,
            outcome=outcome,
            reason=reason,
            policy_refs=tuple(request.policy_refs),
            decided_at=request.decided_at,
            observability_context=request.observability_context,
        )


def evaluate_m0_policy(request: M0PolicyEvaluationRequest) -> PolicyDecision:
    """Evaluate a request with the default minimal M0 policy evaluator."""
    return MinimalM0PolicyEvaluator().evaluate(request)


def _evaluate_outcome(
    request: M0PolicyEvaluationRequest,
) -> tuple[PolicyDecisionOutcome, str]:
    if not request.policy_state_known or not request.work_type:
        return PolicyDecisionOutcome.UNKNOWN, _UNKNOWN_POLICY_STATE_REASON
    if request.work_type not in M0_SUPPORTED_WORK_TYPES:
        return PolicyDecisionOutcome.DENY, _UNSUPPORTED_WORK_TYPE_REASON
    if tuple(request.requested_effects) != M0_SUPPORTED_AUTHORIZING_EFFECTS:
        return PolicyDecisionOutcome.DENY, _UNSUPPORTED_EFFECT_REASON
    return PolicyDecisionOutcome.ALLOW, _READ_ONLY_PROVIDER_INVENTORY_REASON


def _normalize_effects(
    values: Sequence[EffectClassification],
    field_name: str,
) -> tuple[EffectClassification, ...]:
    if isinstance(values, str | bytes | bytearray):
        msg = f"{field_name} must be a sequence of EffectClassification values"
        raise TypeError(msg)
    effects = tuple(EffectClassification(value) for value in values)
    if not effects:
        msg = f"{field_name} must contain at least one effect"
        raise ValueError(msg)
    return effects


def _normalize_object_refs(
    values: Sequence[ObjectReference],
    field_name: str,
) -> tuple[ObjectReference, ...]:
    if isinstance(values, str | bytes | bytearray):
        msg = f"{field_name} must be a sequence of ObjectReference values"
        raise TypeError(msg)
    refs = tuple(values)
    for ref in refs:
        if not isinstance(ref, ObjectReference):
            msg = f"{field_name} must contain ObjectReference values"
            raise TypeError(msg)
    return refs
