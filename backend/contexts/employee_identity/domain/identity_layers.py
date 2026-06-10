from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


IDENTITY_FIELDS = {
    "id",
    "employee_id",
    "employee_code",
    "full_name",
    "gender",
    "date_of_birth",
    "current_designation_id",
    "current_office_id",
    "reporting_officer_id",
    "employee_status",
    "status_effective_date",
    "status_remarks",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "version",
}

EXTENSION_FIELDS = {
    "id",
    "employee_id",
    "employment_type",
    "date_of_initial_engagement",
    "current_department_id",
    "service",
    "pension_scheme",
    "group",
    "mode_of_recruitment",
    "father_name",
    "mother_name",
    "nationality",
    "category",
    "sub_caste",
    "religion",
    "date_of_birth_saka",
    "place_of_birth",
    "blood_group",
    "height_cm",
    "identification_marks",
    "marital_status",
    "spouse_name",
    "educational_qualifications_initial",
    "educational_qualifications_acquired",
    "professional_qualifications",
    "contact",
    "identifiers",
    "photo_url",
    "photo_updated_at",
    "signature_url",
    "thumb_impression_url",
    "workflow_status",
    "workflow_remarks",
    "employee_section_completed",
    "data_entry_section_completed",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "verified_at",
    "verified_by",
    "approved_at",
    "approved_by",
    "locked_at",
    "locked_by",
    "version",
}

CONTACT_FIELDS = {
    "mobile_primary",
    "mobile_alternate",
    "email_personal",
    "email_official",
    "address_line1",
    "address_line2",
    "city",
    "district",
    "state",
    "pincode",
    "present_address_line1",
    "present_address_line2",
    "present_city",
    "present_district",
    "present_state",
    "present_pincode",
    "emergency_name",
    "emergency_phone",
    "emergency_relation",
}

IDENTIFIER_FIELDS = {
    "aadhaar_number",
    "pan_number",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_document(doc: dict[str, Any] | None) -> dict[str, Any]:
    return deepcopy(doc or {})


def split_employee_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    data = normalize_document(payload)
    identity: dict[str, Any] = {}
    extension: dict[str, Any] = {}

    for key, value in data.items():
        if key in IDENTITY_FIELDS:
            identity[key] = value
            continue
        if key in EXTENSION_FIELDS:
            extension[key] = value
            continue
        if key in CONTACT_FIELDS:
            extension.setdefault("contact", {})[key] = value
            continue
        if key in IDENTIFIER_FIELDS:
            extension.setdefault("identifiers", {})[key] = value

    employee_id = identity.get("employee_id") or extension.get("employee_id")
    if employee_id:
        identity.setdefault("employee_id", employee_id)
        extension.setdefault("employee_id", employee_id)

    return identity, extension


def compose_employee_record_view(
    identity: dict[str, Any] | None,
    extension: dict[str, Any] | None,
) -> dict[str, Any]:
    identity_doc = normalize_document(identity)
    for field in IDENTIFIER_FIELDS:
        identity_doc.pop(field, None)
    extension_doc = normalize_document(extension)
    if not identity_doc and not extension_doc:
        return {}

    composed = {**identity_doc, **extension_doc}
    contact = normalize_document(extension_doc.get("contact"))
    identifiers = normalize_document(extension_doc.get("identifiers"))
    composed["contact"] = contact
    composed["identifiers"] = identifiers

    for field in CONTACT_FIELDS:
        if field in contact and field not in composed:
            composed[field] = contact[field]
    for field in IDENTIFIER_FIELDS:
        if field in identifiers and field not in composed:
            composed[field] = identifiers[field]

    if "created_at" not in composed:
        composed["created_at"] = identity_doc.get("created_at") or extension_doc.get("created_at")
    if "updated_at" not in composed:
        composed["updated_at"] = extension_doc.get("updated_at") or identity_doc.get("updated_at")
    if "version" not in composed:
        composed["version"] = max(int(identity_doc.get("version") or 1), int(extension_doc.get("version") or 1))

    return composed


def extract_identity_patch(update_fields: dict[str, Any]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for key, value in normalize_document(update_fields).items():
        if key in IDENTITY_FIELDS and key not in {"id", "employee_id", "created_at", "created_by"}:
            patch[key] = value
    return patch


def extract_extension_patch(update_fields: dict[str, Any]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for key, value in normalize_document(update_fields).items():
        if key in EXTENSION_FIELDS and key not in {"id", "employee_id", "created_at", "created_by"}:
            patch[key] = value
        elif key.startswith("contact.") or key.startswith("identifiers."):
            patch[key] = value
        elif key in CONTACT_FIELDS:
            patch[f"contact.{key}"] = value
        elif key in IDENTIFIER_FIELDS:
            patch[f"identifiers.{key}"] = value
    return patch
