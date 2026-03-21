import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from web.config import UPLOAD_DIR
from web.routers import admin, auth, cars, financials, orders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from bot.database.connection import init_db, close_db
    await init_db()
    logger.info("Database initialized.")
    yield
    await close_db()
    logger.info("Database connection closed.")


app = FastAPI(title="AutoService Master API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(cars.router, prefix="/api")
app.include_router(financials.router, prefix="/api")
app.include_router(admin.router)

from datetime import datetime, timezone
import httpx
from fastapi.responses import JSONResponse, StreamingResponse


@app.get("/api/health")
async def health():
    return JSONResponse({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "1.0.0"})


@app.get("/tg-photo/{file_id:path}")
async def telegram_photo_proxy(file_id: str):
    """Download a Telegram photo once, cache locally, then serve from cache."""
    from web.config import BOT_TOKEN
    if not BOT_TOKEN:
        return JSONResponse({"error": "Bot token not configured"}, status_code=503)

    # Check local cache first
    import hashlib
    cache_dir = UPLOAD_DIR / "tg_cache"
    cache_dir.mkdir(exist_ok=True)
    safe_name = hashlib.sha256(file_id.encode()).hexdigest()
    cached = list(cache_dir.glob(f"{safe_name}.*"))
    if cached:
        from fastapi.responses import FileResponse
        return FileResponse(cached[0], media_type="image/jpeg")

    # Download from Telegram and cache
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                params={"file_id": file_id},
            )
            data = resp.json()
            if not data.get("ok"):
                return JSONResponse({"error": "File not found"}, status_code=404)
            file_path = data["result"]["file_path"]
            ext = file_path.rsplit(".", 1)[-1] if "." in file_path else "jpg"
            photo_resp = await client.get(
                f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            )
            cache_file = cache_dir / f"{safe_name}.{ext}"
            cache_file.write_bytes(photo_resp.content)
            from fastapi.responses import FileResponse
            return FileResponse(cache_file, media_type="image/jpeg")
    except Exception:
        logger.exception("Failed to proxy Telegram photo %s", file_id)
        return JSONResponse({"error": "Failed to fetch photo"}, status_code=502)


app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
