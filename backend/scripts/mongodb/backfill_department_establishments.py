from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app_platform.config.settings import settings  # noqa: E402
from backend.scripts.mongodb.department_establishment_backfill_support import (  # noqa: E402
    backfill_department_establishments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill legacy department sanctioned strength into department_establishments.",
    )
    parser.add_argument(
        "--department-code",
        help="Limit the backfill to one department code.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute the migration plan without writing database changes.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing department_establishments instead of skipping them.",
    )
    return parser.parse_args()


async def run(*, department_code: str | None, dry_run: bool, overwrite: bool) -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await backfill_department_establishments(
            db,
            department_code=department_code,
            dry_run=dry_run,
            overwrite=overwrite,
        )
    finally:
        client.close()


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(
        run(
            department_code=args.department_code,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
        )
    )
    print(json.dumps(result, indent=2))