from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from app.bootstrap.container import wire_app_container
from app.bootstrap.dev_admin_sync import sync_canonical_dev_admin, sync_canonical_dev_workflow_users
from app.bootstrap.router_registry import build_api_router
from app.bootstrap.subscribers import register_app_subscribers
from app_platform.reference_data.infrastructure.versioned_seed import seed_system_managed_masters
from app_platform.config.settings import settings
from app_platform.db.runtime import lifespan as db_lifespan
from app_platform.logging.request_id import RequestIdMiddleware
from app_platform.web.rate_limit import limiter
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


EXPOSED_CORS_HEADERS = [
    "Content-Disposition",
    "X-IEMS-Analytics-Total",
    "X-IEMS-Analytics-Exported",
]


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    async with db_lifespan(app):
        db = getattr(app.state, "db", None)
        if db is not None:
            try:
                if not settings.is_production:
                    await sync_canonical_dev_admin(db)
                    await sync_canonical_dev_workflow_users(db)
            except Exception:
                logger.warning("Failed to sync canonical dev accounts during startup", exc_info=True)
            try:
                seeded_counts = await seed_system_managed_masters(db)
                total_seeded = sum(seeded_counts.values())
                if total_seeded:
                    logger.info("Seeded %s versioned policy master records", total_seeded)
            except Exception:
                logger.warning("Failed to seed versioned policy masters during startup", exc_info=True)

        container = wire_app_container(app)
        register_app_subscribers(app)
        if container.outbox_dispatcher is not None:
            await container.outbox_dispatcher.start()
        try:
            yield
        finally:
            if container.outbox_dispatcher is not None:
                await container.outbox_dispatcher.stop()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp

        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=app_lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(build_api_router())

    @app.get("/health/live")
    async def health_live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    async def health_ready() -> dict[str, str]:
        db = getattr(app.state, "db", None)
        return {"status": "ready" if db is not None else "degraded"}

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)

    cors_origins = settings.cors_origins
    allow_credentials = "*" not in cors_origins
    if not allow_credentials:
        logging.warning(
            "CORS configured with wildcard origin. Credentials disabled for security. "
            "Set specific origins via CORS_ORIGINS environment variable for production."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=allow_credentials,
        allow_origins=cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=EXPOSED_CORS_HEADERS,
    )

    _mount_spa(app)

    return app


def _mount_spa(app: FastAPI) -> None:
    """Serve the Vite SPA when the production image includes frontend/dist."""

    project_root = Path(__file__).resolve().parents[3]
    dist_dir = project_root / "frontend" / "dist"
    index_html = dist_dir / "index.html"
    assets_dir = dist_dir / "assets"

    if not index_html.exists():
        return

    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def serve_spa_root():
        return FileResponse(index_html)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        candidate = (dist_dir / full_path).resolve()
        try:
            candidate.relative_to(dist_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not found")

        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_html)
