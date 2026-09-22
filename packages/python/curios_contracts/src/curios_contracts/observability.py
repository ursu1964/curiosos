"""Curios-owned observability context contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from curios_contracts.identifiers import (
    AgentInstanceId,
    ApplicationId,
    CorrelationId,
    CuriosId,
    ExecutionId,
    MilestoneId,
    ProjectId,
    TraceId,
    WorkId,
    WorkstreamId,
)
from curios_contracts.references import ObjectReference


@dataclass(frozen=True, slots=True)
class ObservabilityContext:
    """Composable context for correlating canonical runtime facts."""

    project_id: ProjectId | None = None
    application_id: ApplicationId | None = None
    milestone_id: MilestoneId | None = None
    workstream_id: WorkstreamId | None = None
    work_id: WorkId | None = None
    execution_id: ExecutionId | None = None
    agent_instance_id: AgentInstanceId | None = None
    principal_ref: ObjectReference | None = None
    trace_id: TraceId | None = None
    correlation_id: CorrelationId | None = None
    causation_ref: ObjectReference | None = None

    def __post_init__(self) -> None:
        _require_optional(self.project_id, ProjectId, "project_id")
        _require_optional(self.application_id, ApplicationId, "application_id")
        _require_optional(self.milestone_id, MilestoneId, "milestone_id")
        _require_optional(self.workstream_id, WorkstreamId, "workstream_id")
        _require_optional(self.work_id, WorkId, "work_id")
        _require_optional(self.execution_id, ExecutionId, "execution_id")
        _require_optional(self.agent_instance_id, AgentInstanceId, "agent_instance_id")
        _require_optional(self.principal_ref, ObjectReference, "principal_ref")
        _require_optional(self.trace_id, TraceId, "trace_id")
        _require_optional(self.correlation_id, CorrelationId, "correlation_id")
        _require_optional(self.causation_ref, ObjectReference, "causation_ref")

    @classmethod
    def from_json(cls, value: object) -> Self:
        """Parse an observability context from canonical JSON object form."""
        if not isinstance(value, dict):
            msg = "observability context JSON value must be an object"
            raise TypeError(msg)

        return cls(
            project_id=_parse_optional_id(value, "project_id", ProjectId),
            application_id=_parse_optional_id(value, "application_id", ApplicationId),
            milestone_id=_parse_optional_id(value, "milestone_id", MilestoneId),
            workstream_id=_parse_optional_id(value, "workstream_id", WorkstreamId),
            work_id=_parse_optional_id(value, "work_id", WorkId),
            execution_id=_parse_optional_id(value, "execution_id", ExecutionId),
            agent_instance_id=_parse_optional_id(value, "agent_instance_id", AgentInstanceId),
            principal_ref=_parse_optional_reference(value, "principal_ref"),
            trace_id=_parse_optional_id(value, "trace_id", TraceId),
            correlation_id=_parse_optional_id(value, "correlation_id", CorrelationId),
            causation_ref=_parse_optional_reference(value, "causation_ref"),
        )

    def to_json(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        serialized: dict[str, object] = {}
        for field_name, value in (
            ("project_id", self.project_id),
            ("application_id", self.application_id),
            ("milestone_id", self.milestone_id),
            ("workstream_id", self.workstream_id),
            ("work_id", self.work_id),
            ("execution_id", self.execution_id),
            ("agent_instance_id", self.agent_instance_id),
            ("principal_ref", self.principal_ref),
            ("trace_id", self.trace_id),
            ("correlation_id", self.correlation_id),
            ("causation_ref", self.causation_ref),
        ):
            if value is None:
                continue
            if isinstance(value, ObjectReference):
                serialized[field_name] = value.to_json_compatible()
            else:
                serialized[field_name] = str(value)
        return serialized

    def to_json_compatible(self) -> dict[str, object]:
        """Return the canonical JSON-compatible object representation."""
        return self.to_json()


def _require_optional[ValueT](value: object, expected_type: type[ValueT], field_name: str) -> None:
    if value is not None and not isinstance(value, expected_type):
        msg = f"{field_name} must be {expected_type.__name__} when present"
        raise TypeError(msg)


def _parse_optional_id[IdT: CuriosId](
    value: dict[object, object],
    field_name: str,
    id_type: type[IdT],
) -> IdT | None:
    raw_value = value.get(field_name)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        msg = f"{field_name} must be a string when present"
        raise TypeError(msg)
    return id_type(raw_value)


def _parse_optional_reference(
    value: dict[object, object],
    field_name: str,
) -> ObjectReference | None:
    raw_value = value.get(field_name)
    if raw_value is None:
        return None
    return ObjectReference.from_json_compatible(raw_value)
