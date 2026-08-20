import asyncio
from decimal import Decimal

import pytest

from app.market_intelligence.link_intake import _ensure_public_url, extract_listing_preview


JSON_LD_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@type": "Vehicle",
  "name": "Volkswagen Passat 2019",
  "description": "Well maintained vehicle",
  "brand": {"@type": "Brand", "name": "Volkswagen"},
  "model": "Passat",
  "vehicleModelDate": "2019-01-01",
  "mileageFromOdometer": {"value": 145000, "unitCode": "KMT"},
  "sku": "offer-123",
  "offers": {"price": "52000", "priceCurrency": "PLN"}
}
</script>
</head><body></body></html>
"""


def test_json_ld_vehicle_is_extracted_without_marketplace_selectors() -> None:
    preview = extract_listing_preview(JSON_LD_HTML, "https://example.com/listing/123")

    assert preview.external_id == "offer-123"
    assert preview.make == "Volkswagen"
    assert preview.model == "Passat"
    assert preview.year == 2019
    assert preview.mileage_km == 145000
    assert preview.price == Decimal("52000")
    assert preview.currency.value == "PLN"
    assert preview.warnings == []


def test_open_graph_is_used_as_safe_fallback() -> None:
    html = (
        '<meta property="og:title" content="Unknown vehicle">'
        '<meta name="description" content="Listing">'
    )

    preview = extract_listing_preview(html, "https://example.com/listing/no-schema")

    assert preview.title == "Unknown vehicle"
    assert preview.description == "Listing"
    assert "make" not in preview.extracted_fields
    assert preview.warnings


def test_next_data_marketplace_payload_is_extracted() -> None:
    html = """
    <html><head><meta property="og:title" content="BMW X5"></head><body>
    <script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"advert":{"id":"98765","price":{"value":129900,
    "currency":"PLN"},"parameters":[{"key":"make","displayValue":"BMW"},
    {"key":"model","displayValue":"X5"},{"key":"year","value":"2021"},
    {"key":"mileage","value":"82 500 km"}],"location":{"cityName":"Poznań",
    "regionName":"Wielkopolskie","countryCode":"PL"}}}}}
    </script></body></html>
    """

    preview = extract_listing_preview(html, "https://www.otomoto.pl/osobowe/oferta/test")

    assert preview.make == "BMW"
    assert preview.model == "X5"
    assert preview.year == 2021
    assert preview.mileage_km == 82500
    assert preview.price == Decimal("129900")
    assert preview.currency.value == "PLN"
    assert preview.location == "Poznań"
    assert preview.location_region == "Wielkopolskie"
    assert preview.country_code == "PL"
    assert preview.warnings == []


def test_otomoto_seller_type_is_normalized() -> None:
    html = """
    <script id="__NEXT_DATA__" type="application/json">
    {"props":{"advert":{"sellerType":"Osoba prywatna"}}}
    </script>
    """

    preview = extract_listing_preview(html, "https://www.otomoto.pl/oferta/test")

    assert preview.seller_type == "private"


def test_structured_vehicle_variant_is_extracted_with_evidence() -> None:
    html = """
    <meta property="og:title" content="Audi A6 40 TDI S line">
    <script id="__NEXT_DATA__" type="application/json">
    {"advert":{"parameters":[{"key":"generation","value":"C8"},
    {"key":"bodyType","value":"Kombi"},{"key":"enginePower","value":"204 KM"},
    {"key":"driveType","value":"quattro"}]}}
    </script>
    """

    preview = extract_listing_preview(html, "https://www.otomoto.pl/oferta/audi-a6")

    assert preview.generation == "C8"
    assert preview.body_type == "Kombi"
    assert preview.power_hp == 204
    assert preview.drivetrain == "quattro"
    assert preview.engine_marketing_name == "40 TDI"
    assert preview.trim_line == "S line"
    assert any(item["source"] == "structured_page_data" for item in preview.specification_evidence)
    assert any(item["source"] == "listing_title" for item in preview.specification_evidence)


def test_private_network_urls_are_rejected() -> None:
    with pytest.raises(ValueError, match="private"):
        asyncio.run(_ensure_public_url("http://127.0.0.1/private"))
