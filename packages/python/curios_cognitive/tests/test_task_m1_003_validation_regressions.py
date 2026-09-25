from __future__ import annotations

import pytest
from curios_cognitive import (
    DecompositionCategory,
    DecompositionStatus,
    UnsupportedIntentReason,
    decompose_intent,
)
from curios_contracts import Intent, IntentId


def _intent(objective: str) -> Intent:
    return Intent(
        intent_id=IntentId("int_01K5V7EDNV6G7GVQ8F94N3EX05"),
        objective=objective,
        submitted_at="2026-09-25T08:00:00Z",
    )


@pytest.mark.parametrize(
    "objective",
    (
        "Address a philosophical question.",
        "Discuss the statusquo of design terms.",
    ),
)
def test_near_miss_keywords_remain_unsupported(objective: str) -> None:
    result = decompose_intent(_intent(objective), created_at="2026-09-25T09:00:00Z")

    assert result.status is DecompositionStatus.UNSUPPORTED
    assert result.unsupported_reason is UnsupportedIntentReason.NO_TEMPLATE_MATCH
    assert result.problem is None
    assert result.assumptions == ()
    assert result.decisions == ()
    assert result.plan is None
    assert result.work_items == ()


@pytest.mark.parametrize(
    ("objective", "expected_category"),
    (
        ("Please, SUMMARIZE.", DecompositionCategory.RECORDED_TRUTH_SUMMARY),
        ("Please, summary.", DecompositionCategory.RECORDED_TRUTH_SUMMARY),
        ("Please, status.", DecompositionCategory.RECORDED_TRUTH_SUMMARY),
        ("Please, recorded.", DecompositionCategory.RECORDED_TRUTH_SUMMARY),
        ("Please, evidence.", DecompositionCategory.RECORDED_TRUTH_SUMMARY),
        ("Please, IMPLEMENT.", DecompositionCategory.IMPLEMENTATION_PLAN),
        ("Please, build.", DecompositionCategory.IMPLEMENTATION_PLAN),
        ("Please, create.", DecompositionCategory.IMPLEMENTATION_PLAN),
        ("Please, add.", DecompositionCategory.IMPLEMENTATION_PLAN),
        ("Please, change.", DecompositionCategory.IMPLEMENTATION_PLAN),
    ),
)
def test_complete_keyword_tokens_remain_supported(
    objective: str,
    expected_category: DecompositionCategory,
) -> None:
    result = decompose_intent(_intent(objective), created_at="2026-09-25T09:00:00Z")

    assert result.status is DecompositionStatus.SUPPORTED
    assert result.category is expected_category
    assert result.problem is not None
    assert result.plan is not None
    assert result.work_items


@pytest.mark.parametrize(
    "objective",
    tuple(
        f"Please {token}."
        for keyword in (
            "summarize",
            "summary",
            "status",
            "recorded",
            "evidence",
            "implement",
            "build",
            "create",
            "add",
            "change",
        )
        for token in (f"{keyword}tail", f"pre{keyword}", f"pre{keyword}tail")
    ),
)
def test_embedded_keyword_tokens_remain_unsupported(objective: str) -> None:
    result = decompose_intent(_intent(objective), created_at="2026-09-25T09:00:00Z")

    assert result.status is DecompositionStatus.UNSUPPORTED
    assert result.unsupported_reason is UnsupportedIntentReason.NO_TEMPLATE_MATCH
    assert result.problem is None
    assert result.assumptions == ()
    assert result.decisions == ()
    assert result.plan is None
    assert result.work_items == ()
