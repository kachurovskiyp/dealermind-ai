from decimal import Decimal

from app.services.poland_analytics import price_percentile


def test_price_percentile_shows_position_inside_market() -> None:
    result = price_percentile(
        Decimal("90000"),
        [Decimal("80000"), Decimal("90000"), Decimal("100000"), Decimal("110000")],
    )

    assert result == 50


def test_price_percentile_requires_more_than_one_comparable() -> None:
    assert price_percentile(Decimal("90000"), [Decimal("90000")]) is None
