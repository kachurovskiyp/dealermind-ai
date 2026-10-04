from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.inspection import ConfigurationReviewRead
from app.services.inspection import configuration_review

router = APIRouter(prefix="/inspection", tags=["configuration review"])


@router.get("/review", response_model=ConfigurationReviewRead)
def review(
    make: str,
    model: str,
    configuration: str | None = None,
    db: Session = Depends(get_db),
) -> ConfigurationReviewRead:
    return ConfigurationReviewRead.model_validate(
        configuration_review(db, make, model, configuration)
    )
