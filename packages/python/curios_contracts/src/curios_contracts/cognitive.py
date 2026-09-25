"""Canonical cognitive intent, problem, assumption, decision, and plan records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from curios_contracts._validation import validate_safe_text
from curios_contracts.identifiers import AssumptionId, DecisionId, IntentId, PlanId, ProblemId
from curios_contracts.references import ObjectReference, ReferenceKind
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp


@dataclass(frozen=True, slots=True)
class Intent:
    """Submitted user/system intent as canonical cognitive input."""

    intent_id: IntentId
    objective: str
    submitted_at: UtcTimestamp
    source_ref: ObjectReference | None = None
    context_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.intent_id, IntentId):
            msg = "intent_id must be an IntentId"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "objective",
            validate_safe_text(self.objective, "objective", max_length=4096),
        )
        object.__setattr__(self, "submitted_at", UtcTimestamp(self.submitted_at))
        if self.source_ref is not None and not isinstance(self.source_ref, ObjectReference):
            msg = "source_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "context_refs",
            _normalize_references(self.context_refs, "context_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "intent JSON must be an object"
            raise TypeError(msg)
        return cls(
            intent_id=IntentId(_require_str(value["intent_id"], "intent_id")),
            objective=_require_str(value["objective"], "objective"),
            submitted_at=UtcTimestamp(_require_str(value["submitted_at"], "submitted_at")),
            source_ref=_optional_reference(value.get("source_ref")),
            context_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("context_refs"), "context_refs")
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "intent_id": str(self.intent_id),
            "objective": self.objective,
            "source_ref": to_json_compatible(self.source_ref),
            "context_refs": to_json_compatible(self.context_refs),
            "submitted_at": to_json_compatible(self.submitted_at),
        }


@dataclass(frozen=True, slots=True)
class Problem:
    """Bounded problem statement derived from an intent."""

    problem_id: ProblemId
    intent_ref: ObjectReference
    objective: str
    statement: str
    created_at: UtcTimestamp
    context_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.problem_id, ProblemId):
            msg = "problem_id must be a ProblemId"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "intent_ref",
            _require_reference_kind(self.intent_ref, ReferenceKind.INTENT, "intent_ref"),
        )
        object.__setattr__(
            self,
            "objective",
            validate_safe_text(self.objective, "objective", max_length=4096),
        )
        object.__setattr__(
            self,
            "statement",
            validate_safe_text(self.statement, "statement", max_length=4096),
        )
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        object.__setattr__(
            self,
            "context_refs",
            _normalize_references(self.context_refs, "context_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "problem JSON must be an object"
            raise TypeError(msg)
        return cls(
            problem_id=ProblemId(_require_str(value["problem_id"], "problem_id")),
            intent_ref=ObjectReference.from_json_compatible(value["intent_ref"]),
            objective=_require_str(value["objective"], "objective"),
            statement=_require_str(value["statement"], "statement"),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            context_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("context_refs"), "context_refs")
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "problem_id": str(self.problem_id),
            "intent_ref": to_json_compatible(self.intent_ref),
            "objective": self.objective,
            "statement": self.statement,
            "context_refs": to_json_compatible(self.context_refs),
            "created_at": to_json_compatible(self.created_at),
        }


@dataclass(frozen=True, slots=True)
class Assumption:
    """Bounded assumption linked to a canonical subject."""

    assumption_id: AssumptionId
    subject_ref: ObjectReference
    statement: str
    created_at: UtcTimestamp
    basis_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.assumption_id, AssumptionId):
            msg = "assumption_id must be an AssumptionId"
            raise TypeError(msg)
        if not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "statement",
            validate_safe_text(self.statement, "statement", max_length=4096),
        )
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        object.__setattr__(
            self,
            "basis_refs",
            _normalize_references(self.basis_refs, "basis_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "assumption JSON must be an object"
            raise TypeError(msg)
        return cls(
            assumption_id=AssumptionId(_require_str(value["assumption_id"], "assumption_id")),
            subject_ref=ObjectReference.from_json_compatible(value["subject_ref"]),
            statement=_require_str(value["statement"], "statement"),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            basis_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("basis_refs"), "basis_refs")
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "assumption_id": str(self.assumption_id),
            "subject_ref": to_json_compatible(self.subject_ref),
            "statement": self.statement,
            "basis_refs": to_json_compatible(self.basis_refs),
            "created_at": to_json_compatible(self.created_at),
        }


@dataclass(frozen=True, slots=True)
class Decision:
    """Bounded cognitive decision fact for planning/runtime reasoning."""

    decision_id: DecisionId
    subject_ref: ObjectReference
    question: str
    selected_option: str
    rationale: str
    decided_at: UtcTimestamp
    input_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, DecisionId):
            msg = "decision_id must be a DecisionId"
            raise TypeError(msg)
        if not isinstance(self.subject_ref, ObjectReference):
            msg = "subject_ref must be an ObjectReference"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "question",
            validate_safe_text(self.question, "question", max_length=2048),
        )
        object.__setattr__(
            self,
            "selected_option",
            validate_safe_text(self.selected_option, "selected_option", max_length=1024),
        )
        object.__setattr__(
            self,
            "rationale",
            validate_safe_text(self.rationale, "rationale", max_length=4096),
        )
        object.__setattr__(self, "decided_at", UtcTimestamp(self.decided_at))
        object.__setattr__(
            self,
            "input_refs",
            _normalize_references(self.input_refs, "input_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "decision JSON must be an object"
            raise TypeError(msg)
        return cls(
            decision_id=DecisionId(_require_str(value["decision_id"], "decision_id")),
            subject_ref=ObjectReference.from_json_compatible(value["subject_ref"]),
            question=_require_str(value["question"], "question"),
            selected_option=_require_str(value["selected_option"], "selected_option"),
            rationale=_require_str(value["rationale"], "rationale"),
            decided_at=UtcTimestamp(_require_str(value["decided_at"], "decided_at")),
            input_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("input_refs"), "input_refs")
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "decision_id": str(self.decision_id),
            "subject_ref": to_json_compatible(self.subject_ref),
            "question": self.question,
            "selected_option": self.selected_option,
            "rationale": self.rationale,
            "input_refs": to_json_compatible(self.input_refs),
            "decided_at": to_json_compatible(self.decided_at),
        }


@dataclass(frozen=True, slots=True)
class Plan:
    """Bounded plan record referencing work without duplicating work state."""

    plan_id: PlanId
    problem_ref: ObjectReference
    objective: str
    created_at: UtcTimestamp
    assumption_refs: tuple[ObjectReference, ...] = ()
    decision_refs: tuple[ObjectReference, ...] = ()
    work_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.plan_id, PlanId):
            msg = "plan_id must be a PlanId"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "problem_ref",
            _require_reference_kind(self.problem_ref, ReferenceKind.PROBLEM, "problem_ref"),
        )
        object.__setattr__(
            self,
            "objective",
            validate_safe_text(self.objective, "objective", max_length=4096),
        )
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        object.__setattr__(
            self,
            "assumption_refs",
            _normalize_references_of_kind(
                self.assumption_refs,
                ReferenceKind.ASSUMPTION,
                "assumption_refs",
            ),
        )
        object.__setattr__(
            self,
            "decision_refs",
            _normalize_references_of_kind(
                self.decision_refs,
                ReferenceKind.DECISION,
                "decision_refs",
            ),
        )
        object.__setattr__(
            self,
            "work_refs",
            _normalize_references_of_kind(self.work_refs, ReferenceKind.WORK, "work_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "plan JSON must be an object"
            raise TypeError(msg)
        return cls(
            plan_id=PlanId(_require_str(value["plan_id"], "plan_id")),
            problem_ref=ObjectReference.from_json_compatible(value["problem_ref"]),
            objective=_require_str(value["objective"], "objective"),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            assumption_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("assumption_refs"), "assumption_refs")
            ),
            decision_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("decision_refs"), "decision_refs")
            ),
            work_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("work_refs"), "work_refs")
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "plan_id": str(self.plan_id),
            "problem_ref": to_json_compatible(self.problem_ref),
            "objective": self.objective,
            "assumption_refs": to_json_compatible(self.assumption_refs),
            "decision_refs": to_json_compatible(self.decision_refs),
            "work_refs": to_json_compatible(self.work_refs),
            "created_at": to_json_compatible(self.created_at),
        }


def _normalize_references(
    references: tuple[ObjectReference, ...],
    field_name: str,
) -> tuple[ObjectReference, ...]:
    normalized = tuple(references)
    for reference in normalized:
        if not isinstance(reference, ObjectReference):
            msg = f"{field_name} must contain ObjectReference values"
            raise TypeError(msg)
    return normalized


def _normalize_references_of_kind(
    references: tuple[ObjectReference, ...],
    expected_kind: ReferenceKind,
    field_name: str,
) -> tuple[ObjectReference, ...]:
    return tuple(
        _require_reference_kind(reference, expected_kind, field_name)
        for reference in _normalize_references(references, field_name)
    )


def _require_reference_kind(
    reference: ObjectReference,
    expected_kind: ReferenceKind,
    field_name: str,
) -> ObjectReference:
    if not isinstance(reference, ObjectReference):
        msg = f"{field_name} must be an ObjectReference"
        raise TypeError(msg)
    if reference.kind is not expected_kind:
        msg = f"{field_name} must reference {expected_kind.value} objects"
        raise ValueError(msg)
    return reference


def _optional_reference(value: object) -> ObjectReference | None:
    if value is None:
        return None
    return ObjectReference.from_json_compatible(value)


def _optional_sequence(value: object, field_name: str) -> tuple[object, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        msg = f"{field_name} must be a list"
        raise TypeError(msg)
    return tuple(value)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    return value
