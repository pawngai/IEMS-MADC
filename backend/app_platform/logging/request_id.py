from __future__ import annotations

import logging
import uuid

from shared_kernel.events.request_context import reset_request_context, set_request_context
from starlette.middleware.base import BaseHTTPMiddleware


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s",
    )


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


for _logger in (logging.getLogger(),):
    _logger.addFilter(RequestIdFilter())


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        idempotency_key = request.headers.get("Idempotency-Key")
        request.state.request_id = request_id
        request.state.idempotency_key = idempotency_key
        tokens = set_request_context(
            request_id=request_id,
            idempotency_key=idempotency_key,
        )
        try:
            response = await call_next(request)
        finally:
            reset_request_context(tokens=tokens)
        response.headers["X-Request-ID"] = request_id
        return response
