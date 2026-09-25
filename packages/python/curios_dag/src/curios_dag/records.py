"""Bounded M1 work DAG records and derived dependency state."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import NoReturn, Self

from curios_contracts import (
    CuriosId,
    ObjectReference,
    ReferenceKind,
    UtcTimestamp,
    WorkId,
    WorkItem,
    WorkItemState,
    to_json_compatible,
)
from curios_persistence import (
    PersistenceError,
    PersistenceErrorCode,
    PersistenceRecord,
    PersistenceRecordKind,
    PersistenceStore,
)

_MAX_DAG_NODES = 100
_MAX_DAG_EDGES = 1000


class WorkDagId(CuriosId):
    """Opaque identifier for a bounded M1 work DAG record."""

    prefix = "dag"


class WorkDagNodeReadiness(StrEnum):
    """Derived DAG readiness for one canonical work item."""

    READY = "READY"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    TERMINAL = "TERMINAL"


class WorkDagErrorCode(StrEnum):
    """Stable bounded failure categories for M1 DAG records."""

    CONFLICT = "CONFLICT"
    CYCLE = "CYCLE"
    CORRUPT_RECORD = "CORRUPT_RECORD"
    INVALID_EDGE = "INVALID_EDGE"
    INVALID_NODE = "INVALID_NODE"
    MISSING_WORK = "MISSING_WORK"
    NOT_FOUND = "NOT_FOUND"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"


class WorkDagError(RuntimeError):
    """Bounded M1 DAG error that does not leak native persistence details."""

    def __init__(
        self,
        code: WorkDagErrorCode,
        message: str,
        *,
        retryable: bool,
        operation: str,
    ) -> None:
        super().__init__(message)
        self.code = WorkDagErrorCode(code)
        self.retryable = retryable
        self.operation = operation

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": str(self),
            "retryable": self.retryable,
            "operation": self.operation,
        }


@dataclass(frozen=True, slots=True)
class WorkDagNode:
    """A DAG node that references canonical work without copying work state."""

    work_ref: ObjectReference

    def __post_init__(self) -> None:
        object.__setattr__(self, "work_ref", _require_work_ref(self.work_ref, "work_ref"))

    @classmethod
    def from_work_id(cls, work_id: WorkId) -> Self:
        return cls(work_ref=ObjectReference.from_id(work_id))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        if not isinstance(value, dict):
            msg = "work DAG node JSON must be an object"
            raise TypeError(msg)
        return cls(work_ref=ObjectReference.from_json_compatible(value["work_ref"]))

    def to_json_compatible(self) -> dict[str, object]:
        return {"work_ref": to_json_compatible(self.work_ref)}


@dataclass(frozen=True, slots=True)
class WorkDagEdge:
    """A dependency edge from upstream work to downstream work."""

    upstream_work_ref: ObjectReference
    downstream_work_ref: ObjectReference

    def __post_init__(self) -> None:
        upstream = _require_work_ref(self.upstream_work_ref, "upstream_work_ref")
        downstream = _require_work_ref(self.downstream_work_ref, "downstream_work_ref")
        if upstream == downstream:
            _raise_dag_error(
                WorkDagError(
                    WorkDagErrorCode.INVALID_EDGE,
                    "Work DAG edges cannot reference the same work item twice.",
                    retryable=False,
                    operation="construct_dag",
                )
            )
        object.__setattr__(self, "upstream_work_ref", upstream)
        object.__setattr__(self, "downstream_work_ref", downstream)

    @classmethod
    def from_work_ids(cls, upstream_work_id: WorkId, downstream_work_id: WorkId) -> Self:
        return cls(
            upstream_work_ref=ObjectReference.from_id(upstream_work_id),
            downstream_work_ref=ObjectReference.from_id(downstream_work_id),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        if not isinstance(value, dict):
            msg = "work DAG edge JSON must be an object"
            raise TypeError(msg)
        return cls(
            upstream_work_ref=ObjectReference.from_json_compatible(value["upstream_work_ref"]),
            downstream_work_ref=ObjectReference.from_json_compatible(value["downstream_work_ref"]),
        )

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "upstream_work_ref": to_json_compatible(self.upstream_work_ref),
            "downstream_work_ref": to_json_compatible(self.downstream_work_ref),
        }


@dataclass(frozen=True, slots=True)
class WorkDag:
    """Persistable bounded DAG over canonical ``WorkItem`` references."""

    dag_id: WorkDagId
    created_at: UtcTimestamp | str
    nodes: tuple[WorkDagNode, ...]
    edges: tuple[WorkDagEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.dag_id, WorkDagId):
            msg = "dag_id must be a WorkDagId"
            raise TypeError(msg)
        nodes = tuple(self.nodes)
        edges = tuple(self.edges)
        _validate_bounds(nodes, edges)
        nodes = tuple(sorted(nodes, key=lambda node: str(node.work_ref.ref_id)))
        edges = tuple(
            sorted(
                edges,
                key=lambda edge: (
                    str(edge.upstream_work_ref.ref_id),
                    str(edge.downstream_work_ref.ref_id),
                ),
            )
        )
        _validate_dag_shape(nodes, edges)
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)

    @classmethod
    def from_work_items(
        cls,
        dag_id: WorkDagId,
        work_items: Iterable[WorkItem],
        *,
        created_at: UtcTimestamp | str,
    ) -> Self:
        items = tuple(work_items)
        by_id = _work_items_by_id(items, operation="construct_dag")
        edges: list[WorkDagEdge] = []
        for item in items:
            for dependency_id in item.dependencies:
                if dependency_id not in by_id:
                    _raise_dag_error(
                        WorkDagError(
                            WorkDagErrorCode.INVALID_EDGE,
                            f"Work dependency {dependency_id} is not present in the DAG.",
                            retryable=False,
                            operation="construct_dag",
                        )
                    )
                edges.append(WorkDagEdge.from_work_ids(dependency_id, item.work_id))
        return cls(
            dag_id=dag_id,
            created_at=created_at,
            nodes=tuple(WorkDagNode.from_work_id(item.work_id) for item in items),
            edges=tuple(edges),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        if not isinstance(value, dict):
            msg = "work DAG JSON must be an object"
            raise TypeError(msg)
        return cls(
            dag_id=WorkDagId(_require_str(value["dag_id"], "dag_id")),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            nodes=tuple(
                WorkDagNode.from_json_compatible(item)
                for item in _required_sequence(value["nodes"], "nodes")
            ),
            edges=tuple(
                WorkDagEdge.from_json_compatible(item)
                for item in _optional_sequence(value.get("edges"), "edges")
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "dag_id": str(self.dag_id),
            "created_at": to_json_compatible(self.created_at),
            "nodes": to_json_compatible(self.nodes),
            "edges": to_json_compatible(self.edges),
        }


@dataclass(frozen=True, slots=True)
class WorkDagNodeState:
    """Derived dependency state for a DAG node.

    This is a read model, not persisted work state. Canonical work lifecycle
    remains owned by ``WorkItem``.
    """

    work_ref: ObjectReference
    readiness: WorkDagNodeReadiness
    waiting_on: tuple[ObjectReference, ...] = ()
    blocked_by: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "work_ref", _require_work_ref(self.work_ref, "work_ref"))
        object.__setattr__(self, "readiness", WorkDagNodeReadiness(self.readiness))
        object.__setattr__(self, "waiting_on", _normalize_work_refs(self.waiting_on, "waiting_on"))
        object.__setattr__(self, "blocked_by", _normalize_work_refs(self.blocked_by, "blocked_by"))

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "work_ref": to_json_compatible(self.work_ref),
            "readiness": self.readiness.value,
            "waiting_on": to_json_compatible(self.waiting_on),
            "blocked_by": to_json_compatible(self.blocked_by),
        }


@dataclass(frozen=True, slots=True)
class WorkDagState:
    """Deterministic derived state for a bounded work DAG."""

    dag_id: WorkDagId
    node_states: tuple[WorkDagNodeState, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.dag_id, WorkDagId):
            msg = "dag_id must be a WorkDagId"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "node_states",
            tuple(sorted(self.node_states, key=lambda state: str(state.work_ref.ref_id))),
        )

    def to_json_compatible(self) -> dict[str, object]:
        return {
            "dag_id": str(self.dag_id),
            "node_states": to_json_compatible(self.node_states),
        }


@dataclass(frozen=True, slots=True)
class StoredWorkDag:
    """A persisted work DAG plus its optimistic concurrency version."""

    dag: WorkDag
    version: str


class M1WorkDagRepository:
    """Repository boundary for M1 work DAG records."""

    def __init__(self, store: PersistenceStore) -> None:
        if not isinstance(store, PersistenceStore):
            msg = "store must be a PersistenceStore"
            raise TypeError(msg)
        self._store = store

    def create_dag(self, dag: WorkDag) -> StoredWorkDag:
        if not isinstance(dag, WorkDag):
            msg = "dag must be a WorkDag"
            raise TypeError(msg)
        record = _dag_to_record(dag)
        try:
            with self._store.transaction() as transaction:
                transaction.insert_record(record)
        except PersistenceError as exc:
            _raise_dag_error(_translate_persistence_error(exc, operation="create_dag"))
        return StoredWorkDag(dag=dag, version=_record_version(record))

    def read_dag(self, dag_id: WorkDagId) -> StoredWorkDag | None:
        if not isinstance(dag_id, WorkDagId):
            msg = "dag_id must be a WorkDagId"
            raise TypeError(msg)
        error: WorkDagError | None = None
        try:
            with self._store.transaction() as transaction:
                record = transaction.read_record(PersistenceRecordKind.WORK_DAG, str(dag_id))
        except PersistenceError as exc:
            error = _translate_persistence_error(exc, operation="read_dag")
        if error is not None:
            _raise_dag_error(error)
        if record is None:
            return None
        dag = _record_to_dag(record, operation="read_dag")
        return StoredWorkDag(dag=dag, version=_record_version(record))

    def list_dags(self, *, limit: int) -> tuple[StoredWorkDag, ...]:
        try:
            with self._store.transaction() as transaction:
                records = transaction.list_records(PersistenceRecordKind.WORK_DAG, limit=limit)
        except PersistenceError as exc:
            _raise_dag_error(_translate_persistence_error(exc, operation="list_dags"))
        return tuple(
            StoredWorkDag(
                dag=_record_to_dag(record, operation="list_dags"),
                version=_record_version(record),
            )
            for record in records
        )


def derive_work_dag_state(dag: WorkDag, work_items: Iterable[WorkItem]) -> WorkDagState:
    """Derive readiness/blocking state without scheduling or executing work."""
    if not isinstance(dag, WorkDag):
        msg = "dag must be a WorkDag"
        raise TypeError(msg)
    by_id = _work_items_by_id(tuple(work_items), operation="derive_state")
    dag_work_ids = tuple(_work_id(node.work_ref) for node in dag.nodes)
    missing = tuple(work_id for work_id in dag_work_ids if work_id not in by_id)
    if missing:
        _raise_dag_error(
            WorkDagError(
                WorkDagErrorCode.MISSING_WORK,
                f"Work DAG state is missing canonical work item {missing[0]}.",
                retryable=False,
                operation="derive_state",
            )
        )

    upstream_by_work = _upstream_dependencies(dag)
    states_by_work: dict[WorkId, WorkDagNodeState] = {}
    for work_id in _topological_work_ids(dag):
        item = by_id[work_id]
        work_ref = ObjectReference.from_id(work_id)
        upstream_ids = upstream_by_work.get(work_id, ())
        if item.state in _TERMINAL_WORK_STATES:
            states_by_work[work_id] = WorkDagNodeState(
                work_ref=work_ref,
                readiness=WorkDagNodeReadiness.TERMINAL,
            )
            continue

        blocked_by = tuple(
            ObjectReference.from_id(upstream_id)
            for upstream_id in upstream_ids
            if by_id[upstream_id].state in _FAILED_WORK_STATES
            or states_by_work[upstream_id].readiness is WorkDagNodeReadiness.BLOCKED
        )
        if blocked_by:
            states_by_work[work_id] = WorkDagNodeState(
                work_ref=work_ref,
                readiness=WorkDagNodeReadiness.BLOCKED,
                blocked_by=blocked_by,
            )
            continue

        waiting_on = tuple(
            ObjectReference.from_id(upstream_id)
            for upstream_id in upstream_ids
            if by_id[upstream_id].state is not WorkItemState.COMPLETED
        )
        states_by_work[work_id] = WorkDagNodeState(
            work_ref=work_ref,
            readiness=(WorkDagNodeReadiness.WAITING if waiting_on else WorkDagNodeReadiness.READY),
            waiting_on=waiting_on,
        )

    return WorkDagState(
        dag_id=dag.dag_id,
        node_states=tuple(states_by_work[work_id] for work_id in dag_work_ids),
    )


_TERMINAL_WORK_STATES = frozenset(
    {WorkItemState.COMPLETED, WorkItemState.FAILED, WorkItemState.CANCELLED}
)
_FAILED_WORK_STATES = frozenset({WorkItemState.FAILED, WorkItemState.CANCELLED})


def _require_work_ref(reference: ObjectReference, field_name: str) -> ObjectReference:
    if not isinstance(reference, ObjectReference):
        msg = f"{field_name} must be an ObjectReference"
        raise TypeError(msg)
    if reference.kind is not ReferenceKind.WORK:
        msg = f"{field_name} must reference work objects"
        raise ValueError(msg)
    return reference


def _normalize_work_refs(
    references: tuple[ObjectReference, ...],
    field_name: str,
) -> tuple[ObjectReference, ...]:
    return tuple(
        sorted(
            (_require_work_ref(reference, field_name) for reference in references),
            key=lambda reference: str(reference.ref_id),
        )
    )


def _validate_bounds(nodes: tuple[WorkDagNode, ...], edges: tuple[WorkDagEdge, ...]) -> None:
    if len(nodes) < 1:
        _raise_dag_error(
            WorkDagError(
                WorkDagErrorCode.INVALID_NODE,
                "Work DAGs require at least one node.",
                retryable=False,
                operation="construct_dag",
            )
        )
    if len(nodes) > _MAX_DAG_NODES:
        _raise_dag_error(
            WorkDagError(
                WorkDagErrorCode.INVALID_NODE,
                "Work DAG node count exceeds the bounded M1 limit.",
                retryable=False,
                operation="construct_dag",
            )
        )
    if len(edges) > _MAX_DAG_EDGES:
        _raise_dag_error(
            WorkDagError(
                WorkDagErrorCode.INVALID_EDGE,
                "Work DAG edge count exceeds the bounded M1 limit.",
                retryable=False,
                operation="construct_dag",
            )
        )


def _validate_dag_shape(nodes: tuple[WorkDagNode, ...], edges: tuple[WorkDagEdge, ...]) -> None:
    node_ids = tuple(_work_id(node.work_ref) for node in nodes)
    if len(set(node_ids)) != len(node_ids):
        _raise_dag_error(
            WorkDagError(
                WorkDagErrorCode.INVALID_NODE,
                "Work DAG nodes must reference distinct work items.",
                retryable=False,
                operation="construct_dag",
            )
        )
    node_id_set = frozenset(node_ids)
    edge_pairs = tuple(
        (_work_id(edge.upstream_work_ref), _work_id(edge.downstream_work_ref)) for edge in edges
    )
    if len(set(edge_pairs)) != len(edge_pairs):
        _raise_dag_error(
            WorkDagError(
                WorkDagErrorCode.INVALID_EDGE,
                "Work DAG edges must be distinct.",
                retryable=False,
                operation="construct_dag",
            )
        )
    for upstream_id, downstream_id in edge_pairs:
        if upstream_id not in node_id_set or downstream_id not in node_id_set:
            _raise_dag_error(
                WorkDagError(
                    WorkDagErrorCode.INVALID_EDGE,
                    "Work DAG edges must reference declared DAG nodes.",
                    retryable=False,
                    operation="construct_dag",
                )
            )
    if _contains_cycle(node_ids, edge_pairs):
        _raise_dag_error(
            WorkDagError(
                WorkDagErrorCode.CYCLE,
                "Work DAG edges must be acyclic.",
                retryable=False,
                operation="construct_dag",
            )
        )


def _contains_cycle(
    node_ids: tuple[WorkId, ...],
    edge_pairs: tuple[tuple[WorkId, WorkId], ...],
) -> bool:
    downstream_by_work: dict[WorkId, list[WorkId]] = {work_id: [] for work_id in node_ids}
    for upstream_id, downstream_id in edge_pairs:
        downstream_by_work[upstream_id].append(downstream_id)
    visiting: set[WorkId] = set()
    visited: set[WorkId] = set()

    def visit(work_id: WorkId) -> bool:
        if work_id in visited:
            return False
        if work_id in visiting:
            return True
        visiting.add(work_id)
        try:
            return any(visit(child_id) for child_id in downstream_by_work[work_id])
        finally:
            visiting.remove(work_id)
            visited.add(work_id)

    return any(visit(work_id) for work_id in node_ids)


def _topological_work_ids(dag: WorkDag) -> tuple[WorkId, ...]:
    node_ids = tuple(_work_id(node.work_ref) for node in dag.nodes)
    downstream_by_work: dict[WorkId, list[WorkId]] = {work_id: [] for work_id in node_ids}
    indegree: dict[WorkId, int] = {work_id: 0 for work_id in node_ids}
    for edge in dag.edges:
        upstream_id = _work_id(edge.upstream_work_ref)
        downstream_id = _work_id(edge.downstream_work_ref)
        downstream_by_work[upstream_id].append(downstream_id)
        indegree[downstream_id] += 1

    ready = sorted((work_id for work_id, degree in indegree.items() if degree == 0), key=str)
    ordered: list[WorkId] = []
    while ready:
        work_id = ready.pop(0)
        ordered.append(work_id)
        for child_id in sorted(downstream_by_work[work_id], key=str):
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                ready.append(child_id)
                ready.sort(key=str)
    return tuple(ordered)


def _upstream_dependencies(dag: WorkDag) -> dict[WorkId, tuple[WorkId, ...]]:
    dependencies: dict[WorkId, list[WorkId]] = {_work_id(node.work_ref): [] for node in dag.nodes}
    for edge in dag.edges:
        dependencies[_work_id(edge.downstream_work_ref)].append(_work_id(edge.upstream_work_ref))
    return {
        work_id: tuple(sorted(upstream_ids, key=str))
        for work_id, upstream_ids in dependencies.items()
    }


def _work_items_by_id(items: tuple[WorkItem, ...], *, operation: str) -> dict[WorkId, WorkItem]:
    by_id: dict[WorkId, WorkItem] = {}
    for item in items:
        if not isinstance(item, WorkItem):
            msg = "work_items must contain WorkItem values"
            raise TypeError(msg)
        if item.work_id in by_id:
            _raise_dag_error(
                WorkDagError(
                    WorkDagErrorCode.INVALID_NODE,
                    f"Duplicate canonical work item {item.work_id}.",
                    retryable=False,
                    operation=operation,
                )
            )
        by_id[item.work_id] = item
    return by_id


def _work_id(reference: ObjectReference) -> WorkId:
    _require_work_ref(reference, "work_ref")
    if not isinstance(reference.ref_id, WorkId):
        msg = "work references must contain WorkId values"
        raise TypeError(msg)
    return reference.ref_id


def _dag_to_record(dag: WorkDag) -> PersistenceRecord:
    return PersistenceRecord(
        PersistenceRecordKind.WORK_DAG,
        str(dag.dag_id),
        dag.to_json_compatible(),
    )


def _record_to_dag(record: PersistenceRecord, *, operation: str) -> WorkDag:
    if record.kind is not PersistenceRecordKind.WORK_DAG:
        _raise_dag_error(_corrupt_record(operation))
    try:
        return WorkDag.from_json_compatible(record.payload)
    except Exception:
        _raise_dag_error(_corrupt_record(operation))


def _record_version(record: PersistenceRecord) -> str:
    encoded = json.dumps(
        record.payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _translate_persistence_error(exc: PersistenceError, *, operation: str) -> WorkDagError:
    if exc.code is PersistenceErrorCode.CONFLICT:
        return WorkDagError(
            WorkDagErrorCode.CONFLICT,
            "Work DAG repository record conflicts with existing state.",
            retryable=False,
            operation=operation,
        )
    return WorkDagError(
        WorkDagErrorCode.PERSISTENCE_FAILURE,
        "Work DAG repository persistence operation failed.",
        retryable=exc.retryable,
        operation=operation,
    )


def _corrupt_record(operation: str) -> WorkDagError:
    return WorkDagError(
        WorkDagErrorCode.CORRUPT_RECORD,
        "Persisted work DAG record did not decode as WorkDag.",
        retryable=False,
        operation=operation,
    )


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value


def _required_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if not isinstance(value, list | tuple):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    return tuple(value)


def _optional_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if value is None:
        return ()
    return _required_sequence(value, field_name)


def _raise_dag_error(error: WorkDagError) -> NoReturn:
    raise error from None
