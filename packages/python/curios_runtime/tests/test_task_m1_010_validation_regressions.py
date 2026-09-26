from __future__ import annotations

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    AgentInstanceId,
    DecisionId,
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    ProviderId,
    ReferenceKind,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_ollama import LocalModelProfile, ModelProfileStatus
from curios_runtime import (
    RouteCandidateKind,
    RoutingCandidate,
    RoutingDecisionError,
    RoutingDecisionErrorCode,
    RoutingDecisionRequest,
    RoutingDecisionStatus,
    RoutingRationaleCode,
    select_m1_route,
)


def test_required_provider_constraint_matching_candidate_is_valid() -> None:
    request = _request(
        resource_constraints={
            "local_only": True,
            "required_provider_ref": ref_for(ProviderId).to_json_compatible(),
        }
    )

    decision = select_m1_route(request)

    assert decision.status is RoutingDecisionStatus.SELECTED
    assert decision.selected_route is not None
    assert decision.selected_route.kind is RouteCandidateKind.MODEL_PROFILE
    assert (
        decision.resource_constraints["required_provider_ref"]
        == ref_for(ProviderId).to_json_compatible()
    )


def test_valid_required_provider_constraint_without_matching_candidate_is_no_route() -> None:
    request = _request(
        resource_constraints={
            "local_only": True,
            "required_provider_ref": ref_for(ProviderId, 1).to_json_compatible(),
        }
    )

    decision = select_m1_route(request)

    assert decision.status is RoutingDecisionStatus.NO_ROUTE
    assert decision.selected_route is None
    assert decision.rationale.code is RoutingRationaleCode.NO_VALID_ROUTE


@pytest.mark.parametrize(
    "bad_reference",
    (
        ObjectReference(kind=ReferenceKind.WORK, ref_id=fixed_id(WorkId)),
        ObjectReference(kind=ReferenceKind.AGENT_INSTANCE, ref_id=fixed_id(AgentInstanceId)),
        ObjectReference(kind=ReferenceKind.EXECUTION, ref_id=fixed_id(ExecutionId)),
    ),
)
def test_required_provider_constraint_rejects_wrong_reference_kinds(
    bad_reference: ObjectReference,
) -> None:
    with pytest.raises(RoutingDecisionError) as exc:
        _request(
            resource_constraints={
                "local_only": True,
                "required_provider_ref": bad_reference.to_json_compatible(),
            }
        )

    assert exc.value.code is RoutingDecisionErrorCode.INVALID_CONSTRAINT
    assert exc.value.to_json_compatible() == {
        "code": "INVALID_CONSTRAINT",
        "message": "Routing constraints require a canonical provider reference.",
        "retryable": False,
        "operation": "construct_request",
    }


@pytest.mark.parametrize(
    "bad_reference",
    (
        "prv_00000000000000000000000000",
        {},
        {"kind": "provider"},
        {"ref_id": "prv_00000000000000000000000000"},
        {"kind": "provider", "ref_id": 10},
        {"kind": "unknown", "ref_id": "prv_00000000000000000000000000"},
        {"kind": "provider", "ref_id": "token=super-secret"},
    ),
)
def test_required_provider_constraint_rejects_malformed_references_safely(
    bad_reference: object,
) -> None:
    with pytest.raises(RoutingDecisionError) as exc:
        _request(resource_constraints={"local_only": True, "required_provider_ref": bad_reference})

    assert exc.value.code in {
        RoutingDecisionErrorCode.INVALID_CONSTRAINT,
        RoutingDecisionErrorCode.INVALID_REQUEST,
    }
    error_surface = str(exc.value.to_json_compatible())
    assert "super-secret" not in error_surface
    assert "token=" not in error_surface


def _request(*, resource_constraints: object) -> RoutingDecisionRequest:
    work = _work()
    return RoutingDecisionRequest(
        decision_id=fixed_id(DecisionId),
        work=work,
        candidates=(RoutingCandidate.model_profile(work_id=work.work_id, profile=_profile()),),
        requested_at=UTC_LATER,
        producer_ref=ref_for(ProviderId),
        observability_context=ObservabilityContext(work_id=work.work_id),
        resource_constraints=resource_constraints,
    )


def _work() -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId),
        work_type="inspect_current_state",
        title="Inspect current state",
        objective="Inspect current state without execution side effects.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
    )


def _profile() -> LocalModelProfile:
    return LocalModelProfile(
        provider_ref=ObjectReference(kind=ReferenceKind.PROVIDER, ref_id=fixed_id(ProviderId)),
        model_name="llama3.2:latest",
        status=ModelProfileStatus.AVAILABLE,
        metadata=None,
    )
