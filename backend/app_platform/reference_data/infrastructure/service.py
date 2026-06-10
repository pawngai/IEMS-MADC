from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException

from app_platform.reference_data.contracts.employment_rules import (
    check_employment_type_allows_service_book,
    get_available_service_book_parts,
    get_employment_type_rules as resolve_employment_type_rules,
    normalize_employment_type_code,
)
from app_platform.reference_data.contracts.employment_type_master import (
    RETAINED_EMPLOYMENT_TYPE_CODES,
    get_employment_type_master,
    normalize_employment_type_code as normalize_final_employment_type_code,
)
from app_platform.reference_data.infrastructure import repo
from app_platform.reference_data.infrastructure.schemas import (
    DEFAULT_CASTE_CATEGORIES,
    DEFAULT_EMPLOYMENT_TYPES,
    DEFAULT_LEAVE_TYPES,
    DEFAULT_PAY_LEVELS,
    DEFAULT_SERVICE_EVENT_TYPES,
    DEFAULT_SERVICE_GROUPS,
    DEFAULT_SERVICES,
)
from app_platform.reference_data.infrastructure.employee_form_schema import (
    COMMON_FIELDS,
    EMPLOYEE_FORM_SCHEMA,
    EMPLOYMENT_TYPE_FIELDS,
    REJECTED_FIELDS,
    WIZARD_STEPS,
    EmploymentType,
    get_fields_for_employment_type,
)
from app_platform.forms.infrastructure.dynamic_forms import DYNAMIC_FORM_RULES


def _get_dynamic_form_rules() -> dict[str, Any]:
    return DYNAMIC_FORM_RULES


