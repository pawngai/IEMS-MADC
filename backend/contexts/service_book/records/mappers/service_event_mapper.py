from __future__ import annotations

from typing import Any

from contexts.service_book.records.domain.value_objects import ServiceRecordType
from contexts.service_book.records.schemas.service_event_schemas import ServiceEventCategory


_CATEGORY_TO_EVENT_TYPE: dict[ServiceEventCategory, ServiceRecordType] = {
    ServiceEventCategory.APPOINTMENT: ServiceRecordType.APPOINTMENT,
    ServiceEventCategory.CONFIRMATION: ServiceRecordType.CONFIRMATION,
    ServiceEventCategory.PROMOTION: ServiceRecordType.PROMOTION,
    ServiceEventCategory.TRANSFER: ServiceRecordType.TRANSFER,
    ServiceEventCategory.PAY: ServiceRecordType.PAY,
    ServiceEventCategory.INCREMENT: ServiceRecordType.INCREMENT,
    ServiceEventCategory.DEPUTATION: ServiceRecordType.DEPUTATION,
    ServiceEventCategory.SUSPENSION: ServiceRecordType.SUSPENSION,
    ServiceEventCategory.REINSTATEMENT: ServiceRecordType.REINSTATEMENT,
    ServiceEventCategory.RETIREMENT: ServiceRecordType.RETIREMENT,
    ServiceEventCategory.DISCIPLINARY: ServiceRecordType.DISCIPLINARY,
    ServiceEventCategory.CUSTOM: ServiceRecordType.GENERIC,
    ServiceEventCategory.GENERIC: ServiceRecordType.GENERIC,
    ServiceEventCategory.FINANCIAL_UPGRADATION: ServiceRecordType.FINANCIAL_UPGRADATION,
    ServiceEventCategory.CPC_PAY_FIXATION: ServiceRecordType.CPC_PAY_FIXATION,
}


def category_to_event_type(category: ServiceEventCategory) -> ServiceRecordType:
    return _CATEGORY_TO_EVENT_TYPE.get(category, ServiceRecordType.GENERIC)


def map_change_request_to_service_event_payload(
    *,
    request_type: str,
    category: str,
    fields: list[dict[str, Any]],
    reason: str,
    entry_id: str | None,
    entry_section: str | None,
    entry_label: str | None,
) -> dict[str, Any]:
    normalized_category = str(category or "GENERIC").strip().upper() or "GENERIC"
    payload_fields: dict[str, Any] = {}
    for item in fields or []:
        key = str(item.get("field_name") or "").strip()
        if not key:
            continue
        payload_fields[key] = item.get("requested_value")

    return {
        "change_request_type": request_type,
        "change_reason": reason,
        "category": normalized_category,
        "entry_id": entry_id,
        "entry_section": entry_section,
        "entry_label": entry_label,
        "fields": payload_fields,
    }


def normalize_service_book_part_code(part_key: str | None, schema_key: str | None) -> str | None:
    part_key_by_roman = {
        "I": "SB_PART_I",
        "II-A": "SB_PART_II_A",
        "II-B": "SB_PART_II_B",
        "III": "SB_PART_III",
        "IV": "SB_PART_IV",
        "V": "SB_PART_V",
        "VI": "SB_PART_VI",
        "VII": "SB_PART_VII",
        "VIII": "SB_PART_VIII",
    }

    normalized = str(part_key or "").strip().upper()
    if normalized in part_key_by_roman:
        return part_key_by_roman[normalized]
    if normalized in set(part_key_by_roman.values()):
        return normalized

    schema = str(schema_key or "").upper()
    by_schema = {
        "PART_I": part_key_by_roman["I"],
        "PART_II_A": part_key_by_roman["II-A"],
        "PART_II_B": part_key_by_roman["II-B"],
        "PART_III": part_key_by_roman["III"],
        "PART_IV": part_key_by_roman["IV"],
        "PART_V": part_key_by_roman["V"],
        "PART_VI": part_key_by_roman["VI"],
        "PART_VII": part_key_by_roman["VII"],
        "PART_VIII": part_key_by_roman["VIII"],
    }
    for token, part_code in by_schema.items():
        if token in schema:
            return part_code
    return None
