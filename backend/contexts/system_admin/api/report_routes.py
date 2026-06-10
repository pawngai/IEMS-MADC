from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app_platform.auth.current_user import get_current_user
from contexts.rbac.application.access_control import require_system_admin
from contexts.system_admin.api.workflow_config_helpers import _csv_response


report_routes = APIRouter(tags=["system-admin"])


def _ensure_system_admin(current_user: dict) -> None:
	require_system_admin(current_user)
@report_routes.get("/reports/employee-statistics")
async def get_employee_statistics(current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	return {"total": 0, "by_department": [], "by_employment_type": []}


@report_routes.get("/reports/leave-utilization")
async def get_leave_utilization(year: int | None = None, current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	return {"year": year, "totals": {}, "by_leave_type": []}


@report_routes.get("/reports/seniority-list")
async def get_seniority_list(
	limit: int = Query(default=100, ge=1, le=500),
	offset: int = Query(default=0, ge=0),
	current_user: dict = Depends(get_current_user),
):
	_ensure_system_admin(current_user)
	return {"items": [], "total": 0, "limit": limit, "offset": offset}


@report_routes.get("/reports/export/employees")
async def export_employees(current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	return _csv_response("employee_directory.csv", [], ["employee_id", "full_name", "department_code", "employment_type"])


@report_routes.get("/reports/export/leave-utilization")
async def export_leave_utilization(current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	return _csv_response("leave_utilization.csv", [], ["leave_type", "applied", "approved", "rejected"])


@report_routes.get("/reports/export/seniority-list")
async def export_seniority_list(current_user: dict = Depends(get_current_user)):
	_ensure_system_admin(current_user)
	return _csv_response("seniority_list.csv", [], ["employee_id", "full_name", "date_of_initial_engagement", "seniority_rank"])


