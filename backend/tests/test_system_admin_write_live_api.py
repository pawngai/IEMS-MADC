from __future__ import annotations

import os

import pytest
import requests

if os.environ.get("IEMS_RUN_LIVE_SYSTEM_ADMIN_WRITE") != "1":
    pytest.skip(
        "Set IEMS_RUN_LIVE_SYSTEM_ADMIN_WRITE=1 to run live system-admin write API tests.",
        allow_module_level=True,
    )

from tests.integration_utils import get_base_url, login_with_fallback

BASE_URL = get_base_url()
ROLE_LOGIN_CANDIDATES = {
    "SYSTEM_ADMIN": [
        {"email": "admin@madc.gov.in", "password": "admin123"},
    ]
}


@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def sys_admin_auth_header(api_client):
    token = login_with_fallback(BASE_URL, ROLE_LOGIN_CANDIDATES["SYSTEM_ADMIN"], "SYSTEM_ADMIN")
    return {"Authorization": f"Bearer {token}"}


def test_delete_employee_write_path_is_forbidden_for_system_admin(api_client, sys_admin_auth_header):
    response = api_client.post(
        f"{BASE_URL}/api/system-admin/employees/EMP-LIVE-NONEXISTENT/delete",
        headers=sys_admin_auth_header,
        json={"reason": "Live test guard: deleting non-existent employee id"},
    )
    assert response.status_code == 403


def test_admin_cancel_leave_write_path_is_forbidden_for_system_admin(api_client, sys_admin_auth_header):
    response = api_client.post(
        f"{BASE_URL}/api/system-admin/leave/LIVE-NONEXISTENT-LEAVE/admin-cancel",
        headers=sys_admin_auth_header,
        json={"reason": "Live test guard: cancelling non-existent leave id"},
    )
    assert response.status_code == 403
