"""Agent definition and runtime instance contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from curios_contracts._validation import normalize_details, validate_safe_text, validate_safe_token
from curios_contracts.identifiers import (
    AgentDefinitionId,
    AgentInstanceId,
    CapabilityId,
    ExecutionId,
    WorkId,
)
from curios_contracts.observability import ObservabilityContext
from curios_contracts.references import ObjectReference
from curios_contracts.schema_version import SchemaVersion
from curios_contracts.serialization import to_json_compatible
from curios_contracts.temporal import UtcTimestamp


class AgentInstanceState(StrEnum):
    """Runtime participant state, separate from work and execution-attempt state."""

    CREATED = "CREATED"
    READY = "READY"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """Reusable provider-neutral specification of an agent role."""

    agent_definition_id: AgentDefinitionId
    name: str
    version: SchemaVersion
    purpose: str
    allowed_capability_ids: tuple[CapabilityId, ...]
    constraints: Mapping[str, object] | None = None
    model_requirement_refs: tuple[ObjectReference, ...] = ()
    input_contract_refs: tuple[ObjectReference, ...] = ()
    output_contract_refs: tuple[ObjectReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.agent_definition_id, AgentDefinitionId):
            msg = "agent_definition_id must be an AgentDefinitionId"
            raise TypeError(msg)
        object.__setattr__(self, "name", validate_safe_token(self.name, "name"))
        if not isinstance(self.version, SchemaVersion):
            msg = "version must be a SchemaVersion"
            raise TypeError(msg)
        object.__setattr__(
            self,
            "purpose",
            validate_safe_text(self.purpose, "purpose", max_length=2048),
        )
        object.__setattr__(
            self,
            "allowed_capability_ids",
            _normalize_capability_ids(self.allowed_capability_ids),
        )
        object.__setattr__(self, "constraints", normalize_details(self.constraints))
        object.__setattr__(
            self,
            "model_requirement_refs",
            _normalize_references(self.model_requirement_refs, "model_requirement_refs"),
        )
        object.__setattr__(
            self,
            "input_contract_refs",
            _normalize_references(self.input_contract_refs, "input_contract_refs"),
        )
        object.__setattr__(
            self,
            "output_contract_refs",
            _normalize_references(self.output_contract_refs, "output_contract_refs"),
        )

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "agent definition JSON must be an object"
            raise TypeError(msg)
        return cls(
            agent_definition_id=AgentDefinitionId(
                _require_str(value["agent_definition_id"], "agent_definition_id")
            ),
            name=_require_str(value["name"], "name"),
            version=SchemaVersion.parse(_require_str(value["version"], "version")),
            purpose=_require_str(value["purpose"], "purpose"),
            allowed_capability_ids=tuple(
                CapabilityId(_require_str(item, "allowed_capability_ids item"))
                for item in _optional_sequence(
                    value.get("allowed_capability_ids"),
                    "allowed_capability_ids",
                )
            ),
            constraints=_optional_mapping(value.get("constraints"), "constraints"),
            model_requirement_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("model_requirement_refs"),
                    "model_requirement_refs",
                )
            ),
            input_contract_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("input_contract_refs"),
                    "input_contract_refs",
                )
            ),
            output_contract_refs=tuple(
                ObjectReference.from_json_compatible(item)
                for item in _optional_sequence(
                    value.get("output_contract_refs"),
                    "output_contract_refs",
                )
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "agent_definition_id": str(self.agent_definition_id),
            "name": self.name,
            "version": to_json_compatible(self.version),
            "purpose": self.purpose,
            "allowed_capability_ids": to_json_compatible(self.allowed_capability_ids),
            "constraints": to_json_compatible(self.constraints),
            "model_requirement_refs": to_json_compatible(self.model_requirement_refs),
            "input_contract_refs": to_json_compatible(self.input_contract_refs),
            "output_contract_refs": to_json_compatible(self.output_contract_refs),
        }


@dataclass(frozen=True, slots=True)
class AgentInstance:
    """Concrete runtime agent participant bound to work and optional execution."""

    agent_instance_id: AgentInstanceId
    agent_definition_id: AgentDefinitionId
    work_id: WorkId
    state: AgentInstanceState
    created_at: UtcTimestamp
    execution_id: ExecutionId | None = None
    observability_context: ObservabilityContext | None = None
    authority_ref: ObjectReference | None = None
    principal_ref: ObjectReference | None = None
    started_at: UtcTimestamp | None = None
    ended_at: UtcTimestamp | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.agent_instance_id, AgentInstanceId):
            msg = "agent_instance_id must be an AgentInstanceId"
            raise TypeError(msg)
        if not isinstance(self.agent_definition_id, AgentDefinitionId):
            msg = "agent_definition_id must be an AgentDefinitionId"
            raise TypeError(msg)
        if not isinstance(self.work_id, WorkId):
            msg = "work_id must be a WorkId"
            raise TypeError(msg)
        object.__setattr__(self, "state", AgentInstanceState(self.state))
        object.__setattr__(self, "created_at", UtcTimestamp(self.created_at))
        if self.execution_id is not None and not isinstance(self.execution_id, ExecutionId):
            msg = "execution_id must be an ExecutionId when provided"
            raise TypeError(msg)
        if self.observability_context is not None and not isinstance(
            self.observability_context,
            ObservabilityContext,
        ):
            msg = "observability_context must be an ObservabilityContext when provided"
            raise TypeError(msg)
        if self.authority_ref is not None and not isinstance(self.authority_ref, ObjectReference):
            msg = "authority_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        if self.principal_ref is not None and not isinstance(self.principal_ref, ObjectReference):
            msg = "principal_ref must be an ObjectReference when provided"
            raise TypeError(msg)
        if self.started_at is not None:
            object.__setattr__(self, "started_at", UtcTimestamp(self.started_at))
        if self.ended_at is not None:
            object.__setattr__(self, "ended_at", UtcTimestamp(self.ended_at))

    @classmethod
    def from_json_compatible(cls, value: object) -> Self:
        """Parse the canonical JSON-compatible representation."""
        if not isinstance(value, dict):
            msg = "agent instance JSON must be an object"
            raise TypeError(msg)
        return cls(
            agent_instance_id=AgentInstanceId(
                _require_str(value["agent_instance_id"], "agent_instance_id")
            ),
            agent_definition_id=AgentDefinitionId(
                _require_str(value["agent_definition_id"], "agent_definition_id")
            ),
            work_id=WorkId(_require_str(value["work_id"], "work_id")),
            state=AgentInstanceState(value["state"]),
            created_at=UtcTimestamp(_require_str(value["created_at"], "created_at")),
            execution_id=(
                ExecutionId(_require_str(value["execution_id"], "execution_id"))
                if value.get("execution_id") is not None
                else None
            ),
            observability_context=(
                ObservabilityContext.from_json(value["observability_context"])
                if value.get("observability_context") is not None
                else None
            ),
            authority_ref=_optional_reference(value.get("authority_ref")),
            principal_ref=_optional_reference(value.get("principal_ref")),
            started_at=(
                UtcTimestamp(_require_str(value["started_at"], "started_at"))
                if value.get("started_at") is not None
                else None
            ),
            ended_at=(
                UtcTimestamp(_require_str(value["ended_at"], "ended_at"))
                if value.get("ended_at") is not None
                else None
            ),
        )

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return {
            "agent_instance_id": str(self.agent_instance_id),
            "agent_definition_id": str(self.agent_definition_id),
            "work_id": str(self.work_id),
            "execution_id": to_json_compatible(self.execution_id),
            "state": self.state.value,
            "observability_context": to_json_compatible(self.observability_context),
            "authority_ref": to_json_compatible(self.authority_ref),
            "principal_ref": to_json_compatible(self.principal_ref),
            "created_at": to_json_compatible(self.created_at),
            "started_at": to_json_compatible(self.started_at),
            "ended_at": to_json_compatible(self.ended_at),
        }


def _normalize_capability_ids(
    capability_ids: tuple[CapabilityId, ...],
) -> tuple[CapabilityId, ...]:
    normalized = tuple(capability_ids)
    for capability_id in normalized:
        if not isinstance(capability_id, CapabilityId):
            msg = "allowed_capability_ids must contain CapabilityId values"
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


def _optional_mapping(value: object, field_name: str) -> Mapping[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be an object when provided"
        raise TypeError(msg)
    for key in value:
        if not isinstance(key, str):
            msg = f"{field_name} keys must be strings"
            raise TypeError(msg)
    return value


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


AGENT_INSTANCE_STATE_VALUES: tuple[str, ...] = tuple(member.value for member in AgentInstanceState)
