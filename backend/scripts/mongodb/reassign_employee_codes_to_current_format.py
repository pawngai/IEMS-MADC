"""One-off: reassign employee_code to the current MADC-NNNN format.

Sorts employee_identities by created_at ascending and assigns MADC-0001..
Updates employee_profiles to keep the denormalised code in sync.
Sets the counters.employee_code seq to the highest assigned sequence.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from contexts.employee_master.identity.domain.employee_code import format_employee_code


async def main() -> None:
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "iems_db")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    identities = db["employee_identities"]
    profiles = db["employee_profiles"]
    counters = db["counters"]

    now = datetime.now(timezone.utc).isoformat()
    docs = []
    async for d in identities.find({}, {"employee_id": 1, "employee_code": 1, "created_at": 1}).sort("created_at", 1):
        docs.append(d)
    print(f"employee_identities: {len(docs)}")

    year = datetime.now(timezone.utc).year
    assignments = []
    for seq, doc in enumerate(docs, start=1):
        new_code = format_employee_code(year=year, employment_type="IDENTITY", sequence=seq)
        assignments.append((doc["employee_id"], doc.get("employee_code"), new_code))

    for employee_id, old_code, new_code in assignments:
        await identities.update_one(
            {"employee_id": employee_id},
            {"$set": {"employee_code": new_code, "updated_at": now}},
        )
        prof_res = await profiles.update_many(
            {"employee_id": employee_id},
            {"$set": {"employee_code": new_code, "updated_at": now}},
        )
        print(f"{employee_id}: {old_code} -> {new_code} (profiles matched={prof_res.matched_count})")

    max_seq = len(assignments)
    await counters.update_one(
        {"_id": "employee_code"},
        {"$set": {"seq": max_seq}},
        upsert=True,
    )
    counter = await counters.find_one({"_id": "employee_code"})
    print(f"counter set to: {counter}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
