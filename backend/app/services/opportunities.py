from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.decision_engine import ScoreType, calculate_weighted_score
from app.models.domain import (
    DecisionType,
    Offer,
    Opportunity,
    OpportunityDecision,
    OpportunityStatus,
    ScoreKind,
    ScoreSnapshot,
)
from app.schemas.opportunity import DecisionCreate, OpportunityCreate, ScoreCalculate
from app.services.ranking import rank_opportunity, ranking_label


class InvalidOpportunityTransition(ValueError):
    """Raised when a decision does not follow the opportunity lifecycle."""


ALLOWED_DECISIONS: dict[OpportunityStatus, set[DecisionType]] = {
    OpportunityStatus.NEW: {DecisionType.EVALUATE, DecisionType.ACCEPT, DecisionType.REJECT},
    OpportunityStatus.EVALUATING: {DecisionType.ACCEPT, DecisionType.REJECT},
    OpportunityStatus.REJECTED: {DecisionType.REOPEN},
    OpportunityStatus.EXPIRED: {DecisionType.REOPEN},
    OpportunityStatus.ACCEPTED: {DecisionType.REJECT},
    OpportunityStatus.ACQUIRED: set(),
}


def next_opportunity_status(
    current: OpportunityStatus, decision: DecisionType
) -> OpportunityStatus:
    if decision not in ALLOWED_DECISIONS[current]:
        raise InvalidOpportunityTransition(
            f"decision '{decision.value}' is not allowed from status '{current.value}'"
        )
    return {
        DecisionType.EVALUATE: OpportunityStatus.EVALUATING,
        DecisionType.ACCEPT: OpportunityStatus.ACCEPTED,
        DecisionType.REJECT: OpportunityStatus.REJECTED,
        DecisionType.REOPEN: OpportunityStatus.EVALUATING,
    }[decision]


def list_opportunities(db: Session) -> list[Opportunity]:
    return list(db.scalars(select(Opportunity).order_by(Opportunity.created_at.desc()).limit(100)))


def opportunity_feed(db: Session) -> list[dict[str, object]]:
    opportunities = db.scalars(
        select(Opportunity)
        .options(
            selectinload(Opportunity.offer).selectinload(Offer.vehicle),
            selectinload(Opportunity.scores),
            selectinload(Opportunity.valuations),
            selectinload(Opportunity.comparable_collections),
            selectinload(Opportunity.logistics_snapshots),
            selectinload(Opportunity.acquisition),
        )
        .order_by(Opportunity.created_at.desc())
        .limit(100)
    ).all()
    feed: list[dict[str, object]] = []
    for opportunity in opportunities:
        latest_scores: dict[str, Decimal] = {}
        latest_by_kind: dict[str, ScoreSnapshot] = {}
        for snapshot in opportunity.scores:
            latest_scores[snapshot.kind.value] = snapshot.value
            latest_by_kind[snapshot.kind.value] = snapshot
        ranking_snapshot = latest_by_kind.get(ScoreKind.OPPORTUNITY.value)
        valuation = opportunity.valuations[-1] if opportunity.valuations else None
        latest_collection = (
            opportunity.comparable_collections[-1]
            if opportunity.comparable_collections
            else None
        )
        logistics = (
            opportunity.logistics_snapshots[-1]
            if opportunity.logistics_snapshots
            else None
        )
        reasons: list[str] = []
        if ranking_snapshot is not None:
            ranked_contributions = sorted(
                ranking_snapshot.contributions,
                key=lambda item: float(item.get("weighted_points", 0)),
                reverse=True,
            )
            reasons = [
                str(item["explanation"])
                for item in ranked_contributions
                if item.get("explanation")
            ][:3]
        feed.append(
            {
                **{
                    column.name: getattr(opportunity, column.name)
                    for column in Opportunity.__table__.columns
                },
                "offer_title": opportunity.offer.title,
                "offer_url": opportunity.offer.url,
                "offer_image_url": opportunity.offer.raw_data.get("image_url"),
                "offer_location": opportunity.offer.location,
                "offer_location_region": opportunity.offer.raw_data.get("location_region"),
                "offer_country_code": opportunity.offer.raw_data.get("country_code"),
                "offer_seller_type": opportunity.offer.seller_type,
                "vehicle_make": opportunity.offer.vehicle.make,
                "vehicle_model": opportunity.offer.vehicle.model,
                "vehicle_year": opportunity.offer.vehicle.year,
                "vehicle_generation": opportunity.offer.vehicle.generation,
                "vehicle_body_type": opportunity.offer.vehicle.body_type,
                "vehicle_engine_marketing_name": (
                    opportunity.offer.vehicle.engine_marketing_name
                ),
                "vehicle_power_hp": opportunity.offer.vehicle.power_hp,
                "vehicle_drivetrain": opportunity.offer.vehicle.drivetrain,
                "vehicle_trim_line": opportunity.offer.vehicle.trim_line,
                "latest_scores": latest_scores,
                "ranking_label": ranking_label(
                    ranking_snapshot.value if ranking_snapshot is not None else None
                ),
                "ranking_reasons": reasons,
                "scoring_version": (
                    ranking_snapshot.configuration_version
                    if ranking_snapshot is not None
                    else None
                ),
                "acquisition_id": (
                    opportunity.acquisition.id if opportunity.acquisition is not None else None
                ),
                "valuation": valuation,
                "latest_collection_status": (
                    latest_collection.status if latest_collection is not None else None
                ),
                "latest_collection_usable_count": (
                    latest_collection.usable_count if latest_collection is not None else None
                ),
                "logistics": logistics,
            }
        )
    feed.sort(
        key=lambda item: (
            float(item["latest_scores"].get(ScoreKind.OPPORTUNITY.value, -1)),  # type: ignore[union-attr]
            item["created_at"],
        ),
        reverse=True,
    )
    return feed


