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
