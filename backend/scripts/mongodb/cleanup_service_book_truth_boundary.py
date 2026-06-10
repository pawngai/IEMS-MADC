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
from backend.scripts.mongodb.service_book_truth_boundary_cleanup_support import (  # noqa: E402
    cleanup_service_book_truth_boundary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find or clean Service Book ledger rows that violate the approved Service Events truth boundary.",
    )
    parser.add_argument("--employee-id", help="Limit scan or cleanup to one employee_id.")
    parser.add_argument("--apply", action="store_true", help="Apply selected cleanup operations. Defaults to dry-run.")
    parser.add_argument(
        "--delete-non-truth",
        action="store_true",
        help="Delete legacy ServiceEventRecorded/document/lifecycle draft projections from service_book_entries.",
    )
    parser.add_argument(
        "--sanitize-payloads",
        action="store_true",
        help="Strip document/workflow fields from approved Service Event and allowed manual exception ledger payloads.",
    )
    args = parser.parse_args()
    validate_args(args, parser=parser)
    return args


def validate_args(args: argparse.Namespace, *, parser: argparse.ArgumentParser | None = None) -> None:
    if not args.apply:
        return
    if args.delete_non_truth or args.sanitize_payloads:
        return
    message = "--apply requires at least one operation: --delete-non-truth or --sanitize-payloads"
    if parser is not None:
        parser.error(message)
    raise ValueError(message)


async def run(args: argparse.Namespace) -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await cleanup_service_book_truth_boundary(
            db,
            dry_run=not args.apply,
            employee_id=args.employee_id,
            delete_non_truth=args.delete_non_truth,
            sanitize_payloads=args.sanitize_payloads,
        )
    finally:
        client.close()


if __name__ == "__main__":
    print(json.dumps(asyncio.run(run(parse_args())), indent=2))