"""Add M1 work DAG persistence table.

Revision ID: 0003_m1_work_dag_records
Revises: 0002_m0_append_order_ordinals
Create Date: 2026-09-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_m1_work_dag_records"
down_revision = "0002_m0_append_order_ordinals"
branch_labels = None
depends_on = None

_TABLE_NAME = "curios_m1_work_dag_records"


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
