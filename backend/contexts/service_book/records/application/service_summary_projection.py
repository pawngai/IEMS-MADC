from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app_platform.reference_data.contracts.employment_type_master import (
    eligibility_from_master,
    get_employment_type_master,
    normalize_employment_type_code,
)
from contexts.service_book.records.repository.service_summary_repository import (
    EmployeeServiceSummaryRepository,
)
from shared_kernel.events import utc_now_iso


ENGAGEMENT_RECORD_TYPES = {
    "ENGAGEMENT_RECORDED",
    "ENGAGEMENT_RENEWED",
    "ENGAGEMENT_EXTENDED",
    "ENGAGEMENT_RATE_REVISED",
    "CONTRACT_EXECUTED",
    "CONTRACT_RENEWED",
    "WAGES_RATE_REVISED",
}
TERMINATION_RECORD_TYPES = {
    "ENGAGEMENT_TERMINATED",
    "CONTRACT_TERMINATED",
}
REGULARISATION_RECORD_TYPES = {"REGULARISATION_RECORDED"}


def normalize_record_type(value: Any, *, event_type: Any = None) -> str:
    raw = str(value or event_type or "").strip().upper()
    if raw == "ENGAGEMENT":
        return "ENGAGEMENT_RECORDED"
    if raw == "REGULARISATION":
        return "REGULARISATION_RECORDED"
    return raw


def is_engagement_record_type(value: Any, *, event_type: Any = None) -> bool:
    record_type = normalize_record_type(value, event_type=event_type)
    return record_type in ENGAGEMENT_RECORD_TYPES or record_type in TERMINATION_RECORD_TYPES


def is_regularisation_record_type(value: Any, *, event_type: Any = None) -> bool:
    return normalize_record_type(value, event_type=event_type) in REGULARISATION_RECORD_TYPES


def is_service_summary_projectable(value: Any, *, event_type: Any = None) -> bool:
    return is_engagement_record_type(value, event_type=event_type) or is_regularisation_record_type(
        value,
        event_type=event_type,
    )


def _required(value: dict[str, Any], key: str) -> str:
    raw = str(value.get(key) or "").strip()
    if not raw:
        raise HTTPException(status_code=422, detail=f"{key} is required")
    return raw


