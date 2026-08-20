"""Poland-only market analytics built from normalized listing observations."""

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import Currency, Market, Marketplace, Offer, OfferStatus
from app.services.variant_intelligence import price_premium, variant_label


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _normalize(value: str | None) -> str:
    return (value or "").strip().casefold()


def price_percentile(price: Decimal, comparison_prices: list[Decimal]) -> int | None:
    if len(comparison_prices) < 2:
        return None
    cheaper_or_equal = sum(value <= price for value in comparison_prices)
    return round(cheaper_or_equal / len(comparison_prices) * 100)


def _offers(db: Session) -> list[Offer]:
    return list(
        db.scalars(
            select(Offer)
            .join(Marketplace, Marketplace.id == Offer.marketplace_id)
            .join(Market, Market.id == Marketplace.market_id)
            .where(Market.code == "PL")
            .options(
                selectinload(Offer.vehicle),
                selectinload(Offer.prices),
                selectinload(Offer.marketplace),
            )
            .order_by(Offer.first_seen_at.desc())
            .limit(5000)
        )
    )


def _latest_price(offer: Offer) -> Decimal | None:
    prices = [item for item in offer.prices if item.currency == Currency.PLN]
    if not prices:
        return None
    return max(prices, key=lambda item: item.observed_at).amount


def _matches(
    offer: Offer,
    make: str | None,
    model: str | None,
    year_from: int | None,
    year_to: int | None,
    fuel_type: str | None,
    gearbox: str | None,
    seller_type: str | None,
    region: str | None,
) -> bool:
    vehicle = offer.vehicle
    values = (
        not make or _normalize(vehicle.make) == _normalize(make),
        not model or _normalize(vehicle.model) == _normalize(model),
        year_from is None or (vehicle.year is not None and vehicle.year >= year_from),
        year_to is None or (vehicle.year is not None and vehicle.year <= year_to),
        not fuel_type or _normalize(vehicle.fuel_type) == _normalize(fuel_type),
        not gearbox or _normalize(vehicle.gearbox) == _normalize(gearbox),
        not seller_type
        or (
            seller_type == "unknown"
            and not offer.seller_type
        )
        or _normalize(offer.seller_type) == _normalize(seller_type),
        not region
        or _normalize(str(offer.raw_data.get("location_region") or ""))
        == _normalize(region),
    )
    return all(values)


def _filter_options(offers: list[Offer]) -> dict[str, object]:
    def unique(values: list[str | None]) -> list[str]:
        return sorted({value.strip() for value in values if value and value.strip()})

    models_by_make: dict[str, set[str]] = defaultdict(set)
    for item in offers:
        make = (item.vehicle.make or "").strip()
        model = (item.vehicle.model or "").strip()
        if make and model:
            models_by_make[make].add(model)
    return {
        "makes": unique([item.vehicle.make for item in offers]),
        "models": unique([item.vehicle.model for item in offers]),
        "models_by_make": {
            make: sorted(models) for make, models in sorted(models_by_make.items())
        },
        "fuel_types": unique([item.vehicle.fuel_type for item in offers]),
        "gearboxes": unique([item.vehicle.gearbox for item in offers]),
        "regions": unique(
            [str(item.raw_data.get("location_region") or "") for item in offers]
        ),
    }


