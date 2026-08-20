from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.logistics import (
    LogisticsProfileRead,
    LogisticsProfileUpsert,
    LogisticsSnapshotRead,
)
from app.services.logistics import calculate_logistics, get_profile, upsert_profile

router = APIRouter(prefix="/logistics", tags=["logistics"])


@router.get("/profile", response_model=LogisticsProfileRead)
def read_profile(db: Session = Depends(get_db)) -> LogisticsProfileRead:
    profile = get_profile(db)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Профиль не настроен"
        )
    return profile


@router.put("/profile", response_model=LogisticsProfileRead)
async def put_profile(
    payload: LogisticsProfileUpsert, db: Session = Depends(get_db)
) -> LogisticsProfileRead:
    return await upsert_profile(db, payload)


@router.post(
    "/opportunities/{opportunity_id}/calculate", response_model=LogisticsSnapshotRead
)
async def post_calculation(
    opportunity_id: UUID, db: Session = Depends(get_db)
) -> LogisticsSnapshotRead:
    return await calculate_logistics(db, opportunity_id)
