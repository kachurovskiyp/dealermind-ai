from app.models.automation import ImportRunStatus, ImportSource
from app.schemas.automation import ImportSourceCreate
from app.services.automation import _batch_from_response


def listing_payload() -> dict[str, object]:
    return {
        "market_code": "PL",
        "marketplace_slug": "otomoto",
        "target_market_code": "PL",
        "external_id": "scheduled-1",
        "url": "https://example.com/1",
        "title": "VW Passat",
        "make": "VW",
        "model": "Passat",
        "price": 40_000,
        "currency": "PLN",
    }


def test_import_automation_tables_are_registered() -> None:
    assert {"import_sources", "import_runs"}.issubset(ImportSource.metadata.tables)


def test_source_schedule_has_safe_bounds() -> None:
    source = ImportSourceCreate(
        name="Partner feed",
        endpoint_url="https://example.com/listings.json",
        interval_minutes=60,
    )

    assert source.enabled is True
    assert source.interval_minutes == 60


def test_http_array_is_normalized_to_import_batch() -> None:
    source = ImportSource(name="Partner", endpoint_url="https://example.com", interval_minutes=60)

    batch = _batch_from_response(source, [listing_payload()])

    assert batch.provider == "Partner"
    assert batch.records[0].external_id == "scheduled-1"


def test_run_status_distinguishes_partial_and_failed() -> None:
    assert ImportRunStatus.PARTIAL.value == "partial"
    assert ImportRunStatus.FAILED.value == "failed"
