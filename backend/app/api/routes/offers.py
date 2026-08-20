from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.offer import (
    OfferCreate,
    OfferRead,
    PriceObservationCreate,
    PriceObservationRead,
    VehicleSpecificationConfirm,
    VehicleSpecificationObservationRead,
)
from app.services.offers import (
    confirm_vehicle_specification,
    create_offer,
    list_offers,
    list_vehicle_specifications,
    record_price_observation,
)

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get(
    "/{offer_id}/specifications",
    response_model=list[VehicleSpecificationObservationRead],
)
def get_specifications(
    offer_id: UUID, db: Session = Depends(get_db)
) -> list[VehicleSpecificationObservationRead]:
    return list_vehicle_specifications(db, offer_id)


@router.post(
    "/{offer_id}/specifications/confirm",
    response_model=VehicleSpecificationObservationRead,
    status_code=status.HTTP_201_CREATED,
)
def post_specification_confirmation(
    offer_id: UUID,
    payload: VehicleSpecificationConfirm,
    db: Session = Depends(get_db),
) -> VehicleSpecificationObservationRead:
    return confirm_vehicle_specification(db, offer_id, payload)


@router.get("", response_model=list[OfferRead])
def get_offers(db: Session = Depends(get_db)) -> list[OfferRead]:
    return list_offers(db)


@router.post("", response_model=OfferRead, status_code=status.HTTP_201_CREATED)
def post_offer(payload: OfferCreate, db: Session = Depends(get_db)) -> OfferRead:
    return create_offer(db, payload)


@router.post(
    "/{offer_id}/prices",
    response_model=PriceObservationRead,
    status_code=status.HTTP_201_CREATED,
)
def post_price_observation(
    offer_id: UUID,
    payload: PriceObservationCreate,
    db: Session = Depends(get_db),
) -> PriceObservationRead:
    return record_price_observation(db, offer_id, payload)
