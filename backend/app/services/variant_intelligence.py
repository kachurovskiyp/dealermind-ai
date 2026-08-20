"""Normalized vehicle-variant identity and hierarchical comparable selection."""

from collections.abc import Mapping
from decimal import Decimal

VARIANT_FIELDS = (
    "generation",
    "body_type",
    "engine_marketing_name",
    "fuel_type",
    "gearbox",
    "drivetrain",
    "trim_line",
    "performance_variant",
)


def _normalized(value: object) -> str:
    return str(value or "").strip().casefold()


def variant_label(specification: Mapping[str, object]) -> str:
    parts = [
        specification.get("generation"),
        specification.get("body_type"),
        specification.get("engine_marketing_name"),
        (
            f'{specification["power_hp"]} KM'
            if specification.get("power_hp") is not None
            else None
        ),
        specification.get("drivetrain"),
        specification.get("trim_line"),
        specification.get("performance_variant"),
    ]
    return " · ".join(str(value) for value in parts if value) or "Версия не определена"


def variant_tier(
    target: Mapping[str, object], candidate: Mapping[str, object]
) -> str:
    known = [field for field in VARIANT_FIELDS if target.get(field)]
    matching = [
        field
        for field in known
        if candidate.get(field)
        and _normalized(target[field]) == _normalized(candidate[field])
    ]
    conflicts = [
        field
        for field in known
        if candidate.get(field)
        and _normalized(target[field]) != _normalized(candidate[field])
    ]
    target_power = target.get("power_hp")
    candidate_power = candidate.get("power_hp")
    power_close = (
        target_power is None
        or candidate_power is None
        or abs(int(target_power) - int(candidate_power)) <= 20
    )
    if len(known) >= 2 and len(matching) >= 2 and not conflicts and power_close:
        return "exact_variant"
    structural = {"generation", "body_type", "fuel_type"}
    if power_close and not any(field in structural for field in conflicts):
        return "close_variant"
    return "broad_model"


def choose_variant_cohort(
    target: Mapping[str, object], candidates: list[dict[str, object]], minimum: int
) -> tuple[list[dict[str, object]], str]:
    by_tier = {"exact_variant": [], "close_variant": [], "broad_model": []}
    for candidate in candidates:
        by_tier[variant_tier(target, candidate)].append(candidate)
    if len(by_tier["exact_variant"]) >= minimum:
        return by_tier["exact_variant"], "exact_variant"
    close = by_tier["exact_variant"] + by_tier["close_variant"]
    if len(close) >= minimum:
        return close, "close_variant"
    return candidates, "broad_model"


def price_premium(median_price: Decimal, base_median: Decimal) -> float:
    if base_median == 0:
        return 0
    return round(float((median_price - base_median) / base_median * 100), 1)
