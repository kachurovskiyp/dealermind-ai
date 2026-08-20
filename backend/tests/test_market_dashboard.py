from app.main import app


def test_market_dashboard_and_read_api_are_registered() -> None:
    page_paths = {route.path for route in app.routes if hasattr(route, "path")}
    api_paths = set(app.openapi()["paths"])

    assert "/market" in page_paths
    assert "/api/v1/market-intelligence/overview" in api_paths
    assert "/api/v1/market-intelligence/valuations" in api_paths
    assert "/api/v1/market-intelligence/collections" in api_paths
    assert "/api/v1/market-intelligence/collections/{collection_id}/listings" in api_paths
    assert "/api/v1/market-intelligence/poland" in api_paths
    assert "/api/v1/market-intelligence/poland/snapshots" in api_paths
    assert "/api/v1/market-intelligence/poland/variants" in api_paths
