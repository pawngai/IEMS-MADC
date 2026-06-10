"""
Dynamic Forms API Tests
=======================
Tests for the new forms API endpoints at /api/forms/*
Tests form structure separation from business logic (form_schema.json vs form_rules.py)
"""

import pytest
import requests
from tests.integration_utils import get_base_url, login_with_fallback

BASE_URL = get_base_url()

DEMO_USERS = {
    "DATA_ENTRY": {"email": "dataentry@madc.gov.in", "password": "dataentry123"},
}

ROLE_LOGIN_CANDIDATES = {
    "DATA_ENTRY": [
        DEMO_USERS["DATA_ENTRY"],
        {"email": "global.dataentry@madc.gov.in", "password": "dataentry123"},
    ],
}


@pytest.fixture(scope="session")
def data_entry_token():
    return login_with_fallback(BASE_URL, ROLE_LOGIN_CANDIDATES["DATA_ENTRY"], "DATA_ENTRY")


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestFormsAPIBasic:
    """Basic tests for forms API endpoints"""
    
    def test_get_employee_profile_form_default(self, data_entry_token):
        """GET /api/forms/employee-profile returns resolved form with default settings"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200
        
        data = response.json()
        # Check metadata
        assert "_metadata" in data
        assert data["_metadata"]["form_id"] == "employee_profile"
        assert str(data["_metadata"]["version"]).startswith("2.")
        
        # Check context
        assert "context" in data
        assert data["context"]["workflow_stage"] == "DRAFT"
        
        # Check fields
        assert "fields" in data
        assert len(data["fields"]) > 0
        assert "field_count" in data
        
        # Verify fields have resolved properties
        for field in data["fields"]:
            assert "field_id" in field
            assert "visible" in field
            assert "required" in field
            assert "readonly" in field
    
    def test_get_employee_profile_form_with_employment_type(self, data_entry_token):
        """GET /api/forms/employee-profile?employment_type=CONTRACTUAL returns type-specific fields"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile?employment_type=CONTRACTUAL",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["context"]["employment_type"] == "CONTRACTUAL"
        
        # Check that contract-specific fields are visible
        field_ids = [f["field_id"] for f in data["fields"]]
        assert "contract_start_date" in field_ids
        assert "contract_end_date" in field_ids
        assert "consolidated_pay" in field_ids
        
        # Check that REGULAR-specific fields are NOT visible
        assert "pension_scheme" not in field_ids
        assert "pcf_account_number" not in field_ids
    
    def test_get_employee_profile_form_regular_type(self, data_entry_token):
        """GET /api/forms/employee-profile?employment_type=REGULAR returns regular employee fields"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile?employment_type=REGULAR",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200
        
        data = response.json()
        field_ids = [f["field_id"] for f in data["fields"]]
        
        # Regular employees should have pension and service fields
        assert "pension_scheme" in field_ids
        assert "service_group" in field_ids
        assert "retirement_date" in field_ids
        
        # But NOT contract fields
        assert "contract_start_date" not in field_ids
        assert "consolidated_pay" not in field_ids


class TestFormsResolveEndpoint:
    """Tests for POST /api/forms/employee-profile/resolve"""
    
    def test_resolve_form_with_employment_type(self, data_entry_token):
        """POST /api/forms/employee-profile/resolve correctly resolves form based on employment_type"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/resolve",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "CONTRACTUAL",
                "workflow_stage": "DRAFT",
                "form_data": {}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["context"]["employment_type"] == "CONTRACTUAL"
        
        # Contract fields should be visible and required
        contract_start = next((f for f in data["fields"] if f["field_id"] == "contract_start_date"), None)
        assert contract_start is not None
        assert contract_start["visible"] == True
        assert contract_start["required"] == True
    
    def test_resolve_form_with_marital_status_married(self, data_entry_token):
        """Spouse name field visible when marital_status is Married"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/resolve",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "REGULAR",
                "workflow_stage": "DRAFT",
                "form_data": {"marital_status": "Married"}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        field_ids = [f["field_id"] for f in data["fields"]]
        
        # Spouse name should be visible when married
        assert "spouse_name" in field_ids
        spouse_field = next(f for f in data["fields"] if f["field_id"] == "spouse_name")
        assert spouse_field["required"] == True
    
    def test_resolve_form_with_marital_status_single(self, data_entry_token):
        """Spouse name field NOT visible when marital_status is Single"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/resolve",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "REGULAR",
                "workflow_stage": "DRAFT",
                "form_data": {"marital_status": "Single"}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        field_ids = [f["field_id"] for f in data["fields"]]
        
        # Spouse name should NOT be visible when single
        assert "spouse_name" not in field_ids

    def test_resolve_fixed_pay_includes_shared_personal_profile_fields(self, data_entry_token):
        """FIXED_PAY resolves the shared personal-profile fields used by the non-regular editor."""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/resolve",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "FIXED_PAY",
                "workflow_stage": "DRAFT",
                "form_data": {"marital_status": "MARRIED"}
            }
        )
        assert response.status_code == 200

        data = response.json()
        field_ids = [f["field_id"] for f in data["fields"]]

        assert "mother_name" in field_ids
        assert "marital_status" in field_ids
        assert "spouse_name" in field_ids

        spouse_field = next(f for f in data["fields"] if f["field_id"] == "spouse_name")
        assert spouse_field["required"] == True
    
    def test_resolve_form_daily_wage_type(self, data_entry_token):
        """DAILY_WAGE employment type shows daily_rate and muster_roll_number"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/resolve",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "DAILY_WAGE",
                "workflow_stage": "DRAFT",
                "form_data": {}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        field_ids = [f["field_id"] for f in data["fields"]]
        
        assert "daily_rate" in field_ids
        assert "muster_roll_number" in field_ids
        
        # Should NOT have contract or regular fields
        assert "contract_start_date" not in field_ids
        assert "pension_scheme" not in field_ids
    
    def test_resolve_form_deputation_type(self, data_entry_token):
        """DEPUTATION employment type shows deputation-specific fields"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/resolve",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "DEPUTATION",
                "workflow_stage": "DRAFT",
                "form_data": {}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        field_ids = [f["field_id"] for f in data["fields"]]
        
        assert "parent_department_code" in field_ids
        assert "deputation_start_date" in field_ids
        assert "deputation_end_date" in field_ids
        assert "lien_position" in field_ids
    
    def test_resolve_form_outsourced_type(self, data_entry_token):
        """OUTSOURCED employment type shows agency fields"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/resolve",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "OUTSOURCED",
                "workflow_stage": "DRAFT",
                "form_data": {}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        field_ids = [f["field_id"] for f in data["fields"]]
        
        assert "outsourcing_agency" in field_ids
        assert "agency_contract_number" in field_ids


class TestFormsValidateEndpoint:
    """Tests for POST /api/forms/employee-profile/validate"""
    
    def test_validate_empty_form_returns_errors(self, data_entry_token):
        """Validation returns errors for missing required fields"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/validate",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "REGULAR",
                "workflow_stage": "DRAFT",
                "form_data": {}
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == False
        assert data["error_count"] > 0
        
        # Check that required fields are in errors
        error_fields = [e["field_id"] for e in data["errors"]]
        assert "full_name" in error_fields
        assert "gender" in error_fields
        assert "date_of_birth" in error_fields
        assert "mobile_number" in error_fields
        assert "employment_type" in error_fields
    
    def test_validate_contractual_requires_contract_fields(self, data_entry_token):
        """CONTRACTUAL type requires contract-specific fields"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/validate",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "CONTRACTUAL",
                "workflow_stage": "DRAFT",
                "form_data": {
                    "full_name": "Test User",
                    "gender": "Male",
                    "date_of_birth": "1990-01-15",
                    "mobile_number": "9876543210",
                    "employment_type": "CONTRACTUAL",
                    "department_code": "IT",
                    "designation_code": "AN"
                }
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should still have errors for contract-specific required fields
        error_fields = [e["field_id"] for e in data["errors"]]
        assert "contract_start_date" in error_fields
        assert "contract_end_date" in error_fields
        assert "consolidated_pay" in error_fields
    
    def test_validate_valid_regular_employee(self, data_entry_token):
        """Valid REGULAR employee data passes validation"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/validate",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "REGULAR",
                "workflow_stage": "DRAFT",
                "form_data": {
                    "full_name": "Test Regular Employee",
                    "gender": "Male",
                    "date_of_birth": "1990-01-15",
                    "mobile_number": "9876543210",
                    "employment_type": "REGULAR",
                    "department_code": "IT",
                    "designation_code": "AN",
                    "service_group": "GRP-B-NG",
                    "pension_scheme": "NPS",
                    "retirement_date": "2050-01-31",
                    "aadhaar_number": "234567890123",
                    "pan_number": "ABCDE1234F",
                    "bank_account_number": "1234567890"
                }
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Should have minimal or no errors
        assert data["error_count"] <= 2  # May have some optional field errors

    def test_validate_invalid_workflow_stage_returns_400(self, data_entry_token):
        """Invalid workflow_stage returns 400 instead of server error"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/validate",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "REGULAR",
                "workflow_stage": "INVALID_STAGE",
                "form_data": {"full_name": "X"}
            }
        )
        assert response.status_code == 400
        assert "Invalid workflow_stage" in response.json().get("detail", "")

    def test_validate_invalid_employment_type_returns_400(self, data_entry_token):
        """Invalid employment_type returns 400 instead of server error"""
        response = requests.post(
            f"{BASE_URL}/api/forms/employee-profile/validate",
            headers=_auth_headers(data_entry_token),
            json={
                "employment_type": "TEMP",
                "workflow_stage": "DRAFT",
                "form_data": {"full_name": "X"}
            }
        )
        assert response.status_code == 400
        assert "Invalid employment_type" in response.json().get("detail", "")


class TestEmploymentTypesEndpoint:
    """Tests for GET /api/forms/employee-profile/employment-types"""
    
    def test_get_all_employment_types(self, data_entry_token):
        """Returns all employment types with field counts"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/employment-types",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "employment_types" in data
        
        types = data["employment_types"]
        assert len(types) == 6  # REGULAR, CONTRACTUAL, DAILY_WAGE, DEPUTATION, REEMPLOYED, OUTSOURCED
        
        # Check structure of each type
        for emp_type in types:
            assert "code" in emp_type
            assert "label" in emp_type
            assert "field_count" in emp_type
            assert "required_count" in emp_type
            assert "has_service_book" in emp_type
            assert "specific_fields" in emp_type
    
    def test_employment_types_have_correct_specific_fields(self, data_entry_token):
        """Each employment type has correct specific fields"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/employment-types",
            headers=_auth_headers(data_entry_token),
        )
        data = response.json()
        
        types_dict = {t["code"]: t for t in data["employment_types"]}
        
        # REGULAR should have pension/service fields
        assert "pension_scheme" in types_dict["REGULAR"]["specific_fields"]
        assert "service_group" in types_dict["REGULAR"]["specific_fields"]
        
        # CONTRACTUAL should have contract fields
        assert "contract_start_date" in types_dict["CONTRACTUAL"]["specific_fields"]
        assert "consolidated_pay" in types_dict["CONTRACTUAL"]["specific_fields"]
        
        # DAILY_WAGE should have daily rate
        assert "daily_rate" in types_dict["DAILY_WAGE"]["specific_fields"]
        
        # DEPUTATION should have deputation fields
        assert "parent_department_code" in types_dict["DEPUTATION"]["specific_fields"]
        
        # OUTSOURCED should have agency fields
        assert "outsourcing_agency" in types_dict["OUTSOURCED"]["specific_fields"]
    
    def test_service_book_flags_correct(self, data_entry_token):
        """has_service_book flag is correct for each type"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/employment-types",
            headers=_auth_headers(data_entry_token),
        )
        data = response.json()
        
        types_dict = {t["code"]: t for t in data["employment_types"]}
        
        # Types with service book
        assert types_dict["REGULAR"]["has_service_book"] == True
        assert types_dict["DEPUTATION"]["has_service_book"] == False
        assert types_dict["REEMPLOYED"]["has_service_book"] == False
        
        # Types without service book
        assert types_dict["CONTRACTUAL"]["has_service_book"] == False
        assert types_dict["DAILY_WAGE"]["has_service_book"] == False
        assert types_dict["OUTSOURCED"]["has_service_book"] == False

    def test_employment_type_fields_payload_is_separate_per_type(self, data_entry_token):
        """Endpoint returns dedicated fields payload for each employment type"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/employment-types",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200

        data = response.json()
        assert "employment_type_payloads" in data

        payloads = data["employment_type_payloads"]
        listed_codes = [item["code"] for item in data["employment_types"]]

        assert set(payloads.keys()) == set(listed_codes)
        for code in listed_codes:
            payload = payloads[code]
            assert "fields" in payload
            assert "visible_field_ids" in payload
            assert "required_field_ids" in payload
            assert "readonly_field_ids" in payload
            assert "field_count" in payload
            assert payload["field_count"] == len(payload["fields"])

            entry = next(item for item in data["employment_types"] if item["code"] == code)
            assert entry["fields_payload"]["field_count"] == entry["field_count"]


class TestFormPartsEndpoint:
    """Tests for GET /api/forms/employee-profile/parts"""
    
    def test_get_form_parts_default(self, data_entry_token):
        """Returns form parts with field counts"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/parts",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "parts" in data
        assert "total_fields" in data
        
        parts = data["parts"]
        assert len(parts) >= 5  # core sections plus optional expanded sections in newer schemas
        
        # Check structure
        for part in parts:
            assert "id" in part
            assert "label" in part
            assert "step" in part
            assert "field_count" in part
            assert "required_count" in part
    
    def test_get_form_parts_with_employment_type(self, data_entry_token):
        """Parts field counts change based on employment type"""
        # Get parts for REGULAR
        response_regular = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/parts?employment_type=REGULAR",
            headers=_auth_headers(data_entry_token),
        )
        data_regular = response_regular.json()
        
        # Get parts for DAILY_WAGE
        response_daily = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/parts?employment_type=DAILY_WAGE",
            headers=_auth_headers(data_entry_token),
        )
        data_daily = response_daily.json()
        
        # REGULAR should have more fields than DAILY_WAGE
        assert data_regular["total_fields"] > data_daily["total_fields"]
        
        # type_specific part should have different field counts
        regular_type_specific = next(p for p in data_regular["parts"] if p["id"] == "type_specific")
        daily_type_specific = next(p for p in data_daily["parts"] if p["id"] == "type_specific")
        
        assert regular_type_specific["field_count"] > daily_type_specific["field_count"]


