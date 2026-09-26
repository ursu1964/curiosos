"""Persistence-local record kind vocabulary."""

from __future__ import annotations

from enum import StrEnum


class PersistenceRecordKind(StrEnum):
    """Runtime record classes owned by the persistence foundation."""

    WORK = "work"
    EXECUTION = "execution"
    EVENT = "event"
    EVIDENCE = "evidence"
    ARTIFACT = "artifact"
    POLICY_DECISION = "policy_decision"
    VERIFICATION = "verification"
    WORK_DAG = "work_dag"
    AGENT_DEFINITION = "agent_definition"
    AGENT_INSTANCE = "agent_instance"
    ROUTING_DECISION = "routing_decision"
