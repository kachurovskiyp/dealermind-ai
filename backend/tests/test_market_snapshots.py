from decimal import Decimal

from app.services.market_snapshots import snapshot_statistics


def test_snapshot_statistics_capture_price_and_seller_mix() -> None:
    result = snapshot_statistics(
        [Decimal("80000"), Decimal("100000"), Decimal("120000")],
        ["private", "dealer", None],
    )

    assert result["listing_count"] == 3
    assert result["median_price"] == Decimal("100000")
    assert result["price_low"] == Decimal("80000")
    assert result["price_high"] == Decimal("120000")
    assert result["private_count"] == 1
    assert result["dealer_count"] == 1
    assert result["unknown_seller_count"] == 1
