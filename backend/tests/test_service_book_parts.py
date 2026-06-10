"""
Servicebook bounded-context integration tests.

These tests intentionally target the new context routes under `/api/service-book/*`.
They replace legacy servicebook route integration assumptions.
"""

from __future__ import annotations

import pytest
import requests

from tests.integration_utils import get_base_url, login_with_fallback

DATA_ENTRY_CREDS = {"email": "dataentry@madc.gov.in", "password": "dataentry123"}
VERIFIER_CREDS = {"email": "verifier@madc.gov.in", "password": "verifier123"}


@pytest.fixture(scope="module")
def base_url():
    return get_base_url()


@pytest.fixture(scope="module")
def data_entry_token(base_url):
    candidates = [
        DATA_ENTRY_CREDS,
        {"email": "global.dataentry@madc.gov.in", "password": "dataentry123"},
    ]
    return login_with_fallback(base_url, candidates, "DATA_ENTRY")


@pytest.fixture(scope="module")
def verifier_token(base_url):
    candidates = [
        VERIFIER_CREDS,
        {"email": "global.verifier@madc.gov.in", "password": "verifier123"},
    ]
    return login_with_fallback(base_url, candidates, "VERIFIER")


@pytest.fixture
def auth_headers(data_entry_token):
    return {
        "Authorization": f"Bearer {data_entry_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def regular_employee_id(base_url, data_entry_token):
    """Discover a REGULAR employee from the live database."""
    headers = {
        "Authorization": f"Bearer {data_entry_token}",
        "Content-Type": "application/json",
    }
    response = requests.get(
        f"{base_url}/api/employee-profiles",
        headers=headers,
        params={"limit": 50},
        timeout=20,
    )
    if response.status_code != 200:
        pytest.skip(f"Cannot list profiles (status {response.status_code})")
    data = response.json()
    profiles = data.get("profiles", data) if isinstance(data, dict) else data
    for p in profiles:
        if p.get("employment_type", "").upper() == "REGULAR" and p.get("employee_id"):
            return p["employee_id"]
    pytest.skip("No REGULAR employee found in database")


def _latest_entry(entries: list[dict]) -> dict | None:
    if not entries:
        return None
    return sorted(
        entries,
        key=lambda item: item.get("updated_at") or item.get("created_at") or "",
        reverse=True,
    )[0]


def _list_entries(base_url: str, employee_id: str, headers: dict, **params):
    response = requests.get(
        f"{base_url}/api/service-book/employees/{employee_id}/entries",
        headers=headers,
        params=params or None,
        timeout=20,
    )
    return response


class TestServicebookSchemas:
    def test_part_i_schema_exists(self, base_url, auth_headers):
        response = requests.get(
            f"{base_url}/api/service-book/parts/I/schema",
            headers=auth_headers,
            timeout=20,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["part_key"] == "SB_PART_I"
        assert "json_schema" in data
        assert "schema_key" in data or "schema_keys" in data

    def test_part_iv_schema_exists(self, base_url, auth_headers):
        response = requests.get(
            f"{base_url}/api/service-book/parts/SB_PART_IV/schema",
            headers=auth_headers,
            timeout=20,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["part_key"] == "SB_PART_IV"


class TestServicebookEntries:
    def test_list_entries_requires_auth(self, base_url):
        response = requests.get(
            f"{base_url}/api/service-book/employees/00000000-0000-0000-0000-000000000000/entries",
            timeout=20,
        )
        assert response.status_code == 401

    def test_list_entries_for_employee(self, base_url, auth_headers, regular_employee_id):
        response = _list_entries(base_url, regular_employee_id, auth_headers, active=True)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_service_book_rejects_direct_part_i_mutation(self, base_url, auth_headers, regular_employee_id):
        payload = {
            "schema_key": "SB_I_BIODATA",
            "part_key": "SB_PART_I",
            "payload": {
                "name_in_block_letters": "CONTEXT TEST EMPLOYEE",
                "father_name": "CONTEXT TEST FATHER",
                "marital_status": "SINGLE",
                "nationality": "Indian",
                "caste_category": "GEN",
                "date_of_birth_christian": "1990-01-01",
            },
        }
        create_response = requests.post(
            f"{base_url}/api/service-book/employees/{regular_employee_id}/entries",
            headers=auth_headers,
            json=payload,
            timeout=20,
        )
        assert create_response.status_code == 405

        list_response = _list_entries(
            base_url,
            regular_employee_id,
            auth_headers,
            schema_key="SB_I_BIODATA",
            active=True,
        )
        assert list_response.status_code == 200
        assert isinstance(list_response.json(), list)

    def test_service_book_rejects_direct_part_iv_mutation(self, base_url, auth_headers, regular_employee_id):
        payload = {
            "schema_key": "SB_IV_SERVICE_HISTORY_ROW",
            "part_key": "SB_PART_IV",
            "payload": {
                "period_from": "2025-01-01",
                "period_to": "2025-12-31",
                "office_station": "Test Office",
                "post_held": "Test Post",
                "event_type": "TRANSFER",
                "pay_level": "Level 11",
                "basic_pay": 67700,
                "event_order_number": "TEST/2025/001",
                "event_order_date": "2024-12-20",
            },
        }
        create_response = requests.post(
            f"{base_url}/api/service-book/employees/{regular_employee_id}/entries",
            headers=auth_headers,
            json=payload,
            timeout=20,
        )
        assert create_response.status_code == 405

        view_response = requests.get(
            f"{base_url}/api/service-book/employees/{regular_employee_id}/parts/SB_PART_IV",
            headers=auth_headers,
            timeout=20,
        )
        if view_response.status_code == 404:
            pytest.skip("Part IV view endpoint not available for this employee")
        assert view_response.status_code == 200, f"Part IV view: {view_response.status_code} {view_response.text[:200]}"
        view_data = view_response.json()
        if view_data is None:
            pytest.skip("Part IV view returned null — part not yet projected for this employee")
        assert view_data.get("part_key") == "SB_PART_IV"
        assert isinstance(view_data.get("entries"), list)


class TestServicebookWorkflow:
    def test_service_book_workflow_mutations_are_removed(
        self, base_url, auth_headers, verifier_token, regular_employee_id
    ):
        submit_response = requests.post(
            f"{base_url}/api/service-book/entries/legacy-entry-id/submit",
            headers=auth_headers,
            json={"remarks": "submit from integration test"},
            timeout=20,
        )
        assert submit_response.status_code == 404

        verifier_headers = {
            "Authorization": f"Bearer {verifier_token}",
            "Content-Type": "application/json",
        }
        verify_response = requests.post(
            f"{base_url}/api/service-book/entries/legacy-entry-id/verify",
            headers=verifier_headers,
            json={"remarks": "verify from integration test"},
            timeout=20,
        )
        assert verify_response.status_code == 404


class TestServicebookPrint:
    def test_print_full_returns_payload_shape(self, base_url, auth_headers, regular_employee_id):
        response = requests.get(
            f"{base_url}/api/service-book/employees/{regular_employee_id}/print/full",
            headers=auth_headers,
            timeout=20,
        )
        if response.status_code == 403:
            pytest.skip("print not permitted for this role in current environment")
        assert response.status_code == 200
        data = response.json()
        assert data.get("employee_id") == regular_employee_id
        assert "generated_at" in data
        assert "parts" in data


class TestServicebookVerificationRead:
    def test_verifier_can_list_entries(self, base_url, verifier_token, regular_employee_id):
        headers = {
            "Authorization": f"Bearer {verifier_token}",
            "Content-Type": "application/json",
        }
        response = _list_entries(base_url, regular_employee_id, headers, active=True)
        if response.status_code == 403:
            pytest.skip("verifier read access is restricted in this deployment")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

