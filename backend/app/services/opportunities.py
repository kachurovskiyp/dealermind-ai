from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.decision_engine import ScoreType, calculate_weighted_score
from app.models.domain import (
    DecisionType,
    Opportunity,
    OpportunityDecision,
    OpportunityStatus,
    ScoreKind,
    ScoreSnapshot,
)
from app.schemas.opportunity import DecisionCreate, OpportunityCreate, ScoreCalculate


class InvalidOpportunityTransition(ValueError):
    """Raised when a decision does not follow the opportunity lifecycle."""


ALLOWED_DECISIONS: dict[OpportunityStatus, set[DecisionType]] = {
    OpportunityStatus.NEW: {DecisionType.EVALUATE, DecisionType.ACCEPT, DecisionType.REJECT},
    OpportunityStatus.EVALUATING: {DecisionType.ACCEPT, DecisionType.REJECT},
    OpportunityStatus.REJECTED: {DecisionType.REOPEN},
    OpportunityStatus.EXPIRED: {DecisionType.REOPEN},
    OpportunityStatus.ACCEPTED: set(),
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
    db.commit()
    db.refresh(opportunity)
    return opportunity


def record_decision(
    db: Session, opportunity_id: UUID, payload: DecisionCreate
) -> OpportunityDecision:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
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
