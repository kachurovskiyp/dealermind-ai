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
    {"key":"mileage","value":"82 500 km"}]}}}}
    </script></body></html>
    """

    preview = extract_listing_preview(html, "https://www.otomoto.pl/osobowe/oferta/test")

    assert preview.make == "BMW"
    assert preview.model == "X5"
    assert preview.year == 2021
    assert preview.mileage_km == 82500
    assert preview.price == Decimal("129900")
    assert preview.currency.value == "PLN"
    assert preview.warnings == []


def test_private_network_urls_are_rejected() -> None:
    with pytest.raises(ValueError, match="private"):
        asyncio.run(_ensure_public_url("http://127.0.0.1/private"))
