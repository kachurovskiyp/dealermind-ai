from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import Currency


class MarketCreate(BaseModel):
    code: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    name: str = Field(min_length=2, max_length=100)
    default_currency: Currency


class MarketRead(MarketCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class MarketplaceCreate(BaseModel):
    market_id: UUID
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    base_url: str = Field(min_length=5, max_length=500)


class MarketplaceRead(MarketplaceCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
