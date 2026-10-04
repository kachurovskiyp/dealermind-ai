from app.main import app
from app.services.knowledge import find_knowledge_profile, knowledge_profiles
from app.services.dealer_knowledge import assess_dealer_configuration
from app.services.vehicle_catalog import poland_budget_catalog


def test_knowledge_page_and_api_are_registered() -> None:
    page_paths = {route.path for route in app.routes if hasattr(route, "path")}
    api_paths = set(app.openapi()["paths"])
    assert "/knowledge" in page_paths
    assert "/api/v1/knowledge/profiles" in api_paths
    assert "/api/v1/knowledge/profiles/{slug}" in api_paths


def test_pilot_profile_keeps_unverified_verdicts_explicit() -> None:
    profile = find_knowledge_profile("audi-a3-8v-pl-v1")
    assert knowledge_profiles()
    assert profile is not None
    assert profile["verification_status"] == "draft"
    verdicts = {item["name"]: item["verdict"] for item in profile["powertrains"]}
    assert verdicts["1.4 TFSI / COD"] == "recommended"
    assert verdicts["1.8 TFSI"] == "caution"
    assert verdicts["1.6 TDI"] == "caution"
    assert verdicts["2.0 TDI"] == "recommended"
    assert {item["trust_level"] for item in profile["sources"]} == {"A", "B"}
    assert all(item["evidence_refs"] for item in profile["powertrains"])
    detailed = [item for item in profile["powertrains"] if item.get("deep_dive")]
    assert {item["name"] for item in detailed} == {
        "1.4 TFSI / COD",
        "1.8 TFSI",
        "1.6 TDI",
        "2.0 TDI",
    }
    assert all(item["deep_dive"]["decision_rule"] for item in detailed)
    assert all(item["deep_dive"]["evidence_confidence"] for item in detailed)
    assert len(profile["gearbox_profiles"]) == 2
    assert len(profile["dealer_configurations"]) == 7
    assert profile["image"]["author"] == "AUDI AG"
    assert "audi-mediacenter.pl" in profile["image"]["source_url"]
    assert "A161803" in profile["image"]["caption"]
    assert {item["classification"] for item in profile["known_issues"]} == {
        "confirmed_model_level",
        "inspection_risk",
        "identification_risk",
    }


def test_configuration_liquidity_api_is_registered() -> None:
    assert "/api/v1/market-intelligence/poland/configurations" in app.openapi()["paths"]
    assert "/api/v1/knowledge/dealer-assessment" in app.openapi()["paths"]


def test_every_focus_catalog_model_has_a_knowledge_profile() -> None:
    profiles = knowledge_profiles()
    covered = {(item["make"].casefold(), item["model"].casefold()) for item in profiles}
    for group in poland_budget_catalog()["groups"]:
        for model in group["models"]:
            assert (group["make"].casefold(), model.casefold()) in covered

    placeholder = find_knowledge_profile("focus-toyota-yaris-pl-v1")
    assert placeholder is not None
    assert placeholder["profile_origin"] == "catalog_placeholder"
    assert placeholder["catalog_tier"] == "core"
    assert placeholder["powertrains"] == []


def test_leon_and_superb_have_reviewed_starting_cards() -> None:
    leon = find_knowledge_profile("seat-leon-iii-pl-v1")
    superb = find_knowledge_profile("skoda-superb-iii-pl-v1")

    assert leon is not None
    assert {item["name"]: item["verdict"] for item in leon["powertrains"]}["1.4 TSI"] == "recommended"
    assert leon["sources"][0]["id"] == "adac-leon-petrol"

    assert superb is not None
    assert {item["name"]: item["verdict"] for item in superb["powertrains"]}["2.0 TDI"] == "recommended"
    assert superb["sources"][0]["id"] == "adac-superb-diesel"


def test_dealer_assessment_matches_engine_and_gearbox() -> None:
    result = assess_dealer_configuration(
        make="Audi",
        model="A3",
        generation="8V",
        engine="1.4 TFSI COD",
        gearbox="manual",
        power_hp=150,
    )

    assert result["configuration_id"] == "14-tfsi-manual"
    assert result["verdict"] == "consider"
    assert result["required_checks"]
    assert result["reject_if"]


def test_dealer_assessment_requires_complete_configuration() -> None:
    result = assess_dealer_configuration(
        make="Audi", model="A3", generation="8V", engine="2.0 TDI"
    )

    assert result["verdict"] == "needs_data"
    assert result["missing_fields"] == ["коробка"]


def test_dealer_assessment_does_not_invent_unknown_model_verdict() -> None:
    result = assess_dealer_configuration(make="BMW", model="3", generation="F30")

    assert result["verdict"] == "no_profile"
