"""User-directed listing preview from public webpage metadata."""

import asyncio
import hashlib
import ipaddress
import json
import re
import socket
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.models.domain import Currency
from app.schemas.intake import LinkPreviewRead

MAX_HTML_BYTES = 2_000_000
MAX_REDIRECTS = 3
USER_AGENT = "DealerMind-LinkIntake/1.0 (+user-directed-preview)"


def _first(value: object) -> object:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _text(value: object) -> str | None:
    value = _first(value)
    if isinstance(value, dict):
        value = value.get("name") or value.get("value")
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _integer(value: object) -> int | None:
    text = _text(value)
    if text is None:
        return None
    match = re.search(r"\d[\d\s.,]*", text)
    if match is None:
        return None
    digits = re.sub(r"\D", "", match.group())
    return int(digits) if digits else None


def _year(value: object) -> int | None:
    text = _text(value)
    if text is None:
        return None
    match = re.search(r"\b(18|19|20|21)\d{2}\b", text)
    return int(match.group()) if match else None


def _decimal(value: object) -> Decimal | None:
    text = _text(value)
    if text is None:
        return None
    normalized = re.sub(r"[^\d,.]", "", text).replace(" ", "")
    if not normalized:
        return None
    if normalized.count(",") == 1 and normalized.count(".") == 0:
        normalized = normalized.replace(",", ".")
    else:
        normalized = normalized.replace(",", "")
    try:
        result = Decimal(normalized)
        return result if result > 0 else None
    except InvalidOperation:
        return None


def _json_ld_objects(soup: BeautifulSoup) -> list[dict[str, object]]:
    objects: list[dict[str, object]] = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.get_text(strip=True))
        except (json.JSONDecodeError, TypeError):
            continue
        queue = data if isinstance(data, list) else [data]
        for item in queue:
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            if isinstance(graph, list):
                objects.extend(node for node in graph if isinstance(node, dict))
            objects.append(item)
    return objects


def _embedded_json_objects(soup: BeautifulSoup) -> list[object]:
    """Read application JSON used by client-rendered marketplaces such as Otomoto."""
    objects: list[object] = []
    for script in soup.select('script[type="application/json"], script#__NEXT_DATA__'):
        try:
            objects.append(json.loads(script.get_text(strip=True)))
        except (json.JSONDecodeError, TypeError):
            continue
    return objects


def _find_json_value(data: object, *aliases: str) -> object:
    wanted = {re.sub(r"[^a-z0-9]", "", alias.lower()) for alias in aliases}
    queue = [data]
    while queue:
        item = queue.pop(0)
        if isinstance(item, dict):
            normalized = {
                re.sub(r"[^a-z0-9]", "", str(key).lower()): value
                for key, value in item.items()
            }
            for alias in wanted:
                if alias in normalized and _text(normalized[alias]) is not None:
                    return normalized[alias]
            parameter_key = _text(item.get("key") or item.get("code") or item.get("name"))
            if parameter_key and re.sub(r"[^a-z0-9]", "", parameter_key.lower()) in wanted:
                for value_key in ("displayValue", "value", "values", "label"):
                    if value_key in item and _text(item[value_key]) is not None:
                        return item[value_key]
            queue.extend(item.values())
        elif isinstance(item, list):
            queue.extend(item)
    return None


