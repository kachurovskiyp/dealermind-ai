from app.services.fleet_intelligence import aggregate_cepik_records, cepik_ssl_context


def test_cepik_aggregation_discards_other_models_and_keeps_only_statistics() -> None:
    records = [
        {"attributes": {"marka": "Audi", "model": "A3", "rok-produkcji": 2018, "rodzaj-paliwa": "benzyna", "wojewodztwo": "14"}},
        {"attributes": {"marka": "Audi", "model": "A3", "rok-produkcji": 2018, "rodzaj-paliwa": "benzyna", "wojewodztwo": "14", "vin": "must-not-be-used"}},
        {"attributes": {"marka": "Ford", "model": "S-Max", "rok-produkcji": 2018}},
    ]
    count, years, fuels, regions = aggregate_cepik_records(records, "Audi", "A3")
    assert count == 2
    assert years == {"2018": 2}
    assert fuels == {"benzyna": 2}
    assert regions == {"Mazowieckie": 2}


def test_cepik_compatibility_context_keeps_certificate_verification_enabled() -> None:
    assert cepik_ssl_context().verify_mode.name == "CERT_REQUIRED"


def test_fleet_routes_and_page_are_registered() -> None:
    from app.main import app

    paths = {route.path for route in app.routes if hasattr(route, "path")}
    api_paths = set(app.openapi()["paths"])
    assert "/fleet" in paths
    assert "/api/v1/fleet-intelligence/status" in api_paths
    assert "/api/v1/fleet-intelligence/profiles/{profile_slug}/collect" in api_paths


def test_budget_catalog_and_page_are_registered() -> None:
    from app.main import app
    from app.services.vehicle_catalog import catalog_entry, poland_budget_catalog

    assert catalog_entry("Toyota", "Yaris") == {"make": "Toyota", "model": "Yaris", "tier": "core"}
    assert catalog_entry("BMW", "3 Series")["tier"] == "review"
    assert poland_budget_catalog()["price_band"] == {"min_pln": 10000, "max_pln": 30000}
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    api_paths = set(app.openapi()["paths"])
    assert "/catalog" in paths
    assert "/api/v1/vehicle-catalog/poland-budget" in api_paths
