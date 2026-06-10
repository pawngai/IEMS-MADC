from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app_platform.config.settings import settings  # noqa: E402
from scripts.mongodb.service_book_msgegis_cleanup_support import (  # noqa: E402
    cleanup_service_book_msgegis_data,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove historical MSGEGIS service book data from persisted MongoDB surfaces.",
    )
    parser.add_argument("--employee-id", help="Limit cleanup to one employee_id.")
    parser.add_argument("--apply", action="store_true", help="Apply the cleanup. Defaults to dry-run.")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await cleanup_service_book_msgegis_data(
            db,
            dry_run=not args.apply,
            employee_id=args.employee_id,
        )
    finally:
        client.close()


if __name__ == "__main__":
    print(json.dumps(asyncio.run(run(parse_args())), indent=2))