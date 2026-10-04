from fastapi import APIRouter
from app.schemas.catalog import VehicleCatalogRead
from app.services.vehicle_catalog import poland_budget_catalog

router = APIRouter(prefix="/vehicle-catalog", tags=["vehicle catalog"])

@router.get("/poland-budget", response_model=VehicleCatalogRead)
def poland_budget() -> VehicleCatalogRead:
    return VehicleCatalogRead.model_validate(poland_budget_catalog())
