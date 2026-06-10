from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app_platform.auth.current_user import _validate_live_user
from contexts.identity_access.identity.infrastructure import auth_session_service


class _RefreshTokens:
    def __init__(self):
        self.rows: list[dict] = []

    async def insert_one(self, document):
        self.rows.append(dict(document))

    async def find_one_and_delete(self, query):
        for index, row in enumerate(self.rows):
            if _matches(row, query):
                return self.rows.pop(index)
        return None

    async def delete_many(self, query):
        self.rows = [row for row in self.rows if not _matches(row, query)]


class _Users:
    def __init__(self, user):
        self.user = dict(user)

    async def find_one(self, query, projection=None):
        if query.get("id") != self.user.get("id"):
            return None
        return dict(self.user)

    async def update_one(self, query, update):
        if query.get("id") != self.user.get("id"):
            return None
        increment = (update.get("$inc") or {}).get("token_version")
        if increment:
            self.user["token_version"] = int(self.user.get("token_version") or 0) + increment


def _matches(row: dict, query: dict) -> bool:
    if "$or" in query:
        return any(_matches(row, item) for item in query["$or"])
    return all(row.get(key) == value for key, value in query.items())


@pytest.mark.asyncio
async def test_refresh_tokens_are_hashed_and_single_use() -> None:
    user = {
        "id": "user-1",
        "email": "user@example.com",
        "name": "User",
        "authorities": ["EMPLOYEE"],
        "token_version": 0,
    }
    db = SimpleNamespace(refresh_tokens=_RefreshTokens(), users=_Users(user))

    refresh_token = "opaque-refresh-token"
    await auth_session_service._store_refresh_token(db, user["id"], refresh_token)

    assert db.refresh_tokens.rows[0].get("token") is None
    assert db.refresh_tokens.rows[0]["token_hash"] != refresh_token

    first = await auth_session_service.refresh_access_token(db, refresh_token)
    assert first["access_token"]
    assert first["refresh_token"]

    with pytest.raises(HTTPException) as exc:
        await auth_session_service.refresh_access_token(db, refresh_token)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_live_user_validation_rejects_revoked_access_token() -> None:
    user = {"id": "user-1", "is_active": True, "token_version": 2}
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=SimpleNamespace(users=_Users(user)))))

    with pytest.raises(HTTPException) as exc:
        await _validate_live_user(request, {"sub": "user-1", "token_version": 1})

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_live_user_validation_rejects_legacy_access_token_without_version() -> None:
    user = {"id": "user-1", "is_active": True, "token_version": 0}
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=SimpleNamespace(users=_Users(user)))))

    with pytest.raises(HTTPException) as exc:
        await _validate_live_user(request, {"sub": "user-1"})

    assert exc.value.status_code == 401
