import asyncio
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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

NAVIGATION_ITEMS = (
    ("/", "Возможности"),
    ("/inspect", "Проверка авто"),
    ("/market", "Аналитика рынка"),
    ("/knowledge", "База знаний"),
    ("/settings", "Настройки"),
)


def web_page(filename: str, current_path: str) -> HTMLResponse:
    content = (web_dir / filename).read_text(encoding="utf-8")
    if "/assets/blue-theme.css" not in content:
        content = content.replace(
            "</head>",
            '<link rel="stylesheet" href="/assets/blue-theme.css"></head>',
            1,
        )
    navigation = "".join(
        '<a href="{}"{}>{}</a>'.format(
            href,
            ' aria-current="page"' if href == current_path else "",
            label,
        )
        for href, label in NAVIGATION_ITEMS
    )
    content = re.sub(
        r"<nav>.*?</nav>",
        f"<nav>{navigation}</nav>",
        content,
        1,
        flags=re.DOTALL,
    )
    if filename == "knowledge.html":
        content = re.sub(
            r'<label>Модель<select id="profile-select".*?</select></label>',
            "",
            content,
            count=1,
            flags=re.DOTALL,
        )
        content = content.replace(
            "</head>",
            '<link rel="stylesheet" href="/assets/knowledge-groups.css"><script src="/assets/knowledge-profile-bridge.js"></script></head>',
            1,
        )
        content = content.replace(
            "</body>",
            '<script src="/assets/knowledge-groups.js" defer></script></body>',
            1,
        )
    return HTMLResponse(content)


@app.get("/", include_in_schema=False)
def web_app() -> HTMLResponse:
    return web_page("index.html", "/")


@app.get("/market", include_in_schema=False)
def market_dashboard() -> HTMLResponse:
    return web_page("market.html", "/market")


@app.get("/knowledge", include_in_schema=False)
def knowledge_base() -> HTMLResponse:
    return web_page("knowledge.html", "/knowledge")


@app.get("/fleet", include_in_schema=False)
def fleet_dashboard() -> HTMLResponse:
    return web_page("fleet.html", "/fleet")


@app.get("/catalog", include_in_schema=False)
def catalog_dashboard() -> HTMLResponse:
    return web_page("catalog.html", "/catalog")


@app.get("/inspect", include_in_schema=False)
def inspection_page() -> HTMLResponse:
    return web_page("inspection.html", "/inspect")


@app.get("/settings", include_in_schema=False)
def settings_page() -> HTMLResponse:
    return web_page("settings.html", "/settings")
