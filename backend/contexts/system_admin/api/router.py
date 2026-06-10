from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app_platform.auth.current_user import get_current_user
from contexts.audit.contracts.audit_directory import (
	count_audit_logs,
	list_audit_log_action_counts,
)
from contexts.employee_master.contracts.identity_commands import delete_identity
from contexts.employee_master.contracts.profile_commands import archive_and_delete_profile
from contexts.employee_master.contracts.profile_directory import (
	count_profiles as count_employee_profiles,
	find_profile_view,
	get_employee_ids_for_department,
	list_profiles,
)
from contexts.identity.contracts.user_directory import count_users
from contexts.identity.contracts.system_config import get_system_config as identity_get_system_config
from contexts.identity.contracts.system_config import set_system_config_key as identity_set_system_config_key
from contexts.leave.contracts.leave_commands import admin_cancel_leave_application
from contexts.leave.contracts.leave_directory import (
	count_leave_applications,
	get_leave_application_by_id,
	list_leave_applications,
	list_pending_leave_applications,
)
from contexts.rbac.contracts.access_control import forbid_system_admin_write, require_system_admin
from contexts.service_book.contracts.service_book_directory import count_servicebook_entries
from contexts.system_admin.api.shared import (
	EmployeeDeleteRequest,
	SodToggleRequest,
	SystemConfigUpdate,
	TransitionOverrideRequest,
	WorkflowConfigResetRequest,
	WorkflowUnlockRequest,
	get_db,
)


_system_admin_routes = APIRouter(tags=["system-admin"])

PROFILE_WORKFLOW_STATES = ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "LOCKED", "REJECTED"]
SERVICE_BOOK_WORKFLOW_STATES = ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "ATTESTED", "REJECTED"]
LEAVE_WORKFLOW_STATES = ["DRAFT", "SUBMITTED", "RECOMMENDED", "SANCTIONED", "REJECTED", "CANCELLED"]
PROFILE_PENDING_STATES = ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED"]
SERVICE_BOOK_PENDING_STATES = ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED"]
LEAVE_PENDING_STATES = ["SUBMITTED", "RECOMMENDED"]
SYSTEM_ADMIN_STUCK_RESULT_LIMIT = 50


def _ensure_system_admin(current_user: dict) -> None:
	require_system_admin(current_user)


def _profile_collection(db):
	read_models = getattr(db, "employee_profile_read_models", None)
	if read_models is not None:
		return read_models
	return getattr(db, "employee_identities", None)


def _stale_threshold_iso(*, days_threshold: int) -> str:
	return (datetime.now(timezone.utc) - timedelta(days=days_threshold)).isoformat()


async def _count_by_statuses(collection, *, field_name: str, statuses: list[str]) -> dict[str, int]:
	counts = await asyncio.gather(
		*(collection.count_documents({field_name: status}) for status in statuses)
	)
	return {status: int(count) for status, count in zip(statuses, counts)}


async def _build_workflow_summary(db) -> dict[str, dict[str, int]]:
	profile_counts = {
		status: int(await count_employee_profiles(db, workflow_status=status))
		for status in PROFILE_WORKFLOW_STATES
	}

	service_book_entries = getattr(db, "service_book_entries", None)
	service_book_counts = (
		await _count_by_statuses(
			service_book_entries,
			field_name="workflow_state",
			statuses=SERVICE_BOOK_WORKFLOW_STATES,
		)
		if service_book_entries is not None
		else {status: 0 for status in SERVICE_BOOK_WORKFLOW_STATES}
	)

	leave_counts = {
		status: int(await count_leave_applications(db, status=status))
		for status in LEAVE_WORKFLOW_STATES
	}

	return {
		"profile_workflows": profile_counts,
		"service_book_workflows": service_book_counts,
		"leave_workflows": leave_counts,
	}


async def _list_collection_items(
	collection,
	*,
	query: dict[str, Any],
	projection: dict[str, int],
	sort_field: str,
	limit: int,
) -> list[dict[str, Any]]:
	if collection is None:
		return []
	return await (
		collection.find(query, projection)
		.sort(sort_field, 1)
		.limit(limit)
		.to_list(limit)
	)


