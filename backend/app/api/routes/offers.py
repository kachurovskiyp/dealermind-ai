from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.offer import OfferCreate, OfferRead
from app.services.offers import create_offer, list_offers

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("", response_model=list[OfferRead])
def get_offers(db: Session = Depends(get_db)) -> list[OfferRead]:
    return list_offers(db)


@router.post("", response_model=OfferRead, status_code=status.HTTP_201_CREATED)
def post_offer(payload: OfferCreate, db: Session = Depends(get_db)) -> OfferRead:
    return create_offer(db, payload)
