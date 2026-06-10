from __future__ import annotations

from typing import Any

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from shared_kernel.events import utc_now_iso
from shared_kernel.ids import new_id

QUEUE_WORKFLOW_STATES = ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "REJECTED"]


class MongoServiceBookEntryRepository:
    def __init__(self, *, db, part_vi_projection_source=None) -> None:
        assert_collection_ownership(
            context="service_book",
            collection_name="service_book_workflow_entries",
            write=True,
        )
        assert_collection_ownership(
            context="service_book",
            collection_name="service_book_entries",
            write=True,
        )
        self._db = db
        self._part_vi_projection_source = part_vi_projection_source

    @property
    def _workflow_entries(self):
        return self._db.service_book_workflow_entries

    @property
    def _projected_entries(self):
        return self._db.service_book_entries

    @staticmethod
    def _entry_matches_part(entry: dict[str, Any], part_code: str | None) -> bool:
        if not part_code:
            return True
        normalized = str(part_code or "").strip().upper()
        if not normalized:
            return True
        return normalized in {
            str(entry.get("part_code") or "").strip().upper(),
            str(entry.get("part_key") or "").strip().upper(),
        }

    @staticmethod
    def _entry_matches_status(entry: dict[str, Any], statuses: list[str] | None, status: str | None) -> bool:
        requested_statuses = [str(value or "").strip().upper() for value in (statuses or []) if str(value or "").strip()]
        requested_status = str(status or "").strip().upper() or None
        if not requested_statuses and not requested_status:
            return True

        entry_statuses = {
            str(entry.get("workflow_state") or "").strip().upper(),
            str(entry.get("status") or "").strip().upper(),
            str((entry.get("payload") or {}).get("workflow_state") or "").strip().upper(),
            str((entry.get("payload") or {}).get("status") or "").strip().upper(),
        }
        entry_statuses.discard("")

        if requested_statuses:
            return bool(entry_statuses.intersection(requested_statuses))
        return requested_status in entry_statuses

    async def append_entry(
        self,
        *,
        employee_id: str,
        event_name: str,
        part_code: str | None,
        payload: dict,
        effective_date: str | None,
        fields_changed: list[str],
        source_event_id: str | None = None,
    ) -> str:
        entry_id = new_id()
        doc = {
            "entry_id": entry_id,
            "employee_id": employee_id,
            "event_name": event_name,
            "part_code": part_code,
            "payload": payload,
            "effective_date": effective_date,
            "fields_changed": fields_changed,
            "created_at": utc_now_iso(),
        }
        if source_event_id:
            doc["source_event_id"] = source_event_id
            await self._projected_entries.update_one(
                {"source_event_id": source_event_id, "event_name": event_name},
                {"$setOnInsert": doc},
                upsert=True,
            )
        else:
            await self._projected_entries.insert_one(doc)
        return entry_id

    async def list_entries(self, *, employee_id: str, filters: dict) -> list[dict]:
        query = {"employee_id": employee_id}
        if filters.get("from_date") or filters.get("to_date"):
            date_query = {}
            if filters.get("from_date"):
                date_query["$gte"] = filters["from_date"]
            if filters.get("to_date"):
                date_query["$lte"] = filters["to_date"]
            query["effective_date"] = date_query

        entries = (
            await self._projected_entries.find(query, {"_id": 0})
            .sort("created_at", -1)
            .to_list(length=500)
        )
        entries = [
            entry
            for entry in entries
            if self._entry_matches_part(entry, filters.get("part_code"))
            and self._entry_matches_status(entry, filters.get("statuses"), filters.get("status"))
        ]
        if self._part_vi_projection_source is None:
            return entries
        return await self._part_vi_projection_source.merge_entries(
            db=self._db,
            entries=entries,
            employee_id=employee_id,
            part_code=filters.get("part_code"),
        )

    async def list_queue_entries(
        self,
        *,
        workflow_state: str | None,
        page_size: int,
        workflow_states: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        clamped = min(max(page_size, 1), 500)
        requested_states = [
            str(state or "").strip().upper()
            for state in (workflow_states or [])
            if str(state or "").strip()
        ]
        if requested_states:
            unique_states = list(dict.fromkeys(requested_states))
            facet = {
                state: [
                    {"$match": {"workflow_state": state}},
                    {"$sort": {"updated_at": -1}},
                    {"$limit": clamped},
                    {"$project": {"_id": 0}},
                ]
                for state in unique_states
            }
            results = await self._workflow_entries.aggregate([
                {"$match": {"is_active": True, "workflow_state": {"$in": unique_states}}},
                {"$facet": facet},
                {"$project": {"entries": {"$concatArrays": [f"${state}" for state in unique_states]}}},
                {"$unwind": "$entries"},
                {"$replaceRoot": {"newRoot": "$entries"}},
                {"$sort": {"updated_at": -1}},
            ]).to_list(length=clamped * len(unique_states))
            entries = results if isinstance(results, list) else []
            return sorted(entries, key=lambda item: str(item.get("updated_at") or ""), reverse=True)

        query: dict[str, Any] = {"is_active": True}
        if workflow_state:
            query["workflow_state"] = workflow_state.upper()
        else:
            query["workflow_state"] = {"$in": QUEUE_WORKFLOW_STATES}
        return (
            await self._workflow_entries.find(query, {"_id": 0})
            .sort("updated_at", -1)
            .to_list(length=clamped)
        )
