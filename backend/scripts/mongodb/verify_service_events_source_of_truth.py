from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
BACKEND_ROOT = os.path.join(ROOT, "backend")
for path in (ROOT, BACKEND_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from app_platform.config.settings import settings  # noqa: E402


async def _count(collection, query: dict) -> int:
    return await collection.count_documents(query)


async def verify_service_events_source_of_truth(db) -> dict:
    approved_query = {"status": "APPROVED", "is_voided": {"$ne": True}}
    approved_records = await db.service_event_records.find(
        approved_query,
        {
            "_id": 0,
            "employee_id": 1,
            "service_event_id": 1,
            "event_type": 1,
            "order_number": 1,
            "order_date": 1,
            "issuing_authority": 1,
        },
    ).to_list(length=100000)

    ids = [str(row.get("service_event_id") or "") for row in approved_records]
    duplicate_ids = sorted(
        event_id for event_id, count in Counter(ids).items() if event_id and count > 1
    )
    missing_order_metadata = [
        row
        for row in approved_records
        if not row.get("order_number")
        or not row.get("order_date")
        or not row.get("issuing_authority")
    ]

    projected_ids = {
        str(row.get("source_event_id") or "")
        for row in await db.service_book_entries.find(
            {"source_event_id": {"$exists": True}},
            {"_id": 0, "source_event_id": 1},
        ).to_list(length=100000)
    }
    approved_ids = {event_id for event_id in ids if event_id}
    missing_projection_ids = sorted(
        event_id for event_id in approved_ids if event_id not in projected_ids
    )
    stale_projection_ids = sorted(
        event_id for event_id in projected_ids if event_id and event_id not in approved_ids
    )

    result = {
        "approved_event_count": len(approved_records),
        "service_book_projected_event_count": len(projected_ids),
        "duplicate_event_ids": duplicate_ids,
        "missing_order_metadata_count": len(missing_order_metadata),
        "missing_order_metadata_examples": missing_order_metadata[:25],
        "missing_projection_count": len(missing_projection_ids),
        "missing_projection_ids": missing_projection_ids[:100],
        "stale_projection_count": len(stale_projection_ids),
        "stale_projection_ids": stale_projection_ids[:100],
        "legacy_service_book_workflow_entries": await _count(
            db.service_book_workflow_entries,
            {"is_active": True},
        ),
    }
    result["ok"] = (
        not result["duplicate_event_ids"]
        and result["missing_order_metadata_count"] == 0
        and result["missing_projection_count"] == 0
        and result["stale_projection_count"] == 0
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify ServiceEvents are the source of truth for ServiceBook projections.",
    )
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


async def run() -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await verify_service_events_source_of_truth(db)
    finally:
        client.close()


if __name__ == "__main__":
    args = parse_args()
    report = asyncio.run(run())
    print(json.dumps(report, indent=2, default=str))
    if args.fail_on_error and not report.get("ok", False):
        raise SystemExit(1)
