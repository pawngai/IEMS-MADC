from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from app_platform.reference_data.contracts.employment_type_master import (
    eligibility_from_master,
    get_employment_type_master,
    normalize_employment_type_code,
)
from contexts.service_book.records.repository.service_summary_repository import (
    EmployeeServiceSummaryRepository,
)
from shared_kernel.events import utc_now_iso


LEGACY_WARNING = "CREATED_FROM_LEGACY_IDENTITY_FIELDS"


def _legacy_employment_type(identity: dict[str, Any]) -> str | None:
    return normalize_employment_type_code(
        identity.get("employment_type_code") or identity.get("employment_type")
    )


def build_summary_from_legacy_identity(identity: dict[str, Any]) -> dict[str, Any] | None:
    employment_type_code = _legacy_employment_type(identity)
    master = get_employment_type_master(employment_type_code)
    if not master:
        return None

    service_status = str(identity.get("service_status") or "").strip().upper()
    if not service_status:
        service_status = "IN_SERVICE" if master["employment_class"] == "REGULAR" else "ENGAGED"

    return {
        "employee_id": identity["employee_id"],
        "current_post_id": identity.get("post_id") or identity.get("current_post_id"),
        "current_department_id": identity.get("department_id") or identity.get("current_department_id"),
        "current_office_id": identity.get("office_id") or identity.get("current_office_id"),
        "current_designation_id": identity.get("designation_id") or identity.get("current_designation_id"),
        "current_service_id": identity.get("service_id") or identity.get("current_service_id"),
        "current_employment_type_code": master["employment_type_code"],
        "current_employment_class": master["employment_class"],
        "current_service_status": service_status,
        "current_pay_level_code": identity.get("pay_level") or identity.get("pay_level_code"),
        "current_service_group_code": identity.get("service_group_code"),
        **eligibility_from_master(master),
        "source_record_id": None,
        "last_projected_at": utc_now_iso(),
        "projection_warnings": [LEGACY_WARNING],
    }


async def backfill(*, mongo_uri: str, database_name: str, dry_run: bool) -> dict[str, int]:
    client = AsyncIOMotorClient(mongo_uri)
    db = client[database_name]
    repository = EmployeeServiceSummaryRepository(db=db)
    stats = {"scanned": 0, "projected": 0, "skipped": 0}

    cursor = db.employee_identities.find(
        {
            "$or": [
                {"employment_type": {"$exists": True, "$ne": None}},
                {"employment_type_code": {"$exists": True, "$ne": None}},
            ]
        },
        {"_id": 0},
    )
    async for identity in cursor:
        stats["scanned"] += 1
        if not identity.get("employee_id"):
            stats["skipped"] += 1
            continue
        summary = build_summary_from_legacy_identity(identity)
        if summary is None:
            stats["skipped"] += 1
            continue
        if not dry_run:
            await repository.upsert_summary(employee_id=identity["employee_id"], summary=summary)
        stats["projected"] += 1

    client.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill employee_service_summaries from legacy identity fields.")
    parser.add_argument("--mongo-uri", default=os.getenv("MONGO_URL") or os.getenv("MONGODB_URI") or "mongodb://localhost:27017")
    parser.add_argument("--database", default=os.getenv("DB_NAME") or os.getenv("MONGO_DB") or "myiems")
    parser.add_argument("--apply", action="store_true", help="Write summaries. Without this flag the script is dry-run only.")
    args = parser.parse_args()

    stats = asyncio.run(backfill(
        mongo_uri=args.mongo_uri,
        database_name=args.database,
        dry_run=not args.apply,
    ))
    mode = "APPLY" if args.apply else "DRY_RUN"
    print({"mode": mode, **stats})


if __name__ == "__main__":
    main()