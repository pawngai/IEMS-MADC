from __future__ import annotations

from fastapi import HTTPException

from contexts.employee_master.contracts.employee_domain import isServiceBookEligible
from contexts.ess.infrastructure import service as ess_service


def _assert_self_scope(current_user: dict, employee_id: str | None = None) -> str:
    current_employee_id = str(current_user.get("employee_id") or "").strip()
    if not current_employee_id:
        raise HTTPException(status_code=400, detail="No employee profile linked to your account")
    target = str(employee_id or current_employee_id).strip()
    if target != current_employee_id:
        raise HTTPException(
            status_code=403,
            detail="ESS actions are restricted to self scope",
        )
    return current_employee_id


async def getEssDashboard(*, db, current_user: dict) -> dict:
    _assert_self_scope(current_user)
    return await ess_service.get_dashboard(db, current_user=current_user)


async def getEssProfile(*, db, current_user: dict) -> dict:
    employee_id = _assert_self_scope(current_user)
    profile = await ess_service.get_my_profile(db, current_user=current_user)
    if str(profile.get("employee_id") or employee_id) != employee_id:
        raise HTTPException(status_code=403, detail="ESS profile access is self scope only")
    return profile


async def getEssServiceBook(*, db, current_user: dict) -> dict:
    _assert_self_scope(current_user)
    profile = await ess_service.get_my_profile(db, current_user=current_user)
    if not isServiceBookEligible(profile):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Service Book not applicable",
                "message": "Service Book is available only for eligible employees.",
                "required_employment_type": "REGULAR",
            },
        )
    return await ess_service.get_my_service_book(db, current_user=current_user)


async def updateEssContact(*, db, updates: dict, current_user: dict) -> dict:
    _assert_self_scope(current_user)
    return await ess_service.update_my_contact(db, updates, current_user=current_user)


async def getEssLeaves(*, db, current_user: dict) -> list[dict]:
    _assert_self_scope(current_user)
    return await ess_service.get_my_leaves(db, current_user=current_user)


async def getEssLeaveBalances(*, db, current_user: dict) -> dict:
    _assert_self_scope(current_user)
    return await ess_service.get_my_leave_balances(db, current_user=current_user)


async def getEssDocuments(
    *,
    db,
    current_user: dict,
    query: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    document_type: str | None = None,
    category: str | None = None,
    source_context: str | None = None,
    is_locked: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    _assert_self_scope(current_user)
    return await ess_service.get_my_documents(
        db,
        current_user=current_user,
        query=query,
        entity_type=entity_type,
        entity_id=entity_id,
        document_type=document_type,
        category=category,
        source_context=source_context,
        is_locked=is_locked,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


async def downloadEssDocument(*, filename: str, db, current_user: dict):
    _assert_self_scope(current_user)
    return await ess_service.download_my_document(filename, db, current_user=current_user)


async def getEssDocument(*, filename: str, db, current_user: dict):
    _assert_self_scope(current_user)
    return await ess_service.get_my_document(filename, db, current_user=current_user)


async def getEssNotifications(*, db, current_user: dict) -> dict:
    _assert_self_scope(current_user)
    return await ess_service.get_notifications(db, current_user=current_user)


async def markEssNotificationRead(*, db, notification_id: str, current_user: dict) -> dict:
    _assert_self_scope(current_user)
    return await ess_service.mark_notification_read(
        db,
        notification_id,
        current_user=current_user,
    )
