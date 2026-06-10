from typing import Any

from contexts.employee_profile.contracts.workflow_status_utils import normalize_workflow_status


_COMPLETION_SECTIONS = {
    "personal": [
        "father_name", "mother_name", "religion", "blood_group",
        "category", "marital_status",
    ],
    "id_documents": [
        "aadhaar_number", "pan_number", "photo_url",
    ],
    "address": [
        "address_line1", "city", "state", "pincode",
        "emergency_name", "emergency_phone",
    ],
    "core": [
        "full_name", "gender", "date_of_birth", "employment_type",
        "date_of_initial_engagement", "current_department_id", "mobile_primary",
    ],
}


def calculate_profile_completion(profile: dict[str, Any]) -> dict[str, Any]:
    sections = {}
    total_filled = 0
    total_fields = 0

    contact = profile.get("contact") or {}
    identifiers = profile.get("identifiers") or {}

    for section_name, fields in _COMPLETION_SECTIONS.items():
        filled = 0
        for field in fields:
            value = profile.get(field) or contact.get(field) or identifiers.get(field)
            if value not in [None, "", 0, False, [], {}]:
                filled += 1
        sections[section_name] = {
            "filled": filled,
            "total": len(fields),
            "percent": round(filled / len(fields) * 100) if fields else 100,
        }
        total_filled += filled
        total_fields += len(fields)

    overall = round(total_filled / total_fields * 100) if total_fields else 0

    return {
        "overall_percent": overall,
        "sections": sections,
        "employee_section_completed": bool(profile.get("employee_section_completed")),
        "data_entry_section_completed": bool(profile.get("data_entry_section_completed")),
    }


def build_bulk_completion_response(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    total_overall = 0
    both_complete_count = 0
    emp_complete_count = 0
    de_complete_count = 0

    for profile in profiles:
        completion = calculate_profile_completion(profile)
        total_overall += completion["overall_percent"]
        if completion["employee_section_completed"]:
            emp_complete_count += 1
        if completion["data_entry_section_completed"]:
            de_complete_count += 1
        if completion["employee_section_completed"] and completion["data_entry_section_completed"]:
            both_complete_count += 1

        results.append({
            "employee_id": profile.get("employee_id"),
            "employee_code": profile.get("employee_code"),
            "full_name": profile.get("full_name"),
            "workflow_status": normalize_workflow_status(profile.get("workflow_status", "DRAFT")) or "DRAFT",
            "overall_percent": completion["overall_percent"],
            "employee_section_completed": completion["employee_section_completed"],
            "data_entry_section_completed": completion["data_entry_section_completed"],
        })

    count = len(profiles)
    average_completion = round(total_overall / count) if count else 0

    return {
        "summary": {
            "total_profiles": count,
            "average_completion": average_completion,
            "employee_section_complete": emp_complete_count,
            "data_entry_section_complete": de_complete_count,
            "both_sections_complete": both_complete_count,
        },
        "profiles": results,
    }
