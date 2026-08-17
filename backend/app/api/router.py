from fastapi import APIRouter

from app.api.routes import acquisitions, automation, imports, markets, offers, opportunities, vehicles

api_router = APIRouter()
api_router.include_router(markets.router)
api_router.include_router(offers.router)
api_router.include_router(opportunities.router)
api_router.include_router(acquisitions.router)
api_router.include_router(vehicles.router)
api_router.include_router(imports.router)
api_router.include_router(automation.router)
