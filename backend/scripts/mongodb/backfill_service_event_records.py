from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
BACKEND_ROOT = os.path.join(ROOT, "backend")
for path in (ROOT, BACKEND_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from app_platform.config.settings import settings  # noqa: E402
from backend.scripts.mongodb.service_event_records_backfill_support import (  # noqa: E402
    backfill_service_event_records,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill normalized service_event_records from legacy service_events streams.",
    )
    parser.add_argument(
        "--employee-id",
        help="Limit the backfill to one employee_id.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute the migration plan without writing database changes.",
    )
    return parser.parse_args()


async def run(*, employee_id: str | None, dry_run: bool) -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await backfill_service_event_records(
            db,
            employee_id=employee_id,
            dry_run=dry_run,
        )
    finally:
        client.close()


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(run(employee_id=args.employee_id, dry_run=args.dry_run))
    print(json.dumps(result, indent=2))
