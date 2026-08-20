"""Versioned time-series snapshots for user-configured Polish market searches."""

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.automation import ImportRun, ImportSource, MarketSegmentSnapshot
from app.models.domain import Currency, Offer

CONFIGURATION_VERSION = "market-snapshot-v1"


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def snapshot_statistics(
    prices: list[Decimal], seller_types: list[str | None]
) -> dict[str, object]:
    sellers = Counter(value or "unknown" for value in seller_types)
    return {
        "listing_count": len(prices),
        "median_price": _money(median(prices)) if prices else None,
        "price_low": min(prices) if prices else None,
        "price_high": max(prices) if prices else None,
        "private_count": sellers["private"],
        "dealer_count": sellers["dealer"],
        "unknown_seller_count": sellers["unknown"],
    }


def create_market_snapshot(
    db: Session,
    source: ImportSource,
    run: ImportRun,
    offer_ids: list[UUID],
    new_count: int,
    updated_count: int,
) -> MarketSegmentSnapshot | None:
    offers = list(
        db.scalars(
            select(Offer)
            .where(Offer.id.in_(offer_ids))
            .options(selectinload(Offer.vehicle), selectinload(Offer.prices))
        )
    )
    prices: list[Decimal] = []
    seller_types: list[str | None] = []
    reductions = 0
    makes: set[str] = set()
    models: set[str] = set()
    years: set[int] = set()
    regions: Counter[str] = Counter()
    for offer in offers:
        observations = sorted(
            (item for item in offer.prices if item.currency == Currency.PLN),
            key=lambda item: item.observed_at,
        )
        if not observations:
            continue
        prices.append(observations[-1].amount)
        seller_types.append(offer.seller_type)
        reductions += int(
            len(observations) > 1
            and observations[-1].amount < observations[-2].amount
        )
        makes.add(offer.vehicle.make)
        models.add(offer.vehicle.model)
        if offer.vehicle.year is not None:
            years.add(offer.vehicle.year)
        region = str(offer.raw_data.get("location_region") or "Не определено")
        regions[region] += 1
    if not prices:
        return None
    stats = snapshot_statistics(prices, seller_types)
    snapshot = MarketSegmentSnapshot(
        source_id=source.id,
        run_id=run.id,
        market_code="PL",
        currency=Currency.PLN,
        new_count=new_count,
        updated_count=updated_count,
        price_reduction_count=reductions,
        dimensions={
            "makes": sorted(makes),
            "models": sorted(models),
            "years": sorted(years),
            "regions": dict(regions.most_common()),
            "search_url": source.endpoint_url,
        },
        explanation={
            "method": "latest_price_per_offer_in_import_run",
            "offer_ids": [str(item.id) for item in offers],
            "source_name": source.name,
        },
        configuration_version=CONFIGURATION_VERSION,
        **stats,
    )
    db.add(snapshot)
    return snapshot


def list_market_snapshots(
    db: Session, source_id: UUID | None = None, limit: int = 500
) -> list[MarketSegmentSnapshot]:
    statement = select(MarketSegmentSnapshot).options(
        selectinload(MarketSegmentSnapshot.source)
    )
    if source_id is not None:
        statement = statement.where(MarketSegmentSnapshot.source_id == source_id)
    return list(
        db.scalars(
            statement.order_by(MarketSegmentSnapshot.captured_at.desc()).limit(
                min(max(limit, 1), 1000)
            )
        )
    )
