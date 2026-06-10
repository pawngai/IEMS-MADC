"""Repository for the ``document_audit_timeline`` read model.

Each row is one timeline entry for one document, keyed by ``source_event_id``
for idempotent projection. Subscribers project document events into this
collection so the per-document audit endpoint can return a single sorted
stream without re-querying the outbox.
"""
from __future__ import annotations

from typing import Any

COLLECTION = "document_audit_timeline"


class DocumentAuditTimelineRepository:
    _indexed_db_keys: set[int] = set()

    def __init__(self, *, db) -> None:
        from app_platform.domain_separation.data_ownership import assert_collection_ownership

        self._db = db
        assert_collection_ownership(
            context="documents", collection_name=COLLECTION, write=True,
        )

    async def ensure_indexes(self) -> None:
        if self._db is None:
            return
        db_key = id(self._db)
        if db_key in self._indexed_db_keys:
            return
        collection = self._db[COLLECTION]
        if not hasattr(collection, "create_index"):
            return
        await collection.create_index(
            [("source_event_id", 1)],
            unique=True,
            background=True,
        )
        await collection.create_index(
            [("document_id", 1), ("occurred_at", -1)],
            background=True,
        )
        await collection.create_index(
            [("filename", 1), ("occurred_at", -1)],
            background=True,
        )
        self._indexed_db_keys.add(db_key)

    async def append(self, entry: dict[str, Any]) -> None:
        if self._db is None:
            return
        await self.ensure_indexes()
        source_event_id = entry.get("source_event_id")
        if not source_event_id:
            return
        await self._db[COLLECTION].update_one(
            {"source_event_id": source_event_id},
            {"$setOnInsert": entry},
            upsert=True,
        )

    async def list_for_document(
        self,
        *,
        document_id: str | None = None,
        filename: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if self._db is None:
            return []
        await self.ensure_indexes()
        query: dict[str, Any] = {}
        if document_id:
            query["document_id"] = document_id
        elif filename:
            query["filename"] = filename
        else:
            return []
        cursor = (
            self._db[COLLECTION]
            .find(query, {"_id": 0})
            .sort("occurred_at", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)
