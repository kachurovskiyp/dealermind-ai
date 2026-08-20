from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.domain import Currency


class LogisticsProfileUpsert(BaseModel):
    name: str = Field(default="Основная база", min_length=1, max_length=100)
    origin_label: str = Field(min_length=2, max_length=255)
    origin_country_code: str = Field(min_length=2, max_length=2)
    fixed_cost: Decimal = Field(default=Decimal(0), ge=0)
    cost_per_km: Decimal = Field(gt=0)
    trip_multiplier: Decimal = Field(default=Decimal("2"), ge=1, le=4)
    cross_border_surcharge: Decimal = Field(default=Decimal(0), ge=0)
    currency: Currency

    @field_validator("origin_country_code", mode="before")
    @classmethod
    def normalize_country(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class LogisticsProfileRead(LogisticsProfileUpsert):
    id: UUID
    origin_latitude: Decimal
    origin_longitude: Decimal
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LogisticsSnapshotRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    profile_id: UUID
    origin_label: str
    destination_label: str
    distance_km: Decimal
    fixed_cost: Decimal
    distance_cost: Decimal
    cross_border_cost: Decimal
    total_cost: Decimal
    currency: Currency
    configuration_version: str
    explanation: dict[str, object]
    calculated_at: datetime
    model_config = ConfigDict(from_attributes=True)
