import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import get_settings
from app.database import Base, engine

logger = logging.getLogger(__name__)


def _resolve_static_dir() -> str | None:
    """Find the frontend static files directory.

    In EXE mode, static files are bundled inside the PyInstaller _MEIPASS directory.
    In development, they may exist at ../frontend/dist relative to the backend.
    """
    # PyInstaller bundle
    if getattr(sys, "frozen", False):
        candidate = os.path.join(sys._MEIPASS, "frontend_dist")  # type: ignore[attr-defined]
        if os.path.isdir(candidate):
            return candidate

    # Development: check for a pre-built frontend/dist
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidate = os.path.join(repo_root, "frontend", "dist")
    if os.path.isdir(candidate):
        return candidate

    return None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="KnowYourRate",
        description="AI-powered influencer rate analysis platform",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    @application.on_event("startup")
    async def on_startup() -> None:
        """Create database tables on startup if they don't exist."""
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Migrate: add agent_outputs column to reports if missing
            if get_settings().is_sqlite:
                from sqlalchemy import text
                try:
                    await conn.execute(
                        text("ALTER TABLE reports ADD COLUMN agent_outputs JSON")
                    )
                    logger.info("Added agent_outputs column to reports table.")
                except Exception:
                    pass  # Column already exists
        logger.info("Database tables ready.")

    # Serve frontend static files (EXE mode or when frontend/dist exists)
    static_dir = _resolve_static_dir()
    if static_dir:
        logger.info("Serving frontend from %s", static_dir)
        # Mount static assets (JS/CSS/images)
        assets_dir = os.path.join(static_dir, "assets")
        if os.path.isdir(assets_dir):
            application.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        # Mount locales
        locales_dir = os.path.join(static_dir, "locales")
        if os.path.isdir(locales_dir):
            application.mount("/locales", StaticFiles(directory=locales_dir), name="locales")

        # Catch-all: serve index.html for any non-API route (SPA routing)
        from fastapi.responses import FileResponse

        index_html = os.path.join(static_dir, "index.html")

        @application.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            # If a specific file exists, serve it; otherwise serve index.html
            file_path = os.path.join(static_dir, full_path)  # type: ignore[arg-type]
            if full_path and os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(index_html)

    return application


app = create_app()
