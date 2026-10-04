"""CEPiK fleet observations: aggregate at collection time; never persist records, VINs or people."""
from collections import Counter
import logging
import ssl
import time
from threading import Lock
from datetime import date, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.automation import PolandFleetSnapshot
from app.models.domain import utcnow
from app.services.knowledge import find_knowledge_profile, knowledge_profiles

REGIONS = {
    "02": "Dolnośląskie", "04": "Kujawsko-pomorskie", "06": "Lubelskie", "08": "Lubuskie",
    "10": "Łódzkie", "12": "Małopolskie", "14": "Mazowieckie", "16": "Opolskie",
    "18": "Podkarpackie", "20": "Podlaskie", "22": "Pomorskie", "24": "Śląskie",
    "26": "Świętokrzyskie", "28": "Warmińsko-mazurskie", "30": "Wielkopolskie", "32": "Zachodniopomorskie",
}
logger = logging.getLogger(__name__)
_collection_lock = Lock()
_collection_states: dict[str, dict[str, str]] = {}


class FleetConfigurationError(ValueError):
    pass


class FleetUpstreamError(ValueError):
    pass


def cepik_ssl_context() -> ssl.SSLContext:
    """Compatibility solely for CEPiK's legacy DH parameters.

    Certificate verification remains enabled.  This context is deliberately not
    shared with database connections or any other HTTP integration.
    """
    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT@SECLEVEL=1")
    return context


def monitored_profiles() -> list[dict[str, object]]:
    return [item for item in knowledge_profiles() if item.get("fleet_monitor", {}).get("enabled", False)]


def aggregate_cepik_records(records: list[object], make: str, model: str) -> tuple[int, dict[str, int], dict[str, int], dict[str, int]]:
    years: Counter[str] = Counter()
    fuels: Counter[str] = Counter()
    regions: Counter[str] = Counter()
    total = 0
    for item in records:
        attributes = item.get("attributes", item) if isinstance(item, dict) else {}
        actual_make = str(attributes.get("marka", attributes.get("make", ""))).strip().casefold()
        actual_model = str(attributes.get("model", "")).strip().casefold()
        if actual_make != make.casefold() or actual_model != model.casefold():
            continue
        total += 1
        year = attributes.get("rok-produkcji", attributes.get("rok_produkcji", attributes.get("year")))
        fuel = attributes.get("rodzaj-paliwa", attributes.get("rodzaj_paliwa", attributes.get("fuel")))
        region = attributes.get("wojewodztwo-kod", attributes.get("wojewodztwo", attributes.get("region")))
        if year: years[str(year)] += 1
        if fuel: fuels[str(fuel)] += 1
        if region: regions[REGIONS.get(str(region).zfill(2), str(region))] += 1
    return total, dict(years), dict(fuels), dict(regions)


def latest_snapshot(db: Session, profile_slug: str) -> PolandFleetSnapshot | None:
    return db.scalar(select(PolandFleetSnapshot).where(PolandFleetSnapshot.profile_slug == profile_slug).order_by(PolandFleetSnapshot.collected_at.desc()))


def list_snapshots(db: Session, profile_slug: str | None = None, limit: int = 104) -> list[PolandFleetSnapshot]:
    statement = select(PolandFleetSnapshot).order_by(PolandFleetSnapshot.period_to.desc(), PolandFleetSnapshot.collected_at.desc()).limit(limit)
    if profile_slug:
        statement = statement.where(PolandFleetSnapshot.profile_slug == profile_slug)
    return list(db.scalars(statement))


def cepik_get(client: httpx.Client, url: str, params: dict[str, object]) -> httpx.Response:
    """One small retry for transient slow CEPiK responses."""
    last_error: httpx.HTTPError | None = None
    for attempt in range(2):
        try:
            return client.get(url, params=params)
        except httpx.TimeoutException as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(1)
    raise FleetUpstreamError("CEPiK не ответил в течение минуты. Повторите сбор немного позже.") from last_error


