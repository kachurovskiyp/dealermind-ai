from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.domain import Currency


class MarketOverviewRead(BaseModel):
    comparable_listings: int
    collections: int
    valuations: int
    valued_opportunities: int


class ValuationHistoryRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    vehicle: str
    market_estimate: Decimal
    conservative_sale_price: Decimal
    price_low: Decimal
    price_high: Decimal
    currency: Currency
    sample_size: int
    confidence: str
    configuration_version: str
    calculated_at: datetime


class CollectionHistoryRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    vehicle: str
    status: str
    source_url: str
    requested_limit: int
    found_count: int
    usable_count: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None


class ComparableListingRead(BaseModel):
    id: UUID
    external_id: str
    url: str
    title: str
    make: str
    model: str
    year: int | None
    mileage_km: int | None
    price: Decimal
    currency: Currency
    observed_at: datetime
