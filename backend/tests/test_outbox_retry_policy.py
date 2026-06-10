from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app_platform.outbox.model import OutboxStatus
from app_platform.outbox.repo import OutboxRepository


class _FakeCursor:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    async def to_list(self, length: int):
        return self._rows[:length]


class _FakeOutboxCollection:
    def __init__(self, doc: dict) -> None:
        self.doc = dict(doc)
        self.find_query: dict | None = None
        self.update_query: dict | None = None
        self.update_doc: dict | None = None

    def find(self, query: dict):
        self.find_query = query
        return _FakeCursor([self.doc])

    async def find_one(self, query: dict, projection: dict | None = None):
        if query.get("_id") == self.doc.get("_id"):
            return {"attempts": self.doc.get("attempts", 0)}
        return None

    async def update_one(self, query: dict, update: dict, **_kwargs):
        self.update_query = query
        self.update_doc = update
        self.doc.update((update or {}).get("$set") or {})
        self.doc["attempts"] = int(self.doc.get("attempts") or 0) + int(
            ((update or {}).get("$inc") or {}).get("attempts") or 0
        )


class _FakeDb:
    def __init__(self, doc: dict) -> None:
        self.outbox_events = _FakeOutboxCollection(doc)


@pytest.mark.asyncio
async def test_get_pending_excludes_dead_letters_and_honors_retry_gate() -> None:
    db = _FakeDb(
        {
            "_id": "evt-retry",
            "status": OutboxStatus.FAILED.value,
            "attempts": 2,
            "next_attempt_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    repo = OutboxRepository(db)

    await repo.get_pending(batch_size=10, max_attempts=5)

    query = db.outbox_events.find_query or {}
    assert OutboxStatus.DEAD_LETTER.value not in query["status"]["$in"]
    assert "next_attempt_at" in str(query)
    assert "attempts" in str(query)


@pytest.mark.asyncio
async def test_mark_failed_dead_letters_after_max_attempts() -> None:
    db = _FakeDb({"_id": "evt-poison", "attempts": 4})
    repo = OutboxRepository(db)

    await repo.mark_failed("evt-poison", "boom", max_attempts=5)

    update = db.outbox_events.update_doc or {}
    assert update["$set"]["status"] == OutboxStatus.DEAD_LETTER.value
    assert update["$set"]["next_attempt_at"] is None
    assert update["$inc"] == {"attempts": 1}


@pytest.mark.asyncio
async def test_mark_failed_sets_next_attempt_before_dead_letter() -> None:
    db = _FakeDb({"_id": "evt-transient", "attempts": 1})
    repo = OutboxRepository(db)

    await repo.mark_failed("evt-transient", "temporary", max_attempts=5)

    update = db.outbox_events.update_doc or {}
    assert update["$set"]["status"] == OutboxStatus.FAILED.value
    assert update["$set"]["next_attempt_at"]
    assert update["$inc"] == {"attempts": 1}