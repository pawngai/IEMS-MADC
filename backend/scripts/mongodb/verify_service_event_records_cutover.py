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
    verify_service_event_records_cutover,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify ServiceEvents normalized records cover the legacy stream projection.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 if any verification check fails.",
    )
    return parser.parse_args()


async def run() -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await verify_service_event_records_cutover(db)
    finally:
        client.close()


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(run())
    print(json.dumps(result, indent=2))
    if args.fail_on_error and not result.get("ok", False):
        raise SystemExit(1)
