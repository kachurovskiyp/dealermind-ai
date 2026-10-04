from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.models.domain import Currency, OfferStatus
from app.services.poland_analytics import configuration_liquidity_from_offers, price_percentile


def test_price_percentile_shows_position_inside_market() -> None:
    result = price_percentile(
        Decimal("90000"),
        [Decimal("80000"), Decimal("90000"), Decimal("100000"), Decimal("110000")],
    )

    assert result == 50


def test_price_percentile_requires_more_than_one_comparable() -> None:
    assert price_percentile(Decimal("90000"), [Decimal("90000")]) is None


def test_configuration_liquidity_keeps_disappearance_as_signal() -> None:
    now = datetime(2026, 8, 21, tzinfo=UTC)

    def offer(status: OfferStatus, price: str, days: int, reduced: bool = False):
        prices = (
            [
                SimpleNamespace(currency=Currency.PLN, amount=Decimal("100000"), observed_at=now - timedelta(days=2)),
                SimpleNamespace(currency=Currency.PLN, amount=Decimal(price), observed_at=now - timedelta(days=1)),
            ]
            if reduced
            else [SimpleNamespace(currency=Currency.PLN, amount=Decimal(price), observed_at=now)]
        )
        return SimpleNamespace(
            vehicle=SimpleNamespace(engine_marketing_name="1.4 TFSI", gearbox="manual"),
            status=status,
            first_seen_at=now - timedelta(days=days),
            prices=prices,
        )

    rows = configuration_liquidity_from_offers(
        [offer(OfferStatus.ACTIVE, "90000", 12, True), offer(OfferStatus.INACTIVE, "95000", 20)],
        now=now,
    )

    assert rows[0]["configuration"] == "1.4 TFSI · manual"
    assert rows[0]["median_price"] == Decimal("92500")
    assert rows[0]["price_reduction_rate"] == 50.0
    assert rows[0]["disappearance_signal_rate"] == 50.0
    assert "не подтверждённая продажа" in rows[0]["interpretation"]
