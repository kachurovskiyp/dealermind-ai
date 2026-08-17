from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VehicleEventRead(BaseModel):
    id: UUID
    vehicle_id: UUID
    event_type: str
    aggregate_type: str
    aggregate_id: UUID | None
    payload: dict[str, object]
    occurred_at: datetime
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)
