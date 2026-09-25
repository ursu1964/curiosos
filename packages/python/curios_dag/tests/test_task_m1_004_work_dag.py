from __future__ import annotations

import pytest
from contract_fixtures import UTC_LATER, UTC_NOW, fixed_id, ref_for
from curios_contracts import (
    IntentId,
    ObjectReference,
    ReferenceKind,
    WorkId,
    WorkItem,
    WorkItemState,
)
from curios_dag import (
    WorkDag,
    WorkDagEdge,
    WorkDagError,
    WorkDagErrorCode,
    WorkDagId,
    WorkDagNode,
    WorkDagNodeReadiness,
    derive_work_dag_state,
)


def test_work_dag_persists_work_references_without_copying_work_state() -> None:
    inspect = _work(0)
    apply = _work(1, dependencies=(inspect.work_id,))
    verify = _work(2, dependencies=(apply.work_id,))

    dag = WorkDag.from_work_items(_dag_id(), (verify, inspect, apply), created_at=UTC_NOW)
    serialized = dag.to_json_compatible()

    assert serialized == {
        "dag_id": str(_dag_id()),
        "created_at": "2026-09-22T08:15:30Z",
        "nodes": [
            {"work_ref": {"kind": "work", "ref_id": str(inspect.work_id)}},
            {"work_ref": {"kind": "work", "ref_id": str(apply.work_id)}},
            {"work_ref": {"kind": "work", "ref_id": str(verify.work_id)}},
        ],
        "edges": [
            {
                "upstream_work_ref": {"kind": "work", "ref_id": str(inspect.work_id)},
                "downstream_work_ref": {"kind": "work", "ref_id": str(apply.work_id)},
            },
            {
                "upstream_work_ref": {"kind": "work", "ref_id": str(apply.work_id)},
                "downstream_work_ref": {"kind": "work", "ref_id": str(verify.work_id)},
            },
        ],
    }
    assert "state" not in str(serialized)
    assert "required_capabilities" not in str(serialized)
    assert WorkDag.from_json_compatible(serialized) == dag


def test_work_dag_rejects_cycles_duplicate_edges_and_unknown_dependencies() -> None:
    first = _work(0)
    second = _work(1, dependencies=(first.work_id,))

    with pytest.raises(WorkDagError) as cycle:
        WorkDag(
            dag_id=_dag_id(),
            created_at=UTC_NOW,
            nodes=(
                WorkDagNode.from_work_id(first.work_id),
                WorkDagNode.from_work_id(second.work_id),
            ),
            edges=(
                WorkDagEdge.from_work_ids(first.work_id, second.work_id),
                WorkDagEdge.from_work_ids(second.work_id, first.work_id),
            ),
        )
    assert cycle.value.code is WorkDagErrorCode.CYCLE

    with pytest.raises(WorkDagError) as duplicate:
        WorkDag(
            dag_id=_dag_id(),
            created_at=UTC_NOW,
            nodes=(
                WorkDagNode.from_work_id(first.work_id),
                WorkDagNode.from_work_id(second.work_id),
            ),
            edges=(
                WorkDagEdge.from_work_ids(first.work_id, second.work_id),
                WorkDagEdge.from_work_ids(first.work_id, second.work_id),
            ),
        )
    assert duplicate.value.code is WorkDagErrorCode.INVALID_EDGE

    with pytest.raises(WorkDagError) as missing:
        WorkDag.from_work_items(_dag_id(), (second,), created_at=UTC_NOW)
    assert missing.value.code is WorkDagErrorCode.INVALID_EDGE


def test_work_dag_requires_work_references_and_rejects_cross_kind_references() -> None:
    with pytest.raises(ValueError, match="work_ref must reference work"):
        WorkDagNode(work_ref=ref_for(IntentId))

    with pytest.raises(ValueError, match="upstream_work_ref must reference work"):
        WorkDagEdge(upstream_work_ref=ref_for(IntentId), downstream_work_ref=ref_for(WorkId))

    with pytest.raises(TypeError, match="work_ref must be an ObjectReference"):
        WorkDagNode(work_ref="wrk_not_a_reference")  # type: ignore[arg-type]

    assert ObjectReference.from_id(fixed_id(WorkId)).kind is ReferenceKind.WORK


