from __future__ import annotations

from typing import Any

from app_platform.reference_data.api.versioning_helpers import build_initial_record
from app_platform.reference_data.infrastructure.schemas import (
    DEFAULT_CASTE_CATEGORIES,
    DEFAULT_EMPLOYMENT_TYPES,
    DEFAULT_LEAVE_TYPES,
    DEFAULT_PAY_LEVELS,
    DEFAULT_SERVICE_EVENT_TYPES,
    DEFAULT_SERVICE_GROUPS,
    DEFAULT_SERVICES,
)
from contexts.documents.domain.validation import ALLOWED_DOCUMENT_TYPES, DOCUMENT_TYPE_RECORDS
from contexts.identity_access.rbac.domain.models import AUTHORITY_PERMISSIONS, Authority, WorkflowStage

SYSTEM_SEED_CREATED_BY = "system_seed"

COLLECTION_MASTER_TYPES = {
    "employment_types": "employment_type",
    "pay_levels": "pay_level",
    "service_event_types": "service_event_type",
    "leave_types": "leave_type",
    "service_groups": "service_group",
    "services": "service",
    "caste_categories": "caste_category",
    "roles": "role",
    "workflow_stages": "workflow_stage",
    "document_types": "document_type",
    "qualifications": "qualification",
}

ROLE_LABELS = {
    Authority.EMPLOYEE.value: "Employee",
    Authority.DEPT_DATA_ENTRY.value: "Department Data Entry",
    Authority.GLOBAL_DATA_ENTRY.value: "Global Data Entry",
    Authority.DEALING_ASSISTANT.value: "Dealing Assistant",
    Authority.SECTION_OFFICER.value: "Section Officer",
    Authority.VERIFIER.value: "Verifier",
    Authority.NODAL_OFFICER.value: "Nodal Officer",
    Authority.DDO.value: "DDO",
    Authority.APPROVING_AUTHORITY.value: "Approving Authority",
    Authority.HOD.value: "HOD",
    Authority.APPOINTING_AUTHORITY.value: "Appointing Authority",
    Authority.DISCIPLINARY_AUTHORITY.value: "Disciplinary Authority",
    Authority.AUDITOR.value: "Auditor",
    Authority.SYSTEM_ADMIN.value: "System Administrator",
}

DEFAULT_DOCUMENT_TYPE_RECORDS = [dict(record) for record in DOCUMENT_TYPE_RECORDS]

DEFAULT_QUALIFICATION_RECORDS = [
    {
        "code": "SECONDARY",
        "name": "Secondary",
        "description": "Secondary school qualification",
        "level": "SECONDARY",
    },
    {
        "code": "HIGHER_SECONDARY",
        "name": "Higher Secondary",
        "description": "Higher secondary school qualification",
        "level": "HIGHER_SECONDARY",
    },
    {
        "code": "DIPLOMA",
        "name": "Diploma",
        "description": "Diploma qualification",
        "level": "DIPLOMA",
    },
    {
        "code": "BACHELOR",
        "name": "Bachelor",
        "description": "Bachelor degree qualification",
        "level": "BACHELOR",
    },
    {
        "code": "MASTER",
        "name": "Master",
        "description": "Master degree qualification",
        "level": "MASTER",
    },
    {
        "code": "DOCTORATE",
        "name": "Doctorate",
        "description": "Doctoral qualification",
        "level": "DOCTORATE",
    },
    {
        "code": "PROFESSIONAL_CERTIFICATION",
        "name": "Professional Certification",
        "description": "Professional or technical certification",
        "level": "CERTIFICATION",
    },
]


def _humanize(code: str) -> str:
    return code.replace("_", " ").title()


def _metadata_from_record(record: dict[str, Any]) -> dict[str, Any]:
    excluded = {
        "id",
        "code",
        "name",
        "description",
        "is_active",
        "effective_from",
        "effective_to",
        "created_at",
        "updated_at",
        "version",
        "created_by",
        "superseded_by",
        "superseded_at",
    }
    return {
        key: value
        for key, value in record.items()
        if key not in excluded and value is not None
    }


def _normalize_seed_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for record in records:
        code = str(record.get("code") or "").strip().upper()
        if not code:
            continue
        name = str(record.get("name") or record.get("description") or code).strip()
        description = str(record.get("description") or name).strip()
        normalized.append(
            {
                "code": code,
                "name": name,
                "description": description,
                "metadata": _metadata_from_record(record),
            }
        )
    return normalized


