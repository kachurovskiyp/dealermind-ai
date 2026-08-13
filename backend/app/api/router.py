from fastapi import APIRouter

from app.api.routes import markets, offers, opportunities

api_router = APIRouter()
api_router.include_router(markets.router)
api_router.include_router(offers.router)
api_router.include_router(opportunities.router)
