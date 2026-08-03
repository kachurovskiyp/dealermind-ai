from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Offer, PriceObservation, Vehicle
from app.schemas.offer import OfferCreate


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
