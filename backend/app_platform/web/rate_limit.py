"""
Centralised rate-limiter instance (slowapi).

Import `limiter` from here in any router that needs per-route limits.
The FastAPI app must register the limiter via:

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Rate budget defaults (per IP):
    - 120 requests / minute  - global fallback
    - 5 requests / minute    - applied via @limiter.limit on auth endpoints

Storage:
    Configurable via the ``RATE_LIMIT_STORAGE_URI`` env var. In production
    deployments this should point at a shared backend (e.g. Redis). When it
    is unset, SlowAPI falls back to process-local in-memory state and logs a
    production warning.
"""

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app_platform.config.settings import settings

logger = logging.getLogger(__name__)


def _resolve_storage_uri() -> str:
    uri = (settings.rate_limit_storage_uri or "").strip()
    if uri:
        return uri
    if settings.is_production:
        logger.error(
            "RATE_LIMIT_STORAGE_URI is unset in production; SlowAPI cannot enforce "
            "shared rate limits across workers. Set a Redis URI (e.g. "
            "'redis://host:6379/0') before serving traffic."
        )
    return "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    storage_uri=_resolve_storage_uri(),
)