def test_readiness_and_terminal_state_are_derived_from_canonical_work_items() -> None:
    inspect = _work(0, state=WorkItemState.COMPLETED)
    apply = _work(1, dependencies=(inspect.work_id,), state=WorkItemState.CREATED)
    verify = _work(2, dependencies=(apply.work_id,), state=WorkItemState.CREATED)
    dag = WorkDag.from_work_items(_dag_id(), (verify, apply, inspect), created_at=UTC_NOW)

    state = derive_work_dag_state(dag, (inspect, apply, verify))
    by_work = {node.work_ref.ref_id: node for node in state.node_states}

    assert by_work[inspect.work_id].readiness is WorkDagNodeReadiness.TERMINAL
    assert by_work[apply.work_id].readiness is WorkDagNodeReadiness.READY
    assert by_work[verify.work_id].readiness is WorkDagNodeReadiness.WAITING
    assert by_work[verify.work_id].waiting_on == (ref_for(WorkId, 1),)


@pytest.mark.parametrize("failed_state", (WorkItemState.FAILED, WorkItemState.CANCELLED))
def test_failed_or_cancelled_dependencies_block_downstream_without_side_effects(
    failed_state: WorkItemState,
) -> None:
    inspect = _work(0, state=failed_state)
    apply = _work(1, dependencies=(inspect.work_id,), state=WorkItemState.CREATED)
    verify = _work(2, dependencies=(apply.work_id,), state=WorkItemState.CREATED)
    dag = WorkDag.from_work_items(_dag_id(), (inspect, apply, verify), created_at=UTC_NOW)

    state = derive_work_dag_state(dag, (inspect, apply, verify))
    by_work = {node.work_ref.ref_id: node for node in state.node_states}

    assert by_work[inspect.work_id].readiness is WorkDagNodeReadiness.TERMINAL
    assert by_work[apply.work_id].readiness is WorkDagNodeReadiness.BLOCKED
    assert by_work[apply.work_id].blocked_by == (ref_for(WorkId),)
    assert by_work[verify.work_id].readiness is WorkDagNodeReadiness.BLOCKED
    assert by_work[verify.work_id].blocked_by == (ref_for(WorkId, 1),)
    assert apply.state is WorkItemState.CREATED
    assert verify.state is WorkItemState.CREATED


def test_state_derivation_bounds_missing_or_duplicate_work_items() -> None:
    inspect = _work(0)
    apply = _work(1, dependencies=(inspect.work_id,))
    dag = WorkDag.from_work_items(_dag_id(), (inspect, apply), created_at=UTC_NOW)

    with pytest.raises(WorkDagError) as missing:
        derive_work_dag_state(dag, (inspect,))
    assert missing.value.code is WorkDagErrorCode.MISSING_WORK

    with pytest.raises(WorkDagError) as duplicate:
        derive_work_dag_state(dag, (inspect, apply, apply))
    assert duplicate.value.code is WorkDagErrorCode.INVALID_NODE


def test_dag_shape_is_bounded_and_deterministic() -> None:
    works = tuple(_work(ordinal) for ordinal in range(3))
    dag = WorkDag(
        dag_id=_dag_id(),
        created_at=UTC_NOW,
        nodes=tuple(WorkDagNode.from_work_id(work.work_id) for work in reversed(works)),
        edges=(
            WorkDagEdge.from_work_ids(works[1].work_id, works[2].work_id),
            WorkDagEdge.from_work_ids(works[0].work_id, works[1].work_id),
        ),
    )

    assert tuple(node.work_ref.ref_id for node in dag.nodes) == tuple(
        work.work_id for work in works
    )
    assert tuple(
        (edge.upstream_work_ref.ref_id, edge.downstream_work_ref.ref_id) for edge in dag.edges
    ) == ((works[0].work_id, works[1].work_id), (works[1].work_id, works[2].work_id))

    with pytest.raises(WorkDagError) as empty:
        WorkDag(dag_id=_dag_id(), created_at=UTC_NOW, nodes=())
    assert empty.value.code is WorkDagErrorCode.INVALID_NODE


def _dag_id() -> WorkDagId:
    return fixed_id(WorkDagId)


def _work(
    ordinal: int,
    *,
    dependencies: tuple[WorkId, ...] = (),
    state: WorkItemState = WorkItemState.CREATED,
) -> WorkItem:
    return WorkItem(
        work_id=fixed_id(WorkId, ordinal),
        work_type="m1_dag_test",
        title=f"M1 DAG test work {ordinal}",
        objective="Exercise bounded M1 work DAG behavior.",
        dependencies=dependencies,
        created_at=UTC_NOW,
        updated_at=UTC_LATER if state is not WorkItemState.CREATED else UTC_NOW,
        state=state,
    )
