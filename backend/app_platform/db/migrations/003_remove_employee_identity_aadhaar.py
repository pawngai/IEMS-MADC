from __future__ import annotations


def _normalize_index_key(key) -> tuple[tuple[str, int], ...]:
    return tuple((str(name), int(direction)) for name, direction in (key or []))


async def _drop_employee_identity_aadhaar_indexes(collection) -> None:
    expected_key = (("aadhaar_number", 1),)
    index_info = await collection.index_information()
    for index_name, metadata in index_info.items():
        if _normalize_index_key(metadata.get("key")) == expected_key:
            await collection.drop_index(index_name)


async def run(db) -> None:
    await db.employee_identities.update_many(
        {"aadhaar_number": {"$exists": True}},
        {"$unset": {"aadhaar_number": ""}},
    )
    await _drop_employee_identity_aadhaar_indexes(db.employee_identities)