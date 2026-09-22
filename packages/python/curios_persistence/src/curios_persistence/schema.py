"""SQLAlchemy Core schema owned by the M0 persistence package."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, MetaData, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB

from curios_persistence.kinds import PersistenceRecordKind

m0_persistence_metadata = MetaData()


def _record_table(name: str) -> Table:
    return Table(
        name,
        m0_persistence_metadata,
        Column("canonical_id", String(128), primary_key=True),
        Column("payload", JSONB, nullable=False),
        Column("payload_sha256", String(64), nullable=False),
        Column(
            "created_at",
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        Column(
            "updated_at",
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )


WORK_RECORDS = _record_table("curios_m0_work_records")
EXECUTION_RECORDS = _record_table("curios_m0_execution_records")
EVENT_RECORDS = _record_table("curios_m0_event_records")
EVIDENCE_RECORDS = _record_table("curios_m0_evidence_records")
ARTIFACT_RECORDS = _record_table("curios_m0_artifact_records")
POLICY_DECISION_RECORDS = _record_table("curios_m0_policy_decision_records")
VERIFICATION_RECORDS = _record_table("curios_m0_verification_records")

TABLES_BY_RECORD_KIND: dict[PersistenceRecordKind, Table] = {
    PersistenceRecordKind.WORK: WORK_RECORDS,
    PersistenceRecordKind.EXECUTION: EXECUTION_RECORDS,
    PersistenceRecordKind.EVENT: EVENT_RECORDS,
    PersistenceRecordKind.EVIDENCE: EVIDENCE_RECORDS,
    PersistenceRecordKind.ARTIFACT: ARTIFACT_RECORDS,
    PersistenceRecordKind.POLICY_DECISION: POLICY_DECISION_RECORDS,
    PersistenceRecordKind.VERIFICATION: VERIFICATION_RECORDS,
}

M0_PERSISTENCE_TABLE_NAMES: tuple[str, ...] = tuple(
    table.name for table in m0_persistence_metadata.sorted_tables
)
