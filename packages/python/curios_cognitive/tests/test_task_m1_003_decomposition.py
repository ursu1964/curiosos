from __future__ import annotations

import json
from dataclasses import fields

import pytest
from curios_cognitive import (
    SUPPORTED_INTENT_CATEGORIES,
    DecompositionCategory,
    DecompositionProposal,
    DecompositionStatus,
    UnsupportedIntentReason,
    decompose_intent,
)
from curios_contracts import (
    Intent,
    IntentId,
    ObjectReference,
    Plan,
    ProjectId,
    ReferenceKind,
    WorkId,
    WorkItem,
    to_json_compatible,
)


def _intent(objective: str) -> Intent:
    return Intent(
        intent_id=IntentId("int_01K5V7EDNV6G7GVQ8F94N3EX01"),
        objective=objective,
        submitted_at="2026-09-25T08:00:00Z",
        source_ref=ObjectReference.from_id(ProjectId("prj_01K5V7EDNV6G7GVQ8F94N3EX02")),
    )


def test_same_intent_produces_same_decomposition_representation() -> None:
    intent = _intent("Summarize the recorded project status.")

    first = decompose_intent(intent, created_at="2026-09-25T09:00:00Z")
    second = decompose_intent(intent, created_at="2026-09-25T09:00:00Z")

    assert first == second
    assert first.to_json_compatible() == second.to_json_compatible()
    assert json.loads(json.dumps(first.to_json_compatible(), sort_keys=True)) == (
        first.to_json_compatible()
    )


def test_supported_summary_intent_builds_bounded_canonical_plan_and_work_items() -> None:
    result = decompose_intent(
        _intent("Summarize the recorded project status."),
        created_at="2026-09-25T09:00:00Z",
    )

    assert result.status is DecompositionStatus.SUPPORTED
    assert result.category is DecompositionCategory.RECORDED_TRUTH_SUMMARY
    assert result.unsupported_reason is None
    assert result.problem is not None
    assert result.plan is not None
    assert len(result.assumptions) == 1
    assert len(result.decisions) == 1
    assert len(result.work_items) == 3
    assert all(isinstance(work_item, WorkItem) for work_item in result.work_items)
    assert result.plan.work_refs == tuple(
        ObjectReference.from_id(work_item.work_id) for work_item in result.work_items
    )
    assert [work_item.dependencies for work_item in result.work_items] == [
        (),
        (result.work_items[0].work_id,),
        (result.work_items[1].work_id,),
    ]
    assert all(reference.kind is ReferenceKind.WORK for reference in result.plan.work_refs)


def test_supported_implementation_intent_uses_fixed_second_template() -> None:
    result = decompose_intent(
        _intent("Implement the smallest bounded change."),
        created_at="2026-09-25T09:00:00Z",
    )

    assert result.status is DecompositionStatus.SUPPORTED
    assert result.category is DecompositionCategory.IMPLEMENTATION_PLAN
    assert [work_item.work_type for work_item in result.work_items] == [
        "inspect_current_state",
        "apply_bounded_change",
        "verify_bounded_change",
    ]


def test_unsupported_intent_is_bounded_and_non_executing() -> None:
    result = decompose_intent(
        _intent("Tell a whimsical story about clouds."),
        created_at="2026-09-25T09:00:00Z",
    )

    assert result.status is DecompositionStatus.UNSUPPORTED
    assert result.unsupported_reason is UnsupportedIntentReason.NO_TEMPLATE_MATCH
    assert result.category is None
    assert result.problem is None
    assert result.plan is None
    assert result.assumptions == ()
    assert result.decisions == ()
    assert result.work_items == ()
    assert result.to_json_compatible()["work_items"] == []


def test_decomposition_rejects_non_intent_input() -> None:
    with pytest.raises(TypeError, match="intent must be an Intent"):
        decompose_intent(object(), created_at="2026-09-25T09:00:00Z")  # type: ignore[arg-type]


def test_proposal_shape_rejects_hidden_authority_for_unsupported_results() -> None:
    intent_ref = ObjectReference.from_id(IntentId("int_01K5V7EDNV6G7GVQ8F94N3EX03"))
    with pytest.raises(ValueError, match="unsupported decomposition must not include"):
        DecompositionProposal(
            status=DecompositionStatus.UNSUPPORTED,
            intent_ref=intent_ref,
            category=DecompositionCategory.RECORDED_TRUTH_SUMMARY,
            unsupported_reason=UnsupportedIntentReason.NO_TEMPLATE_MATCH,
        )


def test_proposal_rejects_non_intent_reference() -> None:
    with pytest.raises(ValueError, match="intent_ref must reference intent objects"):
        DecompositionProposal(
            status=DecompositionStatus.UNSUPPORTED,
            intent_ref=ObjectReference.from_id(WorkId("wrk_01K5V7EDNV6G7GVQ8F94N3EX04")),
            unsupported_reason=UnsupportedIntentReason.NO_TEMPLATE_MATCH,
        )


def test_decomposition_uses_existing_plan_and_workitem_contracts_without_parallel_state() -> None:
    proposal_field_names = {field.name for field in fields(DecompositionProposal)}
    plan_field_names = {field.name for field in fields(Plan)}
    work_field_names = {field.name for field in fields(WorkItem)}

    assert "work_items" in proposal_field_names
    assert "plan" in proposal_field_names
    assert "work_refs" in plan_field_names
    assert "state" not in proposal_field_names
    assert "dependencies" not in proposal_field_names
    assert proposal_field_names.isdisjoint(work_field_names - {"work_items"})


def test_supported_categories_are_fixed_and_serializable() -> None:
    assert SUPPORTED_INTENT_CATEGORIES == (
        DecompositionCategory.RECORDED_TRUTH_SUMMARY,
        DecompositionCategory.IMPLEMENTATION_PLAN,
    )
    assert to_json_compatible(SUPPORTED_INTENT_CATEGORIES) == [
        "recorded_truth_summary",
        "implementation_plan",
    ]
