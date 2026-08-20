from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.domain import Currency


class VehicleInput(BaseModel):
    vin: str | None = Field(default=None, min_length=17, max_length=17)
    make: str
    model: str
    generation: str | None = None
    year: int | None = Field(default=None, ge=1886, le=2100)
    fuel_type: str | None = None
    gearbox: str | None = None
    engine_capacity_cc: int | None = Field(default=None, ge=0)
    power_kw: int | None = Field(default=None, ge=0)
    power_hp: int | None = Field(default=None, ge=0)
    body_type: str | None = None
    facelift: bool | None = None
    engine_marketing_name: str | None = None
    engine_code: str | None = None
    drivetrain: str | None = None
    trim_line: str | None = None
    performance_variant: str | None = None


class OfferCreate(BaseModel):
    marketplace_id: UUID
    external_id: str
    url: HttpUrl
    title: str
    description: str | None = None
    mileage_km: int | None = Field(default=None, ge=0)
    location: str | None = None
    seller_type: str | None = None
    vehicle: VehicleInput
    price: Decimal = Field(gt=0)
    currency: Currency
    raw_data: dict[str, object] = Field(default_factory=dict)


class OfferRead(BaseModel):
    id: UUID
    marketplace_id: UUID
    vehicle_id: UUID
    external_id: str
    url: str
    title: str
    mileage_km: int | None
    location: str | None

    model_config = ConfigDict(from_attributes=True)


class PriceObservationCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: Currency


class PriceObservationRead(BaseModel):
    id: UUID
    offer_id: UUID
    amount: Decimal
    currency: Currency
    observed_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VehicleSpecificationConfirm(BaseModel):
    field_name: str
    value: str | int | bool


class VehicleSpecificationObservationRead(BaseModel):
    id: UUID
    vehicle_id: UUID
    offer_id: UUID
    field_name: str
    normalized_value: object
    raw_value: str | None
    source: str
    confidence: Decimal
    confirmed: bool
    observed_at: datetime
    model_config = ConfigDict(from_attributes=True)
