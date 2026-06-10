from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from io import StringIO
import csv
from typing import Any

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from contexts.rbac.domain.models import AUTHORITY_PERMISSIONS, Authority, Permission

def _csv_response(filename: str, rows: list[dict], headers: list[str]) -> StreamingResponse:
	buff = StringIO()
	writer = csv.DictWriter(buff, fieldnames=headers)
	writer.writeheader()
	for row in rows:
		writer.writerow({k: row.get(k, "") for k in headers})
	buff.seek(0)
	return StreamingResponse(
		iter([buff.getvalue()]),
		media_type="text/csv",
		headers={"Content-Disposition": f'attachment; filename="{filename}"'},
	)


def _workflow_matrix_payload() -> dict:
	transitions = [
		{
			"from": "DRAFT",
			"to": "SUBMITTED",
			"action": "submit",
			"required_authorities": ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"],
			"required_permission": "SERVICE_BOOK_ENTRY_SUBMIT",
			"can_edit": True,
			"can_delete": True,
			"is_immutable": False,
			"is_overridden": False,
		},
		{
			"from": "SUBMITTED",
			"to": "VERIFIED",
			"action": "verify",
			"required_authorities": ["VERIFIER", "HOD", "APPROVING_AUTHORITY"],
			"required_permission": "SERVICE_BOOK_ENTRY_VERIFY",
			"can_edit": False,
			"can_delete": False,
			"is_immutable": False,
			"is_overridden": False,
		},
		{
			"from": "VERIFIED",
			"to": "APPROVED",
			"action": "approve",
			"required_authorities": ["DDO", "HOD", "APPROVING_AUTHORITY"],
			"required_permission": "SERVICE_BOOK_ENTRY_APPROVE",
			"can_edit": False,
			"can_delete": False,
			"is_immutable": False,
			"is_overridden": False,
		},
		{
			"from": "APPROVED",
			"to": "ATTESTED",
			"action": "attest",
			"required_authorities": ["APPOINTING_AUTHORITY", "HOD", "APPROVING_AUTHORITY"],
			"required_permission": "SERVICE_BOOK_ENTRY_ATTEST",
			"can_edit": False,
			"can_delete": False,
			"is_immutable": True,
			"is_overridden": False,
		},
		{
			"from": "SUBMITTED",
			"to": "REJECTED",
			"action": "reject",
			"required_authorities": ["VERIFIER", "HOD", "APPROVING_AUTHORITY", "DDO"],
			"required_permission": "SERVICE_BOOK_ENTRY_VERIFY",
			"can_edit": False,
			"can_delete": False,
			"is_immutable": False,
			"is_overridden": False,
		},
	]

	def _clone_transition(transition: dict[str, Any]) -> dict[str, Any]:
		clone = dict(transition)
		clone["required_authorities"] = list(transition.get("required_authorities") or [])
		return clone

	profile_transitions = [_clone_transition(t) for t in transitions]
	service_book_transitions = [_clone_transition(t) for t in transitions]

	return {
		"has_overrides": False,
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"role_authority_map": {
			"DATA_ENTRY": ["DEPT_DATA_ENTRY", "GLOBAL_DATA_ENTRY", "DEALING_ASSISTANT"],
			"VERIFY": ["VERIFIER", "HOD", "APPROVING_AUTHORITY"],
			"APPROVE": ["DDO", "HOD", "APPROVING_AUTHORITY"],
			"ATTEST": ["APPOINTING_AUTHORITY", "HOD", "APPROVING_AUTHORITY"],
		},
		"sod_rules": [
			{
				"index": 0,
				"name": "Data-entry and attestation must be separated",
				"description": "The same authority must not both create and attest records.",
				"prohibited_roles": ["DATA_ENTRY", "ATTEST"],
				"reason": "Maker-checker separation",
				"enabled": True,
			}
		],
		"workflows": {
			"profile": {
				"name": "Employee Profile",
				"stages": ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "LOCKED", "REJECTED"],
				"final_stage": "LOCKED",
				"transitions": profile_transitions,
			},
			"service_book": {
				"name": "Service Book",
				"stages": ["DRAFT", "SUBMITTED", "VERIFIED", "APPROVED", "ATTESTED", "REJECTED"],
				"final_stage": "ATTESTED",
				"transitions": service_book_transitions,
			},
			"leave": {
				"name": "Leave Application",
				"stages": ["DRAFT", "SUBMITTED", "RECOMMENDED", "SANCTIONED", "REJECTED", "CANCELLED"],
				"final_stage": "SANCTIONED",
				"transitions": [
					{
						"from": "DRAFT",
						"to": "SUBMITTED",
						"action": "submit",
						"required_authorities": ["EMPLOYEE"],
						"required_permission": "LEAVE_APPLY_OWN",
						"can_edit": True,
						"can_delete": True,
						"is_immutable": False,
						"is_overridden": False,
					},
					{
						"from": "SUBMITTED",
						"to": "RECOMMENDED",
						"action": "recommend",
						"required_authorities": ["HOD"],
						"required_permission": "LEAVE_RECOMMEND",
						"can_edit": False,
						"can_delete": False,
						"is_immutable": False,
						"is_overridden": False,
					},
					{
						"from": "RECOMMENDED",
						"to": "SANCTIONED",
						"action": "sanction",
						"required_authorities": ["APPROVING_AUTHORITY", "DDO"],
						"required_permission": "LEAVE_SANCTION",
						"can_edit": False,
						"can_delete": False,
						"is_immutable": True,
						"is_overridden": False,
					},
				],
			},
		},
	}


