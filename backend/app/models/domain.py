"""Persistence model for the DealerMind domain core.

History tables are deliberately append-only. They describe what was known and
decided at a point in time; corrections are represented by a newer record.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Currency(StrEnum):
    PLN = "PLN"
    EUR = "EUR"
    UAH = "UAH"
    USD = "USD"


class OfferStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
    UNKNOWN = "unknown"


class OpportunityStatus(StrEnum):
    NEW = "new"
    EVALUATING = "evaluating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ACQUIRED = "acquired"


class AcquisitionStatus(StrEnum):
    PLANNED = "planned"
    INSPECTING = "inspecting"
    NEGOTIATING = "negotiating"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InventoryStatus(StrEnum):
    IN_TRANSIT = "in_transit"
    PREPARING = "preparing"
    READY_FOR_SALE = "ready_for_sale"
    RESERVED = "reserved"
    SOLD = "sold"


class PreparationStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DecisionType(StrEnum):
    EVALUATE = "evaluate"
    ACCEPT = "accept"
    REJECT = "reject"
    REOPEN = "reopen"


class ScoreKind(StrEnum):
    MARKET = "market"
    DEALER = "dealer"
    OPPORTUNITY = "opportunity"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Market(TimestampMixin, Base):
    __tablename__ = "markets"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(2), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    default_currency: Mapped[Currency] = mapped_column(Enum(Currency, name="currency"))
    marketplaces: Mapped[list["Marketplace"]] = relationship(back_populates="market")


class Marketplace(TimestampMixin, Base):
    __tablename__ = "marketplaces"
    __table_args__ = (UniqueConstraint("market_id", "slug"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    market_id: Mapped[UUID] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100))
    base_url: Mapped[str] = mapped_column(String(500))
    market: Mapped[Market] = relationship(back_populates="marketplaces")
    offers: Mapped[list["Offer"]] = relationship(back_populates="marketplace")


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    vin: Mapped[str | None] = mapped_column(String(17), unique=True, nullable=True, index=True)
    make: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(100), index=True)
    generation: Mapped[str | None] = mapped_column(String(100))
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    fuel_type: Mapped[str | None] = mapped_column(String(50))
    gearbox: Mapped[str | None] = mapped_column(String(50))
    engine_capacity_cc: Mapped[int | None] = mapped_column(Integer)
    power_kw: Mapped[int | None] = mapped_column(Integer)
    offers: Mapped[list["Offer"]] = relationship(back_populates="vehicle")
    inventory_items: Mapped[list["InventoryItem"]] = relationship(back_populates="vehicle")
    events: Mapped[list["VehicleEvent"]] = relationship(
        back_populates="vehicle", order_by="VehicleEvent.occurred_at"
    )


class Offer(TimestampMixin, Base):
    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("marketplace_id", "external_id"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    marketplace_id: Mapped[UUID] = mapped_column(ForeignKey("marketplaces.id"))
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"))
    external_id: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    mileage_km: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(255))
    seller_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, name="offer_status"), default=OfferStatus.ACTIVE
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    raw_data: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    marketplace: Mapped[Marketplace] = relationship(back_populates="offers")
    vehicle: Mapped[Vehicle] = relationship(back_populates="offers")
    prices: Mapped[list["PriceObservation"]] = relationship(back_populates="offer")
    opportunities: Mapped[list["Opportunity"]] = relationship(back_populates="offer")


class PriceObservation(Base):
    __tablename__ = "price_observations"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="price_currency"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    offer: Mapped[Offer] = relationship(back_populates="prices")


class Opportunity(TimestampMixin, Base):
    __tablename__ = "opportunities"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("offers.id"), index=True)
    target_market_id: Mapped[UUID] = mapped_column(ForeignKey("markets.id"), index=True)
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus, name="opportunity_status"), default=OpportunityStatus.NEW
    )
    expected_purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    expected_sale_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    expected_costs: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    expected_profit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="opportunity_currency"))
    offer: Mapped[Offer] = relationship(back_populates="opportunities")
    target_market: Mapped[Market] = relationship()
    scores: Mapped[list["ScoreSnapshot"]] = relationship(
        back_populates="opportunity", order_by="ScoreSnapshot.calculated_at"
    )
    decisions: Mapped[list["OpportunityDecision"]] = relationship(
        back_populates="opportunity", order_by="OpportunityDecision.decided_at"
    )
    acquisition: Mapped["Acquisition | None"] = relationship(
        back_populates="opportunity", uselist=False
    )


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshots"
    __table_args__ = (CheckConstraint("value >= 0 AND value <= 100", name="ck_score_value"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    kind: Mapped[ScoreKind] = mapped_column(Enum(ScoreKind, name="score_kind"))
    value: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    configuration_version: Mapped[str] = mapped_column(String(100))
    contributions: Mapped[list[dict[str, object]]] = mapped_column(JSONB)
    missing_factors: Mapped[list[str]] = mapped_column(JSONB, default=list)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    opportunity: Mapped[Opportunity] = relationship(back_populates="scores")


class OpportunityDecision(Base):
    __tablename__ = "opportunity_decisions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), index=True)
    decision: Mapped[DecisionType] = mapped_column(Enum(DecisionType, name="decision_type"))
    reason: Mapped[str] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(200))
    data_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    opportunity: Mapped[Opportunity] = relationship(back_populates="decisions")


class Acquisition(TimestampMixin, Base):
    __tablename__ = "acquisitions"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), unique=True)
    status: Mapped[AcquisitionStatus] = mapped_column(
        Enum(AcquisitionStatus, name="acquisition_status"), default=AcquisitionStatus.PLANNED
    )
    agreed_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="acquisition_currency"))
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opportunity: Mapped[Opportunity] = relationship(back_populates="acquisition")
    inventory_item: Mapped["InventoryItem | None"] = relationship(
        back_populates="acquisition", uselist=False
    )


class InventoryItem(TimestampMixin, Base):
    __tablename__ = "inventory_items"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    acquisition_id: Mapped[UUID] = mapped_column(ForeignKey("acquisitions.id"), unique=True)
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"), index=True)
    owning_market_id: Mapped[UUID] = mapped_column(ForeignKey("markets.id"), index=True)
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus, name="inventory_status"), default=InventoryStatus.IN_TRANSIT
    )
    stock_number: Mapped[str] = mapped_column(String(100), unique=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    acquisition: Mapped[Acquisition] = relationship(back_populates="inventory_item")
    vehicle: Mapped[Vehicle] = relationship(back_populates="inventory_items")
    owning_market: Mapped[Market] = relationship()
    preparations: Mapped[list["Preparation"]] = relationship(back_populates="inventory_item")
    sale: Mapped["Sale | None"] = relationship(back_populates="inventory_item", uselist=False)


class Preparation(TimestampMixin, Base):
    __tablename__ = "preparations"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    inventory_item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_items.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[PreparationStatus] = mapped_column(
        Enum(PreparationStatus, name="preparation_status"), default=PreparationStatus.PLANNED
    )
    provider: Mapped[str | None] = mapped_column(String(200))
    performed_in_house: Mapped[bool | None] = mapped_column(nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="preparation_currency"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inventory_item: Mapped[InventoryItem] = relationship(back_populates="preparations")


class Sale(TimestampMixin, Base):
    __tablename__ = "sales"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    inventory_item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_items.id"), unique=True)
    market_id: Mapped[UUID] = mapped_column(ForeignKey("markets.id"), index=True)
    sold_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="sale_currency"))
    sold_at: Mapped[date] = mapped_column(Date)
    buyer_reference: Mapped[str | None] = mapped_column(String(200))
    inventory_item: Mapped[InventoryItem] = relationship(back_populates="sale")
    market: Mapped[Market] = relationship()


class VehicleEvent(Base):
    __tablename__ = "vehicle_events"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    aggregate_type: Mapped[str] = mapped_column(String(100))
    aggregate_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    vehicle: Mapped[Vehicle] = relationship(back_populates="events")


def _reject_history_mutation(_mapper: object, _connection: object, target: object) -> None:
    raise ValueError(f"{type(target).__name__} is append-only; append a correction instead")


for history_model in (PriceObservation, ScoreSnapshot, OpportunityDecision, VehicleEvent):
    event.listen(history_model, "before_update", _reject_history_mutation)
    event.listen(history_model, "before_delete", _reject_history_mutation)
