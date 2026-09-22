"""Create M0 runtime persistence tables.

Revision ID: 0001_m0_runtime_records
Revises:
Create Date: 2026-09-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_m0_runtime_records"
down_revision = None
branch_labels = None
depends_on = None

_TABLE_NAMES = (
    "curios_m0_work_records",
    "curios_m0_execution_records",
    "curios_m0_event_records",
    "curios_m0_evidence_records",
    "curios_m0_artifact_records",
    "curios_m0_policy_decision_records",
    "curios_m0_verification_records",
)


def upgrade() -> None:
    schema = op.get_context().opts.get("version_table_schema")
    for table_name in _TABLE_NAMES:
        op.create_table(
            table_name,
            sa.Column("canonical_id", sa.String(length=128), nullable=False),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("payload_sha256", sa.String(length=64), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("canonical_id"),
            schema=schema,
        )


def downgrade() -> None:
    schema = op.get_context().opts.get("version_table_schema")
    for table_name in reversed(_TABLE_NAMES):
        op.drop_table(table_name, schema=schema)
