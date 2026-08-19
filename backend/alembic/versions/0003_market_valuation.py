"""Add append-only market valuation history.

Revision ID: 0003_market_valuation
Revises: 0002_import_automation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_market_valuation"
down_revision: str | None = "0002_import_automation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "valuation_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("market_estimate", sa.Numeric(14, 2), nullable=False),
        sa.Column("conservative_sale_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("price_low", sa.Numeric(14, 2), nullable=False),
        sa.Column("price_high", sa.Numeric(14, 2), nullable=False),
        sa.Column("sample_size", sa.Integer, nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("configuration_version", sa.String(100), nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_valuation_snapshots_opportunity_id", "valuation_snapshots", ["opportunity_id"])


def downgrade() -> None:
    op.drop_table("valuation_snapshots")
