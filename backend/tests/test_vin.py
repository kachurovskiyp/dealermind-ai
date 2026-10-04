from datetime import date

from app.main import app
from app.schemas.vin import VinDecodeRequest
from app.services.vin import decode_vin, prepare_cepik_history


def test_vin_and_cepik_endpoints_are_registered() -> None:
    paths = set(app.openapi()["paths"])
    assert "/api/v1/vin/decode" in paths
    assert "/api/v1/vin/cepik/prepare" in paths


def test_audi_wmi_is_decoded_without_claiming_factory_options() -> None:
    result = decode_vin("WAUZZZ8V1GA123456")
    assert result.valid is True
    assert result.manufacturer == "Audi"
    assert result.wmi == "WAU"
    assert result.model_hint == "A3"
    assert result.generation_hint == "8V"
    assert result.knowledge_slug == "audi-a3-8v-pl-v1"
    assert result.source.startswith("ISO VIN")


def test_pasted_vin_separators_are_removed_before_length_validation() -> None:
    payload = VinDecodeRequest(vin="WAU ZZZ 8V1-GA123456\u200b")
    assert payload.vin == "WAUZZZ8V1GA123456"


def test_cepik_handoff_keeps_official_attribution() -> None:
    result = prepare_cepik_history(
        "WAUZZZ8V1GA123456", "PO 12345", date(2016, 5, 20)
    )
    assert result.registration_number == "PO12345"
    assert result.automation_status == "official_handoff"
    assert "gov.pl" in result.official_url
    assert "Centralnej Ewidencji" in result.attribution
