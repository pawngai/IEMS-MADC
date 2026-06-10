"""
RBAC Workflow Enforcement Tests
===============================

Live integration coverage for the split employee identity/profile APIs:

- create employee identity: /api/employee-identities/
- update employee profile: /api/employee-profiles/{employee_id}
- workflow actions: /api/employee-profiles/{employee_id}/{submit|verify|approve|reject|lock}
"""

from __future__ import annotations

import uuid
import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

from tests.employee_split_test_utils import create_employee_two_step
from tests.integration_utils import get_base_url, login_with_fallback

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
BASE_URL = get_base_url()


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _configured_login_token(
    *,
    label: str,
    email_env: str,
    password_env: str,
    default_email: str,
    default_password: str,
    extra_candidates: list[dict[str, str]] | None = None,
) -> str:
    """Authenticate a real seeded workflow user against the live backend."""

    env_email = str(os.getenv(email_env) or "").strip()
    env_password = str(os.getenv(password_env) or "").strip()
    candidates: list[dict[str, str]] = []
    if env_email and env_password:
        candidates.append({"email": env_email, "password": env_password})
    if env_password:
        candidates.append({"email": default_email, "password": env_password})
    else:
        candidates.append({"email": default_email, "password": default_password})
        candidates.extend(extra_candidates or [])

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        email = str(candidate.get("email") or "").strip()
        password = str(candidate.get("password") or "")
        if not email or not password:
            continue
        key = (email.lower(), password)
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"email": email, "password": password})
    return login_with_fallback(BASE_URL, deduped, label)


def _workflow_payload(suffix: str, *, employment_type: str = "CONTRACTUAL") -> dict:
    base = {
        "full_name": f"TEST_WORKFLOW_{suffix}",
        "gender": "Male",
        "date_of_birth": "1990-01-15",
        "employment_type": employment_type,
        "date_of_initial_engagement": "2024-01-15",
        "current_department_id": "FIN",
        "current_designation_id": "AN",
        "current_office_id": "HQ",
        "mobile_primary": "9876543299",
        "email_personal": f"workflow.{suffix.lower()}@example.com",
        "address_line1": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "pincode": "110001",
        "present_address_line1": "123 Test Street",
        "present_city": "Test City",
        "present_state": "Test State",
        "present_pincode": "110001",
        "employee_section_completed": True,
        "data_entry_section_completed": True,
    }
    if employment_type == "CONTRACTUAL":
        base.update({
            "contract_order_no": f"CON/{suffix}/001",
            "contract_start_date": "2024-01-15",
            "contract_end_date": "2025-01-14",
            "consolidated_pay": 50000,
            "contract_authority": "DC Office",
            "renewal_allowed": "YES",
        })
    else:
        base.update({
            "service": "GENERAL",
            "group": "C",
            "mode_of_recruitment": "DIRECT",
        })
    return base


def _post_workflow_action(
    session: requests.Session,
    *,
    employee_id: str,
    action: str,
    token: str,
    remarks: str,
):
    return session.post(
        f"{BASE_URL}/api/employee-profiles/{employee_id}/{action}",
        json={"remarks": remarks},
        headers=_auth_header(token),
    )


def _complete_identity_workflow(
    session: requests.Session,
    *,
    employee_id: str,
    data_entry_token: str,
    verifier_token: str,
    approver_token: str,
) -> None:
    submit_response = session.post(
        f"{BASE_URL}/api/employee-identities/{employee_id}/submit",
        headers=_auth_header(data_entry_token),
    )
    assert submit_response.status_code == 200, submit_response.text

    verify_response = session.post(
        f"{BASE_URL}/api/employee-identities/{employee_id}/verify",
        headers=_auth_header(verifier_token),
    )
    assert verify_response.status_code == 200, verify_response.text

    activate_response = session.post(
        f"{BASE_URL}/api/employee-identities/{employee_id}/activate",
        headers=_auth_header(approver_token),
    )
    assert activate_response.status_code == 200, activate_response.text


