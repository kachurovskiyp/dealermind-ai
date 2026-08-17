from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import AcquisitionStatus, Currency, InventoryStatus


class AcquisitionCreate(BaseModel):
    currency: Currency
    agreed_price: Decimal | None = Field(default=None, ge=0)


class AcquisitionRead(BaseModel):
    id: UUID
    opportunity_id: UUID
    status: AcquisitionStatus
    agreed_price: Decimal | None
    currency: Currency
    acquired_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AcquisitionComplete(BaseModel):
    agreed_price: Decimal = Field(gt=0)
    stock_number: str = Field(min_length=1, max_length=100)
    acquired_at: datetime | None = None


class InventoryItemRead(BaseModel):
    id: UUID
    acquisition_id: UUID
    vehicle_id: UUID
    owning_market_id: UUID
    status: InventoryStatus
    stock_number: str
    acquired_at: datetime
    model_config = ConfigDict(from_attributes=True)
