from __future__ import annotations

from datetime import datetime, timezone


async def _find_duplicate_compound_keys(collection, *, fields: list[str], partial_field: str) -> list[dict]:
    group_id = {field: f"${field}" for field in fields}
    cursor = collection.aggregate(
        [
            {"$match": {partial_field: {"$type": "string"}}},
            {"$group": {"_id": group_id, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}},
        ]
    )
    return [row async for row in cursor]


async def _quarantine_duplicate_compound_keys(
    db,
    collection,
    *,
    collection_name: str,
    fields: list[str],
    partial_field: str,
) -> None:
    duplicate_rows = await _find_duplicate_compound_keys(
        collection,
        fields=fields,
        partial_field=partial_field,
    )
    if not duplicate_rows:
        return

    quarantined_at = datetime.now(timezone.utc).isoformat()
    quarantine = db.event_duplicate_quarantine
    for row in duplicate_rows:
        key = row.get("_id") or {}
        docs = await collection.find({field: key.get(field) for field in fields}).sort("_id", 1).to_list(length=None)
        duplicate_docs = docs[1:]
        if not duplicate_docs:
            continue
        await quarantine.insert_many(
            [
                {
                    "quarantined_at": quarantined_at,
                    "source_collection": collection_name,
                    "unique_fields": fields,
                    "duplicate_key": key,
                    "document": doc,
                }
                for doc in duplicate_docs
            ]
        )
        await collection.delete_many({"_id": {"$in": [doc["_id"] for doc in duplicate_docs if "_id" in doc]}})


async def run(db) -> None:
    await db.outbox_events.create_index("status", background=True)
    await db.outbox_events.create_index("occurred_at", background=True)
    await db.outbox_events.create_index("locked_until", background=True)
    await db.outbox_events.create_index("next_attempt_at", background=True)
    await _quarantine_duplicate_compound_keys(
        db,
        db.outbox_events,
        collection_name="outbox_events",
        fields=["name", "event_version", "idempotency_key"],
        partial_field="idempotency_key",
    )
    await db.outbox_events.create_index(
        [("name", 1), ("event_version", 1), ("idempotency_key", 1)],
        unique=True,
        partialFilterExpression={"idempotency_key": {"$type": "string"}},
        background=True,
        name="outbox_idempotency_unique",
    )
    await _quarantine_duplicate_compound_keys(
        db,
        db.audit_logs,
        collection_name="audit_logs",
        fields=["source_event_id", "action", "resource_type"],
        partial_field="source_event_id",
    )
    await db.audit_logs.create_index(
        [("source_event_id", 1), ("action", 1), ("resource_type", 1)],
        unique=True,
        partialFilterExpression={"source_event_id": {"$type": "string"}},
        background=True,
        name="audit_source_event_unique",
    )
    await _quarantine_duplicate_compound_keys(
        db,
        db.notifications,
        collection_name="notifications",
        fields=["source_event_id", "type", "employee_id"],
        partial_field="source_event_id",
    )
    await db.notifications.create_index(
        [("source_event_id", 1), ("type", 1), ("employee_id", 1)],
        unique=True,
        partialFilterExpression={"source_event_id": {"$type": "string"}},
        background=True,
        name="notification_source_event_unique",
    )
    await _quarantine_duplicate_compound_keys(
        db,
        db.service_book_entries,
        collection_name="service_book_entries",
        fields=["source_event_id", "event_name"],
        partial_field="source_event_id",
    )
    await db.service_book_entries.create_index(
        [("source_event_id", 1), ("event_name", 1)],
        unique=True,
        partialFilterExpression={"source_event_id": {"$type": "string"}},
        background=True,
        name="service_book_source_event_unique",
    )
    await db.event_duplicate_quarantine.create_index(
        [("source_collection", 1), ("quarantined_at", -1)],
        background=True,
    )
