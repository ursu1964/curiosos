"""Deterministic M1 intent-to-plan decomposition templates."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum

from curios_contracts import (
    Assumption,
    AssumptionId,
    CapabilityId,
    CapabilityQuality,
    CapabilityRequirement,
    Decision,
    DecisionId,
    Intent,
    ObjectReference,
    Plan,
    PlanId,
    Problem,
    ProblemId,
    ReferenceKind,
    UtcTimestamp,
    WorkId,
    WorkItem,
    to_json_compatible,
)
from curios_contracts.identifiers import CuriosId

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_NORMALIZED_TEXT_RE = re.compile(r"\s+")
_TEMPLATE_VERSION = "m1-003.v1"


class DecompositionCategory(StrEnum):
    """Fixed M1 categories supported by deterministic decomposition."""

    RECORDED_TRUTH_SUMMARY = "recorded_truth_summary"
    IMPLEMENTATION_PLAN = "implementation_plan"


SUPPORTED_INTENT_CATEGORIES: tuple[DecompositionCategory, ...] = (
    DecompositionCategory.RECORDED_TRUTH_SUMMARY,
    DecompositionCategory.IMPLEMENTATION_PLAN,
)


class DecompositionStatus(StrEnum):
    """Outcome of deterministic template decomposition."""

    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"


class UnsupportedIntentReason(StrEnum):
    """Bounded reason codes for non-executing unsupported-intent results."""

    NO_TEMPLATE_MATCH = "NO_TEMPLATE_MATCH"


@dataclass(frozen=True, slots=True)
class DecompositionProposal:
    """Inert deterministic decomposition proposal.

    The proposal owns no persistence, runtime, API, provider, prompt, model, or
    workflow authority. Work is represented by canonical ``WorkItem`` proposals;
    the plan references those work items through ``ObjectReference``.
    """

    status: DecompositionStatus
    intent_ref: ObjectReference
    template_version: str = _TEMPLATE_VERSION
    category: DecompositionCategory | None = None
    problem: Problem | None = None
    assumptions: tuple[Assumption, ...] = ()
    decisions: tuple[Decision, ...] = ()
    plan: Plan | None = None
    work_items: tuple[WorkItem, ...] = ()
    unsupported_reason: UnsupportedIntentReason | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", DecompositionStatus(self.status))
        if not isinstance(self.intent_ref, ObjectReference):
            msg = "intent_ref must be an ObjectReference"
            raise TypeError(msg)
        if self.intent_ref.kind is not ReferenceKind.INTENT:
            msg = "intent_ref must reference intent objects"
            raise ValueError(msg)
        if self.category is not None:
            object.__setattr__(self, "category", DecompositionCategory(self.category))
        object.__setattr__(self, "assumptions", _normalize_tuple(self.assumptions, Assumption))
        object.__setattr__(self, "decisions", _normalize_tuple(self.decisions, Decision))
        object.__setattr__(self, "work_items", _normalize_tuple(self.work_items, WorkItem))
        if self.unsupported_reason is not None:
            object.__setattr__(
                self,
                "unsupported_reason",
                UnsupportedIntentReason(self.unsupported_reason),
            )
        _validate_status_shape(self)

    def to_json_compatible(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""
        return {
            "status": self.status.value,
            "intent_ref": to_json_compatible(self.intent_ref),
            "template_version": self.template_version,
            "category": to_json_compatible(self.category),
            "problem": to_json_compatible(self.problem),
            "assumptions": to_json_compatible(self.assumptions),
            "decisions": to_json_compatible(self.decisions),
            "plan": to_json_compatible(self.plan),
            "work_items": to_json_compatible(self.work_items),
            "unsupported_reason": to_json_compatible(self.unsupported_reason),
        }


@dataclass(frozen=True, slots=True)
class _WorkTemplate:
    work_type: str
    title: str
    objective: str
    capability_key: str
    dependency_indexes: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class _IntentTemplate:
    category: DecompositionCategory
    keywords: tuple[str, ...]
    problem_statement: str
    assumption_statement: str
    decision_rationale: str
    plan_objective: str
    work: tuple[_WorkTemplate, ...]


_RECORDED_TRUTH_TEMPLATE = _IntentTemplate(
    category=DecompositionCategory.RECORDED_TRUTH_SUMMARY,
    keywords=("summarize", "summary", "status", "recorded", "evidence"),
    problem_statement="Derive the requested summary from recorded Curios facts.",
    assumption_statement="Recorded Curios evidence is the authority for this summary.",
    decision_rationale="A deterministic recorded-truth summary template fits the intent.",
    plan_objective="Produce a bounded recorded-truth summary.",
    work=(
        _WorkTemplate(
            work_type="collect_recorded_context",
            title="Collect recorded context",
            objective="Collect the canonical records relevant to the requested summary.",
            capability_key="curios.recorded_context.read",
        ),
        _WorkTemplate(
            work_type="compose_recorded_summary",
            title="Compose recorded summary",
            objective="Compose a summary using only collected recorded context.",
            capability_key="curios.recorded_summary.compose",
            dependency_indexes=(0,),
        ),
        _WorkTemplate(
            work_type="verify_recorded_summary",
            title="Verify recorded summary",
            objective="Verify that summary claims trace back to recorded context.",
            capability_key="curios.recorded_summary.verify",
            dependency_indexes=(1,),
        ),
    ),
)

_IMPLEMENTATION_PLAN_TEMPLATE = _IntentTemplate(
    category=DecompositionCategory.IMPLEMENTATION_PLAN,
    keywords=("implement", "build", "create", "add", "change"),
    problem_statement="Turn the requested implementation change into bounded work.",
    assumption_statement="The request can be handled through repository-local bounded work.",
    decision_rationale="A deterministic implementation-plan template fits the intent.",
    plan_objective="Produce a bounded implementation work proposal.",
    work=(
        _WorkTemplate(
            work_type="inspect_current_state",
            title="Inspect current state",
            objective="Inspect relevant repository artifacts before changing implementation.",
            capability_key="curios.repository.inspect",
        ),
        _WorkTemplate(
            work_type="apply_bounded_change",
            title="Apply bounded change",
            objective="Apply the minimum implementation change required by the intent.",
            capability_key="curios.repository.modify",
            dependency_indexes=(0,),
        ),
        _WorkTemplate(
            work_type="verify_bounded_change",
            title="Verify bounded change",
            objective="Run focused verification for the bounded implementation change.",
            capability_key="curios.repository.verify",
            dependency_indexes=(1,),
        ),
    ),
)

_TEMPLATES: tuple[_IntentTemplate, ...] = (
    _RECORDED_TRUTH_TEMPLATE,
    _IMPLEMENTATION_PLAN_TEMPLATE,
)


def decompose_intent(intent: Intent, *, created_at: UtcTimestamp | str) -> DecompositionProposal:
    """Decompose ``intent`` with fixed deterministic templates."""
    if not isinstance(intent, Intent):
        msg = "intent must be an Intent"
        raise TypeError(msg)
    timestamp = UtcTimestamp(created_at)
    intent_ref = ObjectReference.from_id(intent.intent_id)
    template = _select_template(intent.objective)
    if template is None:
        return DecompositionProposal(
            status=DecompositionStatus.UNSUPPORTED,
            intent_ref=intent_ref,
            unsupported_reason=UnsupportedIntentReason.NO_TEMPLATE_MATCH,
        )

    problem = Problem(
        problem_id=_id(ProblemId, template.category, intent.intent_id, "problem"),
        intent_ref=intent_ref,
        objective=intent.objective,
        statement=template.problem_statement,
        context_refs=intent.context_refs,
        created_at=timestamp,
    )
    problem_ref = ObjectReference.from_id(problem.problem_id)
    assumption = Assumption(
        assumption_id=_id(AssumptionId, template.category, intent.intent_id, "assumption"),
        subject_ref=problem_ref,
        statement=template.assumption_statement,
        basis_refs=(intent_ref, *intent.context_refs),
        created_at=timestamp,
    )
    decision = Decision(
        decision_id=_id(DecisionId, template.category, intent.intent_id, "decision"),
        subject_ref=problem_ref,
        question="Which deterministic M1 decomposition template applies?",
        selected_option=template.category.value,
        rationale=template.decision_rationale,
        input_refs=(ObjectReference.from_id(assumption.assumption_id),),
        decided_at=timestamp,
    )
    work_items = _build_work_items(
        intent=intent,
        problem=problem,
        template=template,
        created_at=timestamp,
    )
    plan = Plan(
        plan_id=_id(PlanId, template.category, intent.intent_id, "plan"),
        problem_ref=problem_ref,
        objective=template.plan_objective,
        assumption_refs=(ObjectReference.from_id(assumption.assumption_id),),
        decision_refs=(ObjectReference.from_id(decision.decision_id),),
        work_refs=tuple(ObjectReference.from_id(work.work_id) for work in work_items),
        created_at=timestamp,
    )

    return DecompositionProposal(
        status=DecompositionStatus.SUPPORTED,
        intent_ref=intent_ref,
        category=template.category,
        problem=problem,
        assumptions=(assumption,),
        decisions=(decision,),
        plan=plan,
        work_items=work_items,
    )


def _select_template(objective: str) -> _IntentTemplate | None:
    normalized = _normalize_objective(objective)
    for template in _TEMPLATES:
        if any(keyword in normalized for keyword in template.keywords):
            return template
    return None


def _build_work_items(
    *,
    intent: Intent,
    problem: Problem,
    template: _IntentTemplate,
    created_at: UtcTimestamp,
) -> tuple[WorkItem, ...]:
    intent_ref = ObjectReference.from_id(intent.intent_id)
    problem_ref = ObjectReference.from_id(problem.problem_id)
    work_ids = tuple(
        _id(WorkId, template.category, intent.intent_id, "work", str(index))
        for index, _work_template in enumerate(template.work)
    )
    work_items: list[WorkItem] = []
    for index, work_template in enumerate(template.work):
        dependencies = tuple(
            work_ids[dependency] for dependency in work_template.dependency_indexes
        )
        work_items.append(
            WorkItem(
                work_id=work_ids[index],
                work_type=work_template.work_type,
                title=work_template.title,
                objective=work_template.objective,
                dependencies=dependencies,
                required_capabilities=(
                    CapabilityRequirement(
                        capability_id=_id(
                            CapabilityId,
                            template.category,
                            work_template.capability_key,
                        ),
                        quality=CapabilityQuality.STANDARD,
                    ),
                ),
                inputs=(intent_ref, problem_ref),
                created_at=created_at,
                updated_at=created_at,
            )
        )
    return tuple(work_items)


def _id[IdT: CuriosId](
    id_type: type[IdT],
    *parts: object,
) -> IdT:
    seed = "|".join((_TEMPLATE_VERSION, id_type.prefix, *(str(part) for part in parts)))
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    value = int.from_bytes(digest, byteorder="big")
    suffix = "".join(_ULID_ALPHABET[(value >> shift) & 0b11111] for shift in range(125, -1, -5))
    return id_type(f"{id_type.prefix}_{suffix}")


def _normalize_objective(objective: str) -> str:
    return _NORMALIZED_TEXT_RE.sub(" ", objective.strip().casefold())


def _normalize_tuple[ItemT](items: tuple[ItemT, ...], item_type: type[ItemT]) -> tuple[ItemT, ...]:
    normalized = tuple(items)
    for item in normalized:
        if not isinstance(item, item_type):
            msg = f"expected {item_type.__name__} values"
            raise TypeError(msg)
    return normalized


def _validate_status_shape(proposal: DecompositionProposal) -> None:
    supported_fields = (
        proposal.category,
        proposal.problem,
        proposal.assumptions,
        proposal.decisions,
        proposal.plan,
        proposal.work_items,
    )
    if proposal.status is DecompositionStatus.UNSUPPORTED:
        if any(supported_fields):
            msg = "unsupported decomposition must not include executable proposal fields"
            raise ValueError(msg)
        if proposal.unsupported_reason is None:
            msg = "unsupported decomposition requires unsupported_reason"
            raise ValueError(msg)
        return

    if proposal.unsupported_reason is not None:
        msg = "supported decomposition must not include unsupported_reason"
        raise ValueError(msg)
    if proposal.category is None or proposal.problem is None or proposal.plan is None:
        msg = "supported decomposition requires category, problem, and plan"
        raise ValueError(msg)
    if not proposal.work_items:
        msg = "supported decomposition requires at least one work item"
        raise ValueError(msg)
