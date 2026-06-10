from __future__ import annotations

from typing import Any


def normalize_part_i_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload or {})
    parent_name = str(normalized.get("parent_name") or "").strip()
    father_name = str(normalized.get("father_name") or "").strip()
    resolved_parent_name = father_name or parent_name
    if resolved_parent_name:
        normalized["father_name"] = resolved_parent_name
        normalized["parent_name"] = resolved_parent_name

    block_name = str(normalized.get("name_in_block_letters") or "").strip()
    if block_name:
        normalized["name_in_block_letters"] = block_name.upper()

    return normalized


def normalize_passthrough_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return dict(payload or {})
