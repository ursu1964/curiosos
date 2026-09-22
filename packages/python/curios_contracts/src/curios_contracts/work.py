"""Canonical bounded work-item contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import validate_safe_text, validate_safe_token
from curios_contracts.capabilities import CapabilityRequirement
from curios_contracts.identifiers import WorkId
from curios_contracts.references import ObjectReference
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp


class WorkItemState(StrEnum):
    """Runtime state for bounded work intent, separate from execution attempts."""

    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class WorkItem:
    """Canonical bounded unit of executable work.

    Work owns execution intent and scope. It does not embed schedulers, routers,
    providers, agents, or execution-engine behavior.
    """

    work_id: WorkId
    work_type: str
    title: str
    objective: str
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    state: WorkItemState = WorkItemState.CREATED
    dependencies: tuple[WorkId, ...] = ()
    required_capabilities: tuple[CapabilityRequirement, ...] = ()
    inputs: tuple[ObjectReference, ...] = ()
    expected_outputs: tuple[ObjectReference, ...] = ()
    policy_constraint_refs: tuple[ObjectReference, ...] = ()
    authority_ref: ObjectReference | None = None
    principal_ref: ObjectReference | None = None
    evidence_requirement_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.work_id, WorkId):
            msg = "work_id must be a WorkId"
            raise TypeError(msg)
        object.__setattr__(self, "work_type", validate_safe_token(self.work_type, "work_type"))
        object.__setattr__(
            self,
            "title",
            validate_safe_text(self.title, "title", max_length=256),
        )
        object.__setattr__(
            self,
            "objective",
            validate_safe_text(self.objective, "objective", max_length=4096),
        )
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        object.__setattr__(self, "updated_at", UtcTimestamp(self.updated_at))
        object.__setattr__(self, "state", WorkItemState(self.state))
        object.__setattr__(self, "dependencies", _normalize_work_ids(self.dependencies))
        object.__setattr__(
            self,
            "required_capabilities",
            _normalize_capability_requirements(self.required_capabilities),
        )
        object.__setattr__(self, "inputs", _normalize_references(self.inputs, "inputs"))
        object.__setattr__(
            self,
            "expected_outputs",
            _normalize_references(self.expected_outputs, "expected_outputs"),
        )
        object.__setattr__(
            self,
            "policy_constraint_refs",
            _normalize_references(self.policy_constraint_refs, "policy_constraint_refs"),
        )
        if self.authority_ref is not None and not isinstance(self.authority_ref, ObjectReference):
            msg = "authority_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        if self.principal_ref is not None and not isinstance(self.principal_ref, ObjectReference):
            msg = "principal_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "evidence_requirement_refs",
            _normalize_references(
                self.evidence_requirement_refs,
                "evidence_requirement_refs",
            ),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "work item JSON must be an object"
            raise TypeError(msg)
        return cls(
            work_id=WorkId(_require_str(value["work_id"], "work_id")),
            work_type=_require_str(value["work_type"], "work_type"),
            title=_require_str(value["title"], "title"),
            objective=_require_str(value["objective"], "objective"),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            updated_at=UtcTimestamp(_require_str(value["updated_at"], "updated_at")),
            state=WorkItemState(value["state"]),
            dependencies=tuple(
                WorkId(_require_str(item, "dependencies item"))
                for item in _optional_sequence(value.get("dependencies"), "dependencies")
            ),
            required_capabilities=tuple(
                CapabilityRequirement.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("required_capabilities"),
                    "required_capabilities",
                )
            ),
            inputs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("inputs"), "inputs")
            ),
            expected_outputs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("expected_outputs"), "expected_outputs")
            ),
            policy_constraint_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("policy_constraint_refs"),
                    "policy_constraint_refs",
                )
            ),
            authority_ref=_optional_reference(value.get("authority_ref")),
            principal_ref=_optional_reference(value.get("principal_ref")),
            evidence_requirement_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("evidence_requirement_refs"),
                    "evidence_requirement_refs",
                )
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "work_id": str(self.work_id),
            "work_type": self.work_type,
            "title": self.title,
            "objective": self.objective,
            "dependencies": to_json_compatible(self.dependencies),
            "required_capabilities": to_json_compatible(self.required_capabilities),
            "inputs": to_json_compatible(self.inputs),
            "expected_outputs": to_json_compatible(self.expected_outputs),
            "policy_constraint_refs": to_json_compatible(self.policy_constraint_refs),
            "authority_ref": to_json_compatible(self.authority_ref),
            "principal_ref": to_json_compatible(self.principal_ref),
            "evidence_requirement_refs": to_json_compatible(self.evidence_requirement_refs),
            "created_at": to_json_compatible(self.created_at),
            "updated_at": to_json_compatible(self.updated_at),
            "state": self.state.value,
        }


def _normalize_work_ids(work_ids: tuple[WorkId, ...]) -> tuple[WorkId, ...]:
    normalized = tuple(work_ids)
    for work_id in normalized:
        if not isinstance(work_id, WorkId):
            msg = "dependencies must contain WorkId values"
            raise TypeError(msg)
    return normalized


def _normalize_capability_requirements(
    requirements: tuple[CapabilityRequirement, ...],
) -> tuple[CapabilityRequirement, ...]:
    normalized = tuple(requirements)
    for requirement in normalized:
        if not isinstance(requirement, CapabilityRequirement):
            msg = "required_capabilities must contain CapabilityRequirement values"
            raise TypeError(msg)
    return normalized


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


WORK_ITEM_STATE_VALUES: tuple[str, ...] = tuple(member.value for member in WorkItemState)