def _create_ready_profile(
    session: requests.Session,
    *,
    token: str,
    verifier_token: str,
    approver_token: str,
    suffix: str,
) -> str:
    result = create_employee_two_step(
        session,
        base_url=BASE_URL,
        headers=_auth_header(token),
        payload=_workflow_payload(suffix),
    )
    assert result.identity_response.status_code == 200, result.identity_response.text
    if result.profile_response is not None:
        assert result.profile_response.status_code == 200, result.profile_response.text

    employee_id = result.employee_id
    assert employee_id
    _complete_identity_workflow(
        session,
        employee_id=employee_id,
        data_entry_token=token,
        verifier_token=verifier_token,
        approver_token=approver_token,
    )

    profile_response = session.get(
        f"{BASE_URL}/api/employee-profiles/{employee_id}",
        headers=_auth_header(token),
    )
    assert profile_response.status_code == 200, profile_response.text
    profile = profile_response.json()
    assert profile.get("workflow_status") == "DRAFT"
    assert profile.get("employee_section_completed") is True
    assert profile.get("data_entry_section_completed") is True
    return employee_id


def _create_submitted_profile(
    session: requests.Session,
    *,
    data_entry_token: str,
    verifier_token: str,
    approver_token: str,
    suffix: str,
) -> str:
    employee_id = _create_ready_profile(
        session,
        token=data_entry_token,
        verifier_token=verifier_token,
        approver_token=approver_token,
        suffix=suffix,
    )
    submit_response = _post_workflow_action(
        session,
        employee_id=employee_id,
        action="submit",
        token=data_entry_token,
        remarks="Submitted for workflow validation",
    )
    assert submit_response.status_code == 200, submit_response.text
    assert submit_response.json().get("new_status") == "SUBMITTED"
    return employee_id


def _create_verified_profile(
    session: requests.Session,
    *,
    data_entry_token: str,
    verifier_token: str,
    establishment_token: str,
    suffix: str,
) -> str:
    employee_id = _create_submitted_profile(
        session,
        data_entry_token=data_entry_token,
        verifier_token=verifier_token,
        approver_token=establishment_token,
        suffix=suffix,
    )
    verify_response = _post_workflow_action(
        session,
        employee_id=employee_id,
        action="verify",
        token=verifier_token,
        remarks="Verified by workflow test",
    )
    assert verify_response.status_code == 200, verify_response.text
    assert verify_response.json().get("new_status") == "VERIFIED"
    return employee_id


