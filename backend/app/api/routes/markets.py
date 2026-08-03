from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.market import MarketCreate, MarketRead
from app.services.markets import create_market, list_markets

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("", response_model=list[MarketRead])
def get_markets(db: Session = Depends(get_db)) -> list[MarketRead]:
    return list_markets(db)


@router.post("", response_model=MarketRead, status_code=status.HTTP_201_CREATED)
def post_market(payload: MarketCreate, db: Session = Depends(get_db)) -> MarketRead:
    return create_market(db, payload)
