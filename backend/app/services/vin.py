"""Conservative offline VIN identification and official CEPiK handoff."""

from datetime import date

from app.schemas.vin import CepikHistoryPrepareRead, VinDecodeRead

WMI_MANUFACTURERS = {
    "WAU": "Audi",
    "WUA": "Audi Sport",
    "WVW": "Volkswagen",
    "WBA": "BMW",
    "WBS": "BMW M",
    "WDD": "Mercedes-Benz",
    "WDB": "Mercedes-Benz",
    "WF0": "Ford Europe",
}
YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"
AUDI_PLATFORM_HINTS = {
    "8V": ("A3", "8V", "audi-a3-8v-pl-v1"),
}


def decode_vin(vin: str) -> VinDecodeRead:
    normalized = vin.strip().upper()
    allowed = normalized.isalnum() and not any(char in normalized for char in "IOQ")
    valid = len(normalized) == 17 and allowed
    warnings: list[str] = []
    if not valid:
        warnings.append("VIN должен содержать 17 символов и не использовать I, O или Q")
    wmi = normalized[:3]
    manufacturer = WMI_MANUFACTURERS.get(wmi)
    if manufacturer is None:
        warnings.append("Производитель отсутствует в локальном справочнике WMI")
    model_hint = generation_hint = knowledge_slug = None
    if manufacturer in {"Audi", "Audi Sport"}:
        for code, hint in AUDI_PLATFORM_HINTS.items():
            if code in normalized[3:9]:
                model_hint, generation_hint, knowledge_slug = hint
                break
    region = (
        "Europe"
        if normalized[:1] in "STUVWXYZ"
        else "North America"
        if normalized[:1] in "12345"
        else "Asia"
        if normalized[:1] in "JKLMNPR"
        else "Other"
    )
    candidates: list[int] = []
    if len(normalized) >= 10 and normalized[9] in YEAR_CODES:
        offset = YEAR_CODES.index(normalized[9])
        candidates = [1980 + offset, 2010 + offset, 2040 + offset]
        candidates = [year for year in candidates if 1980 <= year <= date.today().year + 1]
        if len(candidates) > 1:
            warnings.append("Код модельного года цикличен; точный год нужно подтвердить документом")
    else:
        warnings.append("Модельный год не удалось определить")
    return VinDecodeRead(
        vin=normalized,
        valid=valid,
        wmi=wmi,
        manufacturer=manufacturer,
        model_hint=model_hint,
        generation_hint=generation_hint,
        knowledge_slug=knowledge_slug,
        region=region,
        model_year_candidates=candidates,
        serial_number=normalized[-6:] if len(normalized) >= 6 else normalized,
        confidence="medium" if valid and manufacturer else "low",
        source="ISO VIN structure + DealerMind WMI catalog",
        warnings=warnings,
    )


def prepare_cepik_history(
    vin: str, registration_number: str, first_registration_date: date
) -> CepikHistoryPrepareRead:
    decoded = decode_vin(vin)
    if not decoded.valid:
        raise ValueError("Некорректный VIN")
    return CepikHistoryPrepareRead(
        vin=decoded.vin,
        registration_number=registration_number.replace(" ", "").upper(),
        first_registration_date=first_registration_date,
        official_url="https://www.gov.pl/web/gov/sprawdz-historie-pojazdu",
        source="Centralna Ewidencja Pojazdów (CEPiK)",
        attribution="Dane pochodzą z Centralnej Ewidencji Pojazdów i Kierowców",
        automation_status="official_handoff",
        instructions=[
            "Откройте официальный сервис Historia Pojazdu",
            "Введите подготовленные VIN, номер регистрации и дату первой регистрации",
            "При необходимости войдите через Profil Zaufany",
            "Скачайте официальный отчёт PDF для последующего импорта в DealerMind",
        ],
    )
