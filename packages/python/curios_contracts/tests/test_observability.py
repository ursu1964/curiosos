from __future__ import annotations

import json

import pytest
from curios_contracts import (
    AgentInstanceId,
    ApplicationId,
    CorrelationId,
    EventId,
    ExecutionId,
    ObjectReference,
    ObservabilityContext,
    ProjectId,
    ReferenceKind,
    TraceId,
    WorkId,
    to_json_compatible,
)


def test_minimal_observability_context_is_valid_and_serializes_empty() -> None:
    context = ObservabilityContext()

    assert context.to_json() == {}
    assert ObservabilityContext.from_json(context.to_json()) == context


def test_fully_populated_observability_context_round_trips() -> None:
    principal_ref = ObjectReference.from_id(AgentInstanceId.generate())
    causation_ref = ObjectReference.from_id(EventId.generate())
    context = ObservabilityContext(
        project_id=ProjectId.generate(),
        application_id=ApplicationId.generate(),
        work_id=WorkId.generate(),
        execution_id=ExecutionId.generate(),
        agent_instance_id=AgentInstanceId.generate(),
        principal_ref=principal_ref,
        trace_id=TraceId.generate(),
        correlation_id=CorrelationId.generate(),
        causation_ref=causation_ref,
    )

    serialized = context.to_json()
    decoded = json.loads(json.dumps(to_json_compatible(context), sort_keys=True))

    assert decoded == serialized
    assert ObservabilityContext.from_json(serialized) == context
    assert serialized["principal_ref"] == principal_ref.to_json_compatible()
    assert serialized["causation_ref"] == causation_ref.to_json_compatible()


def test_trace_and_correlation_ids_are_distinct_runtime_concepts() -> None:
    trace_id = TraceId.generate()
    correlation_id = CorrelationId.generate()
    context = ObservabilityContext(trace_id=trace_id, correlation_id=correlation_id)

    assert context.trace_id == trace_id
    assert context.correlation_id == correlation_id
    assert str(trace_id).startswith("trc_")
    assert str(correlation_id).startswith("cor_")
    with pytest.raises(TypeError, match="trace_id must be TraceId"):
        ObservabilityContext(trace_id=correlation_id)  # type: ignore[arg-type]


def test_work_execution_and_agent_context_fields_are_typed_independently() -> None:
    context = ObservabilityContext(
        work_id=WorkId.generate(),
        execution_id=ExecutionId.generate(),
        agent_instance_id=AgentInstanceId.generate(),
    )

    assert str(context.to_json()["work_id"]).startswith("wrk_")
    assert str(context.to_json()["execution_id"]).startswith("exe_")
    assert str(context.to_json()["agent_instance_id"]).startswith("agi_")


def test_invalid_identifier_type_and_prefix_are_rejected() -> None:
    application_id = ApplicationId.generate()

    with pytest.raises(TypeError, match="project_id must be ProjectId"):
        ObservabilityContext(project_id=application_id)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must start"):
        ObservabilityContext.from_json({"project_id": str(application_id)})


def test_object_reference_validation_rejects_invalid_kind_and_ref_id() -> None:
    with pytest.raises(ValueError):
        ObjectReference.from_json_compatible(
            {"kind": "not_a_kind", "ref_id": str(WorkId.generate())}
        )
    with pytest.raises(TypeError, match="work references require WorkId"):
        ObjectReference(kind=ReferenceKind.WORK, ref_id=EventId.generate())