def _role_seed_records() -> list[dict[str, Any]]:
    return [
        {
            "code": authority.value,
            "name": ROLE_LABELS.get(authority.value, _humanize(authority.value)),
            "description": f"{ROLE_LABELS.get(authority.value, _humanize(authority.value))} authority",
            "permissions": sorted(
                permission.value
                for permission in AUTHORITY_PERMISSIONS.get(authority, set())
            ),
        }
        for authority in Authority
    ]


def _workflow_stage_seed_records() -> list[dict[str, Any]]:
    from contexts.identity_access.rbac.domain.models import WORKFLOW_TRANSITIONS

    records: list[dict[str, Any]] = []
    for stage in WorkflowStage:
        transition = WORKFLOW_TRANSITIONS.get(stage, {})
        required_authority = transition.get("required_authority")
        if isinstance(required_authority, list):
            required = [authority.value for authority in required_authority]
        elif required_authority is None:
            required = []
        else:
            required = [required_authority.value]

        records.append(
            {
                "code": stage.value,
                "name": _humanize(stage.value),
                "description": f"Workflow stage {_humanize(stage.value)}",
                "next_stages": [next_stage.value for next_stage in transition.get("next_stages", [])],
                "required_authority": required,
                "can_edit": bool(transition.get("can_edit", False)),
            }
        )
    return records


def _document_type_seed_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in DEFAULT_DOCUMENT_TYPE_RECORDS:
        content_types = sorted(ALLOWED_DOCUMENT_TYPES) if record["code"] == "ORDER" else []
        records.append({**record, "supported_content_types": content_types})
    return records


def _qualification_seed_records() -> list[dict[str, Any]]:
    return list(DEFAULT_QUALIFICATION_RECORDS)


def _versioned_seed_definitions() -> dict[str, list[dict[str, Any]]]:
    return {
        "employment_types": _normalize_seed_records(DEFAULT_EMPLOYMENT_TYPES),
        "pay_levels": _normalize_seed_records(DEFAULT_PAY_LEVELS),
        "service_event_types": _normalize_seed_records(DEFAULT_SERVICE_EVENT_TYPES),
        "leave_types": _normalize_seed_records(DEFAULT_LEAVE_TYPES),
        "service_groups": _normalize_seed_records(DEFAULT_SERVICE_GROUPS),
        "services": _normalize_seed_records(DEFAULT_SERVICES),
        "caste_categories": _normalize_seed_records(DEFAULT_CASTE_CATEGORIES),
        "roles": _normalize_seed_records(_role_seed_records()),
        "workflow_stages": _normalize_seed_records(_workflow_stage_seed_records()),
        "document_types": _normalize_seed_records(_document_type_seed_records()),
        "qualifications": _normalize_seed_records(_qualification_seed_records()),
    }


async def _log_seed_create(
    db,
    *,
    master_type: str,
    record: dict[str, Any],
) -> None:
    await db.master_audit_logs.insert_one(
        {
            "id": record["id"],
            "timestamp": record["created_at"],
            "entity_type": "MASTER_DATA",
            "master_type": master_type,
            "action": "SYSTEM_SEED",
            "record_code": record["code"],
            "actor_id": SYSTEM_SEED_CREATED_BY,
            "actor_email": SYSTEM_SEED_CREATED_BY,
            "before_state": None,
            "after_state": {key: value for key, value in record.items() if key != "_id"},
            "reason": "Initial bootstrap seed",
        }
    )


async def seed_system_managed_masters(db) -> dict[str, int]:
    seeded_counts: dict[str, int] = {}

    for collection_name, records in _versioned_seed_definitions().items():
        collection = db[collection_name]
        seeded_counts[collection_name] = 0
        for record in records:
            existing = await collection.find_one({"code": record["code"]}, {"_id": 1})
            if existing:
                continue

            created = build_initial_record(
                code=record["code"],
                name=record["name"],
                description=record["description"],
                metadata=record.get("metadata") or {},
                created_by=SYSTEM_SEED_CREATED_BY,
            )
            await collection.insert_one(created)
            await _log_seed_create(
                db,
                master_type=COLLECTION_MASTER_TYPES[collection_name],
                record=created,
            )
            seeded_counts[collection_name] += 1

    return seeded_counts