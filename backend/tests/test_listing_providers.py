import pytest

from app.market_intelligence import CsvListingProvider, StructuredListingProvider
from app.schemas.imports import ListingImportRecord


CSV_HEADER = (
    "market_code,marketplace_slug,target_market_code,external_id,url,title,make,model,"
    "price,currency,expected_sale_price,expected_costs\n"
)


def test_csv_provider_normalizes_a_listing() -> None:
    provider = CsvListingProvider(
        CSV_HEADER
        + "pl,OTOMOTO,pl,offer-1,https://example.com/1,VW Passat,VW,Passat,"
        "40000,PLN,50000,2000\n"
    )

    records = provider.records()

    assert len(records) == 1
    assert records[0].market_code == "PL"
    assert records[0].marketplace_slug == "otomoto"
    assert records[0].external_id == "offer-1"


def test_csv_provider_reports_source_row_for_invalid_data() -> None:
    provider = CsvListingProvider(
        CSV_HEADER
        + "PL,otomoto,PL,offer-1,not-a-url,VW Passat,VW,Passat,40000,PLN,50000,0\n"
    )

    with pytest.raises(ValueError, match="row 2"):
        provider.records()


def test_structured_provider_preserves_provider_identity() -> None:
    record = ListingImportRecord(
        market_code="PL",
        marketplace_slug="otomoto",
        target_market_code="PL",
        external_id="offer-1",
        url="https://example.com/1",
        image_url="https://example.com/1.jpg",
        title="VW Passat",
        make="VW",
        model="Passat",
        price=40_000,
        currency="PLN",
    )
    provider = StructuredListingProvider([record], name="test-feed")

    assert provider.name == "test-feed"
    assert provider.records() == [record]
    assert str(provider.records()[0].image_url) == "https://example.com/1.jpg"
