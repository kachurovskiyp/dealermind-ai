"""Cautious Otomoto search-page adapter for user-configured watchlists."""

import asyncio
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.market_intelligence.link_intake import (
    MAX_HTML_BYTES,
    USER_AGENT,
    _ensure_public_url,
    extract_listing_preview,
)
from app.schemas.imports import ListingImportRecord


def validate_otomoto_search_url(url: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    if host != "otomoto.pl" and not host.endswith(".otomoto.pl"):
        raise ValueError("Разрешены только публичные ссылки поиска Otomoto")


def extract_listing_urls(html: str, source_url: str, limit: int = 10) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        absolute = urljoin(source_url, str(anchor.get("href", ""))).split("?")[0]
        parsed = urlparse(absolute)
        host = (parsed.hostname or "").lower()
        if not (host == "otomoto.pl" or host.endswith(".otomoto.pl")):
            continue
        if "/osobowe/oferta/" not in parsed.path or absolute in seen:
            continue
        seen.add(absolute)
        urls.append(absolute)
        if len(urls) >= limit:
            break
    return urls


async def _get_html(client: httpx.AsyncClient, url: str) -> str:
    current = url
    for _ in range(4):
        await _ensure_public_url(current)
        response = await client.get(current, headers={"User-Agent": USER_AGENT})
        if response.is_redirect:
            location = response.headers.get("location")
            if not location:
                raise ValueError("Перенаправление не содержит адреса")
            current = urljoin(current, location)
            continue
        response.raise_for_status()
        if "html" not in response.headers.get("content-type", ""):
            raise ValueError("Источник не вернул HTML-страницу")
        if len(response.content) > MAX_HTML_BYTES:
            raise ValueError("HTML-страница превышает ограничение 2 МБ")
        return response.text
    raise ValueError("Слишком много перенаправлений")


async def collect_otomoto_records(
    search_url: str, max_results: int = 10
) -> tuple[list[ListingImportRecord], list[str]]:
    validate_otomoto_search_url(search_url)
    max_results = max(1, min(max_results, 25))
    records: list[ListingImportRecord] = []
    errors: list[str] = []
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        search_html = await _get_html(client, search_url)
        urls = extract_listing_urls(search_html, search_url, max_results)
        if not urls:
            return [], ["На странице поиска Otomoto не найдены объявления"]
        for index, url in enumerate(urls):
            try:
                html = await _get_html(client, url)
                preview = extract_listing_preview(html, url)
                missing = [
                    label
                    for value, label in (
                        (preview.make, "марка"),
                        (preview.model, "модель"),
                        (preview.price, "цена"),
                        (preview.currency, "валюта"),
                    )
                    if value is None
                ]
                if missing:
                    raise ValueError("не распознаны: " + ", ".join(missing))
                records.append(
                    ListingImportRecord(
                        market_code="PL",
                        marketplace_slug="otomoto",
                        target_market_code="PL",
                        external_id=preview.external_id,
                        url=preview.source_url,
                        title=preview.title or f"{preview.make} {preview.model}",
                        make=preview.make,
                        model=preview.model,
                        year=preview.year,
                        mileage_km=preview.mileage_km,
                        location=preview.location,
                        seller_type=preview.seller_type,
                        description=preview.description,
                        price=preview.price,
                        currency=preview.currency,
                    )
                )
            except Exception as exc:
                errors.append(f"{url}: {exc}")
            if index + 1 < len(urls):
                await asyncio.sleep(0.75)
    return records, errors

