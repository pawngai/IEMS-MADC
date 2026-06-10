from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def opening_collection(db):
    collection = getattr(db, "service_book_openings", None)
    if collection is None:
        raise HTTPException(status_code=500, detail="service_book_openings collection is not configured")
    return collection


async def find_opening(db, employee_id: str) -> dict | None:
    return await opening_collection(db).find_one({"employee_id": employee_id}, {"_id": 0})


async def list_openings(db, *, query: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    cursor = opening_collection(db).find(query, {"_id": 0}).sort("updated_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


async def save_opening(db, document: dict) -> dict:
    set_fields = dict(document)
    created_at = set_fields.pop("created_at", None)
    await opening_collection(db).update_one(
        {"employee_id": document["employee_id"]},
        {"$set": set_fields, "$setOnInsert": {"created_at": created_at}},
        upsert=True,
    )
    return await find_opening(db, document["employee_id"]) or document
