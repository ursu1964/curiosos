"""Execution-attempt record contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts.errors import ContractError
from curios_contracts.evidence import EvidenceReference
from curios_contracts.identifiers import AgentInstanceId, EvidenceId, ExecutionId, WorkId
from curios_contracts.observability import ObservabilityContext
from curios_contracts.references import ObjectReference, ReferenceKind
from curios_contracts.results import Result
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp


class ExecutionState(StrEnum):
    """Runtime state for one execution attempt, distinct from work state."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """One attempt to execute a WorkItem."""

    execution_id: ExecutionId
    work_id: WorkId
    executor_ref: ObjectReference
    started_at: UtcTimestamp
    state: ExecutionState
    ended_at: UtcTimestamp | None = None
    agent_instance_id: AgentInstanceId | None = None
    provider_refs: tuple[ObjectReference, ...] = ()
    result: Result[object] | None = None
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...] = ()
    error_refs: tuple[ObjectReference, ...] = ()
    errors: tuple[ContractError, ...] = ()
    observability_context: ObservabilityContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            msg = "execution_id must be an ExecutionId"
            raise TypeError(msg)
        if not isinstance(self.work_id, WorkId):
            msg = "work_id must be a WorkId"
            raise TypeError(msg)
        if not isinstance(self.executor_ref, ObjectReference):
            msg = "executor_ref must be an ObjectReference"
            raise TypeError(msg)
        object.__setattr__(self, "started_at", UtcTimestamp(self.started_at))
        if self.ended_at is not None:
            object.__setattr__(self, "ended_at", UtcTimestamp(self.ended_at))
        object.__setattr__(self, "state", ExecutionState(self.state))
        if self.agent_instance_id is not None and not isinstance(
            self.agent_instance_id,
            AgentInstanceId,
        ):
            msg = "agent_instance_id must be an AgentInstanceId when provided"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "provider_refs",
            _normalize_provider_references(self.provider_refs, "provider_refs"),
        )
        if self.result is not None and not isinstance(self.result, Result):
            msg = "result must be a Result when provided"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_evidence_refs(self.evidence_refs),
        )
        object.__setattr__(
            self,
            "error_refs",
            _normalize_references(self.error_refs, "error_refs"),
        )
        object.__setattr__(self, "errors", _normalize_errors(self.errors))
        if self.observability_context is not None and not isinstance(
            self.observability_context,
            ObservabilityContext,
        ):
            msg = "observability_context must be an ObservabilityContext when provided"
            raise TypeError(msg)

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "execution record JSON must be an object"
            raise TypeError(msg)
        result = value.get("result")
        return cls(
            execution_id=ExecutionId(_require_str(value["execution_id"], "execution_id")),
            work_id=WorkId(_require_str(value["work_id"], "work_id")),
            executor_ref=ObjectReference.from_json_compatible(value["executor_ref"]),
            started_at=UtcTimestamp(_require_str(value["started_at"], "started_at")),
            state=ExecutionState(value["state"]),
            ended_at=(
                UtcTimestamp(_require_str(value["ended_at"], "ended_at"))
                if value.get("ended_at") is not None
                else None
            ),
            agent_instance_id=(
                AgentInstanceId(_require_str(value["agent_instance_id"], "agent_instance_id"))
                if value.get("agent_instance_id") is not None
                else None
            ),
            provider_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("provider_refs"), "provider_refs")
            ),
            result=Result.from_json_compatible(result) if result is not None else None,
            evidence_refs=tuple(
                _parse_evidence_ref(item)
                for item in _optional_sequence(value.get("evidence_refs"), "evidence_refs")
            ),
            error_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(value.get("error_refs"), "error_refs")
            ),
            errors=tuple(
                ContractError.from_json_compatible(item)
                for item in _optional_sequence(value.get("errors"), "errors")
            ),
            observability_context=(
                ObservabilityContext.from_json(value["observability_context"])
                if value.get("observability_context") is not None
                else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "execution_id": str(self.execution_id),
            "work_id": str(self.work_id),
            "executor_ref": to_json_compatible(self.executor_ref),
            "agent_instance_id": to_json_compatible(self.agent_instance_id),
            "provider_refs": to_json_compatible(self.provider_refs),
            "started_at": to_json_compatible(self.started_at),
            "ended_at": to_json_compatible(self.ended_at),
            "state": self.state.value,
            "result": to_json_compatible(self.result),
            "evidence_refs": to_json_compatible(self.evidence_refs),
            "error_refs": to_json_compatible(self.error_refs),
            "errors": to_json_compatible(self.errors),
            "observability_context": to_json_compatible(self.observability_context),
        }


def _normalize_provider_references(
    references: tuple[ObjectReference, ...],
    field_name: str,
) -> tuple[ObjectReference, ...]:
    normalized = _normalize_references(references, field_name)
    for reference in normalized:
        if reference.kind is not ReferenceKind.PROVIDER:
            msg = f"{field_name} must reference provider objects"
            raise ValueError(msg)
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


def _normalize_evidence_refs(
    evidence_refs: tuple[EvidenceReference | EvidenceId, ...],
) -> tuple[EvidenceReference | EvidenceId, ...]:
    normalized = tuple(evidence_refs)
    for evidence_ref in normalized:
        if not isinstance(evidence_ref, EvidenceReference | EvidenceId):
            msg = "evidence_refs must contain EvidenceReference or EvidenceId values"
            raise TypeError(msg)
    return normalized


def _normalize_errors(errors: tuple[ContractError, ...]) -> tuple[ContractError, ...]:
    normalized = tuple(errors)
    for error in normalized:
        if not isinstance(error, ContractError):
            msg = "errors must contain ContractError values"
            raise TypeError(msg)
    return normalized


def _parse_evidence_ref(value: object) -> EvidenceReference | EvidenceId:
    if isinstance(value, str):
        return EvidenceId(value)
    return EvidenceReference.from_json_compatible(value)


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


EXECUTION_STATE_VALUES: tuple[str, ...] = tuple(member.value for member in ExecutionState)
