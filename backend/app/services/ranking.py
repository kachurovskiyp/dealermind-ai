"""Automatic, explainable Opportunity Ranking v1."""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.decision_engine import ScoreResult, ScoreType, calculate_weighted_score
from app.decision_engine.configuration import load_scoring_definition
from app.models.domain import Opportunity, ScoreKind, ScoreSnapshot


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def derive_factor_values(
    opportunity: Opportunity, now: datetime | None = None
) -> tuple[dict[ScoreType, dict[str, float]], dict[ScoreType, dict[str, str]]]:
    """Derive only factors supported by facts already stored in the domain."""
    now = now or datetime.now(UTC)
    values = {score_type: {} for score_type in ScoreType}
    explanations = {score_type: {} for score_type in ScoreType}
    purchase = opportunity.expected_purchase_price
    sale = opportunity.expected_sale_price
    costs = opportunity.expected_costs
    profit = opportunity.expected_profit

    if purchase is not None and sale is not None and sale > 0:
        price_advantage = float((sale - purchase) / sale * Decimal(100))
        values[ScoreType.MARKET]["price_position"] = clamp(50 + price_advantage * 2)
        explanations[ScoreType.MARKET]["price_position"] = (
            f"Expected purchase price is {price_advantage:.1f}% below expected sale price"
        )

    if profit is not None and sale is not None and sale > 0:
        margin = float(profit / sale * Decimal(100))
        values[ScoreType.DEALER]["predicted_net_profit"] = clamp(margin * 4)
        explanations[ScoreType.DEALER]["predicted_net_profit"] = (
            f"Expected net margin is {margin:.1f}% of sale price"
        )
    invested = None
    if purchase is not None and costs is not None:
        invested = purchase + costs
    if profit is not None and invested is not None and invested > 0:
        roi = float(profit / invested * Decimal(100))
        values[ScoreType.DEALER]["roi"] = clamp(roi * 4)
        explanations[ScoreType.DEALER]["roi"] = f"Expected ROI is {roi:.1f}%"
    if costs is not None and sale is not None and sale > 0:
        cost_share = float(costs / sale * Decimal(100))
        values[ScoreType.DEALER]["repair_risk"] = clamp(100 - cost_share * 3)
        explanations[ScoreType.DEALER]["repair_risk"] = (
            f"Declared preparation costs are {cost_share:.1f}% of sale price"
        )

    offer = opportunity.offer
    first_seen = offer.first_seen_at
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=UTC)
    age_days = max(0.0, (now - first_seen).total_seconds() / 86400)
    values[ScoreType.OPPORTUNITY]["listing_freshness"] = clamp(100 - age_days * 3.33)
    explanations[ScoreType.OPPORTUNITY]["listing_freshness"] = (
        f"Listing was first seen {age_days:.1f} days ago"
    )

    vehicle = offer.vehicle
    fields = (
        vehicle.make,
        vehicle.model,
        vehicle.year,
        vehicle.fuel_type,
        vehicle.gearbox,
        offer.mileage_km,
        offer.location,
        offer.description,
    )
    present = sum(value not in (None, "") for value in fields)
    completeness = present / len(fields) * 100
    values[ScoreType.OPPORTUNITY]["data_completeness"] = completeness
    explanations[ScoreType.OPPORTUNITY]["data_completeness"] = (
        f"{present} of {len(fields)} core listing fields are available"
    )
    return values, explanations


def _calculate(
    score_type: ScoreType,
    values: dict[str, float],
    explanations: dict[str, str],
    upstream: dict[ScoreType, ScoreResult],
) -> ScoreResult:
    definition = load_scoring_definition()
    if score_type is ScoreType.OPPORTUNITY:
        for upstream_type, factor in (
            (ScoreType.MARKET, "market_score"),
            (ScoreType.DEALER, "dealer_score"),
        ):
            result = upstream.get(upstream_type)
            if result is not None:
                values[factor] = result.value
                explanations[factor] = (
                    f"Latest automatically calculated {upstream_type.value} score"
                )
    return calculate_weighted_score(
        score_type=score_type,
        factor_values=values,
        factor_weights=definition.weights[score_type],
        configuration_version=definition.version,
        explanations=explanations,
    )


def snapshot_from_result(opportunity_id: UUID, result: ScoreResult) -> ScoreSnapshot:
    return ScoreSnapshot(
        opportunity_id=opportunity_id,
        kind=ScoreKind(result.score_type.value),
        value=Decimal(str(result.value)),
        configuration_version=result.configuration_version,
        contributions=[asdict(item) for item in result.contributions],
        missing_factors=list(result.missing_factors),
    )


def rank_opportunity(db: Session, opportunity: Opportunity) -> list[ScoreSnapshot]:
    values, explanations = derive_factor_values(opportunity)
    results: dict[ScoreType, ScoreResult] = {}
    snapshots: list[ScoreSnapshot] = []
    for score_type in (ScoreType.MARKET, ScoreType.DEALER, ScoreType.OPPORTUNITY):
        if not values[score_type] and score_type is not ScoreType.OPPORTUNITY:
            continue
        result = _calculate(score_type, values[score_type], explanations[score_type], results)
        results[score_type] = result
        snapshot = snapshot_from_result(opportunity.id, result)
        db.add(snapshot)
        snapshots.append(snapshot)
    return snapshots


def ranking_label(value: Decimal | float | None) -> str:
    if value is None:
        return "unscored"
    numeric = float(value)
    if numeric >= 80:
        return "priority"
    if numeric >= 60:
        return "review"
    return "low"