def poland_market_analytics(
    db: Session,
    make: str | None = None,
    model: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    fuel_type: str | None = None,
    gearbox: str | None = None,
    seller_type: str | None = None,
    region: str | None = None,
) -> dict[str, object]:
    all_offers = _offers(db)
    offers = [
        item
        for item in all_offers
        if _matches(
            item,
            make,
            model,
            year_from,
            year_to,
            fuel_type,
            gearbox,
            seller_type,
            region,
        )
    ]
    now = datetime.now(UTC)
    priced = [(item, _latest_price(item)) for item in offers]
    priced = [(item, price) for item, price in priced if price is not None]
    prices = [price for _, price in priced]
    active = [item for item in offers if item.status is OfferStatus.ACTIVE]
    reductions = 0
    history: list[dict[str, object]] = []
    for offer in offers:
        observations = sorted(
            (item for item in offer.prices if item.currency == Currency.PLN),
            key=lambda item: item.observed_at,
        )
        for previous, current in zip(observations, observations[1:]):
            if current.amount < previous.amount:
                reductions += 1
                history.append(
                    {
                        "offer_id": offer.id,
                        "vehicle": f"{offer.vehicle.make} {offer.vehicle.model}",
                        "url": offer.url,
                        "previous_price": previous.amount,
                        "current_price": current.amount,
                        "change_percent": round(
                            float((current.amount - previous.amount) / previous.amount * 100),
                            1,
                        ),
                        "changed_at": current.observed_at,
                    }
                )
    seller_counts = Counter(item.seller_type or "unknown" for item in offers)
    days_seen = [(now - item.first_seen_at).days for item in active]

    price_bands: list[dict[str, object]] = []
    if prices:
        low = min(prices)
        high = max(prices)
        step = max(Decimal("1000"), ((high - low) / 8).quantize(Decimal("1000")))
        counts: Counter[int] = Counter(int((price - low) // step) for price in prices)
        for bucket in range(max(counts, default=0) + 1):
            start = _money(low + step * bucket)
            price_bands.append(
                {
                    "price_from": start,
                    "price_to": _money(start + step),
                    "count": counts[bucket],
                }
            )

    regions: dict[str, list[Decimal]] = defaultdict(list)
    for offer, price in priced:
        offer_region = str(offer.raw_data.get("location_region") or "Не определено")
        regions[offer_region].append(price)
    region_stats = sorted(
        (
            {
                "region": name,
                "listings": len(values),
                "median_price": _money(median(values)),
            }
            for name, values in regions.items()
        ),
        key=lambda item: int(item["listings"]),
        reverse=True,
    )

    seller_prices: dict[str, list[Decimal]] = defaultdict(list)
    for offer, price in priced:
        seller_prices[offer.seller_type or "unknown"].append(price)
    seller_stats = [
        {
            "seller_type": kind,
            "listings": seller_counts[kind],
            "median_price": _money(median(values)) if values else None,
        }
        for kind, values in (
            ("private", seller_prices["private"]),
            ("dealer", seller_prices["dealer"]),
            ("unknown", seller_prices["unknown"]),
        )
    ]

    rows: list[dict[str, object]] = []
    for offer, price in priced[:100]:
        comparison = [
            other_price
            for other, other_price in priced
            if _normalize(other.vehicle.make) == _normalize(offer.vehicle.make)
            and _normalize(other.vehicle.model) == _normalize(offer.vehicle.model)
            and (
                offer.vehicle.year is None
                or other.vehicle.year is None
                or abs(offer.vehicle.year - other.vehicle.year) <= 2
            )
        ]
        rows.append(
            {
                "offer_id": offer.id,
                "vehicle": f"{offer.vehicle.make} {offer.vehicle.model}",
                "year": offer.vehicle.year,
                "price": price,
                "url": offer.url,
                "seller_type": offer.seller_type,
                "region": offer.raw_data.get("location_region"),
                "days_observed": max(0, (now - offer.first_seen_at).days),
                "price_percentile": price_percentile(price, comparison),
                "comparison_size": len(comparison),
            }
        )

    return {
        "market_code": "PL",
        "currency": "PLN",
        "generated_at": now,
        "filters": _filter_options(all_offers),
        "summary": {
            "listings": len(offers),
            "active_listings": len(active),
            "new_7_days": sum(item.first_seen_at >= now - timedelta(days=7) for item in offers),
            "new_30_days": sum(
                item.first_seen_at >= now - timedelta(days=30) for item in offers
            ),
            "median_price": _money(median(prices)) if prices else None,
            "price_reductions": reductions,
            "median_days_observed": round(median(days_seen)) if days_seen else None,
            "private_listings": seller_counts["private"],
            "dealer_listings": seller_counts["dealer"],
        },
        "price_distribution": price_bands,
        "seller_stats": seller_stats,
        "region_stats": region_stats[:16],
        "price_history": sorted(history, key=lambda item: item["changed_at"], reverse=True)[:50],
        "listings": rows,
    }


def model_variant_analytics(
    db: Session, make: str, model: str
) -> list[dict[str, object]]:
    offers = [
        offer
        for offer in _offers(db)
        if _normalize(offer.vehicle.make) == _normalize(make)
        and _normalize(offer.vehicle.model) == _normalize(model)
    ]
    priced = [(offer, _latest_price(offer)) for offer in offers]
    priced = [(offer, price) for offer, price in priced if price is not None]
    if not priced:
        return []
    base_median = _money(median([price for _, price in priced]))
    groups: dict[str, list[tuple[Offer, Decimal]]] = defaultdict(list)
    for offer, price in priced:
        vehicle = offer.vehicle
        label = variant_label(
            {
                "generation": vehicle.generation,
                "body_type": vehicle.body_type,
                "engine_marketing_name": vehicle.engine_marketing_name,
                "power_hp": vehicle.power_hp,
                "drivetrain": vehicle.drivetrain,
                "trim_line": vehicle.trim_line,
            }
        )
        groups[label].append((offer, price))
    result: list[dict[str, object]] = []
    for label, items in groups.items():
        prices = [price for _, price in items]
        group_median = _money(median(prices))
        sample_size = len(items)
        known_fields = sum(
            bool(value)
            for value in (
                items[0][0].vehicle.generation,
                items[0][0].vehicle.body_type,
                items[0][0].vehicle.engine_marketing_name,
                items[0][0].vehicle.power_hp,
                items[0][0].vehicle.drivetrain,
                items[0][0].vehicle.trim_line,
            )
        )
        result.append(
            {
                "variant": label,
                "sample_size": sample_size,
                "median_price": group_median,
                "price_low": min(prices),
                "price_high": max(prices),
                "premium_percent": price_premium(group_median, base_median),
                "confidence": (
                    "high" if sample_size >= 8 else "medium" if sample_size >= 4 else "low"
                ),
                "specification_completeness": round(known_fields / 6 * 100),
            }
        )
    return sorted(result, key=lambda item: int(item["sample_size"]), reverse=True)
