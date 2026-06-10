from __future__ import annotations

from app_platform.db.runtime import get_db
from contexts.audit.services.audit_service import buildAuditTrail, recordAuditEntry
from fastapi import APIRouter, Depends, Query
from contexts.rbac.domain.models import Permission
from contexts.rbac.application.access_control import require_permissions
from app_platform.auth.current_user import get_current_user

audit_router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


@audit_router.post("/logs")
async def record_audit_log(
	payload: dict,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	require_permissions(current_user, Permission.AUDIT_GENERATE_REPORTS)
	return await recordAuditEntry(
		db,
		user_id=str(current_user.get("sub") or current_user.get("id") or "system"),
		user_name=str(current_user.get("name") or current_user.get("username") or "system"),
		authority=str(current_user.get("authority") or "AUDITOR"),
		action=str(payload.get("action") or "MANUAL_AUDIT_LOG"),
		resource_type=str(payload.get("resource_type") or "system"),
		resource_id=str(payload.get("resource_id") or "manual"),
		details=payload.get("details") or {},
		old_value=payload.get("old_value"),
		new_value=payload.get("new_value"),
		workflow_stage=payload.get("workflow_stage"),
		workflow_action=payload.get("workflow_action"),
	)


@audit_router.get("/logs")
async def get_audit_logs(
	resource_type: str | None = None,
	action: str | None = None,
	limit: int = Query(default=100, ge=1, le=500),
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	require_permissions(current_user, Permission.AUDIT_READ_ALL)
	return await buildAuditTrail(
		db,
		current_user=current_user,
		resource_type=resource_type,
		action=action,
		limit=limit,
	)


@audit_router.get("/service-book-logs")
async def get_service_book_logs(
	employee_id: str | None = None,
	limit: int = Query(default=100, ge=1, le=500),
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	require_permissions(current_user, Permission.AUDIT_READ_ALL)
	return await buildAuditTrail(
		db,
		current_user=current_user,
		resource_type="service_book",
		employee_id=employee_id,
		limit=limit,
	)


__all__ = ["audit_router"]
