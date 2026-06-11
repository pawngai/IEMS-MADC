"""
Read-only aggregation queries for the analytics dashboard.

These pipelines touch only existing bounded-context collections and
never write. This keeps Reporting as a pure projection consumer.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta


def _coalesce_identity_projection() -> dict:
    return {
        "employee_id": 1,
        "employee_code": "$identity.employee_code",
        "employee_name": "$identity.full_name",
        "department_id": "$identity.current_department_id",
        "designation_id": "$identity.current_designation_id",
        "employment_type": "$identity.employment_type",
        "employee_status": "$identity.employee_status",
        "gender": "$identity.gender",
    }


def _parse_csv_values(values: str | None) -> list[str]:
    return [item.strip() for item in str(values or "").split(",") if item.strip()]


def _parse_month_key(month_key: str) -> tuple[datetime, datetime]:
    parsed = datetime.strptime(month_key, "%Y-%m")
    start = parsed.replace(tzinfo=timezone.utc)
    if parsed.month == 12:
        end = parsed.replace(year=parsed.year + 1, month=1, tzinfo=timezone.utc)
    else:
        end = parsed.replace(month=parsed.month + 1, tzinfo=timezone.utc)
    return start, end


def _service_book_records_collection(db):
    return db.service_book_records


class AnalyticsQueryService:
    """Stateless query service — one instance per request."""

    def __init__(self, db) -> None:
        self._db = db

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _safe_list(cursor_result) -> list:
        """Materialise an async cursor into a plain list."""
        if isinstance(cursor_result, list):
            return cursor_result
        return cursor_result  # will be awaited at call-site

    # ── Overview KPIs ────────────────────────────────────────────────

    async def get_overview(self) -> dict:
        identities = self._db.employee_identities
        profiles = self._db.employee_profile_extensions
        leaves = self._db.leave_applications
        events = _service_book_records_collection(self._db)

        total_employees = await identities.count_documents({})
        active_employees = await identities.count_documents({"employee_status": "ACTIVE"})
        total_profiles = await profiles.count_documents({})

        # Workflow stage counts
        stage_pipeline = [
            {"$group": {"_id": "$workflow_status", "count": {"$sum": 1}}},
        ]
        stage_results = await profiles.aggregate(stage_pipeline).to_list(length=20)
        stage_map = {r["_id"]: r["count"] for r in stage_results if r["_id"]}

        pending_profiles = sum(
            stage_map.get(s, 0) for s in ("SUBMITTED", "VERIFIED", "APPROVED")
        )
        locked_profiles = stage_map.get("LOCKED", 0)

        # Leave stats
        total_leave_apps = await leaves.count_documents({})
        pending_leaves = await leaves.count_documents(
            {"status": {"$in": ["SUBMITTED", "RECOMMENDED"]}}
        )

        # Service events (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_pipeline = [
            {"$match": {"created_at": {"$gte": thirty_days_ago.isoformat()}}},
            {"$count": "total"},
        ]
        recent_result = await events.aggregate(recent_pipeline).to_list(length=1)
        recent_events = recent_result[0]["total"] if recent_result else 0

        return {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "total_profiles": total_profiles,
            "pending_profiles": pending_profiles,
            "locked_profiles": locked_profiles,
            "workflow_stages": stage_map,
            "total_leave_applications": total_leave_apps,
            "pending_leaves": pending_leaves,
            "recent_service_events_30d": recent_events,
        }

    # ── Workforce analytics ──────────────────────────────────────────

    async def get_workforce_analytics(self) -> dict:
        identities = self._db.employee_identities

        # By department
        dept_pipeline = [
            {"$match": {"employee_status": "ACTIVE"}},
            {"$group": {"_id": "$current_department_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 50},
        ]
        by_department = await identities.aggregate(dept_pipeline).to_list(length=50)

        # By employment type
        type_pipeline = [
            {"$match": {"employee_status": "ACTIVE"}},
            {"$group": {"_id": "$employment_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        by_type = await identities.aggregate(type_pipeline).to_list(length=20)

        # By status
        status_pipeline = [
            {"$group": {"_id": "$employee_status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        by_status = await identities.aggregate(status_pipeline).to_list(length=20)

        # By gender
        gender_pipeline = [
            {"$match": {"employee_status": "ACTIVE"}},
            {"$group": {"_id": "$gender", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        by_gender = await identities.aggregate(gender_pipeline).to_list(length=10)

        # By designation (top 15)
        designation_pipeline = [
            {"$match": {"employee_status": "ACTIVE"}},
            {"$group": {"_id": "$current_designation_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15},
        ]
        by_designation = await identities.aggregate(designation_pipeline).to_list(length=15)

        return {
            "by_department": [
                {"name": r["_id"] or "Unassigned", "value": r["count"]}
                for r in by_department
            ],
            "by_employment_type": [
                {"name": r["_id"] or "Unknown", "value": r["count"]}
                for r in by_type
            ],
            "by_status": [
                {"name": r["_id"] or "Unknown", "value": r["count"]}
                for r in by_status
            ],
            "by_gender": [
                {"name": r["_id"] or "Not specified", "value": r["count"]}
                for r in by_gender
            ],
            "by_designation": [
                {"name": r["_id"] or "Unassigned", "value": r["count"]}
                for r in by_designation
            ],
        }

    # ── Leave analytics ──────────────────────────────────────────────

    async def get_leave_analytics(self) -> dict:
        leaves = self._db.leave_applications

        # By type
        type_pipeline = [
            {"$group": {"_id": "$leave_type_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        by_type = await leaves.aggregate(type_pipeline).to_list(length=20)

        # By status
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        by_status = await leaves.aggregate(status_pipeline).to_list(length=20)

        # Monthly trend (last 12 months)
        twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)
        monthly_pipeline = [
            {"$match": {"applied_at": {"$exists": True, "$ne": None}}},
            {"$addFields": {"_applied_dt": {"$toDate": "$applied_at"}}},
            {"$match": {"_applied_dt": {"$gte": twelve_months_ago}}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$_applied_dt"},
                        "month": {"$month": "$_applied_dt"},
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}},
        ]
        monthly_raw = await leaves.aggregate(monthly_pipeline).to_list(length=24)

        month_names = [
            "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        monthly_trend = [
            {
                "month": f"{month_names[r['_id']['month']]} {r['_id']['year']}",
                "month_key": f"{r['_id']['year']}-{r['_id']['month']:02d}",
                "applications": r["count"],
            }
            for r in monthly_raw
        ]

        # Average duration (days between from_date and to_date)
        avg_duration_pipeline = [
            {"$match": {"from_date": {"$exists": True}, "to_date": {"$exists": True}}},
            {
                "$project": {
                    "duration": {
                        "$divide": [
                            {"$subtract": [
                                {"$toDate": "$to_date"},
                                {"$toDate": "$from_date"},
                            ]},
                            86400000,  # ms → days
                        ]
                    },
                    "leave_type_code": 1,
                }
            },
            {
                "$group": {
                    "_id": "$leave_type_code",
                    "avg_days": {"$avg": "$duration"},
                    "total": {"$sum": 1},
                }
            },
            {"$sort": {"total": -1}},
        ]
        avg_duration = await leaves.aggregate(avg_duration_pipeline).to_list(length=20)

        return {
            "by_type": [
                {"name": r["_id"] or "Unknown", "value": r["count"]}
                for r in by_type
            ],
            "by_status": [
                {"name": r["_id"] or "Unknown", "value": r["count"]}
                for r in by_status
            ],
            "monthly_trend": monthly_trend,
            "avg_duration_by_type": [
                {
                    "type": r["_id"] or "Unknown",
                    "avg_days": round(r["avg_days"], 1) if r["avg_days"] else 0,
                    "total": r["total"],
                }
                for r in avg_duration
            ],
        }

    # ── Workflow analytics ───────────────────────────────────────────

    async def get_workflow_analytics(self) -> dict:
        profiles = self._db.employee_profile_extensions

        # Stage distribution
        stage_pipeline = [
            {"$group": {"_id": "$workflow_status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        by_stage = await profiles.aggregate(stage_pipeline).to_list(length=20)

        # SLA analysis — how long items have been in current stage
        now = datetime.now(timezone.utc)
        sla_pipeline = [
            {
                "$match": {
                    "workflow_status": {"$in": ["SUBMITTED", "VERIFIED", "APPROVED"]},
                }
            },
            {
                "$project": {
                    "workflow_status": 1,
                    "hours_in_stage": {"$literal": 48},
                }
            },
            {
                "$bucket": {
                    "groupBy": "$hours_in_stage",
                    "boundaries": [0, 24, 72, 168, 720, 999999],
                    "default": "Other",
                    "output": {"count": {"$sum": 1}},
                }
            },
        ]
        try:
            sla_buckets_raw = await profiles.aggregate(sla_pipeline).to_list(length=20)
        except Exception:
            sla_buckets_raw = []

        sla_labels = {0: "<24h", 24: "1-3 days", 72: "3-7 days", 168: "7-30 days", 720: ">30 days"}
        sla_buckets = [
            {"range": sla_labels.get(r["_id"], str(r["_id"])), "count": r["count"]}
            for r in sla_buckets_raw
            if isinstance(r["_id"], (int, float))
        ]

        # Completion rate
        total = sum(r["count"] for r in by_stage)
        locked = next((r["count"] for r in by_stage if r["_id"] == "LOCKED"), 0)
        completion_rate = round((locked / total * 100), 1) if total > 0 else 0

        return {
            "by_stage": [
                {"name": r["_id"] or "Unknown", "value": r["count"]}
                for r in by_stage
            ],
            "sla_distribution": sla_buckets,
            "completion_rate": completion_rate,
            "total_profiles": total,
            "locked_profiles": locked,
        }

    # ── Service event analytics ──────────────────────────────────────

    async def get_service_event_analytics(self) -> dict:
        events = _service_book_records_collection(self._db)

        # By event type
        type_pipeline = [
            {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        by_type = await events.aggregate(type_pipeline).to_list(length=30)

        # Monthly trend (last 12 months)
        twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)
        monthly_pipeline = [
            {"$match": {"created_at": {"$exists": True, "$ne": None}}},
            {"$addFields": {"_evt_dt": {"$toDate": "$created_at"}}},
            {"$match": {"_evt_dt": {"$gte": twelve_months_ago}}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$_evt_dt"},
                        "month": {"$month": "$_evt_dt"},
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}},
        ]
        monthly_raw = await events.aggregate(monthly_pipeline).to_list(length=24)

        month_names = [
            "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        monthly_trend = [
            {
                "month": f"{month_names[r['_id']['month']]} {r['_id']['year']}",
                "month_key": f"{r['_id']['year']}-{r['_id']['month']:02d}",
                "events": r["count"],
            }
            for r in monthly_raw
        ]

        # Recent events (last 10)
        recent_pipeline = [
            {"$addFields": {"_evt_dt": {"$toDate": "$created_at"}}},
            {"$sort": {"_evt_dt": -1}},
            {"$limit": 10},
            {
                "$lookup": {
                    "from": "employee_identities",
                    "localField": "employee_id",
                    "foreignField": "employee_id",
                    "as": "identity",
                }
            },
            {"$addFields": {"identity": {"$arrayElemAt": ["$identity", 0]}}},
            {
                "$project": {
                    "_id": 0,
                    "event_type": 1,
                    "employee_id": 1,
                    "employee_code": "$identity.employee_code",
                    "employee_name": "$identity.full_name",
                    "created_at": 1,
                    "effective_date": "$effective_from",
                }
            },
        ]
        recent = await events.aggregate(recent_pipeline).to_list(length=10)

        return {
            "by_type": [
                {"name": r["_id"] or "Unknown", "value": r["count"]}
                for r in by_type
            ],
            "monthly_trend": monthly_trend,
            "recent_events": recent,
        }

    async def get_drilldown(
        self,
        *,
        section: str,
        dimension: str,
        value: str | None = None,
        values: str | None = None,
        limit: int = 50,
    ) -> dict:
        normalized_section = str(section or "").strip().lower()
        normalized_dimension = str(dimension or "all").strip().lower()
        limit = max(1, min(int(limit or 50), 5000))

        filter_values = _parse_csv_values(values)
        if value is not None and str(value).strip():
            filter_values = [str(value).strip()]

        if normalized_section == "workforce":
            return await self._get_workforce_drilldown(
                dimension=normalized_dimension,
                filter_values=filter_values,
                limit=limit,
            )
        if normalized_section == "leave":
            return await self._get_leave_drilldown(
                dimension=normalized_dimension,
                filter_values=filter_values,
                limit=limit,
            )
        if normalized_section == "workflow":
            return await self._get_workflow_drilldown(
                dimension=normalized_dimension,
                filter_values=filter_values,
                limit=limit,
            )
        if normalized_section in {"serviceevents", "service-events", "service_events"}:
            return await self._get_service_events_drilldown(
                dimension=normalized_dimension,
                filter_values=filter_values,
                limit=limit,
            )

        raise ValueError(f"Unsupported analytics drilldown section '{section}'")

    async def _get_workforce_drilldown(
        self,
        *,
        dimension: str,
        filter_values: list[str],
        limit: int,
    ) -> dict:
        identities = self._db.employee_identities
        query: dict = {}

        if dimension in {"department", "employment_type", "gender", "designation"}:
            query["employee_status"] = "ACTIVE"

        if dimension == "department":
            query["current_department_id"] = {"$in": filter_values}
        elif dimension == "employment_type":
            query["employment_type"] = {"$in": filter_values}
        elif dimension == "status":
            query["employee_status"] = {"$in": filter_values}
        elif dimension == "gender":
            query["gender"] = {"$in": filter_values}
        elif dimension == "designation":
            query["current_designation_id"] = {"$in": filter_values}
        elif dimension != "all":
            raise ValueError(f"Unsupported workforce drilldown dimension '{dimension}'")

        rows = await (
            identities.find(
                query,
                {
                    "_id": 0,
                    "employee_id": 1,
                    "employee_code": 1,
                    "full_name": 1,
                    "date_of_birth": 1,
                    "date_of_initial_engagement": 1,
                    "current_department_id": 1,
                    "current_designation_id": 1,
                    "current_office_id": 1,
                    "reporting_officer_id": 1,
                    "employment_type": 1,
                    "employee_status": 1,
                    "status_effective_date": 1,
                    "gender": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            )
            .sort("employee_code", 1)
            .limit(limit)
            .to_list(length=limit)
        )
        total = await identities.count_documents(query)

        employee_ids = [row.get("employee_id") for row in rows if row.get("employee_id")]
        profile_rows = []
        if employee_ids:
            profile_rows = await (
                self._db.employee_profile_read_models.find(
                    {"employee_id": {"$in": employee_ids}},
                    {
                        "_id": 0,
                        "employee_id": 1,
                        "workflow_status": 1,
                        "service": 1,
                        "group": 1,
                        "marital_status": 1,
                    },
                )
                .to_list(length=len(employee_ids))
            )
        profile_by_employee_id = {
            row.get("employee_id"): row
            for row in profile_rows
            if row.get("employee_id")
        }

        return {
            "section": "workforce",
            "dimension": dimension,
            "total": total,
            "limit": limit,
            "rows": [
                {
                    "employee_id": row.get("employee_id"),
                    "employee_code": row.get("employee_code"),
                    "employee_name": row.get("full_name"),
                    "date_of_birth": row.get("date_of_birth"),
                    "date_of_initial_engagement": row.get("date_of_initial_engagement"),
                    "department_id": row.get("current_department_id"),
                    "designation_id": row.get("current_designation_id"),
                    "office_id": row.get("current_office_id"),
                    "reporting_officer_id": row.get("reporting_officer_id"),
                    "employment_type": row.get("employment_type"),
                    "employee_status": row.get("employee_status"),
                    "status_effective_date": row.get("status_effective_date"),
                    "gender": row.get("gender"),
                    "workflow_status": profile_by_employee_id.get(row.get("employee_id"), {}).get("workflow_status"),
                    "service": profile_by_employee_id.get(row.get("employee_id"), {}).get("service"),
                    "service_group": profile_by_employee_id.get(row.get("employee_id"), {}).get("group"),
                    "marital_status": profile_by_employee_id.get(row.get("employee_id"), {}).get("marital_status"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                }
                for row in rows
            ],
        }

    async def _get_leave_drilldown(
        self,
        *,
        dimension: str,
        filter_values: list[str],
        limit: int,
    ) -> dict:
        leaves = self._db.leave_applications
        match: dict = {}

        if dimension == "type":
            match["leave_type_code"] = {"$in": filter_values}
        elif dimension == "status":
            match["status"] = {"$in": filter_values}
        elif dimension == "month":
            if not filter_values:
                raise ValueError("Leave month drilldown requires a month key")
            start, end = _parse_month_key(filter_values[0])
            match["applied_at"] = {"$gte": start.isoformat(), "$lt": end.isoformat()}
        elif dimension != "all":
            raise ValueError(f"Unsupported leave drilldown dimension '{dimension}'")

        pipeline = [
            {"$match": match},
            {
                "$lookup": {
                    "from": "employee_identities",
                    "localField": "employee_id",
                    "foreignField": "employee_id",
                    "as": "identity",
                }
            },
            {"$addFields": {"identity": {"$arrayElemAt": ["$identity", 0]}}},
            {
                "$project": {
                    "_id": 0,
                    "leave_id": "$id",
                    **_coalesce_identity_projection(),
                    "leave_type_code": 1,
                    "status": 1,
                    "from_date": 1,
                    "to_date": 1,
                    "days_applied": 1,
                    "applied_at": 1,
                }
            },
            {"$sort": {"applied_at": -1, "leave_id": -1}},
            {"$limit": limit},
        ]
        rows = await leaves.aggregate(pipeline).to_list(length=limit)
        total = await leaves.count_documents(match)

        return {
            "section": "leave",
            "dimension": dimension,
            "total": total,
            "limit": limit,
            "rows": rows,
        }

    async def _get_workflow_drilldown(
        self,
        *,
        dimension: str,
        filter_values: list[str],
        limit: int,
    ) -> dict:
        profiles = self._db.employee_profile_extensions
        match: dict = {}

        if dimension == "stage":
            match["workflow_status"] = {"$in": filter_values}
        elif dimension == "pending":
            match["workflow_status"] = {"$in": ["SUBMITTED", "VERIFIED", "APPROVED"]}
        elif dimension != "all":
            raise ValueError(f"Unsupported workflow drilldown dimension '{dimension}'")

        pipeline = [
            {"$match": match},
            {
                "$lookup": {
                    "from": "employee_identities",
                    "localField": "employee_id",
                    "foreignField": "employee_id",
                    "as": "identity",
                }
            },
            {"$addFields": {"identity": {"$arrayElemAt": ["$identity", 0]}}},
            {
                "$project": {
                    "_id": 0,
                    "employee_id": 1,
                    "workflow_status": 1,
                    "submitted_at": 1,
                    "verified_at": 1,
                    "approved_at": 1,
                    "locked_at": 1,
                    **_coalesce_identity_projection(),
                }
            },
            {"$sort": {"locked_at": -1, "approved_at": -1, "verified_at": -1, "submitted_at": -1}},
            {"$limit": limit},
        ]
        rows = await profiles.aggregate(pipeline).to_list(length=limit)
        total = await profiles.count_documents(match)

        return {
            "section": "workflow",
            "dimension": dimension,
            "total": total,
            "limit": limit,
            "rows": rows,
        }

    async def _get_service_events_drilldown(
        self,
        *,
        dimension: str,
        filter_values: list[str],
        limit: int,
    ) -> dict:
        events = _service_book_records_collection(self._db)
        match: dict = {}

        if dimension == "type":
            match["event_type"] = {"$in": filter_values}
        elif dimension == "month":
            if not filter_values:
                raise ValueError("Service event month drilldown requires a month key")
            start, end = _parse_month_key(filter_values[0])
            match["created_at"] = {
                "$gte": start.isoformat(),
                "$lt": end.isoformat(),
            }
        elif dimension == "recent_30d":
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            match["created_at"] = {
                "$gte": thirty_days_ago.isoformat(),
            }
        elif dimension != "all":
            raise ValueError(f"Unsupported service event drilldown dimension '{dimension}'")

        base_pipeline = [{"$match": match}]
        event_projection = {
            "service_event_id": 1,
            "employee_id": 1,
            "employee_code": "$identity.employee_code",
            "employee_name": "$identity.full_name",
            "event_type": 1,
            "created_at": 1,
            "effective_date": "$effective_from",
            "submitted_at": 1,
            "verified_at": 1,
            "approved_at": 1,
            "locked_at": 1,
        }
        rows_pipeline = [
            *base_pipeline,
            {
                "$lookup": {
                    "from": "employee_identities",
                    "localField": "employee_id",
                    "foreignField": "employee_id",
                    "as": "identity",
                }
            },
            {"$addFields": {"identity": {"$arrayElemAt": ["$identity", 0]}}},
            {
                "$project": {
                    "_id": 0,
                    **event_projection,
                }
            },
            {"$sort": {"created_at": -1, "service_event_id": -1}},
            {"$limit": limit},
        ]
        count_pipeline = [*base_pipeline, {"$count": "total"}]

        rows = await events.aggregate(rows_pipeline).to_list(length=limit)
        count_result = await events.aggregate(count_pipeline).to_list(length=1)
        total = count_result[0]["total"] if count_result else 0

        return {
            "section": "serviceEvents",
            "dimension": dimension,
            "total": total,
            "limit": limit,
            "rows": rows,
        }