def _create_approved_profile(
    session: requests.Session,
    *,
    data_entry_token: str,
    verifier_token: str,
    establishment_token: str,
    suffix: str,
) -> str:
    employee_id = _create_verified_profile(
        session,
        data_entry_token=data_entry_token,
        verifier_token=verifier_token,
        establishment_token=establishment_token,
        suffix=suffix,
    )
    approve_response = _post_workflow_action(
        session,
        employee_id=employee_id,
        action="approve",
        token=establishment_token,
        remarks="Approved by workflow test",
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json().get("new_status") == "APPROVED"
    return employee_id


@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def data_entry_token():
    return _configured_login_token(
        label="global data entry",
        email_env="IEMS_E2E_DE_EMAIL",
        password_env="IEMS_E2E_DE_PASSWORD",
        default_email="global.dataentry@madc.gov.in",
        default_password="dataentry123",
        extra_candidates=[
            {"email": "dataentry@madc.gov.in", "password": "dataentry123"},
        ],
    )


@pytest.fixture(scope="session")
def verifier_token():
    return _configured_login_token(
        label="verifier",
        email_env="IEMS_E2E_VERIFIER_EMAIL",
        password_env="IEMS_E2E_VERIFIER_PASSWORD",
        default_email="verifier@madc.gov.in",
        default_password="verifier123",
    )


@pytest.fixture(scope="session")
def establishment_token():
    return _configured_login_token(
        label="approving authority",
        email_env="IEMS_E2E_HOO_EMAIL",
        password_env="IEMS_E2E_HOO_PASSWORD",
        default_email="hoo@madc.gov.in",
        default_password="hoo123",
    )


@pytest.fixture(scope="session")
def hoo_token():
    return _configured_login_token(
        label="head of office",
        email_env="IEMS_E2E_HOO_EMAIL",
        password_env="IEMS_E2E_HOO_PASSWORD",
        default_email="hoo@madc.gov.in",
        default_password="hoo123",
    )


@pytest.fixture(scope="session")
def auditor_token():
    return _configured_login_token(
        label="auditor",
        email_env="IEMS_E2E_AUDITOR_EMAIL",
        password_env="IEMS_E2E_AUDITOR_PASSWORD",
        default_email="auditor@madc.gov.in",
        default_password="auditor123",
        extra_candidates=[
            {"email": "admin@madc.gov.in", "password": os.getenv("IEMS_SEED_ADMIN_PASSWORD", "")},
        ],
    )


class TestWorkflowRBAC:
    def test_data_entry_can_submit_completed_profile(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
    ):
        employee_id = _create_submitted_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            approver_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        response = api_client.get(
            f"{BASE_URL}/api/employee-profiles/{employee_id}",
            headers=_auth_header(data_entry_token),
        )
        assert response.status_code == 200
        assert response.json().get("workflow_status") == "SUBMITTED"

    def test_data_entry_cannot_verify_submitted_profile(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
    ):
        employee_id = _create_submitted_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            approver_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        response = _post_workflow_action(
            api_client,
            employee_id=employee_id,
            action="verify",
            token=data_entry_token,
            remarks="Self verification should fail",
        )
        assert response.status_code == 403

    def test_verifier_can_verify_submitted_profile(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
    ):
        employee_id = _create_submitted_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            approver_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        response = _post_workflow_action(
            api_client,
            employee_id=employee_id,
            action="verify",
            token=verifier_token,
            remarks="Verified by workflow test",
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["new_status"] == "VERIFIED"

    def test_approving_authority_can_approve_verified_profile(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
    ):
        employee_id = _create_verified_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            establishment_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        response = _post_workflow_action(
            api_client,
            employee_id=employee_id,
            action="approve",
            token=establishment_token,
            remarks="Approved by workflow test",
        )
        assert response.status_code == 200, response.text
        assert response.json()["new_status"] == "APPROVED"

    def test_approving_authority_can_lock_approved_profile(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
        hoo_token,
    ):
        employee_id = _create_approved_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            establishment_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        response = _post_workflow_action(
            api_client,
            employee_id=employee_id,
            action="lock",
            token=hoo_token,
            remarks="Locked by workflow test",
        )
        assert response.status_code == 200, response.text
        assert response.json()["new_status"] == "LOCKED"

    def test_rejection_requires_remarks(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
    ):
        employee_id = _create_submitted_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            approver_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        response = _post_workflow_action(
            api_client,
            employee_id=employee_id,
            action="reject",
            token=verifier_token,
            remarks="",
        )
        assert response.status_code == 400

    def test_auditor_is_read_only_for_workflow(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
        auditor_token,
    ):
        employee_id = _create_submitted_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            approver_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        list_response = api_client.get(
            f"{BASE_URL}/api/employee-profiles/",
            headers=_auth_header(auditor_token),
        )
        assert list_response.status_code == 200

        verify_response = _post_workflow_action(
            api_client,
            employee_id=employee_id,
            action="verify",
            token=auditor_token,
            remarks="Auditor should not verify",
        )
        assert verify_response.status_code == 403

    def test_locked_profile_blocks_profile_updates(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
        hoo_token,
    ):
        employee_id = _create_approved_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            establishment_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        lock_response = _post_workflow_action(
            api_client,
            employee_id=employee_id,
            action="lock",
            token=hoo_token,
            remarks="Lock before immutability check",
        )
        assert lock_response.status_code == 200, lock_response.text

        update_response = api_client.put(
            f"{BASE_URL}/api/employee-profiles/{employee_id}",
            json={"mobile_primary": "9999999999"},
            headers=_auth_header(data_entry_token),
        )
        assert update_response.status_code == 403
        detail = update_response.json().get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("error_code") == "RECORD_LOCKED"

    def test_audit_trail_is_available_for_workflow_record(
        self,
        api_client,
        data_entry_token,
        verifier_token,
        establishment_token,
    ):
        employee_id = _create_verified_profile(
            api_client,
            data_entry_token=data_entry_token,
            verifier_token=verifier_token,
            establishment_token=establishment_token,
            suffix=uuid.uuid4().hex[:8],
        )

        response = api_client.get(
            f"{BASE_URL}/api/employee-profiles/{employee_id}/audit-trail",
            headers=_auth_header(verifier_token),
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        logs = (
            payload.get("audit_trail")
            or payload.get("logs")
            or payload.get("audit_logs")
            or []
        )
        assert isinstance(logs, list)
        assert len(logs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
