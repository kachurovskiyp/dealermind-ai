from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import (
    Offer,
    PriceObservation,
    Vehicle,
    VehicleSpecificationObservation,
    utcnow,
)
from app.schemas.offer import OfferCreate, PriceObservationCreate, VehicleSpecificationConfirm
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


CONFIRMABLE_SPECIFICATIONS = {
    "generation",
    "body_type",
    "facelift",
    "engine_marketing_name",
    "engine_code",
    "engine_capacity_cc",
    "power_hp",
    "power_kw",
    "fuel_type",
    "gearbox",
    "drivetrain",
    "trim_line",
    "performance_variant",
}
INTEGER_SPECIFICATIONS = {"engine_capacity_cc", "power_hp", "power_kw"}


def list_vehicle_specifications(
    db: Session, offer_id: UUID
) -> list[VehicleSpecificationObservation]:
    if db.get(Offer, offer_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return list(
        db.scalars(
            select(VehicleSpecificationObservation)
            .where(VehicleSpecificationObservation.offer_id == offer_id)
            .order_by(VehicleSpecificationObservation.observed_at.desc())
        )
    )


def confirm_vehicle_specification(
    db: Session, offer_id: UUID, payload: VehicleSpecificationConfirm
) -> VehicleSpecificationObservation:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    if payload.field_name not in CONFIRMABLE_SPECIFICATIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Эту характеристику нельзя подтвердить",
        )
    value: object = payload.value
    if payload.field_name in INTEGER_SPECIFICATIONS:
        try:
            value = int(payload.value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Для этой характеристики требуется целое число",
            ) from exc
    elif payload.field_name == "facelift":
        normalized = str(payload.value).strip().casefold()
        if normalized not in {"true", "false", "1", "0", "yes", "no"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Для рестайлинга требуется значение да/нет",
            )
        value = normalized in {"true", "1", "yes"}
    else:
        value = str(payload.value).strip()
        if not value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Значение не может быть пустым",
            )
    setattr(offer.vehicle, payload.field_name, value)
    observation = VehicleSpecificationObservation(
        vehicle_id=offer.vehicle_id,
        offer_id=offer.id,
        field_name=payload.field_name,
        normalized_value=value,
        raw_value=str(payload.value),
        source="manual_confirmation",
        confidence=Decimal("1.000"),
        confirmed=True,
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


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
