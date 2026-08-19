from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market_intelligence.providers import ListingProvider
from app.models.domain import (
    Market,
    Marketplace,
    Offer,
    Opportunity,
    PriceObservation,
    Vehicle,
    utcnow,
)
from app.schemas.imports import ImportErrorRead, ListingImportRecord, ListingImportResult
from app.services.ranking import rank_opportunity


@dataclass
class ImportCounters:
    received: int
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    errors: list[ImportErrorRead] = field(default_factory=list)
    offer_ids: list[UUID] = field(default_factory=list)


def _market(db: Session, code: str) -> Market:
    market = db.scalar(select(Market).where(Market.code == code))
    if market is None:
        raise ValueError(f"market '{code}' does not exist")
    return market


def _marketplace(db: Session, market_id: UUID, slug: str) -> Marketplace:
    marketplace = db.scalar(
        select(Marketplace).where(
            Marketplace.market_id == market_id,
            Marketplace.slug == slug,
        )
    )
    if marketplace is None:
        raise ValueError(f"marketplace '{slug}' does not exist in source market")
    return marketplace


def _vehicle(db: Session, record: ListingImportRecord) -> Vehicle:
    vehicle = None
    if record.vin is not None:
        vehicle = db.scalar(select(Vehicle).where(Vehicle.vin == record.vin.upper()))
    if vehicle is None:
        vehicle = Vehicle(
            vin=record.vin.upper() if record.vin else None,
            make=record.make,
            model=record.model,
            year=record.year,
            fuel_type=record.fuel_type,
            gearbox=record.gearbox,
        )
        db.add(vehicle)
        db.flush()
    return vehicle


def _profit(record: ListingImportRecord) -> Decimal | None:
    if record.expected_sale_price is None:
        return None
    return record.expected_sale_price - record.price - record.expected_costs


def _create(
    db: Session,
    record: ListingImportRecord,
    marketplace: Marketplace,
    target_market: Market,
    provider_name: str,
) -> Offer:
    vehicle = _vehicle(db, record)
    offer = Offer(
        marketplace_id=marketplace.id,
        vehicle_id=vehicle.id,
        external_id=record.external_id,
        url=str(record.url),
        title=record.title,
        description=record.description,
        mileage_km=record.mileage_km,
        location=record.location,
        seller_type=record.seller_type,
        raw_data={"provider": provider_name, "imported": True},
    )
    db.add(offer)
    db.flush()
    db.add(PriceObservation(offer_id=offer.id, amount=record.price, currency=record.currency))
    opportunity = Opportunity(
        offer_id=offer.id,
        target_market_id=target_market.id,
        expected_purchase_price=record.price,
        expected_sale_price=record.expected_sale_price,
        expected_costs=record.expected_costs,
        expected_profit=_profit(record),
        currency=record.currency,
    )
    db.add(opportunity)
    db.flush()
    rank_opportunity(db, opportunity)
    return offer


def _update(db: Session, offer: Offer, record: ListingImportRecord) -> bool:
    data_changed = any(
        (
            offer.url != str(record.url),
            offer.title != record.title,
            offer.description != record.description,
            offer.mileage_km != record.mileage_km,
            offer.location != record.location,
            offer.seller_type != record.seller_type,
        )
    )
    offer.url = str(record.url)
    offer.title = record.title
    offer.description = record.description
    offer.mileage_km = record.mileage_km
    offer.location = record.location
    offer.seller_type = record.seller_type
    offer.last_seen_at = utcnow()
    vehicle = offer.vehicle
    vehicle_updates = {
        "make": record.make,
        "model": record.model,
        "year": record.year,
        "fuel_type": record.fuel_type,
        "gearbox": record.gearbox,
    }
    for field_name, value in vehicle_updates.items():
        if value is not None and getattr(vehicle, field_name) != value:
            setattr(vehicle, field_name, value)
            data_changed = True
    latest = db.scalar(
        select(PriceObservation)
        .where(PriceObservation.offer_id == offer.id)
        .order_by(PriceObservation.observed_at.desc())
        .limit(1)
    )
    price_changed = (
        latest is None
        or latest.amount != record.price
        or latest.currency != record.currency
    )
    if price_changed:
        db.add(PriceObservation(offer_id=offer.id, amount=record.price, currency=record.currency))
    for opportunity in offer.opportunities:
        same_currency = opportunity.currency == record.currency
        financials_changed = same_currency and (
            opportunity.expected_sale_price != record.expected_sale_price
            or opportunity.expected_costs != record.expected_costs
            or price_changed
        )
        if financials_changed or data_changed:
            if same_currency:
                opportunity.expected_purchase_price = record.price
                opportunity.expected_sale_price = record.expected_sale_price
                opportunity.expected_costs = record.expected_costs
                opportunity.expected_profit = _profit(record)
            rank_opportunity(db, opportunity)
    return price_changed or data_changed


def import_listings(db: Session, provider: ListingProvider) -> ListingImportResult:
    records = provider.records()
    counters = ImportCounters(received=len(records))
    for row_number, record in enumerate(records, start=1):
        try:
            outcome = "unchanged"
            with db.begin_nested():
                source_market = _market(db, record.market_code)
                target_market = _market(db, record.target_market_code)
                marketplace = _marketplace(db, source_market.id, record.marketplace_slug)
                offer = db.scalar(
                    select(Offer).where(
                        Offer.marketplace_id == marketplace.id,
                        Offer.external_id == record.external_id,
                    )
                )
                if offer is None:
                    offer = _create(db, record, marketplace, target_market, provider.name)
                    outcome = "created"
                elif _update(db, offer, record):
                    outcome = "updated"
            if outcome == "created":
                counters.created += 1
            elif outcome == "updated":
                counters.updated += 1
            else:
                counters.unchanged += 1
            counters.offer_ids.append(offer.id)
        except Exception as exc:
            counters.errors.append(
                ImportErrorRead(row=row_number, external_id=record.external_id, message=str(exc))
            )
    db.commit()
    result = ListingImportResult(**counters.__dict__)
    if counters.offer_ids:
        from app.services.valuation import value_opportunities_for_offers

        value_opportunities_for_offers(db, counters.offer_ids)
    return result
