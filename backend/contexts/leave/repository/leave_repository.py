from __future__ import annotations

from typing import Any

from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.employee_profile.contracts.profile_directory import find_profile_view


class LeaveRuntimeRepository:
    def __init__(self, *, db) -> None:
        self._db = db
        assert_collection_ownership(
            context="leave", collection_name="leave_applications", write=True,
        )
        assert_collection_ownership(
            context="leave", collection_name="leave_ledger_entries", write=True,
        )

    async def find_employee_profile(self, employee_id: str) -> dict[str, Any] | None:
        return await find_profile_view(
            self._db,
            employee_id=employee_id,
            projection={"_id": 0},
        )

    async def find_leave_type_record(self, leave_type_code: str) -> dict[str, Any] | None:
        query = {
            "$and": [
                {
                    "$or": [
                        {"code": leave_type_code},
                        {"leave_code": leave_type_code},
                        {"metadata.leave_code": leave_type_code},
                    ]
                },
                {"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]},
            ]
        }
        return await self._db.leave_types.find_one(query, {"_id": 0})

    async def list_leave_types(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return await self._db.leave_types.find({}, {"_id": 0}).to_list(limit)

    async def find_leave_application(self, leave_id: str) -> dict[str, Any] | None:
        return await self._db.leave_applications.find_one({"id": leave_id}, {"_id": 0})

    async def find_overlapping_leave_application(
        self,
        *,
        employee_id: str,
        from_date: str,
        to_date: str,
        statuses: list[str],
    ) -> dict[str, Any] | None:
        return await self._db.leave_applications.find_one(
            {
                "employee_id": employee_id,
                "status": {"$in": statuses},
                "from_date": {"$lte": to_date},
                "to_date": {"$gte": from_date},
            },
            {"_id": 0},
        )

    async def insert_leave_application(self, record: dict[str, Any], *, session=None) -> None:
        if session is None:
            await self._db.leave_applications.insert_one(record)
        else:
            await self._db.leave_applications.insert_one(record, session=session)

    async def list_leave_applications(
        self,
        query: dict[str, Any],
        *,
        limit: int,
        sort_field: str = "applied_at",
        sort_dir: int = -1,
    ) -> list[dict[str, Any]]:
        cursor = (
            self._db.leave_applications.find(query, {"_id": 0})
            .sort(sort_field, sort_dir)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def update_leave_application(self, leave_id: str, update: dict[str, Any], *, session=None) -> None:
        if session is None:
            await self._db.leave_applications.update_one({"id": leave_id}, {"$set": update})
        else:
            await self._db.leave_applications.update_one(
                {"id": leave_id}, {"$set": update}, session=session
            )

    async def list_sanctioned_leave_applications_for_year(
        self,
        *,
        employee_id: str,
        leave_type_code: str,
        year_start_iso: str,
        year_end_iso: str,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        cursor = self._db.leave_applications.find(
            {
                "employee_id": employee_id,
                "leave_type_code": leave_type_code,
                "status": "SANCTIONED",
                "from_date": {"$lte": year_end_iso},
                "to_date": {"$gte": year_start_iso},
            },
            {"_id": 0},
        )
        return await cursor.to_list(length=limit)

    async def list_sanctioned_leave_applications(
        self,
        *,
        employee_id: str,
        leave_type_code: str,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        cursor = self._db.leave_applications.find(
            {
                "employee_id": employee_id,
                "leave_type_code": leave_type_code,
                "status": "SANCTIONED",
            },
            {"_id": 0, "days_applied": 1},
        )
        return await cursor.to_list(length=limit)

    async def find_leave_account(self, employee_id: str) -> dict[str, Any] | None:
        return await self._db.leave_ledger_entries.find_one(
            {"employee_id": employee_id}, {"_id": 0}
        )

    async def insert_leave_account(self, account: dict[str, Any], *, session=None) -> None:
        if session is None:
            await self._db.leave_ledger_entries.insert_one(account)
        else:
            await self._db.leave_ledger_entries.insert_one(account, session=session)

    async def update_leave_account(
        self,
        employee_id: str,
        update: dict[str, Any],
        *,
        upsert: bool = False,
        session=None,
    ) -> None:
        if session is None:
            await self._db.leave_ledger_entries.update_one(
                {"employee_id": employee_id}, update, upsert=upsert
            )
        else:
            await self._db.leave_ledger_entries.update_one(
                {"employee_id": employee_id}, update, upsert=upsert, session=session
            )

