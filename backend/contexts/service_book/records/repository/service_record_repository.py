from __future__ import annotations

from app_platform.domain_separation.data_ownership import assert_collection_ownership


STREAM_COLLECTION = "service_book_record_streams"
RECORD_COLLECTION = "service_book_records"
class ServiceRecordRepository:
    def __init__(self, *, db) -> None:
        assert_collection_ownership(
            context="service_book",
            collection_name=STREAM_COLLECTION,
            write=True,
        )
        assert_collection_ownership(
            context="service_book",
            collection_name=RECORD_COLLECTION,
            write=True,
        )
        self._db = db

    @property
    def _streams(self):
        return self._db.service_book_record_streams

    @property
    def _records(self):
        return self._db.service_book_records

    @staticmethod
    def _event_record_document(*, employee_id: str, event: dict, sequence: int) -> dict:
        date_range = event.get("date_range") or {}
        return {
            **event,
            "employee_id": employee_id,
            "sequence": sequence,
            "effective_from": date_range.get("effective_from") or event.get("effective_from"),
            "effective_to": date_range.get("effective_to") or event.get("effective_to"),
        }

    @staticmethod
    def _event_from_record(record: dict) -> dict:
        event = dict(record)
        event.pop("_id", None)
        event.pop("employee_id", None)
        event.pop("sequence", None)
        event.pop("effective_from", None)
        event.pop("effective_to", None)
        return event

    async def _normalized_stream(self, *, employee_id: str) -> dict | None:
        cursor = (
            self._records.find({"employee_id": employee_id}, {"_id": 0})
            .sort("sequence", 1)
        )
        records = await cursor.to_list(length=10000)
        if not records:
            return None
        return {
            "employee_id": employee_id,
            "events": [self._event_from_record(record) for record in records],
        }

    async def get_stream(self, employee_id: str) -> dict | None:
        return await self._normalized_stream(employee_id=employee_id)

    async def initialize_stream(self, *, employee_id: str) -> None:
        await self._streams.update_one(
            {"employee_id": employee_id},
            {
                "$setOnInsert": {
                    "employee_id": employee_id,
                    "event_count": 0,
                }
            },
            upsert=True,
        )

    async def upsert_stream(self, *, employee_id: str, document: dict, session=None) -> None:
        events = list(document.get("events") or [])
        record_docs = [
            self._event_record_document(
                employee_id=employee_id,
                event=event,
                sequence=index,
            )
            for index, event in enumerate(events, start=1)
        ]
        latest_updated_at = max(
            (str(event.get("updated_at") or event.get("created_at") or "") for event in events),
            default="",
        )

        update_kwargs = {"upsert": True}
        write_kwargs = {}
        if session is not None:
            update_kwargs["session"] = session
            write_kwargs["session"] = session
        await self._streams.update_one(
            {"employee_id": employee_id},
            {
                "$set": {
                    "employee_id": employee_id,
                    "event_count": len(record_docs),
                    "updated_at": latest_updated_at or None,
                }
            },
            **update_kwargs,
        )
        for record_doc in record_docs:
            service_record_id = record_doc.get("service_event_id")
            if not service_record_id:
                continue
            await self._records.update_one(
                {"service_event_id": service_record_id},
                {"$set": record_doc},
                upsert=True,
                **write_kwargs,
            )

    async def find_stream_by_event_id(self, *, service_event_id: str) -> dict | None:
        record = await self._records.find_one(
            {"service_event_id": service_event_id},
            {"_id": 0, "employee_id": 1},
        )
        if record and record.get("employee_id"):
            return await self.get_stream(str(record["employee_id"]))
        return None

    async def get_event(self, *, service_event_id: str) -> dict | None:
        record = await self._records.find_one(
            {"service_event_id": service_event_id},
            {"_id": 0},
        )
        if record is not None:
            return dict(record)

        stream = await self.find_stream_by_event_id(service_event_id=service_event_id)
        if stream is None:
            return None
        for item in stream.get("events") or []:
            if item.get("service_event_id") == service_event_id:
                payload = dict(item)
                payload["employee_id"] = stream.get("employee_id")
                return payload
        return None

    async def list_events(self, *, employee_id: str) -> list[dict]:
        stream = await self.get_stream(employee_id=employee_id)
        if stream is None:
            return []
        return stream.get("events") or []
