"""Versioned, reviewable vehicle knowledge catalog."""

from pathlib import Path
import re

import yaml

from app.services.vehicle_catalog import catalog_entry, poland_budget_catalog

CATALOG_DIR = Path(__file__).parents[1] / "knowledge" / "catalog"


def _normalize(value: str) -> str:
    return value.strip().casefold()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _catalog_placeholder(make: str, model: str, tier: str) -> dict[str, object]:
    """A visible, deliberately unreviewed starting point for every focus model."""
    return {
        "slug": f"focus-{_slug(make)}-{_slug(model)}-pl-v1",
        "make": make,
        "model": model,
        "generation": "Поколение не определено",
        "market_code": "PL",
        "production_years": "Требует уточнения",
        "version": "catalog-link-v1",
        "verification_status": "draft",
        "profile_origin": "catalog_placeholder",
        "catalog_tier": tier,
        "summary": (
            "Карточка создана автоматически из каталога фокуса. "
            "Факты о поколениях, агрегатах и рисках ещё не добавлены и не должны "
            "использоваться для решения о покупке."
        ),
        "body_types": [],
        "powertrains": [],
        "gearbox_profiles": [],
        "known_issues": [],
        "dealer_configurations": [],
        "factory_lines": [],
        "equipment_groups": [],
        "decision_notes": [
            "Перед решением создайте проверенный профиль модели и укажите точную конфигурацию."
        ],
        "sources": [],
    }


def knowledge_profiles() -> list[dict[str, object]]:
    profiles: list[dict[str, object]] = []
    for path in sorted(CATALOG_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as stream:
            profile = yaml.safe_load(stream)
        if isinstance(profile, dict):
            entry = catalog_entry(str(profile.get("make", "")), str(profile.get("model", "")))
            profiles.append(
                {
                    **profile,
                    "profile_origin": "reviewed_profile",
                    "catalog_tier": entry.get("tier") if entry else None,
                }
            )

    covered = {
        (_normalize(str(item.get("make", ""))), _normalize(str(item.get("model", ""))))
        for item in profiles
    }
    for group in poland_budget_catalog()["groups"]:
        make, tier = str(group["make"]), str(group["tier"])
        for model in group["models"]:
            model = str(model)
            if (_normalize(make), _normalize(model)) not in covered:
                profiles.append(_catalog_placeholder(make, model, tier))
    return sorted(profiles, key=lambda item: (str(item["make"]), str(item["model"])))


def find_knowledge_profile(slug: str) -> dict[str, object] | None:
    return next((item for item in knowledge_profiles() if item.get("slug") == slug), None)
