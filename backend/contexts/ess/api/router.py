from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app_platform.db.runtime import get_db
from contexts.ess.infrastructure.schemas import EssContactUpdate
from contexts.ess.services import ess_service
from app_platform.auth.current_user import get_current_user


ess_router = APIRouter(prefix="/ess", tags=["ESS Portal"])


@ess_router.get("/dashboard")
async def get_dashboard(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssDashboard(db=db, current_user=current_user)


@ess_router.get("/my-profile")
async def get_my_profile(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssProfile(db=db, current_user=current_user)


@ess_router.put("/my-profile/contact")
async def update_my_contact(
    payload: EssContactUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updates = payload.model_dump(exclude_unset=True)
    return await ess_service.updateEssContact(db=db, updates=updates, current_user=current_user)


@ess_router.get("/my-service-book")
async def get_my_service_book(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssServiceBook(db=db, current_user=current_user)


@ess_router.get("/my-leaves")
async def get_my_leaves(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssLeaves(db=db, current_user=current_user)


@ess_router.get("/my-leave-balances")
async def get_my_leave_balances(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssLeaveBalances(db=db, current_user=current_user)


@ess_router.get("/my-documents")
async def get_my_documents(
    query: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    source_context: str | None = Query(default=None),
    is_locked: bool | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssDocuments(
        db=db,
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


@ess_router.get("/my-documents/{filename}/download")
async def download_my_document(
    filename: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.downloadEssDocument(filename=filename, db=db, current_user=current_user)


@ess_router.get("/my-documents/{filename}")
async def get_my_document(
    filename: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssDocument(filename=filename, db=db, current_user=current_user)


@ess_router.get("/notifications")
async def get_notifications(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.getEssNotifications(db=db, current_user=current_user)


@ess_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await ess_service.markEssNotificationRead(
        db=db,
        notification_id=notification_id,
        current_user=current_user,
    )


__all__ = ["ess_router"]
