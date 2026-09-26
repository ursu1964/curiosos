from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    DecisionId,
    ObjectReference,
    ObservabilityContext,
    ProviderId,
    ReferenceKind,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_ollama import LocalModelProfile, ModelProfileStatus
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
)
from curios_runtime import (
    M1RoutingDecisionRepository,
    RouteCandidateKind,
    RoutingCandidate,
    RoutingDecisionError,
    RoutingDecisionErrorCode,
    RoutingDecisionRecord,
    RoutingDecisionRequest,
    RoutingDecisionStatus,
    RoutingRationaleCode,
    select_m1_route,
)

_SUPPORTED_WORK_TYPES = (
    "collect_recorded_context",
    "compose_recorded_summary",
    "verify_recorded_summary",
    "inspect_current_state",
    "apply_bounded_change",
    "verify_bounded_change",
)


def test_selects_single_valid_deterministic_executor_without_execution_side_effects() -> None:
    request = _request(candidates=(_executor_candidate(),))

    decision = select_m1_route(request)

    assert decision.status is RoutingDecisionStatus.SELECTED
    assert decision.selected_route == _executor_candidate()
    assert decision.rationale.code is RoutingRationaleCode.SELECTED_SINGLE_VALID_ROUTE
    assert decision.work_ref == ref_for(WorkId)
    assert decision.resource_constraints == {"local_only": True}
    assert not hasattr(decision, "execute")
    assert not hasattr(decision, "invoke_model")
    assert not hasattr(decision, "transition_agent")


def test_model_profile_candidate_reuses_discovery_record_fields_without_metadata_copy() -> None:
    profile = _profile(metadata={"provider_family": "ollama"})

    candidate = RoutingCandidate.model_profile(work_id=fixed_id(WorkId), profile=profile)

    assert candidate.kind is RouteCandidateKind.MODEL_PROFILE
    assert candidate.provider_ref == ref_for(ProviderId)
    assert candidate.model_name == "llama3.2:latest"
    assert candidate.model_status == ModelProfileStatus.AVAILABLE.value
    assert "secret" not in candidate.to_json_compatible()
    assert not hasattr(candidate, "metadata")


def test_candidate_permutation_produces_stable_selected_decision() -> None:
    first = _request(candidates=(_no_model(), _executor_candidate()))
    second = _request(candidates=(_executor_candidate(), _no_model()))

    assert (
        select_m1_route(first).to_json_compatible() == select_m1_route(second).to_json_compatible()
    )


def test_multiple_valid_candidates_produce_no_route_without_hidden_ranking() -> None:
    decision = select_m1_route(
        _request(
            candidates=(
                _executor_candidate(executor_name="deterministic_m1"),
                _model_candidate(model_name="llama3.2:latest"),
            ),
        )
    )

    assert decision.status is RoutingDecisionStatus.NO_ROUTE
    assert decision.selected_route is None
    assert decision.rationale.code is RoutingRationaleCode.AMBIGUOUS_ROUTE
    assert "best" not in decision.rationale.message.lower()
    assert "rank" not in decision.rationale.message.lower()


def test_constraints_can_select_route_kind_without_provider_or_model_invocation() -> None:
    decision = select_m1_route(
        _request(
            candidates=(
                _executor_candidate(executor_name="deterministic_m1"),
                _model_candidate(model_name="llama3.2:latest"),
            ),
            resource_constraints={
                "local_only": True,
                "required_route_kind": RouteCandidateKind.MODEL_PROFILE.value,
                "required_provider_ref": ref_for(ProviderId).to_json_compatible(),
            },
        )
    )

    assert decision.status is RoutingDecisionStatus.SELECTED
    assert decision.selected_route is not None
    assert decision.selected_route.kind is RouteCandidateKind.MODEL_PROFILE
    assert not hasattr(decision.selected_route, "generate")
    assert not hasattr(decision.selected_route, "chat")


@pytest.mark.parametrize(
    "case",
    ("empty", "no-model", "wrong-work-type"),
)
def test_no_valid_candidate_records_bounded_no_route(case: str) -> None:
    candidates = {
        "empty": (),
        "no-model": (_no_model(),),
        "wrong-work-type": (
            _executor_candidate(supported_work_types=("compose_recorded_summary",)),
        ),
    }[case]
    decision = select_m1_route(_request(candidates=candidates))

    assert decision.status is RoutingDecisionStatus.NO_ROUTE
    assert decision.selected_route is None
    assert decision.rationale.code is RoutingRationaleCode.NO_VALID_ROUTE


