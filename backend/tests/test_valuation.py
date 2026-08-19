from decimal import Decimal

from app.models.domain import ValuationSnapshot
from app.services.valuation import estimate_from_comparables


CONFIG = {
    "version": "valuation-v1",
    "minimum_comparables": 2,
    "sale_discount": 0.04,
}


def test_adjusted_median_produces_conservative_explainable_estimate() -> None:
    result = estimate_from_comparables(
        [Decimal("100000"), Decimal("110000"), Decimal("120000")],
        [Decimal("1.00"), Decimal("0.95"), Decimal("0.90")],
        CONFIG,
    )

    assert result is not None
    assert result.market_estimate == Decimal("104500")
    assert result.conservative_sale_price == Decimal("100320")
    assert result.sample_size == 3
    assert result.confidence == "low"
    assert result.configuration_version == "valuation-v1"
    assert result.explanation["method"] == "adjusted_median"


def test_too_few_comparables_returns_no_estimate() -> None:
    assert estimate_from_comparables([Decimal("100000")], [Decimal("1")], CONFIG) is None


def test_valuation_history_table_is_registered() -> None:
    assert "valuation_snapshots" in ValuationSnapshot.metadata.tables
