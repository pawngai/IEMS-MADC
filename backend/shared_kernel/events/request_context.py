from __future__ import annotations

from contextvars import ContextVar, Token


_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_idempotency_key_ctx: ContextVar[str | None] = ContextVar("idempotency_key", default=None)


def set_request_context(*, request_id: str | None, idempotency_key: str | None) -> tuple[Token, Token]:
    token_request = _request_id_ctx.set(request_id)
    token_idempotency = _idempotency_key_ctx.set(idempotency_key)
    return token_request, token_idempotency


def reset_request_context(*, tokens: tuple[Token, Token]) -> None:
    token_request, token_idempotency = tokens
    _request_id_ctx.reset(token_request)
    _idempotency_key_ctx.reset(token_idempotency)


def get_request_id() -> str | None:
    return _request_id_ctx.get()


def get_idempotency_key() -> str | None:
    return _idempotency_key_ctx.get()
