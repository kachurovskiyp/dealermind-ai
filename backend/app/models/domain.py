from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
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
    generation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(nullable=True, index=True)
    fuel_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gearbox: Mapped[str | None] = mapped_column(String(50), nullable=True)
    engine_capacity_cc: Mapped[int | None] = mapped_column(nullable=True)
    power_kw: Mapped[int | None] = mapped_column(nullable=True)

    offers: Mapped[list["Offer"]] = relationship(back_populates="vehicle")


class Offer(TimestampMixin, Base):
    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("marketplace_id", "external_id"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    marketplace_id: Mapped[UUID] = mapped_column(ForeignKey("marketplaces.id"))
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"))
    external_id: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mileage_km: Mapped[int | None] = mapped_column(nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seller_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, name="offer_status"), default=OfferStatus.ACTIVE
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    raw_data: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)

    marketplace: Mapped[Marketplace] = relationship(back_populates="offers")
    vehicle: Mapped[Vehicle] = relationship(back_populates="offers")
    prices: Mapped[list["PriceObservation"]] = relationship(back_populates="offer")


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="price_currency"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    offer: Mapped[Offer] = relationship(back_populates="prices")