def _build_authority_permissions() -> dict[str, list[str]]:
	matrix: dict[str, list[str]] = {}
	for authority in Authority:
		permissions = sorted(permission.value for permission in AUTHORITY_PERMISSIONS.get(authority, set()))
		matrix[authority.value] = permissions
	return matrix


def _build_role_permissions(
	role_authority_map: dict[str, list[str]],
	authority_permissions: dict[str, list[str]],
) -> dict[str, list[str]]:
	role_permissions: dict[str, list[str]] = {}
	for role, authorities in (role_authority_map or {}).items():
		perms: set[str] = set()
		for authority in authorities or []:
			perms.update(authority_permissions.get(authority, []))
		role_permissions[role] = sorted(perms)
	return role_permissions


def _normalize_contract(matrix: dict) -> dict:
	authority_permissions = _build_authority_permissions()
	all_permissions = sorted(permission.value for permission in Permission)
	role_authority_map = matrix.get("role_authority_map") or {}
	role_permissions = _build_role_permissions(role_authority_map, authority_permissions)

	sod_rules = matrix.get("sod_rules") or []
	separation_of_duties: list[dict] = []
	for idx, rule in enumerate(sod_rules):
		rule_index = int(rule.get("index", idx))
		prohibited_roles = rule.get("prohibited_roles") or ["DATA_ENTRY", "ATTEST"]
		reason = str(rule.get("reason") or rule.get("description") or "Separation-of-duties rule")
		separation_of_duties.append(
			{
				"index": rule_index,
				"prohibited_roles": prohibited_roles,
				"enabled": bool(rule.get("enabled", True)),
				"reason": reason,
			}
		)

	matrix["authority_permissions"] = authority_permissions
	matrix["all_permissions"] = all_permissions
	matrix["role_permissions"] = role_permissions
	matrix["separation_of_duties"] = separation_of_duties
	matrix["sod_rules"] = separation_of_duties
	return matrix

_NUMERIC_CONFIG_RANGES: dict[str, tuple[int, int]] = {
	"session_timeout_minutes": (1, 1440),
	"max_login_attempts": (1, 20),
	"password_expiry_days": (1, 3650),
	"sla_verification_days": (0, 365),
	"sla_approval_days": (0, 365),
}


def _validate_module_permissions(value: Any) -> dict[str, Any]:
	if not isinstance(value, dict):
		raise HTTPException(status_code=400, detail="module_permissions must be an object")

	matrix = value.get("matrix")
	if matrix is None:
		return value

	if not isinstance(matrix, dict):
		raise HTTPException(status_code=400, detail="module_permissions.matrix must be an object")

	for authority, flags in matrix.items():
		if not isinstance(authority, str) or not authority.strip():
			raise HTTPException(status_code=400, detail="module_permissions.matrix keys must be non-empty strings")
		if not isinstance(flags, dict):
			raise HTTPException(status_code=400, detail="module_permissions.matrix values must be objects")
		for module_id, enabled in flags.items():
			if not isinstance(module_id, str) or not module_id.strip():
				raise HTTPException(status_code=400, detail="module_permissions module keys must be non-empty strings")
			if not isinstance(enabled, bool):
				raise HTTPException(status_code=400, detail="module_permissions flags must be boolean")

	return value


