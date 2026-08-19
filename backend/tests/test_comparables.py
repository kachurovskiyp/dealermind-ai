from app.models.domain import ComparableCollection, ComparableListing
from app.services.comparables import _slug


def test_comparable_market_tables_are_registered() -> None:
    assert "comparable_collections" in ComparableCollection.metadata.tables
    assert "comparable_listings" in ComparableListing.metadata.tables


def test_vehicle_names_are_converted_to_safe_otomoto_path_segments() -> None:
    assert _slug("Škoda") == "skoda"
    assert _slug("Seria 3") == "seria-3"
