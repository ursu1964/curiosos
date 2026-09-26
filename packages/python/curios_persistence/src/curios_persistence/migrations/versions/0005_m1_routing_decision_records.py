"""Add M1 routing decision persistence table.

Revision ID: 0005_m1_routing_decision_records
Revises: 0004_m1_agent_records
Create Date: 2026-09-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_m1_routing_decision_records"
down_revision = "0004_m1_agent_records"
branch_labels = None
depends_on = None

_TABLE_NAME = "curios_m1_routing_decision_records"


def upgrade() -> None:
    schema = op.get_context().opts.get("version_table_schema")
    op.create_table(
        _TABLE_NAME,
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
    op.drop_table(_TABLE_NAME, schema=schema)
