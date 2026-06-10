from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO

from fastapi.responses import StreamingResponse

from app_platform.reference_data.infrastructure import service as reference_data_service
from contexts.reporting.queries.analytics_queries import AnalyticsQueryService


WORKFLOW_STAGE_LABELS = {
    "DRAFT": "Draft",
    "SUBMITTED": "Submitted",
    "VERIFIED": "Verified",
    "APPROVED": "Approved",
    "LOCKED": "Locked",
}

LEAVE_STATUS_LABELS = {
    "DRAFT": "Draft",
    "SUBMITTED": "Submitted",
    "RECOMMENDED": "Recommended",
    "SANCTIONED": "Sanctioned",
    "APPROVED": "Approved",
    "REJECTED": "Rejected",
    "CANCELLED": "Cancelled",
    "RETURNED": "Returned",
}


def _normalize_code(value: object) -> str:
    return str(value or "").strip().upper()


def _to_title_case(value: object) -> str:
    return " ".join(part.capitalize() for part in str(value or "").replace("_", " ").split())


def _format_category_label(value: object, *, empty_label: str = "Unknown", name_map: dict[str, str] | None = None) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return empty_label

    normalized = _normalize_code(raw_value)
    if name_map and normalized in name_map:
        return name_map[normalized]

    return _to_title_case(raw_value)


def _format_gender_label(value: object) -> str:
    normalized = _normalize_code(value)
    if not normalized:
        return "Not specified"
    if normalized == "MALE":
        return "Male"
    if normalized == "FEMALE":
        return "Female"
    if normalized == "OTHER":
        return "Other"
    return _format_category_label(value, empty_label="Not specified")


def _format_workflow_stage_label(value: object) -> str:
    normalized = _normalize_code(value)
    if not normalized:
        return "Unknown"
    return WORKFLOW_STAGE_LABELS.get(normalized, _to_title_case(normalized))


def _format_leave_status_label(value: object) -> str:
    normalized = _normalize_code(value)
    if not normalized:
        return "Unknown"
    return LEAVE_STATUS_LABELS.get(normalized, _to_title_case(normalized))


def _format_date(value: object, *, include_time: bool = False) -> str:
    if value in (None, ""):
        return ""

    text = str(value).strip()
    if not text:
        return ""

    normalized_text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized_text)
    except ValueError:
        return text

    if include_time:
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if parsed.tzinfo else parsed.strftime("%Y-%m-%d %H:%M")
    return parsed.date().isoformat()


def _sanitize_filename_segment(value: object, fallback: str = "all") -> str:
    normalized = "-".join(
        part for part in "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value or "").strip()).split("-") if part
    )
    return normalized or fallback


