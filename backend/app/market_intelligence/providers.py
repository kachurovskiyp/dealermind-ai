"""Provider boundary for external listing data."""

import csv
from io import StringIO
from typing import Protocol

from pydantic import ValidationError

from app.schemas.imports import ListingImportRecord


class ListingProvider(Protocol):
    name: str

    def records(self) -> list[ListingImportRecord]: ...


class StructuredListingProvider:
    def __init__(self, records: list[ListingImportRecord], name: str = "structured-json") -> None:
        self._records = records
        self.name = name

    def records(self) -> list[ListingImportRecord]:
        return self._records


class CsvListingProvider:
    name = "csv"

    def __init__(self, content: str) -> None:
        self._content = content

    def records(self) -> list[ListingImportRecord]:
        reader = csv.DictReader(StringIO(self._content.lstrip("\ufeff")))
        if reader.fieldnames is None:
            raise ValueError("CSV header is required")
        records: list[ListingImportRecord] = []
        errors: list[str] = []
        for row_number, row in enumerate(reader, start=2):
            cleaned = {
                key: value
                for key, value in row.items()
                if key is not None and value not in (None, "")
            }
            try:
                records.append(ListingImportRecord.model_validate(cleaned))
                if len(records) > 1000:
                    raise ValueError("CSV batch cannot contain more than 1000 records")
            except ValidationError as exc:
                errors.append(f"row {row_number}: {exc.errors()[0]['msg']}")
        if errors:
            raise ValueError("; ".join(errors))
        if not records:
            raise ValueError("CSV contains no listing records")
        return records
