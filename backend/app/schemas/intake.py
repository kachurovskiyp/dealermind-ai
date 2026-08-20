from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl

from app.models.domain import Currency


class LinkPreviewRequest(BaseModel):
    url: HttpUrl


class LinkPreviewRead(BaseModel):
    source_url: str
    external_id: str
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1886, le=2100)
    mileage_km: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, gt=0)
    currency: Currency | None = None
    location: str | None = None
    location_region: str | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    seller_type: str | None = None
    generation: str | None = None
    body_type: str | None = None
    engine_marketing_name: str | None = None
    engine_capacity_cc: int | None = Field(default=None, ge=0)
    power_hp: int | None = Field(default=None, ge=0)
    fuel_type: str | None = None
    gearbox: str | None = None
    drivetrain: str | None = None
    trim_line: str | None = None
    performance_variant: str | None = None
    specification_evidence: list[dict[str, object]] = Field(default_factory=list)
    extracted_fields: list[str]
    warnings: list[str]
