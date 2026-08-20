from decimal import Decimal

from app.services.variant_intelligence import (
    choose_variant_cohort,
    price_premium,
    variant_label,
    variant_tier,
)


def test_exact_variant_requires_matching_known_characteristics() -> None:
    target = {"generation": "C8", "body_type": "Kombi", "fuel_type": "Diesel", "power_hp": 204}
    candidate = {"generation": "c8", "body_type": "Kombi", "fuel_type": "Diesel", "power_hp": 190}

    assert variant_tier(target, candidate) == "exact_variant"


def test_structural_conflict_falls_back_to_broad_model() -> None:
    target = {"generation": "C8", "body_type": "Kombi", "fuel_type": "Diesel"}
    candidate = {"generation": "C7", "body_type": "Sedan", "fuel_type": "Petrol"}

    assert variant_tier(target, candidate) == "broad_model"


def test_cohort_expands_only_when_exact_sample_is_too_small() -> None:
    target = {"generation": "C8", "body_type": "Kombi"}
    candidates = [
        {"generation": "C8", "body_type": "Kombi"},
        {"generation": "C8", "body_type": "Kombi"},
        {"generation": "C8", "body_type": None},
    ]

    rows, cohort = choose_variant_cohort(target, candidates, minimum=3)

    assert len(rows) == 3
    assert cohort == "close_variant"


def test_variant_label_and_price_premium_are_explainable() -> None:
    label = variant_label({"generation": "C8", "engine_marketing_name": "40 TDI", "trim_line": "S line"})

    assert label == "C8 · 40 TDI · S line"
    assert price_premium(Decimal("110000"), Decimal("100000")) == 10.0
