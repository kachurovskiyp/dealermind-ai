"""Collect market comparables without creating Offers or Opportunities."""

import re
import unicodedata
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.market_intelligence.otomoto_watchlist import collect_otomoto_records
from app.models.automation import ImportSource
from app.models.domain import (
    ComparableCollection,
    ComparableListing,
    Offer,
    Opportunity,
    ValuationSnapshot,
    utcnow,
)
from app.schemas.imports import ListingImportRecord
from app.services.valuation import recalculate_valuation


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def comparable_search_url(db: Session, opportunity: Opportunity) -> str:
    provider = str(opportunity.offer.raw_data.get("provider", ""))
    source = db.scalar(
        select(ImportSource).where(
            ImportSource.name == provider,
            ImportSource.provider_type == "otomoto_search",
        )
    )
    if source is not None:
        return source.endpoint_url
    vehicle = opportunity.offer.vehicle
    return f"https://www.otomoto.pl/osobowe/{_slug(vehicle.make)}/{_slug(vehicle.model)}"


async def collect_comparables(
    db: Session, opportunity_id: UUID, limit: int = 25
) -> tuple[ComparableCollection, ValuationSnapshot | None]:
    opportunity = db.scalar(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(selectinload(Opportunity.offer).selectinload(Offer.vehicle))
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    limit = max(3, min(limit, 25))
    source_url = comparable_search_url(db, opportunity)
    collection = ComparableCollection(
        opportunity_id=opportunity.id,
        source_url=source_url,
        requested_limit=limit,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    try:
        records, errors = await collect_otomoto_records(source_url, max_results=limit)
        unique: dict[str, ListingImportRecord] = {}
        for record in records:
            if record.external_id != opportunity.offer.external_id:
                unique[record.external_id] = record
        for record in unique.values():
            db.add(
                ComparableListing(
                    collection_id=collection.id,
                    external_id=record.external_id,
                    url=str(record.url),
                    title=record.title,
                    make=record.make,
                    model=record.model,
                    year=record.year,
                    mileage_km=record.mileage_km,
                    generation=record.generation,
                    body_type=record.body_type,
                    engine_marketing_name=record.engine_marketing_name,
                    power_hp=record.power_hp,
                    fuel_type=record.fuel_type,
                    gearbox=record.gearbox,
                    drivetrain=record.drivetrain,
                    trim_line=record.trim_line,
                    performance_variant=record.performance_variant,
                    price=record.price,
                    currency=record.currency,
                )
            )
        collection.found_count = len(records) + len(errors)
        collection.usable_count = len(unique)
        collection.error_message = "; ".join(errors)[:4000] or None
        collection.status = "partial" if errors else "completed"
        collection.completed_at = utcnow()
        db.commit()
        valuation = None
        if collection.usable_count >= 2:
            valuation = recalculate_valuation(db, opportunity.id)
        db.refresh(collection)
        return collection, valuation
    except Exception as exc:
        db.rollback()
        collection = db.get(ComparableCollection, collection.id)
        if collection is not None:
            collection.status = "failed"
            collection.error_message = str(exc)[:4000]
            collection.completed_at = utcnow()
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось собрать аналоги: {exc}",
        ) from exc