def create_opportunity(db: Session, payload: OpportunityCreate) -> Opportunity:
    profit: Decimal | None = None
    if all(
        value is not None
        for value in (
            payload.expected_purchase_price,
            payload.expected_sale_price,
            payload.expected_costs,
        )
    ):
        profit = (
            payload.expected_sale_price - payload.expected_purchase_price - payload.expected_costs
        )  # type: ignore[operator]
    opportunity = Opportunity(**payload.model_dump(), expected_profit=profit)
    db.add(opportunity)
    db.flush()
    rank_opportunity(db, opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


def recalculate_opportunity(db: Session, opportunity_id: UUID) -> list[ScoreSnapshot]:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    snapshots = rank_opportunity(db, opportunity)
    db.commit()
    for snapshot in snapshots:
        db.refresh(snapshot)
    return snapshots


def record_decision(
    db: Session, opportunity_id: UUID, payload: DecisionCreate
) -> OpportunityDecision:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    if (
        opportunity.status is OpportunityStatus.ACCEPTED
        and payload.decision is DecisionType.REJECT
        and opportunity.acquisition is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Нельзя отказаться от возможности после начала покупки",
        )
    try:
        next_status = next_opportunity_status(opportunity.status, payload.decision)
    except InvalidOpportunityTransition as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    decision = OpportunityDecision(opportunity_id=opportunity_id, **payload.model_dump())
    opportunity.status = next_status
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


def calculate_and_store_score(
    db: Session, opportunity_id: UUID, payload: ScoreCalculate
) -> ScoreSnapshot:
    if db.get(Opportunity, opportunity_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    result = calculate_weighted_score(
        score_type=ScoreType(payload.kind.value),
        factor_values=payload.factor_values,
        factor_weights=payload.factor_weights,
        configuration_version=payload.configuration_version,
        explanations=payload.explanations,
    )
    snapshot = ScoreSnapshot(
        opportunity_id=opportunity_id,
        kind=ScoreKind(result.score_type.value),
        value=Decimal(str(result.value)),
        configuration_version=result.configuration_version,
        contributions=[
            {
                "key": item.key,
                "value": item.value,
                "weight": item.weight,
                "weighted_points": item.weighted_points,
                "explanation": item.explanation,
            }
            for item in result.contributions
        ],
        missing_factors=list(result.missing_factors),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
