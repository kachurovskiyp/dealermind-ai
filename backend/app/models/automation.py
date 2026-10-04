from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.domain import Currency, TimestampMixin, _reject_history_mutation, utcnow


class ImportRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ImportSource(TimestampMixin, Base):
    __tablename__ = "import_sources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    provider_type: Mapped[str] = mapped_column(String(50), default="json_http")
    endpoint_url: Mapped[str] = mapped_column(String(1000))
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    configuration: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    runs: Mapped[list["ImportRun"]] = relationship(back_populates="source")
    market_snapshots: Mapped[list["MarketSegmentSnapshot"]] = relationship(
        back_populates="source", order_by="MarketSegmentSnapshot.captured_at"
    )


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_sources.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ImportRunStatus] = mapped_column(
        Enum(ImportRunStatus, name="import_run_status"), default=ImportRunStatus.RUNNING
    )
    trigger: Mapped[str] = mapped_column(String(30))
    received: Mapped[int] = mapped_column(Integer, default=0)
    created: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    unchanged: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[ImportSource] = relationship(back_populates="runs")
    market_snapshot: Mapped["MarketSegmentSnapshot | None"] = relationship(
        back_populates="run", uselist=False
    )


class MarketSegmentSnapshot(Base):
    """Append-only description of one Polish watchlist result."""

    __tablename__ = "market_segment_snapshots"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_sources.id", ondelete="CASCADE"), index=True
    )
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_runs.id", ondelete="CASCADE"), unique=True
    )
    market_code: Mapped[str] = mapped_column(String(2), default="PL")
    currency: Mapped[Currency] = mapped_column(Enum(Currency, name="market_snapshot_currency"))
    listing_count: Mapped[int] = mapped_column(Integer)
    new_count: Mapped[int] = mapped_column(Integer)
    updated_count: Mapped[int] = mapped_column(Integer)
    price_reduction_count: Mapped[int] = mapped_column(Integer)
    median_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    price_low: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    price_high: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    private_count: Mapped[int] = mapped_column(Integer, default=0)
    dealer_count: Mapped[int] = mapped_column(Integer, default=0)
    unknown_seller_count: Mapped[int] = mapped_column(Integer, default=0)
    dimensions: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    explanation: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    configuration_version: Mapped[str] = mapped_column(String(100), default="market-snapshot-v1")
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    source: Mapped[ImportSource] = relationship(back_populates="market_snapshots")
    run: Mapped[ImportRun] = relationship(back_populates="market_snapshot")


event.listen(MarketSegmentSnapshot, "before_update", _reject_history_mutation)
event.listen(MarketSegmentSnapshot, "before_delete", _reject_history_mutation)


class PolandFleetSnapshot(Base):
    """Immutable weekly, aggregated CEPiK registration observation. No VIN or personal data."""

    __tablename__ = "poland_fleet_snapshots"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    profile_slug: Mapped[str] = mapped_column(String(120), index=True)
    make: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(100), index=True)
    generation: Mapped[str | None] = mapped_column(String(100))
    period_from: Mapped[date] = mapped_column(Date, index=True)
    period_to: Mapped[date] = mapped_column(Date, index=True)
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    by_year: Mapped[dict[str, int]] = mapped_column(JSONB, default=dict)
    by_fuel: Mapped[dict[str, int]] = mapped_column(JSONB, default=dict)
    by_region: Mapped[dict[str, int]] = mapped_column(JSONB, default=dict)
    source_url: Mapped[str] = mapped_column(String(1000))
    configuration_version: Mapped[str] = mapped_column(String(100))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


event.listen(PolandFleetSnapshot, "before_update", _reject_history_mutation)
event.listen(PolandFleetSnapshot, "before_delete", _reject_history_mutation)
