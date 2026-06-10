from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

from contexts.employee_identity.domain.employee_code import (
    employment_type_initial,
    format_employee_code,
    parse_employee_code,
)


MIGRATION_MARKER = "employee-code-madc-appointment-year-v1"
LEGACY_COUNTER_CLEANUP_MARKER = "employee-code-legacy-counter-cleanup-v1"


def _collection(db, name: str):
    try:
        return getattr(db, name)
    except AttributeError:
        return db[name]


def _normalize_index_key(key: Any) -> tuple[tuple[str, int], ...]:
    return tuple((str(name), int(direction)) for name, direction in (key or []))


def _canonical_employee_code(year: int, employment_type: str, sequence: int) -> str:
    return f"MADC-{year}-{employment_type_initial(employment_type)}{sequence:04d}"


def _normalize_appointment_year(value: Any) -> int:
    text = str(value or "").strip()
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        raise ValueError("date_of_initial_engagement must be YYYY-MM-DD")
    year = int(text[:4])
    month = int(text[5:7])
    day = int(text[8:10])
    if month < 1 or month > 12 or day < 1 or day > 31:
        raise ValueError("date_of_initial_engagement must be YYYY-MM-DD")
    return year


def build_employee_code_migration_plan(
    identities: list[dict[str, Any]],
) -> dict[str, Any]:
    valid_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for identity in identities:
        employee_id = str(identity.get("employee_id") or "").strip()
        if not employee_id:
            errors.append({"employee_id": "", "error": "Missing employee_id."})
            continue

        try:
            appointment_year = _normalize_appointment_year(
                identity.get("date_of_initial_engagement")
            )
        except ValueError as exc:
            errors.append({"employee_id": employee_id, "error": str(exc)})
            continue

        employment_type = str(identity.get("employment_type") or "").strip()
        try:
            employment_type_initial(employment_type)
        except ValueError as exc:
            errors.append({"employee_id": employee_id, "error": str(exc)})
            continue

        valid_rows.append(
            {
                "employee_id": employee_id,
                "employee_code": str(identity.get("employee_code") or "").strip() or None,
                "employment_type": employment_type,
                "date_of_initial_engagement": str(
                    identity.get("date_of_initial_engagement") or ""
                ).strip(),
                "created_at": str(identity.get("created_at") or "").strip(),
                "appointment_year": appointment_year,
            }
        )

    valid_rows.sort(
        key=lambda row: (
            row["date_of_initial_engagement"],
            row["created_at"],
            row["employee_code"] or "",
            row["employee_id"],
        )
    )

    per_year_sequences: dict[int, int] = defaultdict(int)
    employees: list[dict[str, Any]] = []

    for row in valid_rows:
        year = row["appointment_year"]
        per_year_sequences[year] += 1
        new_code = _canonical_employee_code(
            year,
            row["employment_type"],
            per_year_sequences[year],
        )
        employees.append(
            {
                "employee_id": row["employee_id"],
                "appointment_year": year,
                "date_of_initial_engagement": row["date_of_initial_engagement"],
                "old_code": row["employee_code"],
                "new_code": new_code,
                "changed": row["employee_code"] != new_code,
            }
        )

    years = [
        {
            "year": year,
            "count": count,
            "counter_id": f"employee_code:{year}",
        }
        for year, count in sorted(per_year_sequences.items())
    ]

    return {
        "migration_marker": MIGRATION_MARKER,
        "employees": employees,
        "years": years,
        "errors": errors,
    }


def _document_metadata_query(employee_id: str, old_code: str | None) -> dict[str, Any]:
    if old_code:
        return {
            "$or": [
                {"uploaded_employee_id": employee_id},
                {
                    "uploaded_employee_id": {"$in": [None, ""]},
                    "uploaded_employee_code": old_code,
                },
            ]
        }
    return {"uploaded_employee_id": employee_id}


def _result_count(result: Any, *, default: int = 0) -> int:
    for key in ("modified_count", "matched_count"):
        value = getattr(result, key, None)
        if isinstance(value, int):
            return value
    return default


def _is_year_scoped_counter_id(counter_id: Any) -> bool:
    return bool(re.fullmatch(r"employee_code:\d{4}", str(counter_id or "").strip()))


def _parse_canonical_employee_code(value: Any) -> tuple[int, int] | None:
    parsed = parse_employee_code(value)
    if parsed is None:
        return None
    year, _prefix, sequence = parsed
    if year is None:
        return None
    return year, sequence