def test_cross_work_candidate_is_rejected_boundedly() -> None:
    with pytest.raises(RoutingDecisionError) as exc:
        _request(candidates=(_executor_candidate(work_id=fixed_id(WorkId, 1)),))

    assert exc.value.code is RoutingDecisionErrorCode.INVALID_REQUEST
    assert "work" in str(exc.value).lower()


def test_duplicate_candidate_identity_is_rejected_without_choosing_first() -> None:
    with pytest.raises(RoutingDecisionError) as exc:
        _request(candidates=(_executor_candidate(), _executor_candidate()))

    assert exc.value.code is RoutingDecisionErrorCode.INVALID_CANDIDATE


@pytest.mark.parametrize(
    "constraints",
    (
        {"unsupported": True},
        {"required_route_kind": "largest_model"},
        {"local_only": False},
        {"token": "secret"},
        {"required_route_kind": "model_profile", "note": "password=hunter2"},
    ),
)
def test_invalid_or_secret_shaped_constraints_fail_boundedly(
    constraints: Mapping[str, object],
) -> None:
    with pytest.raises(RoutingDecisionError) as exc:
        _request(candidates=(_executor_candidate(),), resource_constraints=constraints)

    assert exc.value.code in {
        RoutingDecisionErrorCode.INVALID_CONSTRAINT,
        RoutingDecisionErrorCode.INVALID_REQUEST,
    }
    assert "hunter2" not in str(exc.value)
    assert "secret" not in str(exc.value)


def test_routing_decision_round_trip_and_repository_append_order() -> None:
    repository = M1RoutingDecisionRepository(_MemoryStore())
    first = select_m1_route(_request(decision_id=fixed_id(DecisionId, 0)))
    second = select_m1_route(
        _request(
            decision_id=fixed_id(DecisionId, 1),
            candidates=(_executor_candidate(executor_name="deterministic_m1"), _no_model()),
        )
    )

    stored_first = repository.create_decision(first)
    stored_second = repository.create_decision(second)

    assert repository.read_decision(first.decision_id) == stored_first
    assert repository.list_decisions(limit=10) == (stored_first, stored_second)
    assert RoutingDecisionRecord.from_json_compatible(first.to_json_compatible()) == first

    with pytest.raises(RoutingDecisionError) as duplicate:
        repository.create_decision(first)
    assert duplicate.value.code is RoutingDecisionErrorCode.CONFLICT


def test_repository_bounds_corrupt_and_wrong_kind_records() -> None:
    decision = select_m1_route(_request())
    corrupt_payload = dict(decision.to_json_compatible())
    corrupt_payload["status"] = "ROUTE_BY_QUALITY"
    repository = M1RoutingDecisionRepository(
        _CorruptStore(
            PersistenceRecord(
                PersistenceRecordKind.ROUTING_DECISION,
                str(decision.decision_id),
                corrupt_payload,
            )
        )
    )
    wrong_kind = M1RoutingDecisionRepository(
        _CorruptStore(
            PersistenceRecord(
                PersistenceRecordKind.WORK,
                str(decision.decision_id),
                decision.to_json_compatible(),
            )
        )
    )

    with pytest.raises(RoutingDecisionError) as corrupt:
        repository.read_decision(decision.decision_id)
    with pytest.raises(RoutingDecisionError) as wrong:
        wrong_kind.list_decisions(limit=10)

    assert corrupt.value.code is RoutingDecisionErrorCode.CORRUPT_RECORD
    assert wrong.value.code is RoutingDecisionErrorCode.CORRUPT_RECORD


def test_repository_translates_persistence_failures_without_native_leakage() -> None:
    repository = M1RoutingDecisionRepository(_FailingStore())

    with pytest.raises(RoutingDecisionError) as exc:
        repository.create_decision(select_m1_route(_request()))

    assert exc.value.to_json_compatible() == {
        "code": "PERSISTENCE_FAILURE",
        "message": "Routing decision persistence operation failed.",
        "retryable": True,
        "operation": "create_decision",
    }
    assert "provider_native" not in str(exc.value)


def test_decision_record_contains_no_later_runner_or_execution_authority() -> None:
    payload = select_m1_route(_request()).to_json_compatible()
    payload_text = str(payload).lower()

    assert "execution_id" not in payload_text
    assert "agent_instance_id" not in payload_text
    assert "provider_error" not in payload_text
    assert "prompt" not in payload_text
    assert "generated" not in payload_text
    assert "schedule" not in payload_text
    assert "retry" not in payload_text