def validate_service_record_payload(*, record_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized_type = normalize_record_type(record_type)
    if normalized_type in TERMINATION_RECORD_TYPES:
        return payload

    if is_regularisation_record_type(normalized_type):
        employment_type_code = _required(payload, "new_employment_type_code")
    elif is_engagement_record_type(normalized_type):
        employment_type_code = _required(payload, "employment_type_code")
    else:
        return payload

    master = get_employment_type_master(employment_type_code)
    if not master:
        raise HTTPException(status_code=422, detail="employment_type_code is not active")

    if master["requires_engagement_order"] and not (
        payload.get("engagement_order_no") or payload.get("regularisation_order_no")
    ):
        raise HTTPException(status_code=422, detail="engagement_order_no is required")

    if master["requires_contract_period"]:
        start_value = payload.get("contract_start_date") or payload.get("engagement_start_date")
        end_value = payload.get("contract_end_date") or payload.get("engagement_end_date")
        if not start_value or not end_value:
            raise HTTPException(
                status_code=422,
                detail="contract_start_date and contract_end_date are required",
            )
    return payload


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _field_value(payload: dict[str, Any], current: dict[str, Any], target_key: str, *payload_keys: str) -> Any:
    keys = payload_keys or (target_key,)
    return _first_present(
        *(payload.get(key) for key in keys),
        current.get(target_key),
    )


class EmployeeServiceSummaryProjectionService:
    def __init__(self, *, repository: EmployeeServiceSummaryRepository) -> None:
        self._repository = repository

    async def get_summary(self, *, employee_id: str) -> dict[str, Any] | None:
        return await self._repository.get_summary(employee_id=employee_id)

    async def project_posted_record(self, *, service_record: dict[str, Any]) -> dict[str, Any] | None:
        payload = service_record.get("payload") or {}
        record_type = normalize_record_type(
            payload.get("record_type"),
            event_type=service_record.get("event_type"),
        )
        if not is_service_summary_projectable(record_type):
            return None

        if record_type in TERMINATION_RECORD_TYPES:
            current = await self._repository.get_summary(employee_id=service_record["employee_id"])
            if current is None:
                current = {"employee_id": service_record["employee_id"], "projection_warnings": []}
            next_summary = {
                **current,
                "current_service_status": "TERMINATED",
                "source_record_id": service_record["service_event_id"],
                "last_projected_at": utc_now_iso(),
            }
            return await self._repository.upsert_summary(
                employee_id=service_record["employee_id"],
                summary=next_summary,
            )

        current = await self._repository.get_summary(employee_id=service_record["employee_id"])
        current = current or {}

        if is_regularisation_record_type(record_type):
            employment_type_code = normalize_employment_type_code(
                _first_present(
                    payload.get("new_employment_type_code"),
                    current.get("current_employment_type_code"),
                )
            )
            department_id = _field_value(payload, current, "current_department_id", "new_department_id")
            office_id = _field_value(payload, current, "current_office_id", "new_office_id")
            designation_id = _field_value(payload, current, "current_designation_id", "new_designation_id")
            service_id = _field_value(payload, current, "current_service_id", "new_service_id")
            post_id = _field_value(payload, current, "current_post_id", "sanctioned_post_id")
            service_status = "IN_SERVICE"
        else:
            employment_type_code = normalize_employment_type_code(
                _first_present(
                    payload.get("employment_type_code"),
                    current.get("current_employment_type_code"),
                )
            )
            department_id = _field_value(payload, current, "current_department_id", "department_id")
            office_id = _field_value(payload, current, "current_office_id", "office_id")
            designation_id = _field_value(payload, current, "current_designation_id", "designation_id")
            service_id = _field_value(payload, current, "current_service_id", "service_id")
            post_id = _field_value(payload, current, "current_post_id", "sanctioned_post_id")
            service_status = current.get("current_service_status") or "ENGAGED"

        master = get_employment_type_master(employment_type_code)
        if not master:
            raise HTTPException(status_code=422, detail="employment_type_code is not active")

        engagement_start_date = payload.get("engagement_start_date") or payload.get("contract_start_date") or current.get("engagement_start_date")
        engagement_end_date = payload.get("engagement_end_date") or payload.get("contract_end_date") or current.get("engagement_end_date")

        summary = {
            "employee_id": service_record["employee_id"],
            "current_post_id": post_id,
            "current_department_id": department_id,
            "current_office_id": office_id,
            "current_designation_id": designation_id,
            "current_service_id": service_id,
            "current_employment_type_code": master["employment_type_code"],
            "current_employment_class": master["employment_class"],
            "current_service_status": service_status,
            "current_pay_level_code": _field_value(payload, current, "current_pay_level_code", "pay_level_code", "current_pay_level_code"),
            "current_service_group_code": _field_value(payload, current, "current_service_group_code", "service_group_code"),
            "engagement_order_no": payload.get("engagement_order_no") or current.get("engagement_order_no"),
            "engagement_start_date": engagement_start_date,
            "engagement_end_date": engagement_end_date,
            "contract_start_date": payload.get("contract_start_date") or current.get("contract_start_date"),
            "contract_end_date": payload.get("contract_end_date") or current.get("contract_end_date"),
            "daily_wage_rate": payload.get("daily_wage_rate") if payload.get("daily_wage_rate") is not None else current.get("daily_wage_rate"),
            "fixed_monthly_amount": payload.get("fixed_monthly_amount") if payload.get("fixed_monthly_amount") is not None else current.get("fixed_monthly_amount"),
            **eligibility_from_master(master),
            "source_record_id": service_record["service_event_id"],
            "last_projected_at": utc_now_iso(),
            "projection_warnings": [],
        }
        return await self._repository.upsert_summary(
            employee_id=service_record["employee_id"],
            summary=summary,
        )
