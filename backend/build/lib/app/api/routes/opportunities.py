from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.opportunity import (
    DecisionCreate,
    DecisionRead,
    OpportunityCreate,
    OpportunityFeedItem,
    OpportunityRead,
    ScoreCalculate,
    ScoreSnapshotRead,
)
from app.services.opportunities import (
    calculate_and_store_score,
    create_opportunity,
    list_opportunities,
    opportunity_feed,
    recalculate_opportunity,
    record_decision,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/feed", response_model=list[OpportunityFeedItem])
def get_opportunity_feed(db: Session = Depends(get_db)) -> list[OpportunityFeedItem]:
    return opportunity_feed(db)


@router.post("/{opportunity_id}/recalculate", response_model=list[ScoreSnapshotRead])
def post_opportunity_recalculation(
    opportunity_id: UUID, db: Session = Depends(get_db)
) -> list[ScoreSnapshotRead]:
    return recalculate_opportunity(db, opportunity_id)


@router.get("", response_model=list[OpportunityRead])
def get_opportunities(db: Session = Depends(get_db)) -> list[OpportunityRead]:
    return list_opportunities(db)


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def post_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db)) -> OpportunityRead:
    return create_opportunity(db, payload)


@router.post(
    "/{opportunity_id}/decisions", response_model=DecisionRead, status_code=status.HTTP_201_CREATED
)
def post_decision(
    opportunity_id: UUID, payload: DecisionCreate, db: Session = Depends(get_db)
) -> DecisionRead:
    return record_decision(db, opportunity_id, payload)


@router.post(
    "/{opportunity_id}/scores",
    response_model=ScoreSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
def post_score(
    opportunity_id: UUID, payload: ScoreCalculate, db: Session = Depends(get_db)
) -> ScoreSnapshotRead:
    return calculate_and_store_score(db, opportunity_id, payload)
