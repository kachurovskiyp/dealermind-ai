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


class PolandMarketSummaryRead(BaseModel):
    listings: int
    active_listings: int
    new_7_days: int
    new_30_days: int
    median_price: Decimal | None
    price_reductions: int
    median_days_observed: int | None
    private_listings: int
    dealer_listings: int


class MarketFilterOptionsRead(BaseModel):
    makes: list[str]
    models: list[str]
    models_by_make: dict[str, list[str]]
    fuel_types: list[str]
    gearboxes: list[str]
    regions: list[str]


class PriceBandRead(BaseModel):
    price_from: Decimal
    price_to: Decimal
    count: int


class SellerStatRead(BaseModel):
    seller_type: str
    listings: int
    median_price: Decimal | None


class RegionStatRead(BaseModel):
    region: str
    listings: int
    median_price: Decimal


class PriceChangeRead(BaseModel):
    offer_id: UUID
    vehicle: str
    url: str
    previous_price: Decimal
    current_price: Decimal
    change_percent: float
    changed_at: datetime


class MarketListingPositionRead(BaseModel):
    offer_id: UUID
    vehicle: str
    year: int | None
    price: Decimal
    url: str
    seller_type: str | None
    region: str | None
    days_observed: int
    price_percentile: int | None
    comparison_size: int


class PolandMarketAnalyticsRead(BaseModel):
    market_code: str
    currency: Currency
    generated_at: datetime
    filters: MarketFilterOptionsRead
    summary: PolandMarketSummaryRead
    price_distribution: list[PriceBandRead]
    seller_stats: list[SellerStatRead]
    region_stats: list[RegionStatRead]
    price_history: list[PriceChangeRead]
    listings: list[MarketListingPositionRead]


class MarketSegmentSnapshotRead(BaseModel):
    id: UUID
    source_id: UUID
    run_id: UUID
    source_name: str
    market_code: str
    currency: Currency
    listing_count: int
    new_count: int
    updated_count: int
    price_reduction_count: int
    median_price: Decimal | None
    price_low: Decimal | None
    price_high: Decimal | None
    private_count: int
    dealer_count: int
    unknown_seller_count: int
    dimensions: dict[str, object]
    configuration_version: str
    captured_at: datetime


class ModelVariantStatRead(BaseModel):
    variant: str
    sample_size: int
    median_price: Decimal
    price_low: Decimal
    price_high: Decimal
    premium_percent: float
    confidence: str
    specification_completeness: int
