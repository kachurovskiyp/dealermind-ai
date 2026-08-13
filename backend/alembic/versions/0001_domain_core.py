"""Add Sprint 1 domain core.

Revision ID: 0001_domain_core
Revises: foundation schema
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_domain_core"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid = postgresql.UUID(as_uuid=True)
jsonb = postgresql.JSONB(astext_type=sa.Text())
currency_values = ("PLN", "EUR", "UAH", "USD")


def upgrade() -> None:
    # Foundation tables are included so a clean database can be built solely by Alembic.
    currency = sa.Enum(*currency_values, name="currency")
    offer_status = sa.Enum("ACTIVE", "INACTIVE", "SOLD", "UNKNOWN", name="offer_status")
    op.create_table(
        "markets",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("default_currency", currency, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_markets_code", "markets", ["code"])
    op.create_table(
        "marketplaces",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "market_id", uuid, sa.ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("market_id", "slug"),
    )
    op.create_table(
        "vehicles",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("vin", sa.String(17)),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("generation", sa.String(100)),
        sa.Column("year", sa.Integer),
        sa.Column("fuel_type", sa.String(50)),
        sa.Column("gearbox", sa.String(50)),
        sa.Column("engine_capacity_cc", sa.Integer),
        sa.Column("power_kw", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("vin"),
    )
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"])
    op.create_index("ix_vehicles_make", "vehicles", ["make"])
    op.create_index("ix_vehicles_model", "vehicles", ["model"])
    op.create_index("ix_vehicles_year", "vehicles", ["year"])
    op.create_table(
        "offers",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("marketplace_id", uuid, sa.ForeignKey("marketplaces.id"), nullable=False),
        sa.Column("vehicle_id", uuid, sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("mileage_km", sa.Integer),
        sa.Column("location", sa.String(255)),
        sa.Column("seller_type", sa.String(50)),
        sa.Column("status", offer_status, nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_data", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("marketplace_id", "external_id"),
    )
    op.create_table(
        "price_observations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("offer_id", uuid, sa.ForeignKey("offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.Enum(*currency_values, name="price_currency"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_price_observations_offer_id", "price_observations", ["offer_id"])

    op.create_table(
        "opportunities",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("offer_id", uuid, sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("target_market_id", uuid, sa.ForeignKey("markets.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "NEW",
                "EVALUATING",
                "ACCEPTED",
                "REJECTED",
                "EXPIRED",
                "ACQUIRED",
                name="opportunity_status",
            ),
            nullable=False,
        ),
        sa.Column("expected_purchase_price", sa.Numeric(14, 2)),
        sa.Column("expected_sale_price", sa.Numeric(14, 2)),
        sa.Column("expected_costs", sa.Numeric(14, 2)),
        sa.Column("expected_profit", sa.Numeric(14, 2)),
        sa.Column(
            "currency", sa.Enum(*currency_values, name="opportunity_currency"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opportunities_offer_id", "opportunities", ["offer_id"])
    op.create_index("ix_opportunities_target_market_id", "opportunities", ["target_market_id"])
    op.create_table(
        "score_snapshots",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("opportunity_id", uuid, sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column(
            "kind", sa.Enum("MARKET", "DEALER", "OPPORTUNITY", name="score_kind"), nullable=False
        ),
        sa.Column("value", sa.Numeric(5, 2), nullable=False),
        sa.Column("configuration_version", sa.String(100), nullable=False),
        sa.Column("contributions", jsonb, nullable=False),
        sa.Column("missing_factors", jsonb, nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("value >= 0 AND value <= 100", name="ck_score_value"),
    )
    op.create_index("ix_score_snapshots_opportunity_id", "score_snapshots", ["opportunity_id"])
    op.create_table(
        "opportunity_decisions",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("opportunity_id", uuid, sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column(
            "decision",
            sa.Enum("EVALUATE", "ACCEPT", "REJECT", "REOPEN", name="decision_type"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("actor", sa.String(200), nullable=False),
        sa.Column("data_snapshot", jsonb, nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_opportunity_decisions_opportunity_id", "opportunity_decisions", ["opportunity_id"]
    )
    op.create_table(
        "acquisitions",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "opportunity_id", uuid, sa.ForeignKey("opportunities.id"), nullable=False, unique=True
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PLANNED",
                "INSPECTING",
                "NEGOTIATING",
                "COMPLETED",
                "CANCELLED",
                name="acquisition_status",
            ),
            nullable=False,
        ),
        sa.Column("agreed_price", sa.Numeric(14, 2)),
        sa.Column(
            "currency", sa.Enum(*currency_values, name="acquisition_currency"), nullable=False
        ),
        sa.Column("acquired_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "inventory_items",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "acquisition_id", uuid, sa.ForeignKey("acquisitions.id"), nullable=False, unique=True
        ),
        sa.Column("vehicle_id", uuid, sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("owning_market_id", uuid, sa.ForeignKey("markets.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "IN_TRANSIT",
                "PREPARING",
                "READY_FOR_SALE",
                "RESERVED",
                "SOLD",
                name="inventory_status",
            ),
            nullable=False,
        ),
        sa.Column("stock_number", sa.String(100), nullable=False, unique=True),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_inventory_items_vehicle_id", "inventory_items", ["vehicle_id"])
    op.create_index("ix_inventory_items_owning_market_id", "inventory_items", ["owning_market_id"])
    op.create_table(
        "preparations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("inventory_item_id", uuid, sa.ForeignKey("inventory_items.id"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PLANNED",
                "IN_PROGRESS",
                "BLOCKED",
                "COMPLETED",
                "CANCELLED",
                name="preparation_status",
            ),
            nullable=False,
        ),
        sa.Column("provider", sa.String(200)),
        sa.Column("performed_in_house", sa.Boolean),
        sa.Column("estimated_cost", sa.Numeric(14, 2)),
        sa.Column("actual_cost", sa.Numeric(14, 2)),
        sa.Column(
            "currency", sa.Enum(*currency_values, name="preparation_currency"), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_preparations_inventory_item_id", "preparations", ["inventory_item_id"])
    op.create_table(
        "sales",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "inventory_item_id",
            uuid,
            sa.ForeignKey("inventory_items.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("market_id", uuid, sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("sold_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.Enum(*currency_values, name="sale_currency"), nullable=False),
        sa.Column("sold_at", sa.Date, nullable=False),
        sa.Column("buyer_reference", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sales_market_id", "sales", ["market_id"])
    op.create_table(
        "vehicle_events",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("vehicle_id", uuid, sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("aggregate_type", sa.String(100), nullable=False),
        sa.Column("aggregate_id", uuid),
        sa.Column("payload", jsonb, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vehicle_events_vehicle_id", "vehicle_events", ["vehicle_id"])
    op.create_index("ix_vehicle_events_event_type", "vehicle_events", ["event_type"])
    op.create_index("ix_vehicle_events_occurred_at", "vehicle_events", ["occurred_at"])


def downgrade() -> None:
    for table in (
        "vehicle_events",
        "sales",
        "preparations",
        "inventory_items",
        "acquisitions",
        "opportunity_decisions",
        "score_snapshots",
        "opportunities",
        "price_observations",
        "offers",
        "vehicles",
        "marketplaces",
        "markets",
    ):
        op.drop_table(table)
    for enum_name in (
        "preparation_currency",
        "preparation_status",
        "sale_currency",
        "inventory_status",
        "acquisition_currency",
        "acquisition_status",
        "decision_type",
        "score_kind",
        "opportunity_currency",
        "opportunity_status",
        "price_currency",
        "offer_status",
        "currency",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