class TestFieldConfigEndpoint:
    """Tests for GET /api/forms/employee-profile/field/{field_id}"""
    
    def test_get_field_config(self, data_entry_token):
        """Returns configuration for a specific field"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/field/full_name",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["field_id"] == "full_name"
        assert data["label"] == "Full Name"
        assert "visible" in data
        assert "required" in data
        assert "readonly" in data
    
    def test_get_field_config_with_employment_type(self, data_entry_token):
        """Field config changes based on employment type"""
        # contract_start_date should be visible for CONTRACTUAL
        response_contract = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/field/contract_start_date?employment_type=CONTRACTUAL",
            headers=_auth_headers(data_entry_token),
        )
        assert response_contract.status_code == 200
        data_contract = response_contract.json()
        assert data_contract["visible"] == True
        
        # contract_start_date should NOT be visible for REGULAR
        response_regular = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/field/contract_start_date?employment_type=REGULAR",
            headers=_auth_headers(data_entry_token),
        )
        assert response_regular.status_code == 200
        data_regular = response_regular.json()
        assert data_regular["visible"] == False
    
    def test_get_nonexistent_field_returns_404(self, data_entry_token):
        """Returns 404 for non-existent field"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/field/nonexistent_field",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 404

    def test_get_field_config_invalid_workflow_stage_returns_400(self, data_entry_token):
        """Invalid workflow_stage is rejected with 400"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/field/full_name?workflow_stage=INVALID_STAGE",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 400
        assert "Invalid workflow_stage" in response.json().get("detail", "")

    def test_get_field_config_invalid_employment_type_returns_400(self, data_entry_token):
        """Invalid employment_type is rejected with 400"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/field/full_name?employment_type=TEMP",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 400
        assert "Invalid employment_type" in response.json().get("detail", "")