async def _build_stuck_workflow_payload(
	db,
	*,
	days_threshold: int = 7,
	limit: int = SYSTEM_ADMIN_STUCK_RESULT_LIMIT,
) -> dict[str, Any]:
	threshold = _stale_threshold_iso(days_threshold=days_threshold)
	profiles = _profile_collection(db)
	service_book_entries = getattr(db, "service_book_entries", None)
	leave_applications = getattr(db, "leave_applications", None)

	profile_query = {
		"workflow_status": {"$in": PROFILE_PENDING_STATES},
		"updated_at": {"$lt": threshold},
	}
	service_book_query = {
		"workflow_state": {"$in": SERVICE_BOOK_PENDING_STATES},
		"updated_at": {"$lt": threshold},
	}
	leave_query = {
		"status": {"$in": LEAVE_PENDING_STATES},
		"applied_at": {"$lt": threshold},
	}

	(
		profile_total,
		service_book_total,
		leave_total,
		stuck_profiles,
		stuck_entries,
		stuck_leaves,
	) = await asyncio.gather(
		profiles.count_documents(profile_query) if profiles is not None else asyncio.sleep(0, result=0),
		service_book_entries.count_documents(service_book_query)
		if service_book_entries is not None
		else asyncio.sleep(0, result=0),
		leave_applications.count_documents(leave_query)
		if leave_applications is not None
		else asyncio.sleep(0, result=0),
		_list_collection_items(
			profiles,
			query=profile_query,
			projection={
				"_id": 0,
				"employee_id": 1,
				"full_name": 1,
				"workflow_status": 1,
				"updated_at": 1,
			},
			sort_field="updated_at",
			limit=limit,
		),
		_list_collection_items(
			service_book_entries,
			query=service_book_query,
			projection={
				"_id": 0,
				"entry_id": 1,
				"employee_id": 1,
				"part_code": 1,
				"workflow_state": 1,
				"updated_at": 1,
			},
			sort_field="updated_at",
			limit=limit,
		),
		_list_collection_items(
			leave_applications,
			query=leave_query,
			projection={
				"_id": 0,
				"id": 1,
				"employee_id": 1,
				"leave_type_code": 1,
				"status": 1,
				"from_date": 1,
				"to_date": 1,
				"applied_at": 1,
			},
			sort_field="applied_at",
			limit=limit,
		),
	)

	return {
		"days_threshold": days_threshold,
		"total": int(profile_total) + int(service_book_total) + int(leave_total),
		"stuck_profiles": stuck_profiles,
		"stuck_entries": stuck_entries,
		"stuck_leaves": stuck_leaves,
	}


from contexts.system_admin.api.audit_helpers import (
	_build_audit_query,
	_fetch_audit_logs,
	_normalize_audit_export_row,
	_stream_audit_export_csv,
)

async def _build_audit_stats(db) -> dict[str, Any]:
	start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
	total_logs, today_count, grouped_rows = await asyncio.gather(
		count_audit_logs(db, query={}),
		count_audit_logs(db, query={"timestamp": {"$gte": start_of_day}}),
		list_audit_log_action_counts(db, limit=100),
	)
	return {
		"total_logs": int(total_logs),
		"today_count": int(today_count),
		"by_action": [
			{"action": str(row.get("_id") or "UNKNOWN"), "count": int(row.get("count") or 0)}
			for row in grouped_rows
		],
	}


