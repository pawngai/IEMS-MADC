from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def migrate_service_event_records_to_service_book_records(db, *, dry_run: bool = True) -> dict[str, Any]:
    legacy_records = db.service_event_records
    legacy_streams = db.service_event_streams
    target_records = db.service_book_records
    target_streams = db.service_book_record_streams

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "records_seen": 0,
        "records_inserted": 0,
        "records_existing": 0,
        "streams_seen": 0,
        "streams_upserted": 0,
    }

    async for record in legacy_records.find({}, {"_id": 0}):
        summary["records_seen"] += 1
        service_record_id = record.get("service_event_id")
        if not service_record_id:
            continue
        existing = await target_records.find_one({"service_event_id": service_record_id}, {"_id": 1})
        if existing:
            summary["records_existing"] += 1
            continue
        if not dry_run:
            await target_records.insert_one(dict(record))
        summary["records_inserted"] += 1

    async for stream in legacy_streams.find({}, {"_id": 0}):
        summary["streams_seen"] += 1
        employee_id = stream.get("employee_id")
        if not employee_id:
            continue
        if not dry_run:
            await target_streams.update_one(
                {"employee_id": employee_id},
                {"$set": dict(stream)},
                upsert=True,
            )
        summary["streams_upserted"] += 1

    return summary


async def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy legacy service_event_* collections into Service Book record collections."
    )
    parser.add_argument("--mongo-uri", default=os.getenv("MONGO_URL") or os.getenv("MONGODB_URI"))
    parser.add_argument("--db-name", default=os.getenv("MONGO_DB") or os.getenv("MONGODB_DB") or "myiems")
    parser.add_argument("--write", action="store_true", help="Write changes. Defaults to dry-run.")
    args = parser.parse_args()

    if not args.mongo_uri:
        raise SystemExit("Missing --mongo-uri or MONGO_URL/MONGODB_URI")

    client = AsyncIOMotorClient(args.mongo_uri)
    try:
        summary = await migrate_service_event_records_to_service_book_records(
            client[args.db_name],
            dry_run=not args.write,
        )
        print(summary)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(_main())
