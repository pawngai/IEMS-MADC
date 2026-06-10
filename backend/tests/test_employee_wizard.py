"""
Test Suite for EmployeeWizard APIs
==================================

Tests the EmployeeWizard component's backend integration:
- Employee profile API (CRUD operations)
- Masters API (Departments, Designations)

Employment Types Tested:
- REGULAR
- CONTRACTUAL
- DAILY_WAGE
- DEPUTATION
- OUTSOURCED
"""

import pytest
import re
import requests
import uuid
from datetime import datetime, timedelta
from tests.integration_utils import get_base_url, login_with_fallback
from tests.employee_split_test_utils import create_employee_two_step

BASE_URL = get_base_url()

# Test credentials
DATA_ENTRY_CREDS = {"email": "dataentry@madc.gov.in", "password": "dataentry123"}
VERIFIER_CREDS = {"email": "verifier@madc.gov.in", "password": "verifier123"}
ESTABLISHMENT_CREDS = {"email": "establishment@madc.gov.in", "password": "establishment123"}


def _get_token(role: str) -> str:
    candidates = {
        "DATA_ENTRY": [DATA_ENTRY_CREDS, {"email": "global.dataentry@madc.gov.in", "password": "dataentry123"}],
        "VERIFIER": [VERIFIER_CREDS, {"email": "global.verifier@madc.gov.in", "password": "verifier123"}],
        "ESTABLISHMENT": [ESTABLISHMENT_CREDS],
    }
    return login_with_fallback(BASE_URL, candidates[role], role)


class TestAuthentication:
    """Test authentication for all roles"""
    
    def test_data_entry_login(self):
        """DATA_ENTRY user can login"""
        token = _get_token("DATA_ENTRY")
        assert token
        print("DATA_ENTRY login successful")
    
    def test_verifier_login(self):
        """VERIFIER user can login"""
        token = _get_token("VERIFIER")
        assert token
        print("VERIFIER login successful")
    
    def test_establishment_login(self):
        """APPROVING_AUTHORITY user can login"""
        token = _get_token("ESTABLISHMENT")
        assert token
        print("APPROVING_AUTHORITY login successful")


