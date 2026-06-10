from __future__ import annotations

from typing import Any

from fastapi import HTTPException


SENIORITY_COLLECTION = "seniority_lists"


def collection(db):
    return db[SENIORITY_COLLECTION]


async def insert_list(db, document: dict) -> dict:
    await collection(db).insert_one(document)
    document.pop("_id", None)
    return document


async def get_list(db, list_id: str) -> dict:
    doc = await collection(db).find_one({"list_id": list_id})
    if not doc:
        raise HTTPException(404, "Seniority list not found")
    return doc


async def list_lists(
    db,
    *,
    query: dict[str, Any],
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    total = await collection(db).count_documents(query)
    cursor = (
        collection(db)
        .find(query, {"_id": 0, "employees": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    items = await cursor.to_list(length=limit)
    return items, total


async def update_list(db, list_id: str, values: dict[str, Any]) -> None:
    await collection(db).update_one({"list_id": list_id}, {"$set": values})
