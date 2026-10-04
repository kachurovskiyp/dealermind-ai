"""Explainable dealer-facing configuration assessment from versioned knowledge profiles."""

from app.services.knowledge import knowledge_profiles


VERDICT_LABELS = {
    "consider": "Стоит рассматривать",
    "inspect": "Только после проверки",
    "skip": "Лучше пропустить",
    "needs_data": "Нужно уточнить конфигурацию",
    "no_profile": "Профиль знаний ещё не создан",
    "unreviewed": "Конфигурация ещё не оценена",
}


def _normalize(value: str | None) -> str:
    return (value or "").strip().casefold().replace("-", " ")


def _contains_pattern(value: str | None, patterns: list[str]) -> bool:
    normalized = _normalize(value)
    return any(_normalize(pattern) in normalized for pattern in patterns)


def _profile_for_vehicle(
    make: str, model: str, generation: str | None = None
) -> dict[str, object] | None:
    candidates = [
        profile
        for profile in knowledge_profiles()
        if _normalize(str(profile.get("make"))) == _normalize(make)
        and _normalize(str(profile.get("model"))) == _normalize(model)
    ]
    if generation:
        exact = next(
            (
                profile
                for profile in candidates
                if _normalize(str(profile.get("generation"))) == _normalize(generation)
            ),
            None,
        )
        if exact is not None:
            return exact
    return candidates[0] if len(candidates) == 1 else None


def assess_dealer_configuration(
    *,
    make: str,
    model: str,
    generation: str | None = None,
    engine: str | None = None,
    gearbox: str | None = None,
    power_hp: int | None = None,
) -> dict[str, object]:
    profile = _profile_for_vehicle(make, model, generation)
    if profile is None:
        return {
            "verdict": "no_profile",
            "verdict_label": VERDICT_LABELS["no_profile"],
            "confidence": "none",
            "reasons": [],
            "required_checks": [],
            "reject_if": [],
            "missing_fields": [],
        }

    missing = [name for name, value in (("двигатель", engine), ("коробка", gearbox)) if not value]
    if missing:
        return {
            "profile_slug": profile["slug"],
            "verdict": "needs_data",
            "verdict_label": VERDICT_LABELS["needs_data"],
            "confidence": "none",
            "reasons": ["Без точного двигателя и коробки дилерский вердикт ненадёжен."],
            "required_checks": [],
            "reject_if": [],
            "missing_fields": missing,
        }

    configurations = profile.get("dealer_configurations") or []
    for configuration in configurations:
        engine_patterns = list(configuration.get("engine_patterns") or [])
        gearbox_patterns = list(configuration.get("gearbox_patterns") or [])
        powers = list(configuration.get("power_hp") or [])
        if not _contains_pattern(engine, engine_patterns):
            continue
        if gearbox_patterns and not _contains_pattern(gearbox, gearbox_patterns):
            continue
        if powers and power_hp is not None and power_hp not in powers:
            continue
        verdict = str(configuration["verdict"])
        return {
            "profile_slug": profile["slug"],
            "configuration_id": configuration["id"],
            "configuration_label": configuration["label"],
            "verdict": verdict,
            "verdict_label": VERDICT_LABELS.get(verdict, verdict),
            "confidence": configuration.get("confidence", "low"),
            "reasons": list(configuration.get("dealer_rationale") or []),
            "required_checks": list(configuration.get("required_checks") or []),
            "reject_if": list(configuration.get("reject_if") or []),
            "missing_fields": [],
        }

    return {
        "profile_slug": profile["slug"],
        "verdict": "unreviewed",
        "verdict_label": VERDICT_LABELS["unreviewed"],
        "confidence": "none",
        "reasons": ["Такое сочетание ещё не описано отдельным дилерским правилом."],
        "required_checks": [],
        "reject_if": [],
        "missing_fields": [],
    }
