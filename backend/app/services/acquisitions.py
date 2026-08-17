from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import (
    Acquisition,
    AcquisitionStatus,
    InventoryItem,
    InventoryStatus,
    Opportunity,
    OpportunityStatus,
    VehicleEvent,
    utcnow,
)
from app.schemas.acquisition import AcquisitionComplete, AcquisitionCreate


STARTABLE_OPPORTUNITY_STATUSES = {OpportunityStatus.ACCEPTED}
COMPLETABLE_ACQUISITION_STATUSES = {
    AcquisitionStatus.PLANNED,
    AcquisitionStatus.INSPECTING,
    AcquisitionStatus.NEGOTIATING,
}


def ensure_acquisition_can_start(opportunity: Opportunity) -> None:
    if opportunity.status not in STARTABLE_OPPORTUNITY_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"acquisition cannot start from opportunity status '{opportunity.status.value}'",
        )
    if opportunity.acquisition is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="opportunity already has an acquisition",
        )


def ensure_acquisition_can_complete(acquisition: Acquisition) -> None:
    if acquisition.status not in COMPLETABLE_ACQUISITION_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"acquisition cannot complete from status '{acquisition.status.value}'",
        )
    if acquisition.inventory_item is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="acquisition already created an inventory item",
        )


def start_acquisition(
    db: Session, opportunity_id: UUID, payload: AcquisitionCreate
) -> Acquisition:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    ensure_acquisition_can_start(opportunity)

    acquisition = Acquisition(opportunity_id=opportunity.id, **payload.model_dump())
    db.add(acquisition)
    db.flush()
    db.add(
        VehicleEvent(
            vehicle_id=opportunity.offer.vehicle_id,
            event_type="acquisition.started",
            aggregate_type="acquisition",
            aggregate_id=acquisition.id,
            payload={
                "opportunity_id": str(opportunity.id),
                "currency": acquisition.currency.value,
                "agreed_price": (
                    str(acquisition.agreed_price) if acquisition.agreed_price is not None else None
                ),
            },
        )
    )
    db.commit()
    db.refresh(acquisition)
    return acquisition


def complete_acquisition(
    db: Session, acquisition_id: UUID, payload: AcquisitionComplete
) -> InventoryItem:
    acquisition = db.get(Acquisition, acquisition_id)
    if acquisition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acquisition not found")
    ensure_acquisition_can_complete(acquisition)

    acquired_at = payload.acquired_at or utcnow()
    opportunity = acquisition.opportunity
    inventory_item = InventoryItem(
        acquisition_id=acquisition.id,
        vehicle_id=opportunity.offer.vehicle_id,
        owning_market_id=opportunity.target_market_id,
        status=InventoryStatus.IN_TRANSIT,
        stock_number=payload.stock_number,
        acquired_at=acquired_at,
    )
    acquisition.agreed_price = payload.agreed_price
    acquisition.acquired_at = acquired_at
    acquisition.status = AcquisitionStatus.COMPLETED
    opportunity.status = OpportunityStatus.ACQUIRED
    db.add(inventory_item)
    db.flush()
    db.add(
        VehicleEvent(
            vehicle_id=inventory_item.vehicle_id,
            event_type="purchase.completed",
            aggregate_type="inventory_item",
            aggregate_id=inventory_item.id,
            occurred_at=acquired_at,
            payload={
                "acquisition_id": str(acquisition.id),
                "opportunity_id": str(opportunity.id),
                "stock_number": inventory_item.stock_number,
                "agreed_price": str(payload.agreed_price),
                "currency": acquisition.currency.value,
                "owning_market_id": str(inventory_item.owning_market_id),
            },
        )
    )
    db.commit()
    db.refresh(inventory_item)
    return inventory_item


def list_vehicle_events(db: Session, vehicle_id: UUID) -> list[VehicleEvent]:
    return list(
        db.scalars(
            select(VehicleEvent)
            .where(VehicleEvent.vehicle_id == vehicle_id)
            .order_by(VehicleEvent.occurred_at, VehicleEvent.recorded_at)
        )
    )
