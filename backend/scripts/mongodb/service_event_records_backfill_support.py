from __future__ import annotations

from typing import Any


MIGRATION_MARKER = "service-event-records-backfill-v1"


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _collection(db, name: str):
    return db[name] if hasattr(db, "__getitem__") else getattr(db, name)


def _event_record_document(
    *,
    employee_id: str,
    event: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    date_range = event.get("date_range") or {}
    return {
        **event,
        "employee_id": employee_id,
        "sequence": sequence,
        "effective_from": date_range.get("effective_from") or event.get("effective_from"),
        "effective_to": date_range.get("effective_to") or event.get("effective_to"),
        "migration_marker": MIGRATION_MARKER,
    }


def _stream_update_document(*, employee_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    latest_updated_at = max(
        (
            _normalize_text(record.get("updated_at") or record.get("created_at"))
            for record in records
        ),
        default="",
    )
    return {
        "employee_id": employee_id,
        "event_count": len(records),
        "updated_at": latest_updated_at or None,
        "migration_marker": MIGRATION_MARKER,
    }


def _normalize_index_key(key: Any) -> tuple[tuple[str, int], ...]:
    return tuple((str(field), int(direction)) for field, direction in (key or []))


def _duplicate_values(values: list[str]) -> list[dict[str, Any]]:
    seen: dict[str, int] = {}
    for value in values:
        seen[value] = seen.get(value, 0) + 1
    return [
        {"value": value, "count": count}
        for value, count in sorted(seen.items())
        if count > 1
    ]


async def backfill_service_event_records(
    db,
    *,
    dry_run: bool = False,
    employee_id: str | None = None,
) -> dict[str, Any]:
    normalized_employee_id = _normalize_text(employee_id) or None
    query = {"employee_id": normalized_employee_id} if normalized_employee_id else {}
    cursor = _collection(db, "service_events").find(query, {"_id": 0})

    service_event_streams = _collection(db, "service_event_streams")
    service_event_records = _collection(db, "service_event_records")

    summary: dict[str, Any] = {
        "dry_run": dry_run,
        "migration_marker": MIGRATION_MARKER,
        "employee_filter": normalized_employee_id,
        "streams_scanned": 0,
        "streams_backfilled": 0,
        "stream_metadata_written": 0,
        "events_found": 0,
        "records_written": 0,
        "skipped_existing_records": 0,
        "skipped_duplicate_event_ids": 0,
        "skipped_missing_event_id": 0,
        "skipped_missing_employee_id": 0,
        "streams": [],
    }

    async for stream in cursor:
        summary["streams_scanned"] += 1
        stream_employee_id = _normalize_text(stream.get("employee_id"))
        if not stream_employee_id:
            summary["skipped_missing_employee_id"] += 1
            summary["streams"].append({"employee_id": None, "action": "skipped_missing_employee_id"})
            continue

        events = list(stream.get("events") or [])
        summary["events_found"] += len(events)
        seen_event_ids: set[str] = set()
        valid_record_docs: list[dict[str, Any]] = []
        new_record_docs: list[dict[str, Any]] = []
        stream_detail: dict[str, Any] = {
            "employee_id": stream_employee_id,
            "events_found": len(events),
            "records_written": 0,
            "skipped_existing_records": 0,
            "skipped_duplicate_event_ids": 0,
            "skipped_missing_event_id": 0,
        }

        for sequence, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                summary["skipped_missing_event_id"] += 1
                stream_detail["skipped_missing_event_id"] += 1
                continue

            service_event_id = _normalize_text(event.get("service_event_id"))
            if not service_event_id:
                summary["skipped_missing_event_id"] += 1
                stream_detail["skipped_missing_event_id"] += 1
                continue
            if service_event_id in seen_event_ids:
                summary["skipped_duplicate_event_ids"] += 1
                stream_detail["skipped_duplicate_event_ids"] += 1
                continue
            seen_event_ids.add(service_event_id)

            record_doc = _event_record_document(
                employee_id=stream_employee_id,
                event=event,
                sequence=sequence,
            )
            valid_record_docs.append(record_doc)

            existing = await service_event_records.find_one(
                {"service_event_id": service_event_id},
                {"_id": 0, "service_event_id": 1},
            )
            if existing:
                summary["skipped_existing_records"] += 1
                stream_detail["skipped_existing_records"] += 1
                continue

            new_record_docs.append(record_doc)

        if not valid_record_docs:
            stream_detail["action"] = "skipped_no_new_records"
            summary["streams"].append(stream_detail)
            continue

        stream_detail["action"] = "would_backfill" if dry_run else "backfilled"
        stream_detail["records_written"] = len(new_record_docs)
        summary["streams_backfilled"] += 1
        summary["records_written"] += len(new_record_docs)
        summary["stream_metadata_written"] += 1
        summary["streams"].append(stream_detail)

        if dry_run:
            continue

        await service_event_streams.update_one(
            {"employee_id": stream_employee_id},
            {"$set": _stream_update_document(employee_id=stream_employee_id, records=valid_record_docs)},
            upsert=True,
        )
        if new_record_docs:
            await service_event_records.insert_many(new_record_docs)

    return summary


async def verify_service_event_records_cutover(db) -> dict[str, Any]:
    legacy_streams = _collection(db, "service_events")
    normalized_streams = _collection(db, "service_event_streams")
    normalized_records = _collection(db, "service_event_records")

    legacy_rows = [
        row
        async for row in legacy_streams.find(
            {},
            {"_id": 0, "employee_id": 1, "events": 1},
        )
    ]
    record_rows = [
        row
        async for row in normalized_records.find(
            {},
            {"_id": 0, "employee_id": 1, "service_event_id": 1, "sequence": 1},
        )
    ]
    stream_rows = [
        row
        async for row in normalized_streams.find(
            {},
            {"_id": 0, "employee_id": 1, "event_count": 1},
        )
    ]

    legacy_event_ids: list[str] = []
    legacy_event_count_by_employee: dict[str, int] = {}
    missing_legacy_event_id_count = 0
    for stream in legacy_rows:
        employee_id = _normalize_text(stream.get("employee_id"))
        valid_event_count = 0
        for event in stream.get("events") or []:
            if not isinstance(event, dict):
                missing_legacy_event_id_count += 1
                continue
            service_event_id = _normalize_text(event.get("service_event_id"))
            if not service_event_id:
                missing_legacy_event_id_count += 1
                continue
            legacy_event_ids.append(service_event_id)
            valid_event_count += 1
        if employee_id and valid_event_count:
            legacy_event_count_by_employee[employee_id] = valid_event_count

    record_event_ids = [
        _normalize_text(row.get("service_event_id"))
        for row in record_rows
        if _normalize_text(row.get("service_event_id"))
    ]
    legacy_event_id_set = set(legacy_event_ids)
    record_event_id_set = set(record_event_ids)

    missing_record_event_ids = sorted(legacy_event_id_set - record_event_id_set)
    orphan_record_event_ids = sorted(record_event_id_set - legacy_event_id_set)
    duplicate_legacy_event_ids = _duplicate_values(legacy_event_ids)
    duplicate_record_event_ids = _duplicate_values(record_event_ids)

    stream_count_by_employee = {
        _normalize_text(row.get("employee_id")): int(row.get("event_count") or 0)
        for row in stream_rows
        if _normalize_text(row.get("employee_id"))
    }
    missing_stream_metadata = sorted(
        employee_id
        for employee_id in legacy_event_count_by_employee
        if employee_id not in stream_count_by_employee
    )
    mismatched_stream_metadata = [
        {
            "employee_id": employee_id,
            "legacy_event_count": legacy_count,
            "stream_event_count": stream_count_by_employee.get(employee_id),
        }
        for employee_id, legacy_count in sorted(legacy_event_count_by_employee.items())
        if stream_count_by_employee.get(employee_id) != legacy_count
    ]

    record_index_info = await normalized_records.index_information()
    stream_index_info = await normalized_streams.index_information()
    record_service_event_id_indexes = {
        index_name: metadata
        for index_name, metadata in record_index_info.items()
        if _normalize_index_key(metadata.get("key")) == (("service_event_id", 1),)
    }
    stream_employee_id_indexes = {
        index_name: metadata
        for index_name, metadata in stream_index_info.items()
        if _normalize_index_key(metadata.get("key")) == (("employee_id", 1),)
    }

    checks = {
        "all_legacy_events_backfilled": len(missing_record_event_ids) == 0,
        "no_orphan_normalized_records": len(orphan_record_event_ids) == 0,
        "legacy_event_ids_unique": len(duplicate_legacy_event_ids) == 0,
        "normalized_event_ids_unique": len(duplicate_record_event_ids) == 0,
        "legacy_events_have_ids": missing_legacy_event_id_count == 0,
        "stream_metadata_present": len(missing_stream_metadata) == 0,
        "stream_metadata_counts_match": len(mismatched_stream_metadata) == 0,
        "record_service_event_id_unique_index": any(
            metadata.get("unique", False)
            for metadata in record_service_event_id_indexes.values()
        ),
        "stream_employee_id_unique_index": any(
            metadata.get("unique", False)
            for metadata in stream_employee_id_indexes.values()
        ),
    }

    return {
        "ok": all(checks.values()),
        "migration_marker": MIGRATION_MARKER,
        "checks": checks,
        "legacy_stream_count": len(legacy_rows),
        "legacy_event_count": len(legacy_event_ids),
        "normalized_stream_count": len(stream_rows),
        "normalized_record_count": len(record_event_ids),
        "missing_record_event_ids": missing_record_event_ids[:50],
        "missing_record_event_id_count": len(missing_record_event_ids),
        "orphan_record_event_ids": orphan_record_event_ids[:50],
        "orphan_record_event_id_count": len(orphan_record_event_ids),
        "duplicate_legacy_event_ids": duplicate_legacy_event_ids[:50],
        "duplicate_record_event_ids": duplicate_record_event_ids[:50],
        "missing_legacy_event_id_count": missing_legacy_event_id_count,
        "missing_stream_metadata": missing_stream_metadata[:50],
        "missing_stream_metadata_count": len(missing_stream_metadata),
        "mismatched_stream_metadata": mismatched_stream_metadata[:50],
        "mismatched_stream_metadata_count": len(mismatched_stream_metadata),
    }
