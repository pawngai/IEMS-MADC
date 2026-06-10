from __future__ import annotations

from typing import Any, Optional


async def insert_audit_log(
    db,
    audit_doc: dict[str, Any],
    *,
    source_event_id: str | None = None,
) -> None:
    if source_event_id:
        await db.audit_logs.update_one(
            {
                "source_event_id": source_event_id,
                "action": audit_doc.get("action"),
                "resource_type": audit_doc.get("resource_type"),
            },
            {"$setOnInsert": audit_doc},
            upsert=True,
        )
        return
    await db.audit_logs.insert_one(audit_doc)


async def list_audit_logs(
    db, query: dict[str, Any], *, limit: int
) -> list[dict[str, Any]]:
    cursor = db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(limit)


async def list_service_book_audit_logs(
    db, query: dict[str, Any], *, limit: int
) -> list[dict[str, Any]]:
    cursor = db.ledger_audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(limit)


async def count_audit_logs(db, query: Optional[dict[str, Any]] = None) -> int:
    return int(await db.audit_logs.count_documents(query or {}))


async def insert_immutable_audit_log(db, log_doc: dict[str, Any]) -> None:
    await db.immutable_audit_logs.insert_one(log_doc)


async def list_immutable_audit_logs(
    db, query: dict[str, Any], *, limit: int = 1000, sort_asc: bool = True
) -> list[dict[str, Any]]:
    sort_dir = 1 if sort_asc else -1
    cursor = (
        db.immutable_audit_logs.find(query, {"_id": 0})
        .sort("timestamp", sort_dir)
        .limit(limit)
    )
    return await cursor.to_list(limit)
