from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import fields

import pytest
from curios_contracts import (
    Assumption,
    AssumptionId,
    Decision,
    DecisionId,
    Intent,
    IntentId,
    ObjectReference,
    Plan,
    PlanId,
    Problem,
    ProblemId,
    ProjectId,
    ReferenceKind,
    WorkId,
    WorkItem,
    to_json_compatible,
)


def _timestamp() -> str:
    return "2026-09-25T08:00:00Z"


def _intent_id() -> IntentId:
    return IntentId("int_01K5V7EDNV6G7GVQ8F94N3EX01")


def _problem_id() -> ProblemId:
    return ProblemId("prb_01K5V7EDNV6G7GVQ8F94N3EX02")


def _assumption_id() -> AssumptionId:
    return AssumptionId("asm_01K5V7EDNV6G7GVQ8F94N3EX03")


def _decision_id() -> DecisionId:
    return DecisionId("dcn_01K5V7EDNV6G7GVQ8F94N3EX04")


def _plan_id() -> PlanId:
    return PlanId("pln_01K5V7EDNV6G7GVQ8F94N3EX05")


def _work_ref() -> ObjectReference:
    return ObjectReference.from_id(WorkId("wrk_01K5V7EDNV6G7GVQ8F94N3EX06"))


def test_cognitive_ids_are_referenceable_through_object_reference() -> None:
    assert ObjectReference.from_id(_intent_id()).kind is ReferenceKind.INTENT
    assert ObjectReference.from_id(_problem_id()).kind is ReferenceKind.PROBLEM
    assert ObjectReference.from_id(_assumption_id()).kind is ReferenceKind.ASSUMPTION
    assert ObjectReference.from_id(_decision_id()).kind is ReferenceKind.DECISION
    assert ObjectReference.from_id(_plan_id()).kind is ReferenceKind.PLAN


def test_intent_problem_assumption_decision_and_plan_round_trip_deterministically() -> None:
    intent = Intent(
        intent_id=_intent_id(),
        objective="Summarize the current project status.",
        source_ref=ObjectReference.from_id(ProjectId("prj_01K5V7EDNV6G7GVQ8F94N3EX07")),
        submitted_at=_timestamp(),
    )
    problem = Problem(
        problem_id=_problem_id(),
        intent_ref=ObjectReference.from_id(intent.intent_id),
        objective=intent.objective,
        statement="Determine the current project status from recorded Curios facts.",
        context_refs=(ObjectReference.from_id(intent.intent_id),),
        created_at=_timestamp(),
    )
    assumption = Assumption(
        assumption_id=_assumption_id(),
        subject_ref=ObjectReference.from_id(problem.problem_id),
        statement="Recorded evidence is the authority for current status.",
        basis_refs=(ObjectReference.from_id(intent.intent_id),),
        created_at=_timestamp(),
    )
    decision = Decision(
        decision_id=_decision_id(),
        subject_ref=ObjectReference.from_id(problem.problem_id),
        question="Which bounded plan should be produced?",
        selected_option="recorded_truth_summary",
        rationale="The requested outcome is observational and does not require execution.",
        input_refs=(ObjectReference.from_id(assumption.assumption_id),),
        decided_at=_timestamp(),
    )
    plan = Plan(
        plan_id=_plan_id(),
        problem_ref=ObjectReference.from_id(problem.problem_id),
        objective="Produce a recorded-truth project status summary.",
        assumption_refs=(ObjectReference.from_id(assumption.assumption_id),),
        decision_refs=(ObjectReference.from_id(decision.decision_id),),
        work_refs=(_work_ref(),),
        created_at=_timestamp(),
    )

    contracts = (intent, problem, assumption, decision, plan)
    payload = to_json_compatible(contracts)
    decoded = json.loads(json.dumps(payload, sort_keys=True))

    assert decoded == payload
    assert Intent.from_json_compatible(decoded[0]) == intent
    assert Problem.from_json_compatible(decoded[1]) == problem
    assert Assumption.from_json_compatible(decoded[2]) == assumption
    assert Decision.from_json_compatible(decoded[3]) == decision
    assert Plan.from_json_compatible(decoded[4]) == plan
    assert decoded[4]["work_refs"] == [_work_ref().to_json_compatible()]


def test_cognitive_records_use_object_references_for_cross_record_links() -> None:
    problem = Problem(
        problem_id=_problem_id(),
        intent_ref=ObjectReference.from_id(_intent_id()),
        objective="Investigate a bounded user request.",
        statement="A bounded request needs a plan.",
        created_at=_timestamp(),
    )
    plan = Plan(
        plan_id=_plan_id(),
        problem_ref=ObjectReference.from_id(problem.problem_id),
        objective="Create work references for the bounded request.",
        created_at=_timestamp(),
        work_refs=(_work_ref(),),
    )

    assert problem.intent_ref.kind is ReferenceKind.INTENT
    assert plan.problem_ref.kind is ReferenceKind.PROBLEM
    assert plan.work_refs[0].kind is ReferenceKind.WORK


def test_plan_references_work_without_duplicating_work_item_state() -> None:
    plan_field_names = {field.name for field in fields(Plan)}
    work_field_names = {field.name for field in fields(WorkItem)}

    assert "work_refs" in plan_field_names
    assert "work_id" not in plan_field_names
    assert "state" not in plan_field_names
    assert "dependencies" not in plan_field_names
    assert "required_capabilities" not in plan_field_names
    assert plan_field_names.isdisjoint(
        work_field_names - {"objective", "created_at"},
    )


@pytest.mark.parametrize(
    ("factory", "expected_message"),
    (
        (
            lambda: Problem(
                problem_id=_problem_id(),
                intent_ref=_work_ref(),
                objective="Wrong reference kind.",
                statement="Intent reference must point to an intent.",
                created_at=_timestamp(),
            ),
            "intent_ref must reference intent objects",
        ),
        (
            lambda: Plan(
                plan_id=_plan_id(),
                problem_ref=ObjectReference.from_id(_intent_id()),
                objective="Wrong reference kind.",
                created_at=_timestamp(),
            ),
            "problem_ref must reference problem objects",
        ),
        (
            lambda: Plan(
                plan_id=_plan_id(),
                problem_ref=ObjectReference.from_id(_problem_id()),
                objective="Wrong reference kind.",
                work_refs=(ObjectReference.from_id(_plan_id()),),
                created_at=_timestamp(),
            ),
            "work_refs must reference work objects",
        ),
    ),
)
def test_cognitive_records_reject_wrong_reference_kinds(
    factory: Callable[[], object],
    expected_message: str,
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        factory()
