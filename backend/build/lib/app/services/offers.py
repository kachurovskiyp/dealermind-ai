from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Offer, PriceObservation, Vehicle, utcnow
from app.schemas.offer import OfferCreate, PriceObservationCreate
from app.services.ranking import rank_opportunity


def list_offers(db: Session) -> list[Offer]:
    return list(db.scalars(select(Offer).order_by(Offer.created_at.desc()).limit(100)))


def create_offer(db: Session, payload: OfferCreate) -> Offer:
    vehicle = Vehicle(**payload.vehicle.model_dump())
    db.add(vehicle)
    db.flush()

    offer = Offer(
        marketplace_id=payload.marketplace_id,
        vehicle_id=vehicle.id,
        external_id=payload.external_id,
        url=str(payload.url),
        title=payload.title,
        description=payload.description,
        mileage_km=payload.mileage_km,
        location=payload.location,
        seller_type=payload.seller_type,
        raw_data=payload.raw_data,
    )
    db.add(offer)
    db.flush()
    db.add(PriceObservation(offer_id=offer.id, amount=payload.price, currency=payload.currency))
    db.commit()
    db.refresh(offer)
    return offer


def record_price_observation(
    db: Session, offer_id: UUID, payload: PriceObservationCreate
) -> PriceObservation:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    observation = PriceObservation(offer_id=offer.id, **payload.model_dump())
    offer.last_seen_at = utcnow()
    db.add(observation)
    for opportunity in offer.opportunities:
        if opportunity.currency == payload.currency:
            opportunity.expected_purchase_price = payload.amount
            if (
                opportunity.expected_sale_price is not None
                and opportunity.expected_costs is not None
            ):
                opportunity.expected_profit = (
                    opportunity.expected_sale_price
                    - payload.amount
                    - opportunity.expected_costs
                )
            rank_opportunity(db, opportunity)
    db.commit()
    db.refresh(observation)
    return observation
