from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

from contexts.identity.contracts.password import (
    hash_password,
    verify_password,
)
from contexts.rbac.domain.models import Authority

logger = logging.getLogger(__name__)


CANONICAL_ADMIN_EMAIL = "admin@madc.gov.in"


def _get_seed_admin_password() -> str | None:
    password = str(os.getenv("IEMS_SEED_ADMIN_PASSWORD") or "").strip()
    return password or None


CANONICAL_WORKFLOW_USERS = (
    {
        "email_env": "IEMS_E2E_DE_EMAIL",
        "default_email": "global.dataentry@madc.gov.in",
        "password_env": "IEMS_E2E_DE_PASSWORD",
        "name": "Global Data Entry",
        "authority": Authority.GLOBAL_DATA_ENTRY.value,
        "employee_id": "DE-001",
        "department_code": "ADMIN",
        "office_code": "HQ",
    },
    {
        "email_env": "IEMS_E2E_VERIFIER_EMAIL",
        "default_email": "verifier@madc.gov.in",
        "password_env": "IEMS_E2E_VERIFIER_PASSWORD",
        "name": "Verifier Officer",
        "authority": Authority.VERIFIER.value,
        "employee_id": "VER-001",
        "department_code": "ADMIN",
        "office_code": "HQ",
    },
    {
        "email_env": "IEMS_E2E_HOO_EMAIL",
        "default_email": "hoo@madc.gov.in",
        "password_env": "IEMS_E2E_HOO_PASSWORD",
        "name": "Approving Authority",
        "authority": Authority.APPROVING_AUTHORITY.value,
        "employee_id": "HOO-001",
        "department_code": "ADMIN",
        "office_code": "HQ",
    },
    {
        "email_env": "IEMS_E2E_DEALING_EMAIL",
        "default_email": "dealing.clerk@madc.gov.in",
        "password_env": "IEMS_E2E_DEALING_PASSWORD",
        "name": "Dealing Clerk",
        "authority": Authority.DEALING_ASSISTANT.value,
        "employee_id": "DA-001",
        "department_code": "ADMIN",
        "office_code": "HQ",
    },
    {
        "email_env": "IEMS_E2E_AUDITOR_EMAIL",
        "default_email": "auditor@madc.gov.in",
        "password_env": "IEMS_E2E_AUDITOR_PASSWORD",
        "name": "Auditor",
        "authority": Authority.AUDITOR.value,
        "employee_id": "AUD-001",
        "department_code": "ADMIN",
        "office_code": "HQ",
    },
)


async def sync_canonical_dev_admin(db) -> bool:
    """Ensure the canonical dev admin converges only when an explicit dev password is set."""
    if db is None:
        return False

    seed_admin_password = _get_seed_admin_password()
    if not seed_admin_password:
        return False

    existing = await db.users.find_one({"email": CANONICAL_ADMIN_EMAIL})
    password_matches = bool(
        existing and verify_password(seed_admin_password, existing.get("password_hash", ""))
    )
    has_expected_state = bool(
        existing
        and password_matches
        and existing.get("authorities") == [Authority.SYSTEM_ADMIN.value]
        and existing.get("failed_login_attempts", 0) == 0
        and existing.get("locked_until") is None
        and existing.get("is_active", True) is True
    )
    if has_expected_state:
        return False

    now = datetime.now(timezone.utc).isoformat()
    set_fields: dict = {
        "email": CANONICAL_ADMIN_EMAIL,
        "name": "System Administrator",
        "authorities": [Authority.SYSTEM_ADMIN.value],
        "employee_id": "",
        "department_code": "",
        "office_code": "",
        "is_active": True,
        "is_locked": False,
        "must_change_password": False,
        "failed_login_attempts": 0,
        "locked_until": None,
        "updated_at": now,
    }
    set_on_insert: dict = {
        "id": str(uuid.uuid4()),
        "created_at": now,
    }
    if not existing:
        set_on_insert["password_hash"] = hash_password(seed_admin_password)
    else:
        set_fields["password_hash"] = hash_password(seed_admin_password)

    await db.users.update_one(
        {"email": CANONICAL_ADMIN_EMAIL},
        {"$set": set_fields, "$setOnInsert": set_on_insert},
        upsert=True,
    )
    logger.info(
        "Synced canonical dev admin to configured startup password",
        extra={"email": CANONICAL_ADMIN_EMAIL},
    )
    return True


async def sync_canonical_dev_workflow_users(db) -> int:
    """Ensure canonical workflow users exist when explicit per-role passwords are provided."""
    if db is None:
        return 0

    synced = 0
    now = datetime.now(timezone.utc).isoformat()
    for spec in CANONICAL_WORKFLOW_USERS:
        password = str(os.getenv(spec["password_env"]) or "").strip()
        if not password:
            continue

        email = str(os.getenv(spec["email_env"]) or spec["default_email"]).strip() or spec["default_email"]
        existing = await db.users.find_one({"email": email})
        password_matches = bool(existing and verify_password(password, existing.get("password_hash", "")))
        has_expected_state = bool(
            existing
            and password_matches
            and existing.get("authorities") == [spec["authority"]]
            and existing.get("employee_id") == spec["employee_id"]
            and existing.get("department_code") == spec["department_code"]
            and existing.get("office_code") == spec["office_code"]
            and existing.get("failed_login_attempts", 0) == 0
            and existing.get("locked_until") is None
            and existing.get("is_active", True) is True
        )
        if has_expected_state:
            continue

        await db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "email": email,
                    "name": spec["name"],
                    "password_hash": hash_password(password),
                    "authorities": [spec["authority"]],
                    "employee_id": spec["employee_id"],
                    "department_code": spec["department_code"],
                    "office_code": spec["office_code"],
                    "is_active": True,
                    "is_locked": False,
                    "must_change_password": False,
                    "failed_login_attempts": 0,
                    "locked_until": None,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": now,
                },
            },
            upsert=True,
        )
        synced += 1

    if synced > 0:
        logger.info("Synced canonical workflow users from explicit role-password envs", extra={"count": synced})
    return synced
