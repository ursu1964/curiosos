"""Add M1 agent definition and instance persistence tables.

Revision ID: 0004_m1_agent_records
Revises: 0003_m1_work_dag_records
Create Date: 2026-09-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_m1_agent_records"
down_revision = "0003_m1_work_dag_records"
branch_labels = None
depends_on = None

_TABLE_NAMES = (
    "curios_m1_agent_definition_records",
    "curios_m1_agent_instance_records",
)


def upgrade() -> None:
    schema = op.get_context().opts.get("version_table_schema")
    for table_name in _TABLE_NAMES:
        op.create_table(
            table_name,
            sa.Column(
                "append_ordinal",
                sa.BigInteger(),
                sa.Identity(always=True),
                nullable=False,
            ),
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
