from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import Currency, DecisionType, OpportunityStatus, ScoreKind
from app.schemas.logistics import LogisticsSnapshotRead


class OpportunityCreate(BaseModel):
    offer_id: UUID
    target_market_id: UUID
    expected_purchase_price: Decimal | None = Field(default=None, ge=0)
    expected_sale_price: Decimal | None = Field(default=None, ge=0)
    expected_costs: Decimal | None = Field(default=None, ge=0)
    currency: Currency


class OpportunityRead(BaseModel):
    id: UUID
    offer_id: UUID
    target_market_id: UUID
    status: OpportunityStatus
    expected_purchase_price: Decimal | None
    expected_sale_price: Decimal | None
    expected_costs: Decimal | None
    expected_profit: Decimal | None
    currency: Currency
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DecisionCreate(BaseModel):
    decision: DecisionType
    reason: str = Field(min_length=1)
    actor: str = Field(min_length=1, max_length=200)
    data_snapshot: dict[str, object] = Field(default_factory=dict)


class DecisionRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    decision: DecisionType
    reason: str
    actor: str
    data_snapshot: dict[str, object]
    decided_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ScoreCalculate(BaseModel):
    kind: ScoreKind
    factor_values: dict[str, float] = Field(min_length=1)
    factor_weights: dict[str, float] = Field(min_length=1)
    configuration_version: str = Field(min_length=1, max_length=100)
    explanations: dict[str, str] = Field(default_factory=dict)


class ScoreSnapshotRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    kind: ScoreKind
    value: Decimal
    configuration_version: str
    contributions: list[dict[str, object]]
    missing_factors: list[str]
    calculated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ValuationSnapshotRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    market_estimate: Decimal
    conservative_sale_price: Decimal
    price_low: Decimal
    price_high: Decimal
    sample_size: int
    confidence: str
    configuration_version: str
    explanation: dict[str, object]
    calculated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ComparableCollectionRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    source_url: str
    status: str
    requested_limit: int
    found_count: int
    usable_count: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    valuation: ValuationSnapshotRead | None = None
    model_config = ConfigDict(from_attributes=True)


class OpportunityFeedItem(OpportunityRead):
    offer_title: str
    offer_url: str
    offer_image_url: str | None
    offer_location: str | None
    offer_location_region: str | None
    offer_country_code: str | None
    offer_seller_type: str | None
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int | None
    vehicle_generation: str | None
    vehicle_body_type: str | None
    vehicle_engine_marketing_name: str | None
    vehicle_power_hp: int | None
    vehicle_drivetrain: str | None
    vehicle_trim_line: str | None
    latest_scores: dict[str, Decimal]
    ranking_label: str
    ranking_reasons: list[str]
    scoring_version: str | None
    acquisition_id: UUID | None
    valuation: ValuationSnapshotRead | None
    latest_collection_status: str | None
    latest_collection_usable_count: int | None
    logistics: LogisticsSnapshotRead | None
