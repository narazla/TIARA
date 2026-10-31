"""tambah kolom avg_response_delay_seconds ke voice_analysis_results

Revision ID: a1b2c3d4e5f6
Revises: 7d3e9c1a5b24
Create Date: 2026-10-31 01:10:00

Latar belakang: nilai jeda respons (waktu hingga kata pertama) sudah dihitung
oleh pipeline suara (voice_analysis_service.gabung_fitur) dan disimpan di
raw_features["jeda_respons"]. Migrasi ini mempromoteskan nilai itu ke kolom
dedicated agar dapat dikueri langsung tanpa membongkar JSONB.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7d3e9c1a5b24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "voice_analysis_results",
        sa.Column("avg_response_delay_seconds", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("voice_analysis_results", "avg_response_delay_seconds")
