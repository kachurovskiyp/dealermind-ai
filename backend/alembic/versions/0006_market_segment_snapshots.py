"""Add append-only snapshots for Polish market watchlists.

Revision ID: 0006_market_segment_snapshots
Revises: 0005_logistics_cost
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_market_segment_snapshots"
down_revision: str | None = "0005_logistics_cost"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = postgresql.UUID(as_uuid=True)
jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "market_segment_snapshots",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "source_id",
            uuid,
            sa.ForeignKey("import_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            uuid,
            sa.ForeignKey("import_runs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("market_code", sa.String(2), nullable=False),
        sa.Column(
            "currency",
            sa.Enum("PLN", "EUR", "UAH", "USD", name="market_snapshot_currency"),
            nullable=False,
        ),
        sa.Column("listing_count", sa.Integer, nullable=False),
        sa.Column("new_count", sa.Integer, nullable=False),
        sa.Column("updated_count", sa.Integer, nullable=False),
        sa.Column("price_reduction_count", sa.Integer, nullable=False),
        sa.Column("median_price", sa.Numeric(14, 2)),
        sa.Column("price_low", sa.Numeric(14, 2)),
        sa.Column("price_high", sa.Numeric(14, 2)),
        sa.Column("private_count", sa.Integer, nullable=False),
        sa.Column("dealer_count", sa.Integer, nullable=False),
        sa.Column("unknown_seller_count", sa.Integer, nullable=False),
        sa.Column("dimensions", jsonb, nullable=False),
        sa.Column("explanation", jsonb, nullable=False),
        sa.Column("configuration_version", sa.String(100), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_market_segment_snapshots_source_id",
        "market_segment_snapshots",
        ["source_id"],
    )
    op.create_index(
        "ix_market_segment_snapshots_captured_at",
        "market_segment_snapshots",
        ["captured_at"],
    )


def downgrade() -> None:
    op.drop_table("market_segment_snapshots")
    sa.Enum(name="market_snapshot_currency").drop(op.get_bind(), checkfirst=True)