def _meta(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if tag is not None and tag.get("content"):
            return str(tag["content"]).strip()
    return None


def _currency(value: object, page_text: str) -> Currency | None:
    code = (_text(value) or "").upper()
    for currency in Currency:
        if code == currency.value:
            return currency
    if "zł" in page_text or "PLN" in page_text:
        return Currency.PLN
    if "€" in page_text or "EUR" in page_text:
        return Currency.EUR
    if "грн" in page_text or "UAH" in page_text:
        return Currency.UAH
    return None


def _seller_type(value: object) -> str | None:
    normalized = (_text(value) or "").strip().lower()
    if not normalized:
        return None
    dealer_markers = ("dealer", "business", "professional", "company", "firma", "organization")
    private_markers = ("private", "individual", "person", "osoba prywatna", "prywatny")
    if any(marker in normalized for marker in dealer_markers):
        return "dealer"
    if any(marker in normalized for marker in private_markers):
        return "private"
    return None


def _title_variant(title: str | None) -> dict[str, str]:
    if not title:
        return {}
    result: dict[str, str] = {}
    engine = re.search(
        r"\b(\d{2}\s?(?:TDI|TFSI|TSI)|\d{3}[die]|\d\.\d\s?(?:TDI|TFSI|TSI))\b",
        title,
        re.IGNORECASE,
    )
    if engine:
        result["engine_marketing_name"] = engine.group(1).upper().replace("  ", " ")
    for pattern, normalized in (
        (r"\bS[ -]?line\b", "S line"),
        (r"\bM[ -]?Sport\b", "M Sport"),
        (r"\bAMG[ -]?Line\b", "AMG Line"),
        (r"\bR[ -]?Line\b", "R-Line"),
    ):
        if re.search(pattern, title, re.IGNORECASE):
            result["trim_line"] = normalized
            break
    return result


def extract_listing_preview(html: str, source_url: str) -> LinkPreviewRead:
    soup = BeautifulSoup(html, "html.parser")
    objects = _json_ld_objects(soup)
    product = next(
        (
            item
            for item in objects
            if any(
                kind in str(item.get("@type", "")).lower()
                for kind in ("vehicle", "car", "product")
            )
        ),
        {},
    )
    offers = product.get("offers") if isinstance(product, dict) else None
    offers = _first(offers)
    offer_data = offers if isinstance(offers, dict) else {}
    brand = product.get("brand") if isinstance(product, dict) else None
    title = _text(product.get("name")) or _meta(soup, "og:title", "twitter:title")
    description = _text(product.get("description")) or _meta(
        soup, "og:description", "description"
    )
    image = _text(product.get("image")) or _meta(soup, "og:image", "twitter:image")
    price = _decimal(offer_data.get("price")) or _decimal(_meta(soup, "product:price:amount"))
    currency_value = offer_data.get("priceCurrency") or _meta(soup, "product:price:currency")
    year = _year(product.get("vehicleModelDate") or product.get("productionDate"))
    mileage = _integer(product.get("mileageFromOdometer"))
    make = _text(brand) or _text(product.get("manufacturer"))
    model = _text(product.get("model"))
    location = _text(product.get("areaServed"))
    location_region = None
    country_code = None
    seller = offer_data.get("seller")
    seller_type = _seller_type(
        seller.get("@type") if isinstance(seller, dict) else seller
    )
    external = _text(product.get("sku") or product.get("productID"))
    specifications: dict[str, object] = {}
    evidence: list[dict[str, object]] = []

    def capture(field: str, raw: object, parser: object = _text) -> None:
        if specifications.get(field) is not None or raw is None:
            return
        value = parser(raw) if callable(parser) else _text(raw)
        if value is None:
            return
        specifications[field] = value
        evidence.append(
            {
                "field_name": field,
                "value": value,
                "raw_value": _text(raw),
                "source": "structured_page_data",
                "confidence": 0.95,
            }
        )
    embedded = _embedded_json_objects(soup)
    for data in embedded:
        make = make or _text(_find_json_value(data, "make", "brand"))
        model = model or _text(_find_json_value(data, "model"))
        year = year or _year(_find_json_value(data, "year", "productionYear"))
        mileage = mileage or _integer(
            _find_json_value(data, "mileage", "mileageKm", "mileageFromOdometer")
        )
        price = price or _decimal(_find_json_value(data, "price", "amount"))
        currency_value = currency_value or _find_json_value(
            data, "currency", "priceCurrency", "currencyCode"
        )
        external = external or _text(
            _find_json_value(data, "externalId", "advertId", "listingId")
        )
        location = location or _text(
            _find_json_value(data, "city", "cityName", "locality", "addressLocality")
        )
        location_region = location_region or _text(
            _find_json_value(data, "region", "regionName", "province", "addressRegion")
        )
        country_code = country_code or _text(
            _find_json_value(data, "countryCode", "addressCountry")
        )
        seller_type = seller_type or _seller_type(
            _find_json_value(
                data,
                "sellerType",
                "advertiserType",
                "ownerType",
                "sellerCategory",
                "seller_type",
            )
        )
        capture("generation", _find_json_value(data, "generation", "generationName"))
        capture("body_type", _find_json_value(data, "bodyType", "vehicleBodyType"))
        capture(
            "engine_marketing_name",
            _find_json_value(data, "engineVersion", "engineName", "engineVariant"),
        )
        capture(
            "engine_capacity_cc",
            _find_json_value(data, "engineCapacity", "engineDisplacement"),
            _integer,
        )
        capture("power_hp", _find_json_value(data, "enginePower", "powerHp"), _integer)
        capture("fuel_type", _find_json_value(data, "fuelType", "fuel"))
        capture("gearbox", _find_json_value(data, "gearbox", "transmission"))
        capture("drivetrain", _find_json_value(data, "driveType", "drivetrain"))
        capture(
            "trim_line",
            _find_json_value(data, "trimLine", "equipmentVersion", "equipmentVariant"),
        )
        capture(
            "performance_variant",
            _find_json_value(data, "performanceVariant", "modelVariant"),
        )
    for field, value in _title_variant(title).items():
        if specifications.get(field) is None:
            specifications[field] = value
            evidence.append(
                {
                    "field_name": field,
                    "value": value,
                    "raw_value": title,
                    "source": "listing_title",
                    "confidence": 0.75,
                }
            )
    if country_code is None and (urlparse(source_url).hostname or "").endswith("otomoto.pl"):
        country_code = "PL"
    if external is None:
        external = hashlib.sha256(source_url.encode()).hexdigest()[:24]
    page_text = soup.get_text(" ", strip=True)
    values: dict[str, object] = {
        "title": title,
        "description": description,
        "image_url": urljoin(source_url, image) if image else None,
        "make": make,
        "model": model,
        "year": year,
        "mileage_km": mileage,
        "price": price,
        "currency": _currency(currency_value, page_text),
        "location": location,
        "location_region": location_region,
        "country_code": country_code.upper() if country_code else None,
        "seller_type": seller_type,
        **specifications,
        "specification_evidence": evidence,
    }
    extracted = [key for key, value in values.items() if value is not None]
    labels = {"make": "Марка", "model": "Модель", "price": "Цена", "currency": "Валюта"}
    warnings = [
        f"Поле «{labels[field]}» не удалось распознать — проверьте его вручную"
        for field in labels
        if values[field] is None
    ]
    return LinkPreviewRead(
        source_url=source_url,
        external_id=external,
        extracted_fields=extracted,
        warnings=warnings,
        **values,
    )


async def _ensure_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only public HTTP or HTTPS URLs are allowed")
    loop = asyncio.get_running_loop()
    default_port = 443 if parsed.scheme == "https" else 80
    addresses = await loop.getaddrinfo(
        parsed.hostname,
        parsed.port or default_port,
        type=socket.SOCK_STREAM,
    )
    if not addresses:
        raise ValueError("URL host could not be resolved")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("private, local and reserved network addresses are not allowed")


async def fetch_listing_preview(url: str) -> LinkPreviewRead:
    current = url
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            await _ensure_public_url(current)
            async with client.stream(
                "GET", current, headers={"User-Agent": USER_AGENT}
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("redirect response has no location")
                    current = urljoin(current, location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if "html" not in content_type:
                    raise ValueError("URL did not return an HTML page")
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_HTML_BYTES:
                        raise ValueError("HTML page is larger than 2 MB")
                    chunks.append(chunk)
                html = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
                return extract_listing_preview(html, current)
    raise ValueError("too many redirects")
