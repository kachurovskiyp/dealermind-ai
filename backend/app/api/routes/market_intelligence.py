from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import (
    ComparableCollection,
    ComparableListing,
    Offer,
    Opportunity,
    ValuationSnapshot,
    Vehicle,
)
from app.schemas.market_intelligence import (
    CollectionHistoryRead,
    ComparableListingRead,
    MarketOverviewRead,
    MarketSegmentSnapshotRead,
    ModelVariantStatRead,
    PolandMarketAnalyticsRead,
    ValuationHistoryRead,
)
from app.services.market_snapshots import list_market_snapshots
from app.services.poland_analytics import model_variant_analytics, poland_market_analytics

router = APIRouter(prefix="/market-intelligence", tags=["market intelligence"])


@router.get("/poland/variants", response_model=list[ModelVariantStatRead])
def poland_variants(
    make: str,
    model: str,
    db: Session = Depends(get_db),
) -> list[ModelVariantStatRead]:
    return [
        ModelVariantStatRead.model_validate(item)
        for item in model_variant_analytics(db, make, model)
    ]


@router.get("/poland/snapshots", response_model=list[MarketSegmentSnapshotRead])
def poland_snapshots(
    source_id: UUID | None = None,
    limit: int = 500,
    db: Session = Depends(get_db),
) -> list[MarketSegmentSnapshotRead]:
    return [
        MarketSegmentSnapshotRead(
            id=item.id,
            source_id=item.source_id,
            run_id=item.run_id,
            source_name=item.source.name,
            market_code=item.market_code,
            currency=item.currency,
            listing_count=item.listing_count,
            new_count=item.new_count,
            updated_count=item.updated_count,
            price_reduction_count=item.price_reduction_count,
            median_price=item.median_price,
            price_low=item.price_low,
            price_high=item.price_high,
            private_count=item.private_count,
            dealer_count=item.dealer_count,
            unknown_seller_count=item.unknown_seller_count,
            dimensions=item.dimensions,
            configuration_version=item.configuration_version,
            captured_at=item.captured_at,
        )
        for item in list_market_snapshots(db, source_id=source_id, limit=limit)
    ]


@router.get("/poland", response_model=PolandMarketAnalyticsRead)
def poland_analytics(
    make: str | None = None,
    model: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    fuel_type: str | None = None,
    gearbox: str | None = None,
    seller_type: str | None = None,
    region: str | None = None,
    db: Session = Depends(get_db),
) -> PolandMarketAnalyticsRead:
    return PolandMarketAnalyticsRead.model_validate(
        poland_market_analytics(
            db,
            make=make,
            model=model,
            year_from=year_from,
            year_to=year_to,
            fuel_type=fuel_type,
            gearbox=gearbox,
            seller_type=seller_type,
            region=region,
        )
    )


@router.get("/overview", response_model=MarketOverviewRead)
def overview(db: Session = Depends(get_db)) -> MarketOverviewRead:
    return MarketOverviewRead(
        comparable_listings=db.scalar(select(func.count(ComparableListing.id))) or 0,
        collections=db.scalar(select(func.count(ComparableCollection.id))) or 0,
        valuations=db.scalar(select(func.count(ValuationSnapshot.id))) or 0,
        valued_opportunities=db.scalar(
            select(func.count(distinct(ValuationSnapshot.opportunity_id)))
        )
        or 0,
    )


@router.get("/valuations", response_model=list[ValuationHistoryRead])
def valuations(limit: int = 100, db: Session = Depends(get_db)) -> list[ValuationHistoryRead]:
    rows = db.execute(
        select(ValuationSnapshot, Opportunity.currency, Vehicle.make, Vehicle.model)
        .join(Opportunity, Opportunity.id == ValuationSnapshot.opportunity_id)
        .join(Offer, Offer.id == Opportunity.offer_id)
        .join(Vehicle, Vehicle.id == Offer.vehicle_id)
        .order_by(ValuationSnapshot.calculated_at.desc())
        .limit(min(max(limit, 1), 500))
    ).all()
    return [
        ValuationHistoryRead(
            id=item.id,
            opportunity_id=item.opportunity_id,
            vehicle=f"{make} {model}",
            market_estimate=item.market_estimate,
            conservative_sale_price=item.conservative_sale_price,
            price_low=item.price_low,
            price_high=item.price_high,
            currency=currency,
            sample_size=item.sample_size,
            confidence=item.confidence,
            configuration_version=item.configuration_version,
            calculated_at=item.calculated_at,
        )
        for item, currency, make, model in rows
    ]


@router.get("/collections", response_model=list[CollectionHistoryRead])
def collections(limit: int = 100, db: Session = Depends(get_db)) -> list[CollectionHistoryRead]:
    rows = db.execute(
        select(ComparableCollection, Vehicle.make, Vehicle.model)
        .join(Opportunity, Opportunity.id == ComparableCollection.opportunity_id)
        .join(Offer, Offer.id == Opportunity.offer_id)
        .join(Vehicle, Vehicle.id == Offer.vehicle_id)
        .order_by(ComparableCollection.started_at.desc())
        .limit(min(max(limit, 1), 500))
    ).all()
    return [
        CollectionHistoryRead(
            id=item.id,
            opportunity_id=item.opportunity_id,
            vehicle=f"{make} {model}",
            status=item.status,
            source_url=item.source_url,
            requested_limit=item.requested_limit,
            found_count=item.found_count,
            usable_count=item.usable_count,
            error_message=item.error_message,
            started_at=item.started_at,
            completed_at=item.completed_at,
        )
        for item, make, model in rows
    ]


@router.get("/collections/{collection_id}/listings", response_model=list[ComparableListingRead])
def collection_listings(
    collection_id: UUID, db: Session = Depends(get_db)
) -> list[ComparableListing]:
    if db.get(ComparableCollection, collection_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return list(
        db.scalars(
            select(ComparableListing)
            .where(ComparableListing.collection_id == collection_id)
            .order_by(ComparableListing.price)
        )
    )
