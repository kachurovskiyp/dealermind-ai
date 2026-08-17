from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.acquisition import (
    AcquisitionComplete,
    AcquisitionCreate,
    AcquisitionRead,
    InventoryItemRead,
)
from app.services.acquisitions import complete_acquisition, start_acquisition

router = APIRouter(tags=["acquisitions"])


@router.post(
    "/opportunities/{opportunity_id}/acquisition",
    response_model=AcquisitionRead,
    status_code=status.HTTP_201_CREATED,
)
def post_acquisition(
    opportunity_id: UUID,
    payload: AcquisitionCreate,
    db: Session = Depends(get_db),
) -> AcquisitionRead:
    return start_acquisition(db, opportunity_id, payload)


@router.post(
    "/acquisitions/{acquisition_id}/complete",
    response_model=InventoryItemRead,
    status_code=status.HTTP_201_CREATED,
)
def post_acquisition_completion(
    acquisition_id: UUID,
    payload: AcquisitionComplete,
    db: Session = Depends(get_db),
) -> InventoryItemRead:
    return complete_acquisition(db, acquisition_id, payload)
