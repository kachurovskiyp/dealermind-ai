"""Add Logistics Cost v1 profiles and append-only snapshots.

Revision ID: 0005_logistics_cost
Revises: 0004_comparable_market
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_logistics_cost"
down_revision: str | None = "0004_comparable_market"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = postgresql.UUID(as_uuid=True)
jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "logistics_profiles",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("origin_label", sa.String(255), nullable=False),
        sa.Column("origin_country_code", sa.String(2), nullable=False),
        sa.Column("origin_latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("origin_longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("fixed_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("cost_per_km", sa.Numeric(10, 2), nullable=False),
        sa.Column("trip_multiplier", sa.Numeric(4, 2), nullable=False),
        sa.Column("cross_border_surcharge", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "currency",
            sa.Enum("PLN", "EUR", "UAH", "USD", name="logistics_currency"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "logistics_snapshots",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("opportunity_id", uuid, sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("profile_id", uuid, sa.ForeignKey("logistics_profiles.id"), nullable=False),
        sa.Column("origin_label", sa.String(255), nullable=False),
        sa.Column("destination_label", sa.String(255), nullable=False),
        sa.Column("origin_latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("origin_longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("destination_latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("destination_longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("distance_km", sa.Numeric(10, 1), nullable=False),
        sa.Column("fixed_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("distance_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("cross_border_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "currency",
            sa.Enum("PLN", "EUR", "UAH", "USD", name="logistics_snapshot_currency"),
            nullable=False,
        ),
        sa.Column("configuration_version", sa.String(100), nullable=False),
        sa.Column("explanation", jsonb, nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_logistics_snapshots_opportunity_id", "logistics_snapshots", ["opportunity_id"]
    )
    op.create_index("ix_logistics_snapshots_profile_id", "logistics_snapshots", ["profile_id"])


def downgrade() -> None:
    op.drop_table("logistics_snapshots")
    op.drop_table("logistics_profiles")
    sa.Enum(name="logistics_snapshot_currency").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="logistics_currency").drop(op.get_bind(), checkfirst=True)
