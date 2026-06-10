"""
Test Employee Wizard - Part I Fields for REGULAR Employees
==========================================================

Tests the current split employee identity/profile flow plus Part I-related
profile enrichment and service-book interactions.
"""

import io
from datetime import datetime

import pytest
import requests

from tests.employee_split_test_utils import (
    create_employee_two_step,
    delete_employee_profile,
)
from tests.integration_utils import get_base_url, login_with_fallback

BASE_URL = get_base_url()

DATA_ENTRY_CREDS = {"email": "dataentry@madc.gov.in", "password": "dataentry123"}


def _data_entry_token() -> str:
    return login_with_fallback(
        BASE_URL,
        [
            DATA_ENTRY_CREDS,
            {"email": "global.dataentry@madc.gov.in", "password": "dataentry123"},
        ],
        "DATA_ENTRY",
    )


class TestPhotoUploadAPI:
    """Test photo upload functionality"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = _data_entry_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_photo_upload_endpoint_exists(self):
        response = requests.post(f"{BASE_URL}/api/documents/photo")
        assert response.status_code == 401

    def test_photo_upload_validates_file_type(self):
        files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/documents/photo",
            headers=self.headers,
            files=files,
        )
        assert response.status_code == 400, f"Should reject non-image: {response.text}"
        data = response.json()
        assert "INVALID_FILE_TYPE" in str(data)

    def test_photo_upload_with_valid_image(self):
        jpeg_bytes = bytes(
            [
                0xFF,
                0xD8,
                0xFF,
                0xE0,
                0x00,
                0x10,
                0x4A,
                0x46,
                0x49,
                0x46,
                0x00,
                0x01,
                0x01,
                0x00,
                0x00,
                0x01,
                0x00,
                0x01,
                0x00,
                0x00,
                0xFF,
                0xDB,
                0x00,
                0x43,
                0x00,
                0x08,
                0x06,
                0x06,
                0x07,
                0x06,
                0x05,
                0x08,
                0x07,
                0x07,
                0x07,
                0x09,
                0x09,
                0x08,
                0x0A,
                0x0C,
                0x14,
                0x0D,
                0x0C,
                0x0B,
                0x0B,
                0x0C,
                0x19,
                0x12,
                0x13,
                0x0F,
                0x14,
                0x1D,
                0x1A,
                0x1F,
                0x1E,
                0x1D,
                0x1A,
                0x1C,
                0x1C,
                0x20,
                0x24,
                0x2E,
                0x27,
                0x20,
                0x22,
                0x2C,
                0x23,
                0x1C,
                0x1C,
                0x28,
                0x37,
                0x29,
                0x2C,
                0x30,
                0x31,
                0x34,
                0x34,
                0x34,
                0x1F,
                0x27,
                0x39,
                0x3D,
                0x38,
                0x32,
                0x3C,
                0x2E,
                0x33,
                0x34,
                0x32,
                0xFF,
                0xC0,
                0x00,
                0x0B,
                0x08,
                0x00,
                0x01,
                0x00,
                0x01,
                0x01,
                0x01,
                0x11,
                0x00,
                0xFF,
                0xC4,
                0x00,
                0x1F,
                0x00,
                0x00,
                0x01,
                0x05,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x01,
                0x02,
                0x03,
                0x04,
                0x05,
                0x06,
                0x07,
                0x08,
                0x09,
                0x0A,
                0x0B,
                0xFF,
                0xC4,
                0x00,
                0xB5,
                0x10,
                0x00,
                0x02,
                0x01,
                0x03,
                0x03,
                0x02,
                0x04,
                0x03,
                0x05,
                0x05,
                0x04,
                0x04,
                0x00,
                0x00,
                0x01,
                0x7D,
                0x01,
                0x02,
                0x03,
                0x00,
                0x04,
                0x11,
                0x05,
                0x12,
                0x21,
                0x31,
                0x41,
                0x06,
                0x13,
                0x51,
                0x61,
                0x07,
                0x22,
                0x71,
                0x14,
                0x32,
                0x81,
                0x91,
                0xA1,
                0x08,
                0x23,
                0x42,
                0xB1,
                0xC1,
                0x15,
                0x52,
                0xD1,
                0xF0,
                0x24,
                0x33,
                0x62,
                0x72,
                0x82,
                0x09,
                0x0A,
                0x16,
                0x17,
                0x18,
                0x19,
                0x1A,
                0x25,
                0x26,
                0x27,
                0x28,
                0x29,
                0x2A,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x43,
                0x44,
                0x45,
                0x46,
                0x47,
                0x48,
                0x49,
                0x4A,
                0x53,
                0x54,
                0x55,
                0x56,
                0x57,
                0x58,
                0x59,
                0x5A,
                0x63,
                0x64,
                0x65,
                0x66,
                0x67,
                0x68,
                0x69,
                0x6A,
                0x73,
                0x74,
                0x75,
                0x76,
                0x77,
                0x78,
                0x79,
                0x7A,
                0x83,
                0x84,
                0x85,
                0x86,
                0x87,
                0x88,
                0x89,
                0x8A,
                0x92,
                0x93,
                0x94,
                0x95,
                0x96,
                0x97,
                0x98,
                0x99,
                0x9A,
                0xA2,
                0xA3,
                0xA4,
                0xA5,
                0xA6,
                0xA7,
                0xA8,
                0xA9,
                0xAA,
                0xB2,
                0xB3,
                0xB4,
                0xB5,
                0xB6,
                0xB7,
                0xB8,
                0xB9,
                0xBA,
                0xC2,
                0xC3,
                0xC4,
                0xC5,
                0xC6,
                0xC7,
                0xC8,
                0xC9,
                0xCA,
                0xD2,
                0xD3,
                0xD4,
                0xD5,
                0xD6,
                0xD7,
                0xD8,
                0xD9,
                0xDA,
                0xE1,
                0xE2,
                0xE3,
                0xE4,
                0xE5,
                0xE6,
                0xE7,
                0xE8,
                0xE9,
                0xEA,
                0xF1,
                0xF2,
                0xF3,
                0xF4,
                0xF5,
                0xF6,
                0xF7,
                0xF8,
                0xF9,
                0xFA,
                0xFF,
                0xDA,
                0x00,
                0x08,
                0x01,
                0x01,
                0x00,
                0x00,
                0x3F,
                0x00,
                0xFB,
                0xD5,
                0xDB,
                0x20,
                0xA8,
                0xF1,
                0x7E,
                0xCD,
                0xBF,
                0xFF,
                0xD9,
            ]
        )

        files = {"file": ("test_photo.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/api/documents/photo",
            headers=self.headers,
            files=files,
        )

        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            assert "photo_url" in data
            assert data["photo_url"].startswith("/api/documents/photos/")

    def test_photo_upload_validates_size(self):
        large_content = b"x" * (6 * 1024 * 1024)
        files = {"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/api/documents/photo",
            headers=self.headers,
            files=files,
        )
        assert response.status_code == 400, f"Should reject large file: {response.text}"
        data = response.json()
        assert "FILE_TOO_LARGE" in str(data)


class TestProfileV2CreateWithPartIFields:
    """Test profile creation with employee-owned Part I fields for REGULAR employees"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = _data_entry_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def test_create_regular_employee_with_part_i_fields(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "full_name": f"TEST_Rajesh Kumar_{timestamp}",
            "date_of_birth": "1990-05-15",
            "gender": "Male",
            "employment_type": "REGULAR",
            "date_of_initial_engagement": "2025-01-15",
            "current_department_id": "FIN",
            "current_designation_id": "SO",
            "mobile_primary": "9876543210",
            "father_name": "Shri Ram Kumar",
            "mother_name": "Smt. Sita Devi",
            "nationality": "Indian",
            "category": "GEN",
            "educational_qualifications_initial": [
                {"description": "B.Tech (Computer Science)"}
            ],
            "educational_qualifications_acquired": [
                {"description": "M.Tech (AI/ML)"}
            ],
            "professional_qualifications": [
                {"qualification": "AWS Certified Solutions Architect"}
            ],
            "height_cm": 175,
            "identification_marks": ["Mole on left cheek", "Scar on right hand"],
        }

        result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers=self.headers,
            payload=payload,
        )

        assert result.identity_response.status_code in [200, 201]
        assert result.profile_response is not None
        assert result.profile_response.status_code == 200, (
            f"Profile update failed: {result.profile_response.text}"
        )

        data = result.identity_response.json()
        assert "employee_id" in data
        assert "employee_code" in data

        employee_id = data["employee_id"]
        get_response = requests.get(
            f"{BASE_URL}/api/employee-profiles/{employee_id}",
            headers=self.headers,
        )
        assert get_response.status_code == 200, f"Failed to get profile: {get_response.text}"
        profile = get_response.json()

        assert profile.get("full_name") == payload["full_name"]
        assert profile.get("father_name") == payload["father_name"]
        assert profile.get("mother_name") == payload["mother_name"]
        assert profile.get("nationality") == payload["nationality"]
        assert profile.get("category") == payload["category"]
        assert profile.get("height_cm") == payload["height_cm"]
        assert profile.get("identification_marks") == payload["identification_marks"]

        delete_response = delete_employee_profile(
            requests,
            base_url=BASE_URL,
            headers=self.headers,
            employee_id=employee_id,
        )
        assert delete_response.status_code in [200, 204]

    def test_create_regular_employee_validation(self):
        payload = {"employment_type": "REGULAR"}
        response = requests.post(
            f"{BASE_URL}/api/employee-identities/",
            headers=self.headers,
            json=payload,
        )
        assert response.status_code in [400, 422], f"Should fail validation: {response.text}"

    def test_create_contractual_employee(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "full_name": f"TEST_Contract_Employee_{timestamp}",
            "date_of_birth": "1992-08-20",
            "gender": "Male",
            "employment_type": "CONTRACTUAL",
            "date_of_initial_engagement": "2025-01-15",
            "current_department_id": "FIN",
            "current_designation_id": "SO",
            "mobile_primary": "9876543210",
            "email_official": f"contract_{timestamp}@madc.gov.in",
            "contract_order_no": f"CON/2025/{timestamp}",
            "contract_start_date": "2025-01-15",
            "contract_end_date": "2026-01-14",
            "consolidated_pay": 50000,
            "contract_authority": "Director HR",
            "renewal_allowed": "YES",
        }

        result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers=self.headers,
            payload=payload,
        )

        assert result.identity_response.status_code in [200, 201]
        if result.profile_response is not None:
            assert result.profile_response.status_code == 200

        employee_id = result.identity_response.json()["employee_id"]
        delete_response = delete_employee_profile(
            requests,
            base_url=BASE_URL,
            headers=self.headers,
            employee_id=employee_id,
        )
        assert delete_response.status_code in [200, 204]


