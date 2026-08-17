from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.domain import Currency


class ListingImportRecord(BaseModel):
    market_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    marketplace_slug: str = Field(min_length=2, max_length=100)
    target_market_code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    external_id: str = Field(min_length=1, max_length=200)
    url: HttpUrl
    title: str = Field(min_length=1, max_length=500)
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    vin: str | None = Field(default=None, min_length=17, max_length=17)
    year: int | None = Field(default=None, ge=1886, le=2100)
    mileage_km: int | None = Field(default=None, ge=0)
    fuel_type: str | None = None
    gearbox: str | None = None
    location: str | None = None
    seller_type: str | None = None
    description: str | None = None
    price: Decimal = Field(gt=0)
    currency: Currency
    expected_sale_price: Decimal | None = Field(default=None, gt=0)
    expected_costs: Decimal = Field(default=Decimal(0), ge=0)

    @field_validator("market_code", "target_market_code", mode="before")
    @classmethod
    def normalize_market_code(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("marketplace_slug", mode="before")
    @classmethod
    def normalize_slug(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value


class ListingImportBatch(BaseModel):
    provider: str = Field(default="structured-json", min_length=2, max_length=100)
    records: list[ListingImportRecord] = Field(min_length=1, max_length=1000)


class ImportErrorRead(BaseModel):
    row: int
    external_id: str | None
    message: str


class ListingImportResult(BaseModel):
    received: int
    created: int
    updated: int
    unchanged: int
    errors: list[ImportErrorRead]
    offer_ids: list[UUID]
