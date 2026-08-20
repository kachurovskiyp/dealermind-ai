from decimal import Decimal

from sqlalchemy import event

from app.models.domain import LogisticsSnapshot, Opportunity, _reject_history_mutation
from app.services.logistics import calculate_costs, haversine_km


def test_logistics_tables_and_append_only_history_are_registered() -> None:
    assert {"logistics_profiles", "logistics_snapshots"}.issubset(Opportunity.metadata.tables)
    assert event.contains(LogisticsSnapshot, "before_update", _reject_history_mutation)
    assert event.contains(LogisticsSnapshot, "before_delete", _reject_history_mutation)


def test_haversine_distance_is_stable() -> None:
    distance = haversine_km(
        Decimal("52.4064"), Decimal("16.9252"), Decimal("52.2297"), Decimal("21.0122")
    )

    assert Decimal("278") < distance < Decimal("280")


def test_cost_formula_explains_round_trip_and_border_surcharge() -> None:
    distance, distance_cost, border_cost, total = calculate_costs(
        direct_distance_km=Decimal("100"),
        fixed_cost=Decimal("100"),
        cost_per_km=Decimal("2.50"),
        trip_multiplier=Decimal("2"),
        cross_border_surcharge=Decimal("300"),
        cross_border=True,
    )

    assert distance == Decimal("240.0")
    assert distance_cost == Decimal("600.00")
    assert border_cost == Decimal("300.00")
    assert total == Decimal("1000.00")