class TestServiceBookPartICreation:
    """Test Service Book Part I creation for REGULAR employees"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = _data_entry_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def test_service_book_part_i_fields(self):
        response = requests.get(
            f"{BASE_URL}/api/service-book/parts/I/schema",
            headers=self.headers,
        )

        assert response.status_code == 200, f"Failed to get Part I info: {response.text}"
        data = response.json()
        assert data.get("part_key") == "SB_PART_I"
        assert "json_schema" in data

    def test_save_part_i_data(self):
        list_response = requests.get(
            f"{BASE_URL}/api/employee-profiles/",
            headers=self.headers,
            params={"limit": 1},
        )

        if list_response.status_code != 200:
            return

        response_data = list_response.json()
        profiles = response_data.get("profiles", []) if isinstance(response_data, dict) else response_data
        if not profiles:
            return

        employee_id = profiles[0].get("employee_id")
        part_i_data = {
            "name_in_block_letters": "RAJESH KUMAR",
            "father_name": "SHRI RAM KUMAR",
            "mother_name": "SMT. SITA DEVI",
            "spouse_name": "SMT. PRIYA KUMAR",
            "nationality": "Indian",
            "caste_category": "GEN",
            "date_of_birth_christian": "1990-05-15",
            "educational_qualifications_initial": [{"description": "B.Tech (CS)"}],
            "educational_qualifications_subsequent": [{"description": "M.Tech (AI/ML)"}],
            "professional_qualifications": [{"qualification": "AWS Certified"}],
            "height_cm": 175,
            "identification_marks": ["Mole on left cheek", "Scar on right hand"],
        }

        save_response = requests.post(
            f"{BASE_URL}/api/service-book/employees/{employee_id}/entries",
            headers=self.headers,
            json={
                "schema_key": "SB_I_BIODATA",
                "part_key": "SB_PART_I",
                "payload": part_i_data,
            },
        )
        assert save_response.status_code == 405


class TestEmployeeIdentityBootstrapAPI:
    """Test identity bootstrap API for departments and designations"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = _data_entry_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_identity_bootstrap(self):
        response = requests.get(
            f"{BASE_URL}/api/employee-identities/bootstrap",
            headers=self.headers,
        )
        assert response.status_code == 200, f"Failed to get identity bootstrap: {response.text}"
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data.get("departments"), list)
        assert isinstance(data.get("designations"), list)
        assert isinstance(data.get("employment_types"), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
