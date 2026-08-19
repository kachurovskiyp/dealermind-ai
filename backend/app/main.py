import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.services.automation import scheduler_loop


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    stop = asyncio.Event()
    scheduler = asyncio.create_task(scheduler_loop(stop))
    try:
        yield
    finally:
        stop.set()
        await scheduler


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)

web_dir = Path(__file__).parent / "web"
app.mount("/assets", StaticFiles(directory=web_dir), name="assets")


@app.get("/", include_in_schema=False)
def web_app() -> FileResponse:
    return FileResponse(web_dir / "index.html")


@app.get("/market", include_in_schema=False)
def market_dashboard() -> FileResponse:
    return FileResponse(web_dir / "market.html")
