"""add gps points table

Revision ID: 0003_gps_points
Revises: 0002_camera_registry_audit
Create Date: 2026-05-26 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_gps_points"
down_revision: Union[str, None] = "0002_camera_registry_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gps_points",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_gps_points_device_id", "gps_points", ["device_id"])
    op.create_index("ix_gps_points_ts", "gps_points", ["ts"])
    op.create_index("ix_gps_points_device_ts", "gps_points", ["device_id", "ts"])


def downgrade() -> None:
    op.drop_index("ix_gps_points_device_ts", table_name="gps_points")
    op.drop_index("ix_gps_points_ts", table_name="gps_points")
    op.drop_index("ix_gps_points_device_id", table_name="gps_points")
    op.drop_table("gps_points")
