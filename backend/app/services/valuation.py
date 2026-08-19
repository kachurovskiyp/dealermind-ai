"""Explainable comparable-listing valuation with append-only snapshots."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from statistics import median
from uuid import UUID

import yaml
from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import (
    ComparableListing,
    Offer,
    Opportunity,
    PriceObservation,
    ValuationSnapshot,
    Vehicle,
)
from app.services.ranking import rank_opportunity

CONFIG_PATH = Path(__file__).parents[1] / "core" / "configuration" / "valuation.v1.yaml"


@dataclass(frozen=True)
class ValuationResult:
    market_estimate: Decimal
    conservative_sale_price: Decimal
    price_low: Decimal
    price_high: Decimal
    sample_size: int
    confidence: str
    configuration_version: str
    explanation: dict[str, object]


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def estimate_from_comparables(
    prices: list[Decimal], adjustments: list[Decimal], config: dict[str, object]
) -> ValuationResult | None:
    minimum = int(config["minimum_comparables"])
    if len(prices) < minimum:
        return None
    adjusted = [_money(price * adjustment) for price, adjustment in zip(prices, adjustments)]
    estimate = _money(Decimal(str(median(adjusted))))
    discount = Decimal(str(config["sale_discount"]))
    confidence = "high" if len(adjusted) >= 8 else "medium" if len(adjusted) >= 4 else "low"
    return ValuationResult(
        market_estimate=estimate,
        conservative_sale_price=_money(estimate * (Decimal(1) - discount)),
        price_low=_money(estimate * Decimal("0.94")),
        price_high=_money(estimate * Decimal("1.06")),
        sample_size=len(adjusted),
        confidence=confidence,
        configuration_version=str(config["version"]),
        explanation={
            "method": "adjusted_median",
            "comparables": len(adjusted),
            "sale_discount_percent": float(discount * 100),
            "adjusted_prices": [str(value) for value in adjusted],
        },
    )


def _load_config() -> dict[str, object]:
    with CONFIG_PATH.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def calculate_valuation(db: Session, opportunity: Opportunity) -> ValuationResult | None:
    config = _load_config()
    vehicle = opportunity.offer.vehicle
    latest = (
        select(PriceObservation.offer_id, func.max(PriceObservation.observed_at).label("seen"))
        .group_by(PriceObservation.offer_id)
        .subquery()
    )
    statement = (
        select(PriceObservation.amount, Vehicle.year, Offer.mileage_km, Offer.external_id)
        .join(latest, and_(latest.c.offer_id == PriceObservation.offer_id, latest.c.seen == PriceObservation.observed_at))
        .join(Offer, Offer.id == PriceObservation.offer_id)
        .join(Vehicle, Vehicle.id == Offer.vehicle_id)
        .where(
            Offer.id != opportunity.offer_id,
            func.lower(Vehicle.make) == vehicle.make.lower(),
            func.lower(Vehicle.model) == vehicle.model.lower(),
            PriceObservation.currency == opportunity.currency,
        )
        .limit(50)
    )
    if vehicle.year is not None:
        statement = statement.where(func.abs(Vehicle.year - vehicle.year) <= int(config["year_tolerance"]))
    if opportunity.offer.mileage_km is not None:
        statement = statement.where(
            func.abs(Offer.mileage_km - opportunity.offer.mileage_km)
            <= int(config["mileage_tolerance_km"])
        )
    offer_rows = db.execute(statement).all()
    rows = [(price, year, mileage) for price, year, mileage, _external_id in offer_rows]
    seen_external_ids = {external_id for _price, _year, _mileage, external_id in offer_rows}
    comparable_statement = (
        select(
            ComparableListing.external_id,
            ComparableListing.price,
            ComparableListing.year,
            ComparableListing.mileage_km,
        )
        .where(
            func.lower(ComparableListing.make) == vehicle.make.lower(),
            func.lower(ComparableListing.model) == vehicle.model.lower(),
            ComparableListing.currency == opportunity.currency,
        )
        .order_by(ComparableListing.observed_at.desc())
        .limit(250)
    )
    comparable_rows = db.execute(comparable_statement).all()
    for external_id, price, comp_year, comp_mileage in comparable_rows:
        if external_id in seen_external_ids or external_id == opportunity.offer.external_id:
            continue
        if vehicle.year is not None and comp_year is not None:
            if abs(comp_year - vehicle.year) > int(config["year_tolerance"]):
                continue
        if opportunity.offer.mileage_km is not None and comp_mileage is not None:
            if abs(comp_mileage - opportunity.offer.mileage_km) > int(config["mileage_tolerance_km"]):
                continue
        seen_external_ids.add(external_id)
        rows.append((price, comp_year, comp_mileage))
    prices: list[Decimal] = []
    adjustments: list[Decimal] = []
    for price, comp_year, comp_mileage in rows:
        adjustment = Decimal(1)
        if vehicle.year is not None and comp_year is not None:
            adjustment += Decimal(vehicle.year - comp_year) * Decimal(str(config["year_adjustment"]))
        if opportunity.offer.mileage_km is not None and comp_mileage is not None:
            mileage_delta = Decimal(comp_mileage - opportunity.offer.mileage_km) / Decimal(10000)
            adjustment += mileage_delta * Decimal(str(config["mileage_adjustment_per_10000_km"]))
        prices.append(price)
        adjustments.append(max(Decimal("0.80"), min(Decimal("1.20"), adjustment)))
    return estimate_from_comparables(prices, adjustments, config)


def value_opportunity(db: Session, opportunity: Opportunity) -> ValuationSnapshot | None:
    result = calculate_valuation(db, opportunity)
    if result is None:
        return None
    previous = opportunity.valuations[-1] if opportunity.valuations else None
    auto_sale_price = previous is None or opportunity.expected_sale_price in (
        None,
        previous.conservative_sale_price,
    )
    snapshot = ValuationSnapshot(opportunity_id=opportunity.id, **result.__dict__)
    db.add(snapshot)
    if auto_sale_price:
        opportunity.expected_sale_price = result.conservative_sale_price
    if opportunity.expected_costs in (None, Decimal(0)) and opportunity.offer.raw_data.get("imported"):
        costs = _load_config()["default_costs"]
        opportunity.expected_costs = Decimal(str(costs.get(opportunity.currency.value, 0)))
    if opportunity.expected_sale_price is not None and opportunity.expected_purchase_price is not None:
        opportunity.expected_profit = (
            opportunity.expected_sale_price
            - opportunity.expected_purchase_price
            - (opportunity.expected_costs or Decimal(0))
        )
    rank_opportunity(db, opportunity)
    return snapshot


def value_opportunities_for_offers(db: Session, offer_ids: list[UUID]) -> int:
    opportunities = db.scalars(
        select(Opportunity)
        .where(Opportunity.offer_id.in_(offer_ids))
        .options(
            selectinload(Opportunity.offer).selectinload(Offer.vehicle),
            selectinload(Opportunity.valuations),
        )
    ).all()
    created = sum(value_opportunity(db, item) is not None for item in opportunities)
    db.commit()
    return created


def recalculate_valuation(db: Session, opportunity_id: UUID) -> ValuationSnapshot:
    opportunity = db.scalar(
        select(Opportunity)
        .where(Opportunity.id == opportunity_id)
        .options(selectinload(Opportunity.offer).selectinload(Offer.vehicle), selectinload(Opportunity.valuations))
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    snapshot = value_opportunity(db, opportunity)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Недостаточно сопоставимых объявлений: нужно минимум 2")
    db.commit()
    db.refresh(snapshot)
    return snapshot
