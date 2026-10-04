import re
from datetime import date

from pydantic import BaseModel, Field, field_validator


class VinDecodeRequest(BaseModel):
    vin: str

    @field_validator("vin", mode="before")
    @classmethod
    def normalize_vin(cls, value: object) -> object:
        if value is None:
            return value
        normalized = re.sub(r"[^A-Z0-9]", "", str(value).upper())
        if len(normalized) != 17:
            raise ValueError(
                f"VIN должен содержать ровно 17 символов после очистки; получено {len(normalized)}"
            )
        return normalized


class VinDecodeRead(BaseModel):
    vin: str
    valid: bool
    wmi: str
    manufacturer: str | None
    model_hint: str | None
    generation_hint: str | None
    knowledge_slug: str | None
    region: str
    model_year_candidates: list[int]
    serial_number: str
    confidence: str
    source: str
    warnings: list[str]


class CepikHistoryPrepareRequest(BaseModel):
    vin: str
    registration_number: str = Field(min_length=2, max_length=12)
    first_registration_date: date

    @field_validator("vin", mode="before")
    @classmethod
    def normalize_vin(cls, value: object) -> object:
        return VinDecodeRequest(vin=value).vin

    @field_validator("registration_number", mode="before")
    @classmethod
    def normalize_registration(cls, value: object) -> object:
        return re.sub(r"[^A-Z0-9]", "", str(value).upper()) if value is not None else value


class CepikHistoryPrepareRead(BaseModel):
    vin: str
    registration_number: str
    first_registration_date: date
    official_url: str
    source: str
    attribution: str
    automation_status: str
    instructions: list[str]
