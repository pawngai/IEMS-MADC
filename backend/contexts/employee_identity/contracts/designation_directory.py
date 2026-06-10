from __future__ import annotations


async def get_designation_name(db, *, code: str | None) -> str | None:
    normalized = str(code or "").strip()
    if not normalized or getattr(db, "designations", None) is None:
        return None
    row = await db.designations.find_one(
        {"code": normalized},
        {"_id": 0, "name": 1},
    )
    if not row:
        return None
    return row.get("name")
