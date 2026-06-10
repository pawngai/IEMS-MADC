from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app_platform.config.settings import settings  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove orphaned Service Book records whose employee_id no longer exists in employee identity.",
    )
    parser.add_argument(
        "--employee-id",
        help="Limit cleanup to one employee_id.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect orphaned records without deleting anything.",
    )
    parser.add_argument(
        "--include-service-events",
        action="store_true",
        help="Also delete service_events rows for the orphaned employee_id set.",
    )
    return parser.parse_args()


async def _find_orphan_employee_ids(db, *, employee_id: str | None = None) -> list[str]:
    query = {"employee_id": employee_id} if employee_id else {}
    candidate_ids = [value for value in await db.service_book_entries.distinct("employee_id", query) if value]
    if not candidate_ids:
        return []

    identity_ids = set(
        value
        for value in await db.employee_identities.distinct(
            "employee_id",
            {"employee_id": {"$in": candidate_ids}},
        )
        if value
    )
    return sorted(candidate_id for candidate_id in candidate_ids if candidate_id not in identity_ids)


async def _build_employee_summary(db, *, employee_id: str) -> dict:
    workflow_states = Counter()
    schema_keys = Counter()
    active_entry_count = 0

    cursor = db.service_book_entries.find(
        {"employee_id": employee_id},
        {"_id": 0, "workflow_state": 1, "schema_key": 1, "is_active": 1},
    )
    async for entry in cursor:
        state = str(entry.get("workflow_state") or "UNKNOWN").upper()
        schema_key = str(entry.get("schema_key") or "UNKNOWN").upper()
        workflow_states[state] += 1
        schema_keys[schema_key] += 1
        if entry.get("is_active"):
            active_entry_count += 1

    return {
        "employee_id": employee_id,
        "service_book_entries": await db.service_book_entries.count_documents({"employee_id": employee_id}),
        "active_service_book_entries": active_entry_count,
        "service_book_part_projections": await db.service_book_part_projections.count_documents({"employee_id": employee_id}),
        "workflow_states": dict(sorted(workflow_states.items())),
        "schema_keys": dict(sorted(schema_keys.items())),
        "service_events": await db.service_events.count_documents({"employee_id": employee_id}),
    }


async def run(*, employee_id: str | None, dry_run: bool, include_service_events: bool) -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        orphan_employee_ids = await _find_orphan_employee_ids(db, employee_id=employee_id)
        summaries = [await _build_employee_summary(db, employee_id=value) for value in orphan_employee_ids]

        result = {
            "dry_run": dry_run,
            "include_service_events": include_service_events,
            "orphan_employee_count": len(orphan_employee_ids),
            "employees": summaries,
            "deleted": {
                "service_book_entries": 0,
                "service_book_part_projections": 0,
                "service_events": 0,
            },
        }

        if dry_run or not orphan_employee_ids:
            return result

        query = {"employee_id": {"$in": orphan_employee_ids}}
        result["deleted"]["service_book_entries"] = (
            await db.service_book_entries.delete_many(query)
        ).deleted_count
        result["deleted"]["service_book_part_projections"] = (
            await db.service_book_part_projections.delete_many(query)
        ).deleted_count

        if include_service_events:
            result["deleted"]["service_events"] = (
                await db.service_events.delete_many(query)
            ).deleted_count

        return result
    finally:
        client.close()


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(
        run(
            employee_id=args.employee_id,
            dry_run=args.dry_run,
            include_service_events=args.include_service_events,
        )
    )
    print(json.dumps(result, indent=2))