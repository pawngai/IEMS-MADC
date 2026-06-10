"""Repository for the ``document_retention_policies`` collection."""
from __future__ import annotations

from typing import Any

from contexts.documents.domain.retention import ANY, RetentionPolicy

COLLECTION = "document_retention_policies"


class RetentionPolicyRepository:
    def __init__(self, *, db) -> None:
        from app_platform.domain_separation.data_ownership import assert_collection_ownership

        self._db = db
        assert_collection_ownership(
            context="documents", collection_name=COLLECTION, write=True,
        )

    async def list_active(self) -> list[RetentionPolicy]:
        if self._db is None:
            return []
        cursor = self._db[COLLECTION].find({"active": True}, {"_id": 0})
        rows: list[dict[str, Any]] = await cursor.to_list(length=1000)
        return [self._to_policy(row) for row in rows if row.get("key")]

    async def upsert(self, policy: RetentionPolicy, *, active: bool = True) -> None:
        if self._db is None:
            return
        await self._db[COLLECTION].update_one(
            {"key": policy.key},
            {
                "$set": {
                    "key": policy.key,
                    "document_type": policy.document_type,
                    "category": policy.category,
                    "source_context": policy.source_context,
                    "archive_after_days": policy.archive_after_days,
                    "delete_after_archive_days": policy.delete_after_archive_days,
                    "requires_legal_hold_release": policy.requires_legal_hold_release,
                    "active": active,
                }
            },
            upsert=True,
        )

    @staticmethod
    def _to_policy(row: dict[str, Any]) -> RetentionPolicy:
        return RetentionPolicy(
            key=str(row.get("key")),
            document_type=str(row.get("document_type") or ANY),
            category=str(row.get("category") or ANY),
            source_context=str(row.get("source_context") or ANY),
            archive_after_days=row.get("archive_after_days"),
            delete_after_archive_days=row.get("delete_after_archive_days"),
            requires_legal_hold_release=bool(row.get("requires_legal_hold_release")),
        )
