from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.vehicle_event import VehicleEventRead
from app.services.acquisitions import list_vehicle_events

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/{vehicle_id}/events", response_model=list[VehicleEventRead])
def get_vehicle_events(
    vehicle_id: UUID, db: Session = Depends(get_db)
) -> list[VehicleEventRead]:
    return list_vehicle_events(db, vehicle_id)
