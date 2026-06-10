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
from backend.scripts.mongodb.employee_code_migration_support import (  # noqa: E402
    migrate_employee_codes_to_madc_format,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite employee codes to MADC-appointmentYear-typeInitial-serial and reseed year-scoped counters."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute the migration plan without writing database changes.",
    )
    return parser.parse_args()


async def run(*, dry_run: bool) -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await migrate_employee_codes_to_madc_format(db, dry_run=dry_run)
    finally:
        client.close()


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(run(dry_run=args.dry_run))
    print(json.dumps(result, indent=2))