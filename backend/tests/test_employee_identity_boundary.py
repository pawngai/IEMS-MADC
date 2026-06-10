from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from contexts.employee_master.identity.api import write_router as identity_write_router
from contexts.employee_master.identity.schemas.commands import EmployeeIdentityCreate
from contexts.employee_master.identity.schemas.commands import EmployeeIdentityUpdate
from contexts.rbac.domain.models import Permission


BACKEND_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = BACKEND_ROOT / "contexts" / "employee_identity" / "api"
CONTRACT_PATH = BACKEND_ROOT / "contexts" / "employee_master" / "identity" / "contracts" / "identity_directory.py"

FORBIDDEN_DIRECT_DB_PATTERNS = (
    "db.employee_identities",
    'db["employee_identities"]',
    "db['employee_identities']",
    "db.counters",
    'db["counters"]',
    "db['counters']",
)


def test_employee_identity_api_avoids_direct_collection_access() -> None:
    violations: list[str] = []
    for file_path in sorted(API_ROOT.glob("*.py")):
        source = file_path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_DIRECT_DB_PATTERNS:
            if pattern in source:
                violations.append(
                    f"{file_path.relative_to(BACKEND_ROOT).as_posix()}: contains {pattern}"
                )

    assert not violations, (
        "Employee identity API layer must delegate collection access to application/repository code:\n"
        + "\n".join(violations)
    )


def test_employee_identity_directory_contract_stays_read_only() -> None:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    assert "def delete_identity(" not in source


@pytest.mark.parametrize(
    "field_name",
    [
        "employment_type",
        "date_of_initial_engagement",
        "current_department_id",
        "department_id",
        "designation_id",
        "office_id",
        "service_id",
        "post_id",
        "service_status",
    ],
)
def test_employee_identity_create_rejects_non_identity_assignment_fields(field_name: str) -> None:
    payload = {
        "full_name": "Boundary Test Employee",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        field_name: "NOT-IDENTITY",
    }

    with pytest.raises(ValueError, match="core identity fields"):
        EmployeeIdentityCreate.model_validate(payload)


@pytest.mark.asyncio
async def test_department_scoped_identity_create_fails_closed_without_department_target() -> None:
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(container=None)))
    payload = EmployeeIdentityCreate(
        full_name="Scoped Employee",
        gender="Male",
        date_of_birth="1990-01-01",
    )
    current_user = {
        "sub": "dept-user",
        "authorities": ["DEPT_DATA_ENTRY"],
        "department_code": "PWD",
        "permissions": [Permission.IDENTITY_CREATE.value],
    }

    with pytest.raises(HTTPException) as exc:
        await identity_write_router.create_employee_identity(
            payload,
            request,
            db=object(),
            current_user=current_user,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Department-scoped access only allows your own department records."


@pytest.mark.asyncio
async def test_department_scoped_identity_update_rejects_other_department(monkeypatch) -> None:
    class _Repo:
        async def get_identity(self, *, employee_id):
            return {"employee_id": employee_id, "full_name": "Other Employee"}

        async def update_identity(self, **_kwargs):
            raise AssertionError("update should not be reached")

    async def _department(_db, *, employee_id):
        assert employee_id == "EMP-OTHER"
        return "FIN"

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(container=None)))
    current_user = {
        "sub": "dept-user",
        "authorities": ["DEPT_DATA_ENTRY"],
        "department_code": "PWD",
        "permissions": [Permission.IDENTITY_UPDATE_ALL.value],
    }
    monkeypatch.setattr(identity_write_router, "_repo_from_request", lambda _request, _db: _Repo())
    monkeypatch.setattr(identity_write_router, "resolve_employee_department_code", _department)

    with pytest.raises(HTTPException) as exc:
        await identity_write_router.update_employee_identity(
            "EMP-OTHER",
            EmployeeIdentityUpdate(full_name="Changed"),
            request,
            db=object(),
            current_user=current_user,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Department-scoped access only allows your own department records."
