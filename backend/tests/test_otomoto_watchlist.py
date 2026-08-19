import pytest

from app.market_intelligence.otomoto_watchlist import (
    extract_listing_urls,
    validate_otomoto_search_url,
)
from app.schemas.automation import ImportSourceCreate


def test_extract_listing_urls_deduplicates_and_limits_results() -> None:
    html = """
    <a href="/osobowe/oferta/bmw-x5-ID6AAA.html?foo=1">BMW</a>
    <a href="https://www.otomoto.pl/osobowe/oferta/bmw-x5-ID6AAA.html">duplicate</a>
    <a href="/osobowe/oferta/audi-q7-ID6BBB.html">Audi</a>
    <a href="https://example.com/osobowe/oferta/external">external</a>
    """

    urls = extract_listing_urls(html, "https://www.otomoto.pl/osobowe/bmw", limit=2)

    assert urls == [
        "https://www.otomoto.pl/osobowe/oferta/bmw-x5-ID6AAA.html",
        "https://www.otomoto.pl/osobowe/oferta/audi-q7-ID6BBB.html",
    ]


def test_watchlist_source_type_is_accepted() -> None:
    source = ImportSourceCreate(
        name="BMW X5",
        provider_type="otomoto_search",
        endpoint_url="https://www.otomoto.pl/osobowe/bmw/x5",
        interval_minutes=60,
        configuration={"max_results": 10},
    )

    assert source.provider_type == "otomoto_search"
    assert source.configuration["max_results"] == 10


def test_non_otomoto_watchlist_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="Otomoto"):
        validate_otomoto_search_url("https://example.com/osobowe")

