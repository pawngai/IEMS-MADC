from __future__ import annotations

import pytest

from app_platform.db.runtime import _quarantine_duplicate_compound_keys


class _AsyncRows:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __aiter__(self):
        self._iter = iter(self._rows)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class _FindResult:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def sort(self, field: str, direction: int):
        self._rows = sorted(self._rows, key=lambda row: row[field], reverse=direction < 0)
        return self

    async def to_list(self, length=None):
        return list(self._rows)


class _Collection:
    def __init__(self, docs: list[dict]) -> None:
        self.docs = docs

    def aggregate(self, pipeline):
        return _AsyncRows(
            [
                {
                    "_id": {"name": "Event", "event_version": "v1", "idempotency_key": "key-1"},
                    "count": 2,
                }
            ]
        )

    def find(self, query: dict):
        return _FindResult(
            [
                doc
                for doc in self.docs
                if all(doc.get(field) == value for field, value in query.items())
            ]
        )

    async def delete_many(self, query: dict):
        ids = set(query.get("_id", {}).get("$in", []))
        self.docs = [doc for doc in self.docs if doc.get("_id") not in ids]


class _Quarantine:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    async def insert_many(self, docs: list[dict]):
        self.docs.extend(docs)


class _Db:
    def __init__(self) -> None:
        self.event_duplicate_quarantine = _Quarantine()


@pytest.mark.asyncio
async def test_duplicate_compound_keys_are_quarantined_before_unique_index() -> None:
    db = _Db()
    collection = _Collection(
        [
            {"_id": 1, "name": "Event", "event_version": "v1", "idempotency_key": "key-1"},
            {"_id": 2, "name": "Event", "event_version": "v1", "idempotency_key": "key-1"},
        ]
    )

    await _quarantine_duplicate_compound_keys(
        collection,
        db=db,
        collection_name="outbox_events",
        fields=["name", "event_version", "idempotency_key"],
        partial_field="idempotency_key",
    )

    assert [doc["_id"] for doc in collection.docs] == [1]
    assert len(db.event_duplicate_quarantine.docs) == 1
    assert db.event_duplicate_quarantine.docs[0]["document"]["_id"] == 2