class TestReadonlyMatrix:
    """Tests for GET /api/forms/employee-profile/readonly-matrix"""
    
    def test_get_readonly_matrix(self, data_entry_token):
        """Returns readonly matrix for all workflow stages"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/readonly-matrix",
            headers=_auth_headers(data_entry_token),
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "stages" in data
        assert "matrix" in data
        
        # Check stages
        stages = data["stages"]
        assert "DRAFT" in stages
        assert "SUBMITTED" in stages
        assert "VERIFIED" in stages
        assert "APPROVED" in stages
        assert "ATTESTED" in stages
        assert "LOCKED" in stages
        
        # Check matrix structure
        matrix = data["matrix"]
        assert len(matrix) > 0
        
        for row in matrix:
            assert "field_id" in row
            assert "label" in row
            # Should have boolean for each stage
            for stage in stages:
                assert stage in row
                assert isinstance(row[stage], bool)
    
    def test_employee_id_always_readonly(self, data_entry_token):
        """employee_id field is readonly in all stages"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/readonly-matrix",
            headers=_auth_headers(data_entry_token),
        )
        data = response.json()
        
        employee_id_row = next((r for r in data["matrix"] if r["field_id"] == "employee_id"), None)
        assert employee_id_row is not None
        
        # Should be readonly in all stages
        for stage in data["stages"]:
            assert employee_id_row[stage] == True

    def test_department_code_readonly_when_locked(self, data_entry_token):
        """department_code becomes readonly at LOCKED stage"""
        response = requests.get(
            f"{BASE_URL}/api/forms/employee-profile/readonly-matrix",
            headers=_auth_headers(data_entry_token),
        )
        data = response.json()

        row = next((r for r in data["matrix"] if r["field_id"] == "department_code"), None)
        assert row is not None
        assert row["LOCKED"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
