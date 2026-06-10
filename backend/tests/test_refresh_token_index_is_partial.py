"""Refresh-token index guard.

New refresh-token documents persist only ``token_hash``; the legacy ``token``
field is absent. A non-partial unique index on ``token`` would treat every
missing value as the implicit ``null`` and reject more than one login per user.
The index must be PARTIAL so it only applies to legacy documents that still
carry the field as a string.

These tests run against a real Mongo instance (``MONGO_URL`` env var, defaults
to ``mongodb://localhost:27017``) and skip when no Mongo is reachable. They
exercise the runtime index-rebuild helper and verify duplicate-key behavior
on the resulting indexes.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


pytestmark = pytest.mark.asyncio


async def _make_db():
    motor = pytest.importorskip("motor.motor_asyncio")
    from pymongo.errors import ServerSelectionTimeoutError

    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    client = motor.AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=1500)
    try:
        await client.admin.command("ping")
    except ServerSelectionTimeoutError:
        client.close()
        pytest.skip(f"Mongo not reachable at {mongo_url}")
    db_name = f"iems_test_refresh_token_{uuid.uuid4().hex[:12]}"
    return client, client[db_name]


async def test_legacy_non_partial_token_index_is_dropped() -> None:
    from app_platform.db.runtime import _drop_index_if_non_partial

    client, db = await _make_db()
    try:
        await db.refresh_tokens.create_index([("token", 1)], unique=True, name="legacy_non_partial")
        await _drop_index_if_non_partial(
            db.refresh_tokens, field="token", collection_name="refresh_tokens"
        )
        info = await db.refresh_tokens.index_information()
        assert "legacy_non_partial" not in info
    finally:
        await client.drop_database(db.name)
        client.close()


async def test_partial_token_index_is_preserved() -> None:
    from app_platform.db.runtime import _drop_index_if_non_partial

    client, db = await _make_db()
    try:
        await db.refresh_tokens.create_index(
            [("token", 1)],
            unique=True,
            partialFilterExpression={"token": {"$type": "string"}},
            name="partial_unique",
        )
        await _drop_index_if_non_partial(
            db.refresh_tokens, field="token", collection_name="refresh_tokens"
        )
        info = await db.refresh_tokens.index_information()
        assert "partial_unique" in info
    finally:
        await client.drop_database(db.name)
        client.close()


async def test_multiple_refresh_tokens_without_token_field_can_coexist() -> None:
    client, db = await _make_db()
    try:
        await db.refresh_tokens.create_index(
            [("token_hash", 1)],
            unique=True,
            partialFilterExpression={"token_hash": {"$type": "string"}},
        )
        await db.refresh_tokens.create_index(
            [("token", 1)],
            unique=True,
            partialFilterExpression={"token": {"$type": "string"}},
        )

        await db.refresh_tokens.insert_one({"user_id": "u1", "token_hash": "h1"})
        await db.refresh_tokens.insert_one({"user_id": "u2", "token_hash": "h2"})
        await db.refresh_tokens.insert_one({"user_id": "u3", "token_hash": "h3"})

        assert await db.refresh_tokens.count_documents({}) == 3
    finally:
        await client.drop_database(db.name)
        client.close()


async def test_legacy_and_new_documents_can_coexist() -> None:
    client, db = await _make_db()
    try:
        await db.refresh_tokens.create_index(
            [("token_hash", 1)],
            unique=True,
            partialFilterExpression={"token_hash": {"$type": "string"}},
        )
        await db.refresh_tokens.create_index(
            [("token", 1)],
            unique=True,
            partialFilterExpression={"token": {"$type": "string"}},
        )

        await db.refresh_tokens.insert_one(
            {"user_id": "legacy", "token": "raw-legacy", "token_hash": "h-legacy"}
        )
        await db.refresh_tokens.insert_one({"user_id": "new-1", "token_hash": "h-new-1"})
        await db.refresh_tokens.insert_one({"user_id": "new-2", "token_hash": "h-new-2"})

        assert await db.refresh_tokens.count_documents({}) == 3
    finally:
        await client.drop_database(db.name)
        client.close()
