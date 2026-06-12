from __future__ import annotations

from typing import Any

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.service_book.contracts.servicebook.revisions import REVISION_COLLECTION


class MongoServiceBookRevisionRepository:
    def __init__(self, *, db) -> None:
        assert_collection_ownership(
            context="service_book",
            collection_name=REVISION_COLLECTION,
            write=True,
        )
        self._db = db

    async def get_latest_revision(self, *, entry_id: str) -> dict[str, Any] | None:
        return await self._db[REVISION_COLLECTION].find_one(
            {"entry_id": entry_id},
            {"_id": 0},
            sort=[("revision_number", -1)],
        )

    async def insert_revision(self, revision: dict[str, Any]) -> None:
        await self._db[REVISION_COLLECTION].insert_one(revision)
