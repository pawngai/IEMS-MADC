"""One-shot migration: drop the legacy ``uploaded_by`` alias from
``document_metadata`` rows. For each row that has ``uploaded_by`` but not
``uploaded_by_user_id``, copy the value across; then ``$unset`` ``uploaded_by``
on every row. Safe to re-run.
"""
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

COLLECTION = "document_metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Drop the legacy uploaded_by alias from document metadata.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without writing changes.",
    )
    return parser.parse_args()


async def run(*, dry_run: bool) -> dict:
    if not settings.mongo_url:
        raise RuntimeError("MONGO_URL is required")

    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    try:
        return await drop_uploaded_by_alias(db, dry_run=dry_run)
    finally:
        client.close()


async def drop_uploaded_by_alias(db, *, dry_run: bool = False) -> dict:
    collection = db[COLLECTION]
    needs_copy = await collection.count_documents(
        {"uploaded_by": {"$exists": True}, "uploaded_by_user_id": {"$in": [None, ""]}}
    )
    needs_copy_missing = await collection.count_documents(
        {"uploaded_by": {"$exists": True}, "uploaded_by_user_id": {"$exists": False}}
    )
    total_with_alias = await collection.count_documents({"uploaded_by": {"$exists": True}})

    plan = {
        "collection": COLLECTION,
        "total_with_alias": total_with_alias,
        "rows_needing_value_copy": needs_copy + needs_copy_missing,
        "dry_run": dry_run,
    }

    if dry_run or total_with_alias == 0:
        return plan

    # Step 1 — copy uploaded_by → uploaded_by_user_id wherever the canonical
    # field is missing or blank.
    copy_result = await collection.update_many(
        {
            "uploaded_by": {"$exists": True, "$ne": None, "$ne": ""},
            "$or": [
                {"uploaded_by_user_id": {"$exists": False}},
                {"uploaded_by_user_id": None},
                {"uploaded_by_user_id": ""},
            ],
        },
        [{"$set": {"uploaded_by_user_id": "$uploaded_by"}}],
    )

    # Step 2 — strip the alias from every row.
    unset_result = await collection.update_many(
        {"uploaded_by": {"$exists": True}},
        {"$unset": {"uploaded_by": ""}},
    )

    plan.update(
        {
            "rows_value_copied": getattr(copy_result, "modified_count", 0),
            "rows_alias_unset": getattr(unset_result, "modified_count", 0),
        }
    )
    return plan


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(run(dry_run=args.dry_run))
    print(json.dumps(result, indent=2))
