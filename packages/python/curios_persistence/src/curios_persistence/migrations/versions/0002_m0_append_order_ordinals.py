"""Add persistence append-order ordinals.

Revision ID: 0002_m0_append_order_ordinals
Revises: 0001_m0_runtime_records
Create Date: 2026-09-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_m0_append_order_ordinals"
down_revision = "0001_m0_runtime_records"
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
        op.add_column(
            table_name,
            sa.Column(
                "append_ordinal",
                sa.BigInteger(),
                sa.Identity(always=True),
                nullable=False,
            ),
            schema=schema,
        )


def downgrade() -> None:
    schema = op.get_context().opts.get("version_table_schema")
    for table_name in reversed(_TABLE_NAMES):
        op.drop_column(table_name, "append_ordinal", schema=schema)
