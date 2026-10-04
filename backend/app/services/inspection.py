"""Manual pre-purchase configuration review; no photos or external AI calls."""

from sqlalchemy.orm import Session

from app.services.fleet_intelligence import latest_snapshot
from app.services.knowledge import knowledge_profiles
from app.services.poland_analytics import model_configuration_liquidity
from app.services.vehicle_catalog import catalog_entry


def configuration_review(
    db: Session, make: str, model: str, configuration: str | None = None
) -> dict[str, object]:
    catalog = catalog_entry(make, model)
    liquidity = model_configuration_liquidity(db, make, model)
    selected = next(
        (item for item in liquidity if item["configuration"] == configuration), None
    )
    profile = next(
        (
            item
            for item in knowledge_profiles()
            if str(item.get("make", "")).casefold() == make.casefold()
            and str(item.get("model", "")).casefold() == model.casefold()
        ),
        None,
    )
    result: dict[str, object] = {
        "make": make,
        "model": model,
        "configuration": configuration,
        "catalog_tier": catalog.get("tier") if catalog else None,
        "catalog_label": {"core": "Основной фокус", "review": "Усиленная проверка"}.get(
            catalog.get("tier") if catalog else ""
        ),
        "knowledge_notes": [],
        "liquidity": liquidity,
        "market_valuation": None,
        "registrations_30_days": None,
        "registrations_period": None,
    }
    if selected:
        result["market_valuation"] = {
            "median_price": selected["median_price"],
            "sample_size": selected["sample_size"],
            "confidence": selected["confidence"],
            "basis": "Похожие предложения в DealerMind, не цена конкретного автомобиля.",
        }
    if profile:
        result["knowledge_notes"] = [
            f"{issue.get('component')}: {issue.get('note')}"
            for issue in profile.get("known_issues", [])
        ][:4]
        snapshot = latest_snapshot(db, str(profile["slug"]))
        if snapshot:
            result["registrations_30_days"] = snapshot.records_count
            result["registrations_period"] = f"{snapshot.period_from} — {snapshot.period_to}"
    return result
