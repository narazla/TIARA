"""tambah tabel mood_entries

Revision ID: 7d3e9c1a5b24
Revises: 2caa6c789422
Create Date: 2026-10-30 17:45:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7d3e9c1a5b24"
down_revision: Union[str, None] = "2caa6c789422"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mood_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mood", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mood_entries_patient_user_id"), "mood_entries", ["patient_user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mood_entries_patient_user_id"), table_name="mood_entries")
    op.drop_table("mood_entries")