async def _count_stuck_workflows(db, *, days_threshold: int = 7) -> int:
	threshold = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).isoformat()
	tasks: list[Any] = []

	profiles = _profile_collection(db)
	if profiles is not None:
		tasks.append(
			profiles.count_documents(
				{
					"workflow_status": {"$in": ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED"]},
					"updated_at": {"$lt": threshold},
				}
			)
		)

	service_book_entries = getattr(db, "service_book_entries", None)
	if service_book_entries is not None:
		tasks.append(
			service_book_entries.count_documents(
				{
					"payload.status": {"$in": ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED"]},
					"updated_at": {"$lt": threshold},
				}
			)
		)

	leave_applications = getattr(db, "leave_applications", None)
	if leave_applications is not None:
		tasks.append(
			leave_applications.count_documents(
				{
					"status": {"$in": ["SUBMITTED", "RECOMMENDED"]},
					"applied_at": {"$lt": threshold},
				}
			)
		)

	if not tasks:
		return 0

	counts = await asyncio.gather(*tasks)
	return sum(int(count) for count in counts)


from contexts.system_admin.api.workflow_config_helpers import (
	_apply_workflow_overrides,
	_csv_response,
	_validate_system_config_update,
	_validate_transition_override_input,
	_workflow_matrix_payload,
)

@_system_admin_routes.get("/dashboard/stats")
async def get_dashboard_stats(
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
	stuck_payload = await _build_stuck_workflow_payload(db)
	(
		total_users,
		active_users,
		total_employees,
		today_audit_logs,
	) = await asyncio.gather(
		count_users(db, query={}),
		count_users(db, query={"is_active": {"$ne": False}}),
		count_employee_profiles(db),
		count_audit_logs(db, query={"timestamp": {"$gte": start_of_day}}),
	)
	return {
		"users": {"total": total_users, "active": active_users},
		"employees": {"total": total_employees},
		"workflows": {"stuck": stuck_payload["total"]},
		"audit": {"today": today_audit_logs},
	}


@_system_admin_routes.get("/workflows/summary")
async def get_workflow_summary(db=Depends(get_db), current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	return await _build_workflow_summary(db)


@_system_admin_routes.get("/workflows/stuck")
async def get_stuck_workflows(
	days_threshold: int = Query(default=7, ge=1, le=365),
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	return await _build_stuck_workflow_payload(db, days_threshold=days_threshold)


@_system_admin_routes.post("/workflows/unlock/{entity_type}/{entity_id}")
async def unlock_workflow(
	entity_type: str,
	entity_id: str,
	payload: WorkflowUnlockRequest,
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	forbid_system_admin_write(current_user, "workflow unlock")
	return {
		"status": "accepted",
		"message": "Workflow unlock endpoint is in compatibility mode.",
		"entity_type": entity_type,
		"entity_id": entity_id,
		"reason": payload.reason,
	}


@_system_admin_routes.get("/audit/logs")
async def get_audit_logs(
	limit: int = Query(default=50, ge=1, le=500),
	offset: int = Query(default=0, ge=0),
	action_filter: str | None = None,
	entity_type_filter: str | None = None,
	from_timestamp: str | None = None,
	to_timestamp: str | None = None,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	return await _fetch_audit_logs(
		db,
		limit=limit,
		offset=offset,
		action_filter=action_filter,
		entity_type_filter=entity_type_filter,
		from_timestamp=from_timestamp,
		to_timestamp=to_timestamp,
	)


@_system_admin_routes.get("/audit/stats")
async def get_audit_stats(db=Depends(get_db), current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	return await _build_audit_stats(db)


@_system_admin_routes.get("/audit/export")
async def export_audit_logs(
	limit: int = Query(default=10000, ge=1, le=50000),
	action_filter: str | None = None,
	entity_type_filter: str | None = None,
	from_timestamp: str | None = None,
	to_timestamp: str | None = None,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	query = _build_audit_query(
		action_filter=action_filter,
		entity_type_filter=entity_type_filter,
		from_timestamp=from_timestamp,
		to_timestamp=to_timestamp,
	)
	return StreamingResponse(
		_stream_audit_export_csv(db, query=query, limit=limit),
		media_type="text/csv",
		headers={"Content-Disposition": 'attachment; filename="audit_logs.csv"'},
	)


@_system_admin_routes.get("/config")
async def get_config(db=Depends(get_db), current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	config = await identity_get_system_config(db)
	return {"config": config}


@_system_admin_routes.put("/config/{key}")
async def update_config(
	key: str,
	payload: SystemConfigUpdate,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	if key != payload.key:
		raise HTTPException(status_code=400, detail="Path key and payload key mismatch")
	validated_value = _validate_system_config_update(key, payload.value)
	updated_by = str(current_user.get("sub") or current_user.get("id") or "system_admin")
	config = await identity_set_system_config_key(
		db,
		key=key,
		value=validated_value,
		updated_by=updated_by,
		reason=payload.reason,
	)
	return {
		"status": "updated",
		"key": key,
		"value": validated_value,
		"reason": payload.reason,
		"config": config,
	}


@_system_admin_routes.get("/employees")
async def list_employees(
	limit: int = Query(default=50, ge=1, le=500),
	offset: int = Query(default=0, ge=0),
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
	search: str | None = None,
	department: str | None = None,
	employment_type: str | None = None,
	workflow_status: str | None = None,
):
	_ensure_system_admin(current_user)
	employees = await list_profiles(
		db,
		search=search,
		workflow_status=workflow_status,
		employment_type=employment_type,
		department_code=department,
		limit=limit,
		offset=offset,
	)
	total = await count_employee_profiles(
		db,
		search=search,
		workflow_status=workflow_status,
		employment_type=employment_type,
		department_code=department,
	)
	return {"employees": employees, "total": total, "limit": limit, "offset": offset}


@_system_admin_routes.get("/employees/{employee_id}")
async def get_employee(employee_id: str, db=Depends(get_db), current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	employee = await find_profile_view(db, employee_id=employee_id, projection={"_id": 0})
	if not employee:
		raise HTTPException(status_code=404, detail="Employee not found")
	entries_count = await count_servicebook_entries(db, employee_id=employee_id)
	return {"employee": employee, "service_book_entries_count": entries_count}


@_system_admin_routes.post("/employees/{employee_id}/delete")
async def delete_employee(
	employee_id: str,
	payload: EmployeeDeleteRequest,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	forbid_system_admin_write(current_user, "employee deletion")
	profile = await find_profile_view(db, employee_id=employee_id, projection={"_id": 0})
	if not profile:
		raise HTTPException(status_code=404, detail="Employee not found")

	entries_count = await count_servicebook_entries(db, employee_id=employee_id)
	if entries_count > 0:
		raise HTTPException(
			status_code=409,
			detail={
				"error_code": "SERVICE_BOOK_ENTRIES_EXIST",
				"message": "Employee cannot be deleted because service book entries exist.",
				"employee_id": employee_id,
				"service_book_entries_count": entries_count,
			},
		)

	actor = str(current_user.get("sub") or current_user.get("id") or "system_admin")
	await archive_and_delete_profile(
		db,
		employee_id=employee_id,
		actor_user_id=actor,
		reason=payload.reason,
	)
	await delete_identity(db, employee_id=employee_id)
	return {
		"status": "deleted",
		"employee_id": employee_id,
		"reason": payload.reason,
	}


@_system_admin_routes.get("/leave/overview")
async def get_leave_overview(
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
	department: str | None = None,
):
	_ensure_system_admin(current_user)
	employee_ids = None
	if department:
		employee_ids = await get_employee_ids_for_department(db, department_code=department)

	total = await count_leave_applications(db, employee_ids=employee_ids)
	pending_submitted = await count_leave_applications(db, employee_ids=employee_ids, status="SUBMITTED")
	pending_recommended = await count_leave_applications(db, employee_ids=employee_ids, status="RECOMMENDED")
	pending_count = pending_submitted + pending_recommended

	statuses = ["SUBMITTED", "RECOMMENDED", "SANCTIONED", "REJECTED", "CANCELLED"]
	by_status = {
		status: await count_leave_applications(db, employee_ids=employee_ids, status=status)
		for status in statuses
	}

	recent = await list_leave_applications(db, employee_ids=employee_ids, limit=500, offset=0)
	leave_type_counts: dict[str, int] = {}
	for item in recent:
		code = str(item.get("leave_type_code") or "UNKNOWN")
		leave_type_counts[code] = leave_type_counts.get(code, 0) + 1
	by_type = [{"leave_type_code": k, "count": v} for k, v in sorted(leave_type_counts.items())]

	pending_queue = await list_pending_leave_applications(
		db,
		employee_ids=employee_ids or [],
		statuses=["SUBMITTED", "RECOMMENDED"],
		limit=50,
	) if employee_ids is not None else await list_leave_applications(
		db,
		status="SUBMITTED",
		limit=50,
		offset=0,
	)

	return {
		"total_applications": total,
		"pending_count": pending_count,
		"by_status": by_status,
		"by_type": by_type,
		"pending_queue": pending_queue,
	}


@_system_admin_routes.get("/leave/applications")
async def get_leave_applications(
	limit: int = Query(default=50, ge=1, le=500),
	offset: int = Query(default=0, ge=0),
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
	status: str | None = None,
	leave_type: str | None = None,
	department: str | None = None,
):
	_ensure_system_admin(current_user)
	employee_ids = None
	if department:
		employee_ids = await get_employee_ids_for_department(db, department_code=department)
	items = await list_leave_applications(
		db,
		employee_ids=employee_ids,
		status=status,
		leave_type_code=leave_type,
		limit=limit,
		offset=offset,
	)
	total = await count_leave_applications(
		db,
		employee_ids=employee_ids,
		status=status,
		leave_type_code=leave_type,
	)
	return {"items": items, "total": total, "limit": limit, "offset": offset}


@_system_admin_routes.post("/leave/{leave_id}/admin-cancel")
async def admin_cancel_leave(
	leave_id: str,
	payload: EmployeeDeleteRequest,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	forbid_system_admin_write(current_user, "leave cancellation")
	record = await get_leave_application_by_id(db, leave_id=leave_id)
	if not record:
		raise HTTPException(status_code=404, detail="Leave application not found")

	updated = await admin_cancel_leave_application(
		db,
		leave_id=leave_id,
		reason=payload.reason,
		cancelled_by=str(current_user.get("sub") or current_user.get("id") or "system_admin"),
	)
	return updated


from contexts.system_admin.api.report_routes import (
	report_routes,
	export_employees,
	export_leave_utilization,
	export_seniority_list,
	get_employee_statistics,
	get_leave_utilization,
	get_seniority_list,
)

_system_admin_routes.include_router(report_routes)

@_system_admin_routes.get("/reports/workflow-matrix")
async def get_workflow_matrix(db=Depends(get_db), current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	base_matrix = _workflow_matrix_payload()
	config = await identity_get_system_config(db)
	overrides = (config or {}).get("workflow_matrix_overrides") if isinstance(config, dict) else {}
	return _apply_workflow_overrides(base_matrix, overrides)


@_system_admin_routes.put("/workflow-config/transition")
async def update_transition_override(
	payload: TransitionOverrideRequest,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	workflow_type, from_stage, to_stage, authorities = _validate_transition_override_input(
		workflow_type=payload.workflow_type,
		from_stage=payload.from_stage,
		to_stage=payload.to_stage,
		authorities=payload.authorities,
	)
	config = await identity_get_system_config(db)
	overrides = dict((config or {}).get("workflow_matrix_overrides") or {})
	transitions = dict(overrides.get("transitions") or {})
	override_key = f"{workflow_type}:{from_stage}:{to_stage}"
	transitions[override_key] = {
		"authorities": authorities,
		"reason": payload.reason,
		"updated_by": str(current_user.get("sub") or current_user.get("id") or "system_admin"),
		"updated_at": datetime.now(timezone.utc).isoformat(),
	}
	overrides["transitions"] = transitions
	updated_by = str(current_user.get("sub") or current_user.get("id") or "system_admin")
	await identity_set_system_config_key(
		db,
		key="workflow_matrix_overrides",
		value=overrides,
		updated_by=updated_by,
		reason=payload.reason,
	)
	return {"status": "updated", "override_key": override_key, "authorities": authorities}


@_system_admin_routes.delete("/workflow-config/transition/{workflow_type}/{from_stage}/{to_stage}")
async def delete_transition_override(
	workflow_type: str,
	from_stage: str,
	to_stage: str,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	config = await identity_get_system_config(db)
	overrides = dict((config or {}).get("workflow_matrix_overrides") or {})
	transitions = dict(overrides.get("transitions") or {})
	override_key = f"{workflow_type}:{from_stage}:{to_stage}"
	transitions.pop(override_key, None)
	overrides["transitions"] = transitions
	updated_by = str(current_user.get("sub") or current_user.get("id") or "system_admin")
	await identity_set_system_config_key(
		db,
		key="workflow_matrix_overrides",
		value=overrides,
		updated_by=updated_by,
		reason=f"Revert transition override {override_key}",
	)
	return {"status": "reverted", "override_key": override_key}


@_system_admin_routes.put("/workflow-config/sod-rule")
async def toggle_sod_rule(
	payload: SodToggleRequest,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	config = await identity_get_system_config(db)
	overrides = dict((config or {}).get("workflow_matrix_overrides") or {})
	sod_rules = dict(overrides.get("sod_rules") or {})
	sod_rules[str(payload.rule_index)] = payload.enabled
	overrides["sod_rules"] = sod_rules
	updated_by = str(current_user.get("sub") or current_user.get("id") or "system_admin")
	await identity_set_system_config_key(
		db,
		key="workflow_matrix_overrides",
		value=overrides,
		updated_by=updated_by,
		reason=payload.reason,
	)
	return {"status": "updated", "rule_index": payload.rule_index, "enabled": payload.enabled}


@_system_admin_routes.post("/workflow-config/reset")
async def reset_workflow_config(
	payload: WorkflowConfigResetRequest,
	db=Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	updated_by = str(current_user.get("sub") or current_user.get("id") or "system_admin")
	await identity_set_system_config_key(
		db,
		key="workflow_matrix_overrides",
		value={"transitions": {}, "sod_rules": {}},
		updated_by=updated_by,
		reason=payload.reason,
	)
	return {"status": "reset", "message": "Workflow matrix overrides reset to defaults."}

system_admin_router = APIRouter(prefix="/system-admin", tags=["system-admin"])
sysadmin_router = APIRouter(prefix="/sysadmin", tags=["system-admin-compat"])

system_admin_router.include_router(_system_admin_routes)
