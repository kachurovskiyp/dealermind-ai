from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.decision_engine import ScoreType
from app.decision_engine.configuration import load_scoring_definition
from app.models.domain import Offer, Opportunity, Vehicle
from app.services.ranking import derive_factor_values, rank_opportunity, ranking_label


def opportunity_fixture() -> Opportunity:
    vehicle = Vehicle(make="Volkswagen", model="Passat", year=2019)
    offer = Offer(
        vehicle=vehicle,
        title="Volkswagen Passat 2019",
        url="https://example.com/offer",
        external_id="ranking-test",
        first_seen_at=datetime.now(UTC) - timedelta(days=2),
        mileage_km=140_000,
    )
    return Opportunity(
        id=uuid4(),
        offer=offer,
        expected_purchase_price=Decimal("40000"),
        expected_sale_price=Decimal("50000"),
        expected_costs=Decimal("2000"),
        expected_profit=Decimal("8000"),
    )


def test_ranking_derives_only_evidence_backed_factors() -> None:
    values, explanations = derive_factor_values(opportunity_fixture())

    assert values[ScoreType.MARKET]["price_position"] == 90
    assert round(values[ScoreType.DEALER]["roi"], 2) == 76.19
    assert "preparation_duration" not in values[ScoreType.DEALER]
    assert "listing_freshness" in explanations[ScoreType.OPPORTUNITY]


def test_versioned_configuration_is_active() -> None:
    definition = load_scoring_definition()

    assert definition.version == "scoring-v1"
    assert definition.weights[ScoreType.OPPORTUNITY]["market_score"] == 40


def test_ranking_produces_three_explainable_snapshots() -> None:
    db = MagicMock()

    snapshots = rank_opportunity(db, opportunity_fixture())

    assert [snapshot.kind.value for snapshot in snapshots] == [
        "market",
        "dealer",
        "opportunity",
    ]
    assert snapshots[-1].configuration_version == "scoring-v1"
    assert snapshots[-1].contributions
    assert db.add.call_count == 3


def test_priority_thresholds_are_explicit() -> None:
    assert ranking_label(Decimal("80")) == "priority"
    assert ranking_label(Decimal("60")) == "review"
    assert ranking_label(Decimal("59.99")) == "low"
    assert ranking_label(None) == "unscored"
