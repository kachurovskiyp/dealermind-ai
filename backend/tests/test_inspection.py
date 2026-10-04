from app.main import app


def test_configuration_review_page_and_api_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/inspection/review" in paths
    assert "/api/v1/inspection/analyze" not in paths
    assert any(getattr(route, "path", None) == "/inspect" for route in app.routes)
