from __future__ import annotations

from typing import Any


REQUIRED_PART_FIELDS = {
    "part_i": (
        "name_in_block_letters",
        "father_name",
        "marital_status",
        "caste_category",
        "date_of_birth_christian",
    ),
    "part_iia": (
        "medical_fitness_certificate",
        "character_verification_done",
        "entries_confirmed",
    ),
    "part_iib": (),
    "part_iii": (),
}


def missing_required_parts(parts: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for part_id, fields in REQUIRED_PART_FIELDS.items():
        part = parts.get(part_id) or {}
        part_missing = [field for field in fields if part.get(field) is None or str(part.get(field)).strip() == ""]
        if part_missing:
            missing[part_id] = part_missing
    return missing
