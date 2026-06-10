from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from contexts.leave.domain.eligibility_backfill import build_leave_eligibility_backfill_update


async def run_backfill(*, mongo_uri: str, db_name: str, limit: int | None = None) -> None:
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    query = {"eligibility_context_version": {"$exists": False}}
    cursor = db.leave_applications.find(query, {"_id": 0}).sort("applied_at", 1)
    if limit:
        cursor = cursor.limit(limit)

    processed = 0
    review_required = 0

    async for record in cursor:
        update = build_leave_eligibility_backfill_update(record)
        await db.leave_applications.update_one({"id": record.get("id")}, update)
        processed += 1
        if update["$set"].get("eligibility_review_required"):
            review_required += 1

    print(f"Processed {processed} legacy leave records")
    print(f"Records flagged for review: {review_required}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill leave eligibility context markers on legacy leave records.")
    parser.add_argument("--mongo-uri", default=os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    parser.add_argument("--db-name", default=os.getenv("MONGODB_DB_NAME", "iems_db"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(run_backfill(mongo_uri=args.mongo_uri, db_name=args.db_name, limit=args.limit))


if __name__ == "__main__":
    main()