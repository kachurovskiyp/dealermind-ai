"""Add comparable market collection snapshots.

Revision ID: 0004_comparable_market
Revises: 0003_market_valuation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_comparable_market"
down_revision: str | None = "0003_market_valuation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "comparable_collections",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("opportunity_id", uuid, sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("requested_limit", sa.Integer, nullable=False),
        sa.Column("found_count", sa.Integer, nullable=False),
        sa.Column("usable_count", sa.Integer, nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_comparable_collections_opportunity_id", "comparable_collections", ["opportunity_id"])
    op.create_table(
        "comparable_listings",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("collection_id", uuid, sa.ForeignKey("comparable_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer),
        sa.Column("mileage_km", sa.Integer),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.Enum("PLN", "EUR", "UAH", "USD", name="comparable_currency"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("collection_id", "external_id", "make", "model"):
        op.create_index(f"ix_comparable_listings_{column}", "comparable_listings", [column])


def downgrade() -> None:
    op.drop_table("comparable_listings")
    op.drop_table("comparable_collections")
    sa.Enum(name="comparable_currency").drop(op.get_bind(), checkfirst=True)
