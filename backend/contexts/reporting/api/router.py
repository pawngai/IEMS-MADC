"""
Reporting / Analytics API — read-only aggregation endpoints.

All queries run against existing bounded-context collections
via **read-only** aggregation pipelines.  No cross-context writes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app_platform.auth.current_user import get_current_user
from app_platform.db.runtime import get_db
from contexts.identity_access.contracts.access_control import require_permissions
from contexts.identity_access.contracts.models import Permission
from contexts.reporting.queries.analytics_export import build_drilldown_csv_response
from contexts.reporting.queries.analytics_queries import AnalyticsQueryService

reporting_router = APIRouter(prefix="/reporting", tags=["Reporting & Analytics"])


def _require_drilldown_permission(*, section: str, current_user: dict) -> None:
    normalized_section = str(section or "").strip().lower()
    if normalized_section in {"workforce", "workflow"}:
        require_permissions(current_user, Permission.PROFILE_READ_ALL)
        return
    if normalized_section == "leave":
        require_permissions(current_user, Permission.LEAVE_READ_ALL)
        return
    if normalized_section in {"serviceevents", "service-events", "service_events"}:
        require_permissions(current_user, Permission.SERVICE_BOOK_READ_ALL)
        return
    raise HTTPException(status_code=400, detail=f"Unsupported analytics drilldown section '{section}'")


@reporting_router.get("/analytics/overview")
async def get_analytics_overview(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Top-level KPI summary: headcount, leave, workflow, service events."""
    require_permissions(current_user, Permission.PROFILE_READ_ALL)
    svc = AnalyticsQueryService(db)
    return await svc.get_overview()


@reporting_router.get("/analytics/workforce")
async def get_workforce_analytics(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Workforce composition: by department, employment type, status, gender."""
    require_permissions(current_user, Permission.PROFILE_READ_ALL)
    svc = AnalyticsQueryService(db)
    return await svc.get_workforce_analytics()


@reporting_router.get("/analytics/leave")
async def get_leave_analytics(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Leave usage trends: by type, status, monthly distribution."""
    require_permissions(current_user, Permission.LEAVE_READ_ALL)
    svc = AnalyticsQueryService(db)
    return await svc.get_leave_analytics()


@reporting_router.get("/analytics/leave-summary")
async def get_leave_analytics_summary(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Alias for leave analytics used by the frontend dashboard."""
    require_permissions(current_user, Permission.LEAVE_READ_ALL)
    svc = AnalyticsQueryService(db)
    return await svc.get_leave_analytics()


@reporting_router.get("/analytics/workflow")
async def get_workflow_analytics(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Workflow stage distribution and SLA metrics for profiles."""
    require_permissions(current_user, Permission.PROFILE_READ_ALL)
    svc = AnalyticsQueryService(db)
    return await svc.get_workflow_analytics()


@reporting_router.get("/analytics/service-events")
async def get_service_event_analytics(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Service event frequency and type distribution."""
    require_permissions(current_user, Permission.SERVICE_BOOK_READ_ALL)
    svc = AnalyticsQueryService(db)
    return await svc.get_service_event_analytics()


@reporting_router.get("/analytics/drilldown")
async def get_analytics_drilldown(
    section: str = Query(..., min_length=1),
    dimension: str = Query("all", min_length=1),
    value: str | None = Query(None),
    values: str | None = Query(None),
    limit: int = Query(50, ge=1, le=5000),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record-level drilldown for analytics dashboard summaries and charts."""
    _require_drilldown_permission(section=section, current_user=current_user)
    svc = AnalyticsQueryService(db)
    try:
        return await svc.get_drilldown(
            section=section,
            dimension=dimension,
            value=value,
            values=values,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@reporting_router.get("/analytics/drilldown/export")
async def export_analytics_drilldown_csv(
    section: str = Query(..., min_length=1),
    dimension: str = Query("all", min_length=1),
    value: str | None = Query(None),
    values: str | None = Query(None),
    limit: int = Query(5000, ge=1, le=5000),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _require_drilldown_permission(section=section, current_user=current_user)
    try:
        return await build_drilldown_csv_response(
            db=db,
            section=section,
            dimension=dimension,
            value=value,
            values=values,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
