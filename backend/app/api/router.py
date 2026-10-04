from fastapi import APIRouter

from app.api.routes import (
    acquisitions,
    catalog,
    fleet,
    automation,
    imports,
    intake,
    inspection,
    knowledge,
    logistics,
    market_intelligence,
    markets,
    offers,
    opportunities,
    vehicles,
    vin,
)

api_router = APIRouter()
api_router.include_router(markets.router)
api_router.include_router(offers.router)
api_router.include_router(opportunities.router)
api_router.include_router(acquisitions.router)
api_router.include_router(vehicles.router)
api_router.include_router(imports.router)
api_router.include_router(automation.router)
api_router.include_router(intake.router)
api_router.include_router(knowledge.router)
api_router.include_router(market_intelligence.router)
api_router.include_router(logistics.router)
api_router.include_router(vin.router)
api_router.include_router(fleet.router)
api_router.include_router(catalog.router)
api_router.include_router(inspection.router)
