"""One-off: align employee_identities with the current regular-form schema.

Unsets fields no longer owned by Employee Identity (now owned by Profile or
removed) and ensures the form-owned optional fields exist (null if missing).
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient


FIELDS_TO_UNSET = [
    "aadhaar_number",
    "current_department_id",
    "current_designation_id",
    "current_office_id",
    "reporting_officer_id",
    "date_of_initial_engagement",
    "employment_type",
    "employee_code_migration_marker",
    "status_effective_date",
    "status_remarks",
]

FORM_OPTIONAL_FIELDS = ["mobile_primary", "email_official"]


async def main() -> None:
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "iems_db")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    coll = db["employee_identities"]

    total = await coll.count_documents({})
    print(f"db={db_name} employee_identities={total}")

    now = datetime.now(timezone.utc).isoformat()
    strip = await coll.update_many(
        {},
        {
            "$unset": {field: "" for field in FIELDS_TO_UNSET},
            "$set": {"updated_at": now},
        },
    )
    print(f"strip: matched={strip.matched_count} modified={strip.modified_count}")

    for field in FORM_OPTIONAL_FIELDS:
        res = await coll.update_many(
            {field: {"$exists": False}},
            {"$set": {field: None}},
        )
        print(f"ensure {field}: matched={res.matched_count} modified={res.modified_count}")

    remaining_fields: set[str] = set()
    async for doc in coll.find({}, {}):
        remaining_fields.update(doc.keys())
    print(f"fields remaining: {sorted(remaining_fields)}")

    sample = await coll.find_one({}, {"_id": 0})
    print("sample after backfill:")
    for key, value in sorted(sample.items()):
        print(f"  {key!r}: {value!r}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
