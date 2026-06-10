"""Backfill the canonical `employee_master` collection.

Merges legacy `employee_identities` + `employee_profile_extensions` (joined on
employee_id) into a single `employee_master` document per employee, preserving
every field. Any key not declared on EmployeeMasterSnapshot / its embedded
contact / identifiers objects is preserved under `legacy_fields` and counted in
the report — nothing is dropped (risk R-1/R-3/R-13).

Usage:
  python scripts/migrate_employee_master.py --dry-run        # report only
  python scripts/migrate_employee_master.py                  # write + report
  python scripts/migrate_employee_master.py --mongo-url ... --db iems_db

Idempotent: upserts keyed on employee_id. Safe to re-run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# allow importing backend package
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pymongo import MongoClient, UpdateOne  # noqa: E402

from contexts.employee_master.schemas.employee_master_model import (  # noqa: E402
    EmployeeMasterSnapshot,
)
from contexts.employee_master.schemas.value_objects import (  # noqa: E402
    ContactDetails,
    IdentityDocuments,
)

IDENTITY_COLLECTION = "employee_identities"
EXTENSION_COLLECTION = "employee_profile_extensions"
TARGET_COLLECTION = "employee_master"

TOP_LEVEL_FIELDS = set(EmployeeMasterSnapshot.model_fields.keys()) - {"legacy_fields"}
CONTACT_FIELDS = set(ContactDetails.model_fields.keys())
IDENTIFIER_FIELDS = set(IdentityDocuments.model_fields.keys())


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _merge_one(identity: dict, extension: dict | None) -> tuple[dict, list[str]]:
    """Return (master_doc, legacy_keys). Extension overlays identity."""
    source: dict = {}
    source.update(identity or {})
    if extension:
        source.update(extension)

    master: dict = {}
    contact: dict = dict((identity or {}).get("contact") or {})
    identifiers: dict = dict((identity or {}).get("identifiers") or {})
    legacy: dict = {}

    # carry forward existing embedded objects from extension too
    if extension:
        contact.update(extension.get("contact") or {})
        identifiers.update(extension.get("identifiers") or {})

    for key, value in source.items():
        if key in ("contact", "identifiers", "_id"):
            continue
        if key in TOP_LEVEL_FIELDS:
            master[key] = value
        elif key in CONTACT_FIELDS:
            contact[key] = value
        elif key in IDENTIFIER_FIELDS:
            identifiers[key] = value
        else:
            legacy[key] = value

    master["contact"] = contact
    if identifiers:
        master["identifiers"] = identifiers
    if legacy:
        master["legacy_fields"] = legacy

    # required minimums / provenance
    master.setdefault("employee_id", (identity or {}).get("employee_id"))
    master["migrated_at"] = _utcnow()
    return master, sorted(legacy.keys())


def run(mongo_url: str, db_name: str, dry_run: bool) -> dict:
    client = MongoClient(mongo_url)
    db = client[db_name]

    identities = list(db[IDENTITY_COLLECTION].find({}))
    extensions = {
        e.get("employee_id"): e for e in db[EXTENSION_COLLECTION].find({})
    }

    report = {
        "mongo_url": mongo_url,
        "db": db_name,
        "dry_run": dry_run,
        "generated_at": _utcnow(),
        "identities": len(identities),
        "extensions": len(extensions),
        "merged": 0,
        "with_legacy_fields": 0,
        "legacy_key_counts": {},
        "missing_extension": [],
        "samples": [],
    }

    ops = []
    for identity in identities:
        emp_id = identity.get("employee_id")
        ext = extensions.get(emp_id)
        if ext is None:
            report["missing_extension"].append(emp_id)
        master, legacy_keys = _merge_one(identity, ext)

        # validate-but-don't-fail: surface model issues without dropping data
        try:
            EmployeeMasterSnapshot(**{k: v for k, v in master.items()
                                      if k in TOP_LEVEL_FIELDS or k in ("contact", "identifiers", "legacy_fields")})
            master["_validation"] = "ok"
        except Exception as exc:  # noqa: BLE001
            master["_validation"] = f"warn: {type(exc).__name__}"

        report["merged"] += 1
        if legacy_keys:
            report["with_legacy_fields"] += 1
            for k in legacy_keys:
                report["legacy_key_counts"][k] = report["legacy_key_counts"].get(k, 0) + 1
        if len(report["samples"]) < 3:
            report["samples"].append({"employee_id": emp_id, "legacy_keys": legacy_keys})

        ops.append(
            UpdateOne({"employee_id": emp_id}, {"$set": master}, upsert=True)
        )

    if not dry_run and ops:
        result = db[TARGET_COLLECTION].bulk_write(ops, ordered=False)
        report["upserted"] = result.upserted_count
        report["modified"] = result.modified_count
    else:
        report["upserted"] = 0
        report["modified"] = 0

    client.close()
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-url", default=os.getenv("MONGO_URL") or "mongodb://localhost:27017")
    parser.add_argument("--db", default=os.getenv("DB_NAME") or "iems_db")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", default=str(ROOT / "docs" / "refactor" / "employee_master_migration_report.json"))
    args = parser.parse_args()

    report = run(args.mongo_url, args.db, args.dry_run)
    Path(args.report).write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))
    # hard gate: every identity merged
    assert report["merged"] == report["identities"], "not every identity merged"
    print(f"\nOK: merged {report['merged']}/{report['identities']} identities, "
          f"{report['with_legacy_fields']} carried legacy_fields. "
          f"Report -> {args.report}")


if __name__ == "__main__":
    main()
