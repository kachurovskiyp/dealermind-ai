"""Add normalized vehicle variants and specification evidence.

Revision ID: 0007_vehicle_variants
Revises: 0006_market_segment_snapshots
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007_vehicle_variants"
down_revision: str | None = "0006_market_segment_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    for name, length in (
        ("body_type", 80),
        ("engine_marketing_name", 100),
        ("engine_code", 100),
        ("drivetrain", 80),
        ("trim_line", 100),
        ("performance_variant", 100),
    ):
        op.add_column("vehicles", sa.Column(name, sa.String(length)))
    op.add_column("vehicles", sa.Column("facelift", sa.Boolean))
    op.add_column("vehicles", sa.Column("power_hp", sa.Integer))
    for name, column_type in (
        ("generation", sa.String(100)),
        ("body_type", sa.String(80)),
        ("engine_marketing_name", sa.String(100)),
        ("power_hp", sa.Integer),
        ("fuel_type", sa.String(50)),
        ("gearbox", sa.String(50)),
        ("drivetrain", sa.String(80)),
        ("trim_line", sa.String(100)),
        ("performance_variant", sa.String(100)),
    ):
        op.add_column("comparable_listings", sa.Column(name, column_type))
    op.create_table(
        "vehicle_specification_observations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("vehicle_id", uuid, sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("offer_id", uuid, sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("normalized_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_value", sa.Text),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("confirmed", sa.Boolean, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("vehicle_id", "offer_id", "field_name"):
        op.create_index(
            f"ix_vehicle_specification_observations_{column}",
            "vehicle_specification_observations",
            [column],
        )


def downgrade() -> None:
    op.drop_table("vehicle_specification_observations")
    for name in (
        "trim_line",
        "performance_variant",
        "drivetrain",
        "gearbox",
        "fuel_type",
        "power_hp",
        "engine_marketing_name",
        "body_type",
        "generation",
    ):
        op.drop_column("comparable_listings", name)
    for name in (
        "power_hp",
        "facelift",
        "performance_variant",
        "trim_line",
        "drivetrain",
        "engine_code",
        "engine_marketing_name",
        "body_type",
    ):
        op.drop_column("vehicles", name)
