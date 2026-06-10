from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from dotenv import load_dotenv


def _load_env() -> None:
    """
    Load the project-root .env once.

    This project historically relied on importing `backend/server.py`, which
    loaded `backend/.env` at import-time. The canonical `.env` now lives at
    the project root (one level above `backend/`).
    """

    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env")


_load_env()


def _get_jwt_secret() -> str:
    """Get JWT secret from environment or raise error if not set."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise ValueError(
            "JWT_SECRET environment variable is required for security. "
            "Please set a strong secret key (minimum 32 characters)."
        )
    return secret


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", ""}


def _env_optional_str(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def _is_production_environment() -> bool:
    value = (
        os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or os.getenv("ENV")
        or "development"
    ).strip().lower()
    return value in {"production", "prod"}


def _default_refresh_cookie_secure() -> bool:
    return _is_production_environment()


def _default_refresh_cookie_samesite() -> str:
    return "none" if _is_production_environment() else "lax"


def _default_document_storage_local_fallback() -> bool:
    """Local-disk fallback for the document store.

    Defaults to ``False`` in production so a misconfigured GCS client never
    silently degrades to writing files to the container filesystem (which is
    ephemeral and not backed up). Development defaults to ``True`` so a single
    `start-dev.ps1` flow works without needing a cloud bucket.
    """

    return not _is_production_environment()


def _default_cors_origins_raw() -> str:
    """Development default for CORS_ORIGINS.

    Production refuses to fall back to a localhost-heavy default — startup
    raises in ``Settings.__post_init__`` unless ``CORS_ORIGINS`` is set.
    """

    return (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000,"
        "http://localhost:5501,http://127.0.0.1:5501"
    )


def _default_cors_origin_regex() -> str:
    """Development default for CORS_ORIGIN_REGEX.

    Production forces this to empty unless the operator explicitly opts in
    via ``CORS_ALLOW_PRIVATE_NETWORK_REGEX=1`` — the LAN-wide default is too
    broad for a public deployment.
    """

    return (
        r"^https?://(localhost|127\.0\.0\.1|"
        r"10(?:\.\d{1,3}){3}|"
        r"192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
        r"(?::\d{1,5})?$"
    )


@dataclass(frozen=True)
class Settings:
    """Application settings.

    Every env-dependent value uses ``field(default_factory=...)`` so that
    ``os.getenv()`` is evaluated at **instantiation** time — not at module
    import time.  This makes it safe to call ``load_dotenv()`` or set env
    vars *before* the singleton ``settings = Settings()`` line at the
    bottom of this module.
    """

    mongo_url: str = field(default_factory=lambda: os.getenv("MONGO_URL", ""))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "iems_db"))
    environment: str = field(
        default_factory=lambda: (
            os.getenv("ENVIRONMENT")
            or os.getenv("APP_ENV")
            or os.getenv("ENV")
            or "development"
        ).strip().lower()
    )

    jwt_secret: str = field(default_factory=_get_jwt_secret)
    jwt_algorithm: str = "HS256"  # Hardcoded for security - don't accept from environment

    cors_origins_raw: str = field(
        default_factory=lambda: (
            os.getenv("CORS_ORIGINS")
            if os.getenv("CORS_ORIGINS") is not None
            else ("" if _is_production_environment() else _default_cors_origins_raw())
        )
    )
    cors_origin_regex_raw: str = field(
        default_factory=lambda: (
            os.getenv("CORS_ORIGIN_REGEX")
            if os.getenv("CORS_ORIGIN_REGEX") is not None
            else (
                ""
                if _is_production_environment()
                and not _env_bool("CORS_ALLOW_PRIVATE_NETWORK_REGEX", False)
                else _default_cors_origin_regex()
            )
        )
    )

    api_title: str = field(default_factory=lambda: os.getenv("API_TITLE", "MADC-HRMS"))
    api_description: str = field(
        default_factory=lambda: os.getenv(
            "API_DESCRIPTION",
            "MADC Human Resource Management System",
        )
    )
    api_version: str = field(default_factory=lambda: os.getenv("API_VERSION", "2.0.0"))

    # File uploads
    uploads_dir: str = field(
        default_factory=lambda: os.getenv(
            "UPLOAD_DIR",
            str(Path(__file__).resolve().parents[3] / "uploads"),
        )
    )
    document_storage_backend: str = field(
        default_factory=lambda: os.getenv("DOCUMENT_STORAGE_BACKEND", "local").strip().lower() or "local"
    )
    gcs_bucket_name: str = field(
        default_factory=lambda: os.getenv("GCS_BUCKET_NAME", "").strip()
    )
    gcp_project_id: str = field(
        default_factory=lambda: os.getenv("GCP_PROJECT_ID", "").strip()
    )
    document_storage_local_fallback_enabled: bool = field(
        default_factory=lambda: _env_bool(
            "DOCUMENT_STORAGE_LOCAL_FALLBACK_ENABLED",
            _default_document_storage_local_fallback(),
        )
    )
    allow_document_in_memory_listing: bool = field(
        default_factory=lambda: _env_bool(
            "ALLOW_DOCUMENT_IN_MEMORY_LISTING",
            not _is_production_environment(),
        )
    )
    document_scanner_backend: str = field(
        default_factory=lambda: (os.getenv("DOCUMENT_SCANNER_BACKEND", "noop") or "noop").strip().lower()
    )
    document_scanner_block_on_pending: bool = field(
        default_factory=lambda: _env_bool("DOCUMENT_SCANNER_BLOCK_ON_PENDING", True)
    )
    document_preview_backend: str = field(
        default_factory=lambda: (os.getenv("DOCUMENT_PREVIEW_BACKEND", "noop") or "noop").strip().lower()
    )
    rate_limit_storage_uri: str = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_STORAGE_URI", "").strip()
    )
    refresh_cookie_secure: bool = field(
        default_factory=lambda: _env_bool("REFRESH_COOKIE_SECURE", _default_refresh_cookie_secure())
    )
    refresh_cookie_samesite: str = field(
        default_factory=lambda: os.getenv("REFRESH_COOKIE_SAMESITE", _default_refresh_cookie_samesite()).strip().lower() or _default_refresh_cookie_samesite()
    )
    refresh_cookie_domain: str | None = field(
        default_factory=lambda: _env_optional_str("REFRESH_COOKIE_DOMAIN")
    )

    def __post_init__(self) -> None:
        if self.db_name == "iems":
            raise ValueError(
                "DB_NAME='iems' is not allowed. "
                "The correct database name is 'iems_db'. "
                "Using 'iems' creates a stale empty database in MongoDB."
            )
        if self.refresh_cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("REFRESH_COOKIE_SAMESITE must be one of: lax, strict, none")
        if self.is_production:
            origins = self.cors_origins
            if not origins:
                raise ValueError(
                    "CORS_ORIGINS must be explicitly configured in production. "
                    "Set CORS_ORIGINS to the comma-separated list of fully qualified "
                    "frontend origins; localhost defaults are not allowed in production."
                )
            if "*" in origins:
                raise ValueError(
                    "CORS_ORIGINS='*' is not allowed in production: credentialed "
                    "requests require an explicit origin list."
                )
            if (
                self.document_storage_backend != "local"
                and self.document_storage_local_fallback_enabled
                and not _env_bool("DOCUMENT_STORAGE_LOCAL_FALLBACK_ENABLED", False)
            ):
                # Defensive: this branch should be unreachable because the default
                # factory disables fallback in production. Kept as a sanity check.
                raise ValueError(
                    "DOCUMENT_STORAGE_LOCAL_FALLBACK_ENABLED must remain false in "
                    "production unless explicitly opted in."
                )

    @property
    def is_production(self) -> bool:
        return self.environment in {"production", "prod"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def cors_origin_regex(self) -> str:
        return self.cors_origin_regex_raw or ""


settings = Settings()