def _request(
    *,
    decision_id: DecisionId | None = None,
    work: WorkItem | None = None,
    candidates: tuple[RoutingCandidate, ...] | None = None,
    resource_constraints: Mapping[str, object] | None = None,
) -> RoutingDecisionRequest:
    selected_work = work or _work()
    selected_candidates = (
        (_executor_candidate(work_id=selected_work.work_id),) if candidates is None else candidates
    )
    return RoutingDecisionRequest(
        decision_id=decision_id or fixed_id(DecisionId),
        work=selected_work,
        candidates=selected_candidates,
        requested_at=UTC_LATER,
        producer_ref=ref_for(ProviderId),
        observability_context=ObservabilityContext(work_id=selected_work.work_id),
        resource_constraints=(
            {"local_only": True} if resource_constraints is None else resource_constraints
        ),
    )


def _work(work_type: str = "inspect_current_state", ordinal: int = 0) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal),
        work_type=work_type,
        title=f"Inspect current state {ordinal}",
        objective="Inspect current state without execution side effects.",
        created_at=UTC_NOW,
        updated_at=UTC_NOW,
        state=WorkItemState.READY,
    )


def _executor_candidate(
    *,
    work_id: WorkId | None = None,
    executor_name: str = "deterministic_m1",
    supported_work_types: tuple[str, ...] = _SUPPORTED_WORK_TYPES,
) -> RoutingCandidate:
    return RoutingCandidate.deterministic_executor(
        work_id=work_id or fixed_id(WorkId),
        executor_name=executor_name,
        supported_work_types=supported_work_types,
    )


def _model_candidate(
    *,
    work_id: WorkId | None = None,
    model_name: str,
) -> RoutingCandidate:
    return RoutingCandidate.model_profile(
        work_id=work_id or fixed_id(WorkId),
        profile=_profile(model_name=model_name),
    )


def _no_model(*, work_id: WorkId | None = None) -> RoutingCandidate:
    return RoutingCandidate.no_model(work_id=work_id or fixed_id(WorkId))


def _profile(
    *,
    model_name: str = "llama3.2:latest",
    metadata: Mapping[str, object] | None = None,
) -> LocalModelProfile:
    return LocalModelProfile(
        provider_ref=ObjectReference(kind=ReferenceKind.PROVIDER, ref_id=fixed_id(ProviderId)),
        model_name=model_name,
        status=ModelProfileStatus.AVAILABLE,
        metadata=metadata,
    )


class _MemoryStore(PersistenceStore):
    def __init__(self) -> None:
        self._records: dict[tuple[PersistenceRecordKind, str], PersistenceRecord] = {}
        self._order: list[tuple[PersistenceRecordKind, str]] = []

    @contextmanager
    def transaction(self) -> Iterator[_MemoryTransaction]:  # type: ignore[override]
        yield _MemoryTransaction(self)


class _MemoryTransaction:
    def __init__(self, store: _MemoryStore) -> None:
        self._store = store

    def insert_record(self, record: PersistenceRecord) -> None:
        key = (record.kind, record.record_id)
        if key in self._store._records:
            raise PersistenceError(
                PersistenceErrorCode.CONFLICT,
                "duplicate",
                retryable=False,
                operation="insert",
                cause_type="IntegrityError",
            )
        self._store._records[key] = record
        self._store._order.append(key)

    def read_record(
        self,
        kind: PersistenceRecordKind,
        record_id: str,
    ) -> PersistenceRecord | None:
        return self._store._records.get((PersistenceRecordKind(kind), record_id))

    def list_records(
        self,
        kind: PersistenceRecordKind,
        *,
        limit: int,
    ) -> tuple[PersistenceRecord, ...]:
        normalized_kind = PersistenceRecordKind(kind)
        return tuple(
            self._store._records[key] for key in self._store._order if key[0] is normalized_kind
        )[:limit]


class _CorruptStore(_MemoryStore):
    def __init__(self, record: PersistenceRecord) -> None:
        super().__init__()
        self._records[(PersistenceRecordKind.ROUTING_DECISION, record.record_id)] = record
        self._order.append((PersistenceRecordKind.ROUTING_DECISION, record.record_id))


class _FailingStore(PersistenceStore):
    def __init__(self) -> None:
        pass

    @contextmanager
    def transaction(self) -> Iterator[_FailingTransaction]:  # type: ignore[override]
        yield _FailingTransaction()


class _FailingTransaction:
    def insert_record(self, record: PersistenceRecord) -> None:
        raise PersistenceError(
            PersistenceErrorCode.CONNECTIVITY,
            "provider_native token=secret",
            retryable=True,
            operation=f"insert_{record.kind.value}",
            cause_type="OperationalError",
        )
