from decimal import Decimal

import pytest
from sqlalchemy import event

from app.models.domain import (
    DecisionType,
    Opportunity,
    OpportunityDecision,
    OpportunityStatus,
    ScoreSnapshot,
    VehicleEvent,
    _reject_history_mutation,
)
from app.schemas.opportunity import OpportunityCreate
from app.services.opportunities import InvalidOpportunityTransition, next_opportunity_status


def test_domain_core_tables_are_registered() -> None:
    assert {
        "opportunities",
        "score_snapshots",
        "opportunity_decisions",
        "acquisitions",
        "inventory_items",
        "preparations",
        "sales",
        "vehicle_events",
    }.issubset(Opportunity.metadata.tables)


def test_history_models_enforce_append_only_listeners() -> None:
    for model in (ScoreSnapshot, OpportunityDecision, VehicleEvent):
        assert event.contains(model, "before_update", _reject_history_mutation)
        assert event.contains(model, "before_delete", _reject_history_mutation)


def test_append_only_guard_rejects_mutation() -> None:
    with pytest.raises(ValueError, match="append-only"):
        _reject_history_mutation(None, None, VehicleEvent())


def test_opportunity_input_rejects_negative_costs() -> None:
    with pytest.raises(ValueError):
        OpportunityCreate(
            offer_id="f533d790-2b92-4fef-a7a3-571936923407",
            target_market_id="48fa3630-15de-47d2-a812-ce1fc3c18fa6",
            expected_costs=Decimal("-1"),
            currency="PLN",
        )


def test_opportunity_lifecycle_accepts_valid_transition() -> None:
    assert (
        next_opportunity_status(OpportunityStatus.EVALUATING, DecisionType.ACCEPT)
        is OpportunityStatus.ACCEPTED
    )


def test_rejected_opportunity_must_be_reopened_before_accepting() -> None:
    with pytest.raises(InvalidOpportunityTransition, match="not allowed"):
        next_opportunity_status(OpportunityStatus.REJECTED, DecisionType.ACCEPT)


def test_accepted_opportunity_can_be_rejected_before_acquisition() -> None:
    assert (
        next_opportunity_status(OpportunityStatus.ACCEPTED, DecisionType.REJECT)
        is OpportunityStatus.REJECTED
    )