async def _find_duplicate_employee_codes(collection, *, limit: int = 5) -> list[dict[str, Any]]:
    cursor = collection.aggregate(
        [
            {"$match": {"employee_code": {"$type": "string", "$ne": ""}}},
            {
                "$group": {
                    "_id": "$employee_code",
                    "count": {"$sum": 1},
                    "employee_ids": {"$push": "$employee_id"},
                }
            },
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$limit": limit},
        ]
    )
    return [row async for row in cursor]


async def verify_employee_code_cutover(db) -> dict[str, Any]:
    employee_identities = _collection(db, "employee_identities")
    employee_profile_read_models = _collection(db, "employee_profile_read_models")
    counters = _collection(db, "counters")

    identity_duplicates = await _find_duplicate_employee_codes(employee_identities)
    read_model_duplicates = await _find_duplicate_employee_codes(employee_profile_read_models)

    identity_rows = [
        row
        async for row in employee_identities.find(
            {},
            {"_id": 0, "employee_id": 1, "employee_code": 1},
        )
    ]
    invalid_format_rows = [
        {
            "employee_id": row.get("employee_id"),
            "employee_code": row.get("employee_code"),
        }
        for row in identity_rows
        if row.get("employee_code") and _parse_canonical_employee_code(row.get("employee_code")) is None
    ]

    expected_counter_state: dict[str, int] = {}
    for row in identity_rows:
        parsed = _parse_canonical_employee_code(row.get("employee_code"))
        if parsed is None:
            continue
        year, sequence = parsed
        counter_id = f"employee_code:{year}"
        expected_counter_state[counter_id] = max(expected_counter_state.get(counter_id, 0), sequence)

    counter_rows = [row async for row in counters.find({}, {"_id": 1, "seq": 1})]
    legacy_counter = next(
        (row for row in counter_rows if str(row.get("_id") or "").strip() == "employee_code"),
        None,
    )
    year_scoped_counter_map = {
        str(row.get("_id")): int(row.get("seq") or 0)
        for row in counter_rows
        if _is_year_scoped_counter_id(row.get("_id"))
    }
    missing_year_scoped_counters = sorted(
        counter_id for counter_id in expected_counter_state if counter_id not in year_scoped_counter_map
    )
    mismatched_year_scoped_counters = [
        {
            "counter_id": counter_id,
            "expected_seq": expected_counter_state[counter_id],
            "actual_seq": year_scoped_counter_map.get(counter_id),
        }
        for counter_id in sorted(expected_counter_state)
        if year_scoped_counter_map.get(counter_id) != expected_counter_state[counter_id]
    ]

    index_info = await employee_identities.index_information()
    employee_code_indexes = {
        index_name: metadata
        for index_name, metadata in index_info.items()
        if _normalize_index_key(metadata.get("key")) == (("employee_code", 1),)
    }
    has_unique_employee_code_index = any(
        metadata.get("unique", False) for metadata in employee_code_indexes.values()
    )

    checks = {
        "identity_duplicates": len(identity_duplicates) == 0,
        "read_model_duplicates": len(read_model_duplicates) == 0,
        "canonical_format": len(invalid_format_rows) == 0,
        "employee_code_unique_index": has_unique_employee_code_index,
        "legacy_counter_absent": legacy_counter is None,
        "year_scoped_counters_present": len(missing_year_scoped_counters) == 0,
        "year_scoped_counter_values": len(mismatched_year_scoped_counters) == 0,
    }

    return {
        "ok": all(checks.values()),
        "checks": checks,
        "identity_row_count": len(identity_rows),
        "identity_duplicate_count": len(identity_duplicates),
        "identity_duplicates_preview": identity_duplicates,
        "read_model_duplicate_count": len(read_model_duplicates),
        "read_model_duplicates_preview": read_model_duplicates,
        "invalid_format_count": len(invalid_format_rows),
        "invalid_format_preview": invalid_format_rows[:10],
        "employee_code_indexes": employee_code_indexes,
        "legacy_counter": legacy_counter,
        "year_scoped_counters": [
            {"_id": counter_id, "seq": year_scoped_counter_map[counter_id]}
            for counter_id in sorted(year_scoped_counter_map)
        ],
        "missing_year_scoped_counters": missing_year_scoped_counters,
        "mismatched_year_scoped_counters": mismatched_year_scoped_counters,
        "expected_year_scoped_counters": [
            {"_id": counter_id, "seq": expected_counter_state[counter_id]}
            for counter_id in sorted(expected_counter_state)
        ],
    }


