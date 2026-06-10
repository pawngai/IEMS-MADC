from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")


def is_transaction_not_supported(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = (
        "transaction numbers are only allowed",
        "replica set",
        "mongos",
        "transactions are not supported",
    )
    return any(marker in message for marker in markers)


async def run_atomic(db, operation: Callable[[object | None], Awaitable[T]]) -> T:
    start_session = getattr(getattr(db, "client", None), "start_session", None)
    if start_session is None:
        return await operation(None)
    try:
        async with await db.client.start_session() as session:
            async with session.start_transaction():
                return await operation(session)
    except Exception as exc:
        if not is_transaction_not_supported(exc):
            raise
        return await operation(None)


async def call_with_optional_session(callable_obj, *args, session=None, **kwargs):
    if session is None:
        return await callable_obj(*args, **kwargs)
    try:
        return await callable_obj(*args, session=session, **kwargs)
    except TypeError as exc:
        if "session" not in str(exc):
            raise
        return await callable_obj(*args, **kwargs)