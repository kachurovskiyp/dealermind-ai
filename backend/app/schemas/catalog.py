from pydantic import BaseModel

class CatalogGroupRead(BaseModel):
    make: str
    tier: str
    models: list[str]

class VehicleCatalogRead(BaseModel):
    version: str
    price_band: dict[str, int]
    groups: list[CatalogGroupRead]