def _validate_system_config_update(key: str, value: Any) -> Any:
	if key == "financial_year":
		if not isinstance(value, str) or not value.strip():
			raise HTTPException(status_code=400, detail="financial_year must be a non-empty string")
		return value.strip()

	if key in _NUMERIC_CONFIG_RANGES:
		if isinstance(value, bool) or not isinstance(value, int):
			raise HTTPException(status_code=400, detail=f"{key} must be an integer")
		min_value, max_value = _NUMERIC_CONFIG_RANGES[key]
		if value < min_value or value > max_value:
			raise HTTPException(
				status_code=400,
				detail=f"{key} must be between {min_value} and {max_value}",
			)
		return value

	if key == "maintenance_mode":
		if not isinstance(value, bool):
			raise HTTPException(status_code=400, detail="maintenance_mode must be boolean")
		return value

	if key == "module_permissions":
		return _validate_module_permissions(value)

	raise HTTPException(status_code=400, detail=f"Unsupported config key: {key}")


def _apply_workflow_overrides(base_matrix: dict, overrides: dict | None) -> dict:
	matrix = deepcopy(base_matrix)

	for workflow in (matrix.get("workflows") or {}).values():
		transitions = workflow.get("transitions") or []
		workflow["transitions"] = [
			{
				**dict(transition),
				"required_authorities": list((transition or {}).get("required_authorities") or []),
			}
			for transition in transitions
		]

	if not overrides:
		return _normalize_contract(matrix)

	transitions_override = overrides.get("transitions") if isinstance(overrides, dict) else {}
	sod_override = overrides.get("sod_rules") if isinstance(overrides, dict) else {}

	has_overrides = bool(transitions_override) or bool(sod_override)
	for workflow_key, workflow in (matrix.get("workflows") or {}).items():
		for transition in workflow.get("transitions", []):
			override_key = f"{workflow_key}:{transition.get('from')}:{transition.get('to')}"
			override = (transitions_override or {}).get(override_key)
			if not isinstance(override, dict):
				continue
			authorities = override["authorities"] if "authorities" in override else []
			if isinstance(authorities, list) and authorities:
				transition["required_authorities"] = authorities
				transition["is_overridden"] = True

	for idx, rule in enumerate(matrix.get("sod_rules") or []):
		flag = (sod_override or {}).get(str(idx))
		if isinstance(flag, bool):
			rule["enabled"] = flag

	matrix["has_overrides"] = has_overrides
	return _normalize_contract(matrix)


def _validate_transition_override_input(
	workflow_type: str,
	from_stage: str,
	to_stage: str,
	authorities: list[str],
) -> tuple[str, str, str, list[str]]:
	normalized_workflow_type = workflow_type.strip().lower()
	normalized_from_stage = from_stage.strip().upper()
	normalized_to_stage = to_stage.strip().upper()

	workflow = (_workflow_matrix_payload().get("workflows") or {}).get(normalized_workflow_type)
	if not workflow:
		raise HTTPException(status_code=400, detail="Invalid workflow_type")

	valid_transitions = {
		(str(transition.get("from") or "").upper(), str(transition.get("to") or "").upper())
		for transition in (workflow.get("transitions") or [])
	}
	if (normalized_from_stage, normalized_to_stage) not in valid_transitions:
		raise HTTPException(status_code=400, detail="Invalid transition for workflow_type")

	known_authorities = {authority.value for authority in Authority}
	normalized_authorities: list[str] = []
	for authority in authorities:
		normalized_authority = str(authority).strip().upper()
		if not normalized_authority:
			continue
		if normalized_authority not in known_authorities:
			raise HTTPException(status_code=400, detail=f"Invalid authority: {normalized_authority}")
		if normalized_authority not in normalized_authorities:
			normalized_authorities.append(normalized_authority)

	if not normalized_authorities:
		raise HTTPException(status_code=400, detail="At least one valid authority is required")

	return normalized_workflow_type, normalized_from_stage, normalized_to_stage, normalized_authorities


