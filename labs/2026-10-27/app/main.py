import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers import auth, devices, items
from .services.database import Database

def create_app(database_url=None, secret=None):
    @asynccontextmanager
    async def lifespan(app):
        yield
        app.state.db.engine.dispose()
    app = FastAPI(title="10/27 IoT Backend Practice", lifespan=lifespan)
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./runtime/learning.db")
    if url.startswith("sqlite:///./runtime/"):
        Path("runtime").mkdir(exist_ok=True)
    configured = secret or os.getenv("JWT_SECRET")
    if configured and len(configured) < 32:
        raise ValueError("JWT_SECRET needs at least 32 characters")
    # Local-only convenience. Deployment must explicitly set JWT_SECRET.
    app.state.secret = configured or secrets.token_urlsafe(48)
    app.state.db = Database(url)
    origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "").split(",") if s.strip()]
    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET","POST","PUT","PATCH","DELETE"], allow_headers=["Authorization","Content-Type"])
    for router in (auth.router, items.router, devices.router):
        app.include_router(router, prefix="/api/v1")
    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "hardware_connected": "see per-device telemetry"}
    app.mount("/web", StaticFiles(directory=Path(__file__).resolve().parents[1]/"web", html=True), name="web")
    return app

app = create_app()
