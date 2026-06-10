from __future__ import annotations

import inspect
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app_platform.db.atomic import call_with_optional_session
from contexts.change_requests.contracts.dto import CreateChangeRequestDTO
from contexts.change_requests.contracts.ports import ChangeRequestGateway
from contexts.change_requests.infrastructure.document_lock import (
    lock_documents_for_approved_request as _lock_documents_for_approved_request,
)
from contexts.employee_profile.contracts.profile_directory import (
    find_profile_view,
)
from fastapi import HTTPException
from contexts.rbac.application.access_control import require_permissions
from contexts.identity.contracts.user_role import get_user_role
from contexts.identity.contracts.user_directory import (
    get_user_department_code,
    get_user_display_name as _identity_display_name,
)
from contexts.notifications.contracts.publisher import publish_notification

COLLECTION = "change_requests"
DEPARTMENT_SCOPED_ROLES = {"DEPT_DATA_ENTRY", "HOD"}

logger = logging.getLogger(__name__)


async def _find_employee_profile_view(db, *, employee_id: str, projection: dict | None = None) -> dict | None:
    return await find_profile_view(
        db,
        employee_id=employee_id,
        projection=projection,
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


def _get_employee_id(current_user: dict) -> str:
    employee_id = current_user.get("employee_id")
    if not employee_id:
        raise HTTPException(400, "No employee profile linked to your account")
    return employee_id


def _require_change_request_operator_access(current_user: dict) -> None:
    if get_user_role(current_user) in DEPARTMENT_SCOPED_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Department-scoped roles cannot access change request operations.",
        )


def _is_transaction_not_supported(exc: Exception) -> bool:
    message = str(exc).lower()
    transaction_markers = [
        "transaction numbers are only allowed",
        "replica set",
        "mongos",
        "transactions are not supported",
    ]
    return any(marker in message for marker in transaction_markers)


async def _resolve_user_department(db, current_user: dict) -> str | None:
    dept = current_user.get("department_code") or current_user.get("department_id")
    if dept:
        return dept

    user_id = (
        current_user.get("sub") or current_user.get("user_id") or current_user.get("id")
    )
    if user_id:
        dept_code = await get_user_department_code(db, user_id=user_id)
        if dept_code:
            return dept_code

    employee_id = current_user.get("employee_id")
    if employee_id:
        profile = await _find_employee_profile_view(
            db,
            employee_id=employee_id,
            projection={"_id": 0, "current_department_id": 1},
        )
        if profile:
            return profile.get("current_department_id")
    return None


async def _get_user_display_name(db, user_id: str) -> str:
    return await _identity_display_name(db, user_id=user_id)


async def _notify_employee(db, request_doc: dict, status: str) -> None:
    title_map = {
        "APPLIED": "Change Request Approved & Applied",
        "REJECTED": "Change Request Rejected",
    }
    message_map = {
        "APPLIED": f"Your {request_doc['request_type'].lower()} change request ({request_doc['category']}) has been approved and applied.",
        "REJECTED": f"Your {request_doc['request_type'].lower()} change request ({request_doc['category']}) was rejected. Reason: {request_doc.get('review_remarks', 'N/A')}",
    }
    await publish_notification(
        db,
        notification_id=f"NOTIF-{uuid.uuid4().hex[:8].upper()}",
        employee_id=request_doc["employee_id"],
        message_type="CHANGE_REQUEST",
        title=title_map.get(status, "Change Request Update"),
        message=message_map.get(status, "Your change request has been updated."),
        level="success" if status == "APPLIED" else "warning",
        timestamp=_now_iso(),
        action_url="/ess/change-requests",
    )


async def _apply_changes(db, request_doc: dict, session=None) -> None:
    from contexts.change_requests.application.apply_handler import apply_approved_changes

    await apply_approved_changes(db, request_doc, session=session)


