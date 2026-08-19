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
    seller_type: str | None = None
    extracted_fields: list[str]
    warnings: list[str]