async def get_employment_types(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        types = DEFAULT_EMPLOYMENT_TYPES
    else:
        types = await repo.list_employment_types(db_optional)
    if not types:
        types = DEFAULT_EMPLOYMENT_TYPES
    normalized_types = [normalize_employment_type_record(item) for item in types]
    retained_codes = set(RETAINED_EMPLOYMENT_TYPE_CODES)
    filtered_by_code = {
        code: item
        for item in normalized_types
        if (code := normalize_final_employment_type_code(item.get("code") or item.get("type_code"))) in retained_codes
    }
    if not filtered_by_code:
        filtered_by_code = {
            code: normalize_employment_type_record(item)
            for item in DEFAULT_EMPLOYMENT_TYPES
            if (code := normalize_final_employment_type_code(item.get("code") or item.get("type_code"))) in retained_codes
        }
    return [filtered_by_code[code] for code in RETAINED_EMPLOYMENT_TYPE_CODES if code in filtered_by_code]


async def get_employment_type_rules(
    code: str, db_optional=None
) -> dict[str, Any]:
    normalized_code = normalize_employment_type_code(code)
    resolved_code = normalized_code.value if normalized_code else str(code).strip().upper()

    if db_optional is not None:
        employment_types = await get_employment_types(db_optional)
        for item in employment_types:
            item_code = str(item.get("code") or item.get("type_code") or "").strip().upper()
            if item_code == resolved_code:
                return dict(item.get("rules") or {})

    rules = resolve_employment_type_rules(code)
    if rules:
        return rules
    raise HTTPException(status_code=404, detail="Employment type not found")


def normalize_employment_type_record(record: dict) -> dict[str, Any]:
    meta = record.get("metadata") or {}

    def pick(key: str, default=None):
        value = record.get(key)
        if value is None:
            value = meta.get(key, default)
        return value

    code = normalize_final_employment_type_code(pick("code") or pick("type_code"))
    description = record.get("description") or record.get("name") or meta.get("description") or code
    master = get_employment_type_master(code) or {}
    raw_rules = pick("rules", {}) or {}
    if not isinstance(raw_rules, dict):
        raw_rules = {}

    merged_rules = {
        **(resolve_employment_type_rules(code or "") or {}),
        **raw_rules,
    }
    merged_rules["has_service_book"] = check_employment_type_allows_service_book(code or "")
    merged_rules["service_book_parts"] = get_available_service_book_parts(code or "")

    normalized = dict(record)
    normalized.update(
        {
            **master,
            "code": code,
            "description": description,
            "type_code": code,
            "rules": merged_rules,
        }
    )
    return normalized


def normalize_service_event_type_record(record: dict) -> dict:
    meta = record.get("metadata") or {}

    def pick(key: str, default=None):
        value = record.get(key)
        if value is None:
            value = meta.get(key, default)
        return value

    code = pick("code") or pick("event_code") or meta.get("event_code")
    description = record.get("description") or record.get("name") or meta.get("description")

    return {
        "code": code,
        "description": description,
        "event_code": pick("event_code"),
        "service_book_part": pick("service_book_part"),
        "requires_order_number": bool(pick("requires_order_number", True)),
        "affects_pay": bool(pick("affects_pay", False)),
        "affects_posting": bool(pick("affects_posting", False)),
        "is_active": record.get("is_active", True),
        "version": record.get("version"),
    }


def normalize_leave_type_record(record: dict) -> dict:
    meta = record.get("metadata") or {}

    def pick(key: str, default=None):
        value = record.get(key)
        if value is None:
            value = meta.get(key, default)
        return value

    code = pick("code") or pick("leave_code") or meta.get("leave_code")
    leave_code = pick("leave_code") or code
    description = record.get("description") or record.get("name") or meta.get("description")

    return {
        "code": code,
        "description": description,
        "leave_code": leave_code,
        "max_days_per_year": pick("max_days_per_year"),
        "is_encashable": bool(pick("is_encashable", False)),
        "is_accumulative": bool(pick("is_accumulative", False)),
        "applicable_employment_types": pick("applicable_employment_types", []) or [],
        "is_active": record.get("is_active", True),
        "version": record.get("version"),
    }


async def get_service_event_types(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        types = DEFAULT_SERVICE_EVENT_TYPES
    else:
        types = await repo.list_service_event_types(db_optional)
    if not types:
        types = DEFAULT_SERVICE_EVENT_TYPES
    return [normalize_service_event_type_record(t) for t in types if t.get("is_active", True)]


async def get_leave_types(
    db_optional, *, employment_type_code: Optional[str]
) -> list[dict[str, Any]]:
    if db_optional is None:
        types = DEFAULT_LEAVE_TYPES
    else:
        types = await repo.list_leave_types(db_optional)
    if not types:
        types = DEFAULT_LEAVE_TYPES
    normalized = [normalize_leave_type_record(t) for t in types if t.get("is_active", True)]
    if employment_type_code:
        normalized = [
            t
            for t in normalized
            if employment_type_code in (t.get("applicable_employment_types") or [])
        ]
    return normalized


async def get_pay_levels(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        return DEFAULT_PAY_LEVELS
    levels = await repo.list_pay_levels(db_optional)
    return levels or DEFAULT_PAY_LEVELS


async def get_service_groups(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        return DEFAULT_SERVICE_GROUPS
    groups = await repo.list_service_groups(db_optional)
    return groups or DEFAULT_SERVICE_GROUPS


async def get_services(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        return DEFAULT_SERVICES
    services = await repo.list_services(db_optional)
    return services or DEFAULT_SERVICES


async def get_caste_categories(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        return DEFAULT_CASTE_CATEGORIES
    categories = await repo.list_caste_categories(db_optional)
    return categories or DEFAULT_CASTE_CATEGORIES


async def get_departments(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        return []
    return await repo.list_departments(db_optional)


async def get_designations(db_optional) -> list[dict[str, Any]]:
    if db_optional is None:
        return []
    return await repo.list_designations(db_optional)


async def get_offices(
    db_optional, *, department_code: Optional[str]
) -> list[dict[str, Any]]:
    if db_optional is None:
        return []
    return await repo.list_offices(db_optional, department_code=department_code)


async def get_form_config(form_id: str, *, employment_type_code: Optional[str]) -> dict[str, Any]:
    config = _get_dynamic_form_rules().get(form_id)
    if not config:
        raise HTTPException(status_code=404, detail="Form configuration not found")

    if employment_type_code:
        filtered_sections: list[dict[str, Any]] = []
        for section in config.get("sections", []):
            filtered_fields = []
            for field in section.get("fields", []):
                visibility = field.get("visibility", {})
                if visibility.get("all_employment_types", False):
                    filtered_fields.append(field)
                elif employment_type_code in visibility.get("employment_types", []):
                    filtered_fields.append(field)
            if filtered_fields:
                filtered_sections.append({**section, "fields": filtered_fields})
        return {**config, "sections": filtered_sections}

    return config


async def get_employee_form_schema(*, employment_type: Optional[str]) -> dict[str, Any]:
    if employment_type:
        try:
            emp_type = EmploymentType(employment_type)
            fields = get_fields_for_employment_type(employment_type)
            type_specific = EMPLOYMENT_TYPE_FIELDS.get(emp_type, [])
            return {
                "common_fields": COMMON_FIELDS,
                "type_specific_fields": type_specific,
                "all_fields": fields,
                "wizard_steps": WIZARD_STEPS,
                "employment_type": employment_type,
                "rejected_fields": REJECTED_FIELDS,
            }
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid employment type: {employment_type}")

    return EMPLOYEE_FORM_SCHEMA


async def get_employee_form_fields(employment_type: str) -> dict[str, Any]:
    try:
        fields = get_fields_for_employment_type(employment_type)
        return {
            "employment_type": employment_type,
            "fields": fields,
            "wizard_steps": WIZARD_STEPS,
            "total_fields": len(fields),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
