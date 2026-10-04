from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FleetSnapshotRead(BaseModel):
    id: UUID
    profile_slug: str
    make: str
    model: str
    generation: str | None
    period_from: date
    period_to: date
    records_count: int
    by_year: dict[str, int] = Field(default_factory=dict)
    by_fuel: dict[str, int] = Field(default_factory=dict)
    by_region: dict[str, int] = Field(default_factory=dict)
    source_url: str
    configuration_version: str
    collected_at: datetime

    model_config = {"from_attributes": True}


class FleetProfileRead(BaseModel):
    slug: str
    make: str
    model: str
    generation: str
    latest: FleetSnapshotRead | None = None


class FleetStatusRead(BaseModel):
    configured: bool
    message: str


class FleetCollectionStatusRead(BaseModel):
    profile_slug: str
    state: str
    message: str