async def _lock_request_attachments_if_applied(db, request_doc: dict, *, session=None) -> None:
    status = str(request_doc.get("status") or "").upper()
    attachments = request_doc.get("attachments") or []
    if status not in {"APPROVED", "APPLIED"} or not attachments:
        return

    try:
        try:
            lock_result = _lock_documents_for_approved_request(
                attachments,
                request_id=str(request_doc.get("request_id") or ""),
                status=status,
                db=db,
                session=session,
            )
        except TypeError as exc:
            if "session" not in str(exc):
                raise
            lock_result = _lock_documents_for_approved_request(
                attachments,
                request_id=str(request_doc.get("request_id") or ""),
                status=status,
                db=db,
            )
        if inspect.isawaitable(lock_result):
            await lock_result
    except Exception:
        logger.exception(
            "Failed to lock attachment metadata after change request apply",
            extra={
                "request_id": request_doc.get("request_id"),
                "attachment_count": len(attachments),
            },
        )


class ChangeRequestMongoGateway(ChangeRequestGateway):
    def __init__(self, db) -> None:
        from app_platform.domain_separation.data_ownership import assert_collection_ownership

        self._db = db
        assert_collection_ownership(
            context="change_requests", collection_name="change_requests", write=True,
        )

    async def create_change_request(
        self, payload: CreateChangeRequestDTO, *, current_user: dict, session=None
    ) -> dict:
        employee_id = _get_employee_id(current_user)

        profile = await _find_employee_profile_view(
            self._db,
            employee_id=employee_id,
            projection={
                "_id": 0,
                "workflow_status": 1,
                "full_name": 1,
                "current_department_id": 1,
            },
        )
        if not profile:
            raise HTTPException(404, "Profile not found")

        data = payload.model_dump()
        request_type = data["request_type"]
        category = data["category"]
        fields = data["fields"]

        if request_type == "PROFILE":
            full_profile = await _find_employee_profile_view(
                self._db,
                employee_id=employee_id,
                projection={"_id": 0},
            )
            for field in fields:
                actual = full_profile.get(field["field_name"]) if full_profile else None
                if actual is not None:
                    field["current_value"] = str(actual)
        elif request_type == "SERVICE_BOOK":
            for field in fields:
                field.setdefault("current_value", None)

        doc = {
            "request_id": f"CR-{uuid.uuid4().hex[:8].upper()}",
            "employee_id": employee_id,
            "employee_name": profile.get("full_name", ""),
            "department_id": profile.get("current_department_id", ""),
            "request_type": request_type,
            "category": category,
            "fields": fields,
            "reason": data["reason"],
            "supporting_info": data.get("supporting_info"),
            "attachments": data.get("attachments", []),
            "entry_id": data.get("entry_id"),
            "entry_section": data.get("entry_section"),
            "entry_label": data.get("entry_label"),
            "status": "PENDING",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "reviewed_by": None,
            "reviewer_name": None,
            "reviewed_at": None,
            "review_remarks": None,
            "applied_at": None,
        }
        await call_with_optional_session(
            self._db[COLLECTION].insert_one,
            doc,
            session=session,
        )
        return _serialize(doc)

    async def list_my_change_requests(
        self, *, current_user: dict, status: str | None = None
    ) -> dict:
        employee_id = _get_employee_id(current_user)
        query: dict[str, Any] = {"employee_id": employee_id}
        if status:
            query["status"] = status.upper()
        cursor = self._db[COLLECTION].find(query, {"_id": 0}).sort("created_at", -1)
        items = await cursor.to_list(length=200)
        return {"items": items, "total": len(items)}

    async def get_change_request(self, request_id: str, *, current_user: dict) -> dict:
        doc = await self._db[COLLECTION].find_one(
            {"request_id": request_id}, {"_id": 0}
        )
        if not doc:
            raise HTTPException(404, "Change request not found")

        employee_id = current_user.get("employee_id")
        if doc["employee_id"] == employee_id:
            return doc

        require_permissions(current_user, "PROFILE_READ_ALL")
        _require_change_request_operator_access(current_user)

        return doc

    async def cancel_change_request(
        self, request_id: str, *, current_user: dict, session=None
    ) -> dict:
        employee_id = _get_employee_id(current_user)
        doc = await self._db[COLLECTION].find_one(
            {"request_id": request_id, "employee_id": employee_id}
        )
        if not doc:
            raise HTTPException(404, "Change request not found")
        if doc["status"] != "PENDING":
            raise HTTPException(400, f"Cannot cancel a {doc['status']} request")

        await call_with_optional_session(
            self._db[COLLECTION].update_one,
            {"request_id": request_id},
            {"$set": {"status": "CANCELLED", "updated_at": _now_iso()}},
            session=session,
        )
        doc["status"] = "CANCELLED"
        return _serialize(doc)

    async def list_change_requests(
        self,
        *,
        current_user: dict,
        status: str | None = None,
        employee_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        require_permissions(current_user, "PROFILE_READ_ALL")
        _require_change_request_operator_access(current_user)

        query: dict[str, Any] = {}
        if status:
            query["status"] = status.upper()
        if employee_id:
            query["employee_id"] = employee_id

        total = await self._db[COLLECTION].count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            self._db[COLLECTION]
            .find(query, {"_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        items = await cursor.to_list(length=page_size)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def review_change_request(
        self,
        request_id: str,
        *,
        action: str,
        remarks: str | None,
        current_user: dict,
        session=None,
    ) -> dict:
        require_permissions(current_user, "PROFILE_UPDATE_ALL")
        _require_change_request_operator_access(current_user)

        doc = await self._db[COLLECTION].find_one({"request_id": request_id})
        if not doc:
            raise HTTPException(404, "Change request not found")
        if doc["status"] != "PENDING":
            raise HTTPException(400, f"Request is already {doc['status']}")

        user_id = (
            current_user.get("sub")
            or current_user.get("user_id")
            or current_user.get("id", "")
        )
        reviewer_name = await _get_user_display_name(self._db, user_id)

        now = _now_iso()
        new_status = "APPROVED" if action == "APPROVE" else "REJECTED"
        update_fields = {
            "status": new_status,
            "reviewed_by": user_id,
            "reviewer_name": reviewer_name,
            "reviewed_at": now,
            "review_remarks": remarks or "",
            "updated_at": now,
        }

        if new_status == "APPROVED":
            update_fields["status"] = "APPLIED"
            update_fields["applied_at"] = now
            if session is not None:
                await _apply_changes(self._db, doc, session=session)
                await call_with_optional_session(
                    self._db[COLLECTION].update_one,
                    {"request_id": request_id},
                    {"$set": update_fields},
                    session=session,
                )
            elif bool(getattr(getattr(self._db, "client", None), "start_session", None)):
                try:
                    async with await self._db.client.start_session() as transaction_session:
                        async with transaction_session.start_transaction():
                            await _apply_changes(self._db, doc, session=transaction_session)
                            await self._db[COLLECTION].update_one(
                                {"request_id": request_id},
                                {"$set": update_fields},
                                session=transaction_session,
                            )
                except Exception as exc:
                    if not _is_transaction_not_supported(exc):
                        raise
                    await _apply_changes(self._db, doc)
                    await self._db[COLLECTION].update_one(
                        {"request_id": request_id},
                        {"$set": update_fields},
                    )
            else:
                await _apply_changes(self._db, doc)
                await self._db[COLLECTION].update_one(
                    {"request_id": request_id},
                    {"$set": update_fields},
                )
        else:
            await call_with_optional_session(
                self._db[COLLECTION].update_one,
                {"request_id": request_id},
                {"$set": update_fields},
                session=session,
            )

        doc.update(update_fields)
        doc.pop("_id", None)

        await _lock_request_attachments_if_applied(self._db, doc, session=session)

        await _notify_employee(
            self._db, doc, new_status if new_status == "REJECTED" else "APPLIED"
        )
        return doc

    async def get_pending_count(self, *, current_user: dict) -> int:
        _require_change_request_operator_access(current_user)
        query: dict[str, Any] = {"status": "PENDING"}
        return await self._db[COLLECTION].count_documents(query)