class TestEmployeeIdentityBootstrapAPI:
    """Test identity bootstrap API endpoints used by the identity step"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for DATA_ENTRY"""
        return _get_token("DATA_ENTRY")
    
    def test_get_identity_bootstrap(self, auth_token):
        """GET /api/employee-identities/bootstrap returns identity editor bootstrap data"""
        response = requests.get(
            f"{BASE_URL}/api/employee-identities/bootstrap",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "departments" in data
        assert "designations" in data
        assert "employment_types" in data
        assert isinstance(data["departments"], list)
        assert isinstance(data["designations"], list)
        assert isinstance(data["employment_types"], list)
        print(
            f"Found {len(data['departments'])} departments and {len(data['designations'])} designations"
        )


class TestEmployeeProfileAPI:
    """Test employee profile API CRUD operations"""
    
    @pytest.fixture
    def data_entry_token(self):
        """Get auth token for DATA_ENTRY"""
        return _get_token("DATA_ENTRY")
    
    @pytest.fixture
    def verifier_token(self):
        """Get auth token for VERIFIER"""
        return _get_token("VERIFIER")
    
    def test_list_profiles(self, data_entry_token):
        """GET /api/employee-profiles/ returns profile list"""
        response = requests.get(
            f"{BASE_URL}/api/employee-profiles/",
            headers={"Authorization": f"Bearer {data_entry_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
        assert "total" in data
        print(f"Found {data['total']} profiles")
    
    def test_create_regular_profile(self, data_entry_token):
        """Split identity/profile flow creates REGULAR employee profile"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "full_name": f"TEST_Regular_{unique_id}",
            "date_of_birth": "1990-05-15",
            "gender": "Male",
            "employment_type": "REGULAR",
            "date_of_initial_engagement": "2025-01-15",
            "current_department_id": "FIN",
            "current_designation_id": "SO",
            "mobile_primary": "9876543210",
            "email_official": f"test_{unique_id}@gov.in",
            "father_name": "Test Father",
        }

        result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {data_entry_token}"},
            payload=payload,
        )
        assert result.identity_response.status_code == 200
        assert result.profile_response is not None
        assert result.profile_response.status_code == 200
        data = result.identity_response.json()
        assert "employee_id" in data
        assert "employee_code" in data
        assert re.fullmatch(r"MADC-\d{4}", data["employee_code"])
        assert result.profile_response.json()["workflow_status"] == "DRAFT"
        print(f"Created REGULAR profile: {data['employee_code']}")
    
    def test_create_contractual_profile(self, data_entry_token):
        """Split identity/profile flow creates CONTRACTUAL employee profile"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "full_name": f"TEST_Contractual_{unique_id}",
            "date_of_birth": "1992-08-20",
            "gender": "Female",
            "employment_type": "CONTRACTUAL",
            "date_of_initial_engagement": "2025-02-01",
            "current_department_id": "HR",
            "mobile_primary": "9876543211",
        }
        
        result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {data_entry_token}"},
            payload=payload,
        )
        assert result.identity_response.status_code == 200
        data = result.identity_response.json()
        assert re.fullmatch(r"MADC-\d{4}", data["employee_code"])
        print(f"Created CONTRACTUAL profile: {data['employee_code']}")
    
    def test_create_daily_wage_profile(self, data_entry_token):
        """Split identity/profile flow creates DAILY_WAGE employee profile"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "full_name": f"TEST_DailyWage_{unique_id}",
            "date_of_birth": "1995-03-10",
            "gender": "Male",
            "employment_type": "DAILY_WAGE",
            "date_of_initial_engagement": "2025-01-20",
            "current_department_id": "ADMIN",
            "mobile_primary": "9876543212",
        }
        
        result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {data_entry_token}"},
            payload=payload,
        )
        assert result.identity_response.status_code == 200
        data = result.identity_response.json()
        assert re.fullmatch(r"MADC-\d{4}", data["employee_code"])
        print(f"Created DAILY_WAGE profile: {data['employee_code']}")
    
    def test_create_deputation_profile(self, data_entry_token):
        """Split identity/profile flow creates DEPUTATION employee profile"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "full_name": f"TEST_Deputation_{unique_id}",
            "date_of_birth": "1988-11-25",
            "gender": "Female",
            "employment_type": "DEPUTATION",
            "date_of_initial_engagement": "2025-01-01",
            "current_department_id": "LEGAL",
            "mobile_primary": "9876543213",
        }
        
        result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {data_entry_token}"},
            payload=payload,
        )
        assert result.identity_response.status_code == 200
        data = result.identity_response.json()
        assert re.fullmatch(r"MADC-\d{4}", data["employee_code"])
        print(f"Created DEPUTATION profile: {data['employee_code']}")
    
    def test_create_outsourced_profile(self, data_entry_token):
        """Split identity/profile flow creates OUTSOURCED employee profile"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "full_name": f"TEST_Outsourced_{unique_id}",
            "date_of_birth": "1998-07-15",
            "gender": "Male",
            "employment_type": "OUTSOURCED",
            "date_of_initial_engagement": "2025-02-15",
            "current_department_id": "IT",
            "mobile_primary": "9876543214",
        }
        
        result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {data_entry_token}"},
            payload=payload,
        )
        assert result.identity_response.status_code == 200
        data = result.identity_response.json()
        assert re.fullmatch(r"MADC-\d{4}", data["employee_code"])
        print(f"Created OUTSOURCED profile: {data['employee_code']}")
    
    def test_get_profile_by_id(self, data_entry_token):
        """GET /api/employee-profiles/{employee_id} returns profile details"""
        unique_id = str(uuid.uuid4())[:8]
        create_result = create_employee_two_step(
            requests,
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {data_entry_token}"},
            payload={
                "full_name": f"TEST_GetById_{unique_id}",
                "date_of_birth": "1990-01-01",
                "gender": "Male",
                "employment_type": "REGULAR",
                "date_of_initial_engagement": "2025-01-01",
                "current_department_id": "FIN",
                "mobile_primary": "9876543215",
            },
        )
        assert create_result.identity_response.status_code == 200
        employee_id = create_result.employee_id
        assert employee_id

        # Get the profile
        response = requests.get(
            f"{BASE_URL}/api/employee-profiles/{employee_id}",
            headers={"Authorization": f"Bearer {data_entry_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == employee_id
        assert f"TEST_GetById_{unique_id}" in data["full_name"]
        print(f"Retrieved profile: {data['employee_code']}")
    
    def test_verifier_cannot_create_profile(self, verifier_token):
        """VERIFIER cannot create employee identities (RBAC check)"""
        payload = {
            "full_name": "TEST_ShouldFail",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "current_designation_id": "SO",
        }

        response = requests.post(
            f"{BASE_URL}/api/employee-identities/",
            headers={"Authorization": f"Bearer {verifier_token}"},
            json=payload
        )
        assert response.status_code == 403
        print("RBAC check passed: VERIFIER cannot create profiles")




if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

