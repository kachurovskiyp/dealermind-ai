"""Add immutable aggregated CEPiK fleet observations.

Revision ID: 0008_poland_fleet
Revises: 0007_vehicle_variants
"""
from collections.abc import Sequence
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0008_poland_fleet"
down_revision: str | None = "0007_vehicle_variants"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table("poland_fleet_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_slug", sa.String(120), nullable=False),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("generation", sa.String(100)),
        sa.Column("period_from", sa.Date(), nullable=False),
        sa.Column("period_to", sa.Date(), nullable=False),
        sa.Column("records_count", sa.Integer(), nullable=False),
        sa.Column("by_year", postgresql.JSONB(), nullable=False),
        sa.Column("by_fuel", postgresql.JSONB(), nullable=False),
        sa.Column("by_region", postgresql.JSONB(), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("configuration_version", sa.String(100), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("profile_slug", "make", "model", "period_from", "period_to", "collected_at"):
        op.create_index(f"ix_poland_fleet_snapshots_{column}", "poland_fleet_snapshots", [column])

def downgrade() -> None:
    op.drop_table("poland_fleet_snapshots")
