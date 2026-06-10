from __future__ import annotations

from typing import Any

from app_platform.domain_separation.data_ownership import assert_collection_ownership


SUMMARY_COLLECTION = "employee_service_summaries"


class EmployeeServiceSummaryRepository:
    def __init__(self, *, db) -> None:
        assert_collection_ownership(
            context="service_book",
            collection_name=SUMMARY_COLLECTION,
            write=True,
        )
        self._db = db

    @property
    def _collection(self):
        collection = getattr(self._db, SUMMARY_COLLECTION, None)
        if collection is not None:
            return collection
        try:
            return self._db[SUMMARY_COLLECTION]
        except (KeyError, TypeError, AttributeError):
            return None

    async def get_summary(self, *, employee_id: str) -> dict[str, Any] | None:
        collection = self._collection
        if collection is None:
            return None
        return await collection.find_one({"employee_id": employee_id}, {"_id": 0})

    async def upsert_summary(self, *, employee_id: str, summary: dict[str, Any]) -> dict[str, Any]:
        document = {"employee_id": employee_id, **summary}
        collection = self._collection
        if collection is None:
            raise RuntimeError("Database handle is missing employee_service_summaries")
        await collection.update_one(
            {"employee_id": employee_id},
            {"$set": document},
            upsert=True,
        )
        return document
