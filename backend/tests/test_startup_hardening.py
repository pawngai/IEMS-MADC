from __future__ import annotations

from types import SimpleNamespace

import pytest

from app_platform.db import migration_runner, runtime


class _AsyncCursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        row = self._rows[self._index]
        self._index += 1
        return row


class _MigrationCollection:
    def __init__(self, applied=None):
        self.rows = [{"migration_id": item} for item in (applied or [])]
        self.created_indexes = []
        self.inserted = []

    async def create_index(self, *args, **kwargs):
        self.created_indexes.append((args, kwargs))

    def find(self, *_args, **_kwargs):
        return _AsyncCursor(self.rows)

    async def insert_one(self, document):
        self.inserted.append(dict(document))
        self.rows.append(dict(document))


class _MigrationDb:
    def __init__(self, applied=None):
        self.schema_migrations = _MigrationCollection(applied=applied)
        self.calls = []

    def __getitem__(self, name):
        return getattr(self, name)


def _migration(name, calls):
    async def run(db):
        db.calls.append(name)
        calls.append(name)

    return SimpleNamespace(__name__=f"app_platform.db.migrations.{name}", run=run)


@pytest.mark.asyncio
async def test_migration_runner_records_only_pending_migrations() -> None:
    calls = []
    db = _MigrationDb(applied=["001_indexes"])
    modules = [_migration("001_indexes", calls), _migration("002_collections", calls)]

    applied = await migration_runner.run_pending_migrations(db, modules=modules)

    assert applied == ["002_collections"]
    assert calls == ["002_collections"]
    assert db.schema_migrations.created_indexes == [
        (("migration_id",), {"unique": True, "background": True})
    ]
    assert db.schema_migrations.inserted[0]["migration_id"] == "002_collections"


@pytest.mark.asyncio
async def test_production_startup_requires_mongo_url(monkeypatch) -> None:
    runtime.mongo_state.client = None
    runtime.mongo_state.db = None
    monkeypatch.setattr(
        runtime,
        "settings",
        SimpleNamespace(mongo_url="", db_name="iems_db", is_production=True),
    )

    with pytest.raises(RuntimeError, match="MONGO_URL is required in production"):
        await runtime._connect()


class _FakeDb:
    async def command(self, command):
        assert command == "ping"
        return {"ok": 1}


class _FakeClient:
    def __init__(self, *_args, database_names=None, **_kwargs):
        self.closed = False
        self._database_names = list(database_names or [])
        self.db = _FakeDb()

    def __getitem__(self, _name):
        return self.db

    async def list_database_names(self):
        return list(self._database_names)

    def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_production_startup_fails_when_database_is_missing(monkeypatch) -> None:
    clients = []

    async def _no_sleep(_seconds):
        return None

    def _client_factory(*args, **kwargs):
        client = _FakeClient(*args, database_names=["other_db"], **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(runtime, "AsyncIOMotorClient", _client_factory)
    monkeypatch.setattr(runtime.asyncio, "sleep", _no_sleep)
    runtime.mongo_state.client = None
    runtime.mongo_state.db = None
    monkeypatch.setattr(
        runtime,
        "settings",
        SimpleNamespace(mongo_url="mongodb://example", db_name="iems_db", is_production=True),
    )

    with pytest.raises(RuntimeError, match="MongoDB database 'iems_db' does not exist"):
        await runtime._connect()

    assert clients
    assert all(client.closed for client in clients)
    assert runtime.mongo_state.db is None


@pytest.mark.asyncio
async def test_post_connect_bootstrap_propagates_index_failures(monkeypatch) -> None:
    async def _migrations_ok(_db):
        return []

    async def _indexes_fail(_db):
        raise RuntimeError("index conflict")

    monkeypatch.setattr(runtime, "run_pending_migrations", _migrations_ok)
    monkeypatch.setattr(runtime, "_ensure_indexes", _indexes_fail)

    with pytest.raises(RuntimeError, match="index conflict"):
        await runtime._run_post_connect_bootstrap(object())