async def cleanup_legacy_employee_code_counter(
    db,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    counters = _collection(db, "counters")
    cursor = counters.find({}, {"_id": 1, "seq": 1})
    counter_rows = [row async for row in cursor]

    legacy_counter = next(
        (row for row in counter_rows if str(row.get("_id") or "").strip() == "employee_code"),
        None,
    )
    year_scoped_counters = sorted(
        [row for row in counter_rows if _is_year_scoped_counter_id(row.get("_id"))],
        key=lambda row: str(row.get("_id") or ""),
    )

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "force": force,
        "cleanup_marker": LEGACY_COUNTER_CLEANUP_MARKER,
        "legacy_counter_present": legacy_counter is not None,
        "legacy_counter": legacy_counter,
        "year_scoped_counter_count": len(year_scoped_counters),
        "year_scoped_counters": year_scoped_counters,
        "deleted": False,
        "skip_reason": None,
    }

    if legacy_counter is None:
        summary["skip_reason"] = "legacy_counter_missing"
        return summary

    if not year_scoped_counters and not force:
        summary["skip_reason"] = "year_scoped_counters_missing"
        return summary

    if dry_run:
        return summary

    delete_result = await counters.delete_one({"_id": "employee_code"})
    deleted_count = getattr(delete_result, "deleted_count", 0)
    summary["deleted"] = isinstance(deleted_count, int) and deleted_count > 0
    return summary


async def migrate_employee_codes_to_madc_format(
    db,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    cursor = _collection(db, "employee_identities").find(
        {},
        {
            "_id": 0,
            "employee_id": 1,
            "employee_code": 1,
            "employment_type": 1,
            "date_of_initial_engagement": 1,
            "created_at": 1,
        },
    )
    identities = [identity async for identity in cursor]
    plan = build_employee_code_migration_plan(identities)

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "migration_marker": MIGRATION_MARKER,
        "identities_scanned": len(identities),
        "identities_planned": len(plan["employees"]),
        "identities_needing_update": sum(1 for row in plan["employees"] if row["changed"]),
        "identity_rows_updated": 0,
        "read_models_updated": 0,
        "legacy_profiles_updated": 0,
        "document_metadata_updated": 0,
        "counters_updated": 0,
        "years": plan["years"],
        "employees": plan["employees"],
        "errors": plan["errors"],
    }

    if dry_run:
        return summary

    employee_identities = _collection(db, "employee_identities")
    employee_profile_read_models = _collection(db, "employee_profile_read_models")
    employee_profiles = _collection(db, "employee_profiles")
    document_metadata = _collection(db, "document_metadata")
    counters = _collection(db, "counters")

    for row in plan["employees"]:
        if not row["changed"]:
            continue

        employee_id = row["employee_id"]
        old_code = row["old_code"]
        new_code = row["new_code"]

        identity_result = await employee_identities.update_one(
            {"employee_id": employee_id},
            {
                "$set": {
                    "employee_code": new_code,
                    "employee_code_migration_marker": MIGRATION_MARKER,
                }
            },
        )
        summary["identity_rows_updated"] += _result_count(identity_result, default=1)

        read_model_result = await employee_profile_read_models.update_one(
            {"employee_id": employee_id},
            {
                "$set": {
                    "employee_code": new_code,
                    "employee_code_migration_marker": MIGRATION_MARKER,
                }
            },
        )
        summary["read_models_updated"] += _result_count(read_model_result)

        legacy_profile_result = await employee_profiles.update_one(
            {"employee_id": employee_id},
            {
                "$set": {
                    "employee_code": new_code,
                    "employee_code_migration_marker": MIGRATION_MARKER,
                }
            },
        )
        summary["legacy_profiles_updated"] += _result_count(legacy_profile_result)

        document_result = await document_metadata.update_many(
            _document_metadata_query(employee_id, old_code),
            {
                "$set": {
                    "uploaded_employee_code": new_code,
                    "employee_code_migration_marker": MIGRATION_MARKER,
                }
            },
        )
        summary["document_metadata_updated"] += _result_count(document_result)

    for year_entry in plan["years"]:
        counter_result = await counters.update_one(
            {"_id": year_entry["counter_id"]},
            {
                "$set": {
                    "seq": year_entry["count"],
                    "employee_code_migration_marker": MIGRATION_MARKER,
                }
            },
            upsert=True,
        )
        summary["counters_updated"] += max(_result_count(counter_result), 1)

    return summary