"""Persistence-local record kind vocabulary."""

from __future__ import annotations

from enum import StrEnum


class PersistenceRecordKind(StrEnum):
    """M0 runtime record classes owned by the persistence foundation."""

    WORK = "work"
    EXECUTION = "execution"
    EVENT = "event"
    EVIDENCE = "evidence"
    ARTIFACT = "artifact"
    POLICY_DECISION = "policy_decision"
    VERIFICATION = "verification"
