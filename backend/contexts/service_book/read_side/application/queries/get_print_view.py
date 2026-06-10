from __future__ import annotations

async def build_part_print_view(*, repo, employee_id: str, part_key: str, normalize_part_code_fn) -> dict:
	part_code = normalize_part_code_fn(part_key)
	if not part_code:
		return {
			"employee_id": employee_id,
			"part_key": part_key,
			"generated_at": None,
			"entries": [],
			"print_templates": [],
		}

	entries = await repo.list_entries(
		employee_id=employee_id,
		filters={"part_code": part_code},
	)
	return {
		"employee_id": employee_id,
		"part_key": part_code,
		"generated_at": entries[0].get("created_at") if entries else None,
		"entries": entries,
		"print_templates": [],
	}


async def build_full_print_view(*, repo, employee_id: str) -> dict:
	entries = await repo.list_entries(employee_id=employee_id, filters={})
	grouped: dict[str, list[dict]] = {}
	for row in entries:
		grouped.setdefault(row.get("part_code") or "UNKNOWN", []).append(row)

	return {
		"employee_id": employee_id,
		"generated_at": entries[0].get("created_at") if entries else None,
		"parts": grouped,
	}