def _build_lookup_map(records: list[dict], *, code_keys: tuple[str, ...], label_keys: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for record in records or []:
        code = next((str(record.get(key) or "").strip() for key in code_keys if str(record.get(key) or "").strip()), "")
        label = next((str(record.get(key) or "").strip() for key in label_keys if str(record.get(key) or "").strip()), "")
        if code and label:
            result[_normalize_code(code)] = label
    return result


async def _load_name_maps(db) -> dict[str, dict[str, str]]:
    departments = await reference_data_service.get_departments(db)
    designations = await reference_data_service.get_designations(db)
    offices = await reference_data_service.get_offices(db)
    services = await reference_data_service.get_services(db)
    service_groups = await reference_data_service.get_service_groups(db)
    leave_types = await reference_data_service.get_leave_types(db, employment_type_code=None)
    service_event_types = await reference_data_service.get_service_event_types(db)

    return {
        "departments": _build_lookup_map(departments, code_keys=("code", "department_code"), label_keys=("name", "description")),
        "designations": _build_lookup_map(designations, code_keys=("code", "designation_code"), label_keys=("name", "description")),
        "offices": _build_lookup_map(offices, code_keys=("code", "office_code"), label_keys=("name", "description")),
        "services": _build_lookup_map(services, code_keys=("code", "service_code"), label_keys=("name", "description")),
        "service_groups": _build_lookup_map(service_groups, code_keys=("code", "group_code"), label_keys=("name", "description")),
        "leave_types": _build_lookup_map(leave_types, code_keys=("code", "leave_code"), label_keys=("description", "name")),
        "service_event_types": _build_lookup_map(service_event_types, code_keys=("code", "event_code"), label_keys=("description", "name")),
    }


def _build_export_dataset(*, section: str, rows: list[dict], name_maps: dict[str, dict[str, str]]) -> tuple[list[str], list[dict[str, object]]]:
    departments = name_maps.get("departments") or {}
    designations = name_maps.get("designations") or {}
    offices = name_maps.get("offices") or {}
    services = name_maps.get("services") or {}
    service_groups = name_maps.get("service_groups") or {}
    leave_types = name_maps.get("leave_types") or {}
    service_event_types = name_maps.get("service_event_types") or {}

    if section == "workforce":
        headers = [
            "Employee ID",
            "Employee Code",
            "Employee Name",
            "Department",
            "Designation",
            "Office",
            "Employment Type",
            "Employee Status",
            "Workflow Status",
            "Service",
            "Service Group",
            "Marital Status",
            "Gender",
            "Date of Birth",
            "Initial Engagement",
            "Status Effective",
            "Reporting Officer",
            "Created At",
            "Updated At",
        ]
        export_rows = [
            {
                "Employee ID": row.get("employee_id") or "",
                "Employee Code": row.get("employee_code") or "",
                "Employee Name": row.get("employee_name") or "",
                "Department": _format_category_label(row.get("department_id"), empty_label="Unassigned", name_map=departments),
                "Designation": _format_category_label(row.get("designation_id"), empty_label="Unassigned", name_map=designations),
                "Office": _format_category_label(row.get("office_id"), empty_label="Unassigned", name_map=offices),
                "Employment Type": _format_category_label(row.get("employment_type")),
                "Employee Status": _format_category_label(row.get("employee_status")),
                "Workflow Status": _format_workflow_stage_label(row.get("workflow_status")),
                "Service": _format_category_label(row.get("service"), empty_label="Unassigned", name_map=services),
                "Service Group": _format_category_label(row.get("service_group"), empty_label="Unassigned", name_map=service_groups),
                "Marital Status": _format_category_label(row.get("marital_status"), empty_label="Not specified"),
                "Gender": _format_gender_label(row.get("gender")),
                "Date of Birth": _format_date(row.get("date_of_birth")),
                "Initial Engagement": _format_date(row.get("date_of_initial_engagement")),
                "Status Effective": _format_date(row.get("status_effective_date")),
                "Reporting Officer": row.get("reporting_officer_id") or "",
                "Created At": _format_date(row.get("created_at"), include_time=True),
                "Updated At": _format_date(row.get("updated_at"), include_time=True),
            }
            for row in rows
        ]
        return headers, export_rows

    if section == "workflow":
        headers = [
            "Employee ID",
            "Employee Code",
            "Employee Name",
            "Department",
            "Workflow Stage",
            "Submitted At",
            "Verified At",
            "Approved At",
            "Locked At",
        ]
        export_rows = [
            {
                "Employee ID": row.get("employee_id") or "",
                "Employee Code": row.get("employee_code") or "",
                "Employee Name": row.get("employee_name") or "",
                "Department": _format_category_label(row.get("department_id"), empty_label="Unassigned", name_map=departments),
                "Workflow Stage": _format_workflow_stage_label(row.get("workflow_status")),
                "Submitted At": _format_date(row.get("submitted_at"), include_time=True),
                "Verified At": _format_date(row.get("verified_at"), include_time=True),
                "Approved At": _format_date(row.get("approved_at"), include_time=True),
                "Locked At": _format_date(row.get("locked_at"), include_time=True),
            }
            for row in rows
        ]
        return headers, export_rows

    if section == "leave":
        headers = [
            "Leave ID",
            "Employee ID",
            "Employee Code",
            "Employee Name",
            "Department",
            "Designation",
            "Leave Type",
            "Status",
            "From Date",
            "To Date",
            "Days Applied",
            "Applied At",
        ]
        export_rows = [
            {
                "Leave ID": row.get("leave_id") or "",
                "Employee ID": row.get("employee_id") or "",
                "Employee Code": row.get("employee_code") or "",
                "Employee Name": row.get("employee_name") or "",
                "Department": _format_category_label(row.get("department_id"), empty_label="Unassigned", name_map=departments),
                "Designation": _format_category_label(row.get("designation_id"), empty_label="Unassigned", name_map=designations),
                "Leave Type": _format_category_label(row.get("leave_type_code"), name_map=leave_types),
                "Status": _format_leave_status_label(row.get("status")),
                "From Date": row.get("from_date") or "",
                "To Date": row.get("to_date") or "",
                "Days Applied": row.get("days_applied") if row.get("days_applied") is not None else "",
                "Applied At": _format_date(row.get("applied_at"), include_time=True),
            }
            for row in rows
        ]
        return headers, export_rows

    headers = [
        "Service Event ID",
        "Employee ID",
        "Employee Code",
        "Employee Name",
        "Event Type",
        "Effective Date",
        "Recorded At",
        "Submitted At",
        "Verified At",
        "Approved At",
        "Locked At",
    ]
    export_rows = [
        {
            "Service Event ID": row.get("service_event_id") or "",
            "Employee ID": row.get("employee_id") or "",
            "Employee Code": row.get("employee_code") or "",
            "Employee Name": row.get("employee_name") or "",
            "Event Type": _format_category_label(row.get("event_type"), name_map=service_event_types),
            "Effective Date": _format_date(row.get("effective_date")),
            "Recorded At": _format_date(row.get("created_at"), include_time=True),
            "Submitted At": _format_date(row.get("submitted_at"), include_time=True),
            "Verified At": _format_date(row.get("verified_at"), include_time=True),
            "Approved At": _format_date(row.get("approved_at"), include_time=True),
            "Locked At": _format_date(row.get("locked_at"), include_time=True),
        }
        for row in rows
    ]
    return headers, export_rows


def _build_filename(*, section: str, dimension: str, value: str | None, values: str | None) -> str:
    value_segment = value or values or "selection"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return (
        f"analytics-{_sanitize_filename_segment(section, 'analytics')}-"
        f"{_sanitize_filename_segment(dimension, 'all')}-"
        f"{_sanitize_filename_segment(value_segment, 'selection')}-"
        f"{timestamp}.csv"
    )


async def build_drilldown_csv_response(
    *,
    db,
    section: str,
    dimension: str,
    value: str | None = None,
    values: str | None = None,
    limit: int = 5000,
) -> StreamingResponse:
    drilldown = await AnalyticsQueryService(db).get_drilldown(
        section=section,
        dimension=dimension,
        value=value,
        values=values,
        limit=limit,
    )
    name_maps = await _load_name_maps(db)
    headers, export_rows = _build_export_dataset(
        section=str(drilldown.get("section") or section),
        rows=list(drilldown.get("rows") or []),
        name_maps=name_maps,
    )

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for row in export_rows:
        writer.writerow({header: row.get(header, "") for header in headers})
    buffer.seek(0)

    exported_count = len(export_rows)
    total = int(drilldown.get("total") or exported_count)
    filename = _build_filename(section=section, dimension=dimension, value=value, values=values)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-IEMS-Analytics-Total": str(total),
            "X-IEMS-Analytics-Exported": str(exported_count),
        },
    )