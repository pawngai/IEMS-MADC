from __future__ import annotations


async def run(db) -> None:
    existing = await db.list_collection_names()
    if "outbox_events" not in existing:
        await db.create_collection("outbox_events")