def collect_profile(db: Session, profile_slug: str, period_from: date | None = None, period_to: date | None = None) -> PolandFleetSnapshot:
    profile = find_knowledge_profile(profile_slug)
    if profile is None or not profile.get("fleet_monitor", {}).get("enabled", False):
        raise LookupError("Fleet monitoring is not enabled for this knowledge profile")
    settings = get_settings()
    period_to = period_to or date.today()
    period_from = period_from or period_to - timedelta(days=29)
    all_records: list[object] = []
    try:
        with httpx.Client(timeout=settings.cepik_request_timeout_seconds, verify=cepik_ssl_context()) as client:
            for code in REGIONS:
                for page in range(1, settings.cepik_fleet_max_pages_per_region + 1):
                    # CEPiK's public contract supports attribute filters.  Applying
                    # them here prevents downloading a whole voivodeship just to find
                    # one model. CPA sandbox was the only endpoint that rejected it.
                    response = cepik_get(client, settings.cepik_api_url, {
                        "wojewodztwo": code, "data-od": period_from.strftime("%Y%m%d"),
                        "data-do": period_to.strftime("%Y%m%d"), "typ-daty": "2",
                        "tylko-zarejestrowane": "true",
                        "filter[marka]": str(profile["make"]),
                        "filter[model]": str(profile["model"]),
                        "fields": ["marka", "model", "rok-produkcji", "rodzaj-paliwa", "wojewodztwo-kod"],
                        "limit": 500, "page": page,
                    })
                    response.raise_for_status()
                    payload = response.json()
                    records = payload.get("data", []) if isinstance(payload, dict) else []
                    if not records: break
                    all_records.extend(records)
                    if len(records) < 500: break
    except httpx.HTTPStatusError as exc:
        # CEPiK may return a useful JSON error or a small HTML/plain-text reason.
        # Never include request headers, so credentials cannot reach the UI or logs.
        detail = exc.response.text.replace("\n", " ").strip()[:300]
        suffix = f" Причина CEPiK: {detail}" if detail else ""
        raise FleetUpstreamError(f"CEPiK ответил {exc.response.status_code}.{suffix}") from exc
    except httpx.HTTPError as exc:
        raise FleetUpstreamError(f"Не удалось подключиться к CEPiK: {exc}") from exc
    count, years, fuels, regions = aggregate_cepik_records(all_records, str(profile["make"]), str(profile["model"]))
    snapshot = PolandFleetSnapshot(profile_slug=profile_slug, make=str(profile["make"]), model=str(profile["model"]), generation=str(profile.get("generation") or "") or None, period_from=period_from, period_to=period_to, records_count=count, by_year=years, by_fuel=fuels, by_region=regions, source_url=settings.cepik_api_url, configuration_version=str(profile.get("fleet_monitor", {}).get("configuration_version", "cepik-registration-observation-v1")))
    db.add(snapshot); db.commit(); db.refresh(snapshot)
    return snapshot


def collect_due_snapshots() -> None:
    """Run from the application scheduler. A failed model never blocks the next one."""
    with SessionLocal() as db:
        for profile in monitored_profiles():
            slug = str(profile["slug"])
            previous = latest_snapshot(db, slug)
            if previous and previous.collected_at >= utcnow() - timedelta(days=7):
                continue
            try:
                collect_profile(db, slug)
            except Exception:
                db.rollback()
                logger.exception("CEPiK fleet collection failed for %s", slug)


def collection_status(profile_slug: str) -> dict[str, str]:
    with _collection_lock:
        return _collection_states.get(profile_slug, {"profile_slug": profile_slug, "state": "idle", "message": "Готово к сбору"}).copy()


def begin_collection(profile_slug: str) -> dict[str, str]:
    with _collection_lock:
        current = _collection_states.get(profile_slug)
        if current and current["state"] == "collecting":
            return {**current, "message": "Сбор уже выполняется"}
        state = {"profile_slug": profile_slug, "state": "collecting", "message": "Собираем обезличенную статистику CEPiK…"}
        _collection_states[profile_slug] = state
        return state.copy()


def collect_in_background(profile_slug: str, period_days: int = 30) -> None:
    """Background entry point: the web request returns before all regions finish."""
    try:
        with SessionLocal() as db:
            period_to = date.today()
            collect_profile(db, profile_slug, period_from=period_to - timedelta(days=period_days - 1), period_to=period_to)
        outcome = {"profile_slug": profile_slug, "state": "completed", "message": "Снимок CEPiK готов"}
    except Exception as exc:
        logger.exception("manual CEPiK fleet collection failed for %s", profile_slug)
        outcome = {"profile_slug": profile_slug, "state": "failed", "message": str(exc)[:500]}
    with _collection_lock:
        _collection_states[profile_slug] = outcome
