"""
Employee Form Wizard API Tests - Multi-step Wizard with Employment-Type-Driven Validation
Tests for: Form Schema, Type-Specific Fields, Validation, Rejected Fields
"""
import pytest
import requests
import uuid
from tests.employee_split_test_utils import create_employee_two_step
from tests.integration_utils import get_base_url, login_with_fallback

BASE_URL = get_base_url()

# Demo credentials
DEMO_USERS = {
    "DATA_ENTRY": {"email": "dataentry@madc.gov.in", "password": "dataentry123"},
    "SYSTEM_ADMIN": {"email": "admin@madc.gov.in", "password": "admin123"},
}

ROLE_LOGIN_CANDIDATES = {
    "DATA_ENTRY": [
        DEMO_USERS["DATA_ENTRY"],
        {"email": "global.dataentry@madc.gov.in", "password": "dataentry123"},
    ],
    "SYSTEM_ADMIN": [DEMO_USERS["SYSTEM_ADMIN"]],
}

EMPLOYMENT_TYPES = ["REGULAR", "CONTRACTUAL", "DAILY_WAGE", "DEPUTATION", "REEMPLOYED", "OUTSOURCED"]

# Service Book fields that should be rejected
REJECTED_FIELDS = [
    "pay_scale", "increment_date", "promotion_date",
    "transfer_history", "leave_balance", "disciplinary_case", "macp_acp",
    "suspension_details", "annual_increment", "current_pay", "grade_pay"
]


@pytest.fixture(scope="session")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def data_entry_token(api_client):
    """Get auth token for DATA_ENTRY user"""
    return login_with_fallback(BASE_URL, ROLE_LOGIN_CANDIDATES["DATA_ENTRY"], "DATA_ENTRY")


def get_auth_header(token):
    """Get authorization header"""
    return {"Authorization": f"Bearer {token}"}


# ==================== FORM SCHEMA API TESTS ====================
class TestFormSchemaAPI:
    """Tests for /api/masters/employee-form-schema endpoint"""
    
    def test_get_full_form_schema(self, api_client):
        """Test getting complete form schema without employment type filter"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-schema")
        assert response.status_code == 200
        data = response.json()
        
        # Verify schema structure
        assert "form_id" in data
        assert data["form_id"] == "employee_profile_wizard"
        assert "common_fields" in data
        assert "employment_type_fields" in data
        assert "rejected_fields" in data
        assert "wizard_steps" in data
        
        # Verify wizard has 5 steps
        assert len(data["wizard_steps"]) == 5
        
        # Verify all employment types have fields defined
        for emp_type in EMPLOYMENT_TYPES:
            assert emp_type in data["employment_type_fields"], f"Missing fields for {emp_type}"
        
        print(f"SUCCESS: Form schema has {len(data['common_fields'])} common fields, {len(data['wizard_steps'])} steps")
    
    def test_get_form_schema_for_regular(self, api_client):
        """Test getting form schema filtered for REGULAR employment type"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-schema?employment_type=REGULAR")
        assert response.status_code == 200
        data = response.json()
        
        assert "common_fields" in data
        assert "type_specific_fields" in data
        assert "all_fields" in data
        assert data["employment_type"] == "REGULAR"
        
        # REGULAR should have pension_scheme field
        field_ids = [f["field_id"] for f in data["type_specific_fields"]]
        assert "pension_scheme" in field_ids
        assert "appointment_order_no" in field_ids
        
        print(f"SUCCESS: REGULAR schema has {len(data['type_specific_fields'])} type-specific fields")
    
    def test_get_form_schema_for_contractual(self, api_client):
        """Test getting form schema filtered for CONTRACTUAL employment type"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-schema?employment_type=CONTRACTUAL")
        assert response.status_code == 200
        data = response.json()
        
        # CONTRACTUAL should have contract fields, NOT pension_scheme
        field_ids = [f["field_id"] for f in data["type_specific_fields"]]
        assert "contract_order_no" in field_ids
        assert "contract_start_date" in field_ids
        assert "consolidated_pay" in field_ids
        assert "pension_scheme" not in field_ids
        
        print(f"SUCCESS: CONTRACTUAL schema has {len(data['type_specific_fields'])} type-specific fields")
    
    def test_get_form_schema_invalid_type(self, api_client):
        """Test getting form schema with invalid employment type"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-schema?employment_type=INVALID")
        assert response.status_code == 400
        print("SUCCESS: Invalid employment type returns 400")


# ==================== TYPE-SPECIFIC FIELDS API TESTS ====================
class TestTypeSpecificFieldsAPI:
    """Tests for /api/masters/employee-form-fields/{employment_type} endpoint"""
    
    @pytest.mark.parametrize("emp_type", EMPLOYMENT_TYPES)
    def test_get_fields_for_each_type(self, api_client, emp_type):
        """Test getting fields for each employment type"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-fields/{emp_type}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["employment_type"] == emp_type
        assert "fields" in data
        assert "wizard_steps" in data
        assert "total_fields" in data
        assert len(data["fields"]) > 0
        
        print(f"SUCCESS: {emp_type} has {data['total_fields']} fields")
    
    def test_regular_has_pension_fields(self, api_client):
        """Test REGULAR employment type has pension-related fields"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-fields/REGULAR")
        data = response.json()
        
        field_ids = [f["field_id"] for f in data["fields"]]
        assert "pension_scheme" in field_ids
        assert "retirement_date" in field_ids
        assert "cadre" in field_ids
        assert "service_group" in field_ids
        
        print("SUCCESS: REGULAR has pension_scheme, retirement_date, cadre, service_group")
    
    def test_contractual_has_contract_fields(self, api_client):
        """Test CONTRACTUAL employment type has contract-related fields"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-fields/CONTRACTUAL")
        data = response.json()
        
        field_ids = [f["field_id"] for f in data["fields"]]
        assert "contract_order_no" in field_ids
        assert "contract_start_date" in field_ids
        assert "contract_end_date" in field_ids
        assert "consolidated_pay" in field_ids
        assert "renewal_allowed" in field_ids
        
        # Should NOT have REGULAR-specific fields
        assert "pension_scheme" not in field_ids
        assert "cadre" not in field_ids
        
        print("SUCCESS: CONTRACTUAL has contract fields, no pension fields")
    
    def test_daily_wage_has_engagement_fields(self, api_client):
        """Test DAILY_WAGE employment type has engagement-related fields"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-fields/DAILY_WAGE")
        data = response.json()
        
        field_ids = [f["field_id"] for f in data["fields"]]
        assert "engagement_order_no" in field_ids
        assert "engagement_date" in field_ids
        assert "wage_rate_per_day" in field_ids
        assert "nature_of_work" in field_ids
        
        print("SUCCESS: DAILY_WAGE has engagement fields")
    
    def test_deputation_has_deputation_fields(self, api_client):
        """Test DEPUTATION employment type has deputation-related fields"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-fields/DEPUTATION")
        data = response.json()
        
        field_ids = [f["field_id"] for f in data["fields"]]
        assert "parent_department" in field_ids
        assert "parent_designation" in field_ids
        assert "deputation_order_no" in field_ids
        assert "deputation_start_date" in field_ids
        assert "lien_retained" in field_ids
        
        print("SUCCESS: DEPUTATION has deputation fields")
    
    def test_outsourced_has_vendor_fields(self, api_client):
        """Test OUTSOURCED employment type has vendor-related fields"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-fields/OUTSOURCED")
        data = response.json()
        
        field_ids = [f["field_id"] for f in data["fields"]]
        assert "vendor_name" in field_ids
        assert "vendor_contract_no" in field_ids
        assert "role_description" in field_ids
        
        print("SUCCESS: OUTSOURCED has vendor fields")


# ==================== VALIDATION API TESTS ====================
class TestValidationAPI:
    """Tests for /api/forms/employee-profile/validate endpoint"""
    
    def test_validate_missing_required_fields(self, api_client, data_entry_token):
        """Test validation returns errors for missing required fields"""
        headers = get_auth_header(data_entry_token)
        response = api_client.post(
            f"{BASE_URL}/api/forms/employee-profile/validate",
            json={"employment_type": "REGULAR", "form_data": {"full_name": "Test User"}},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
        assert data["error_count"] > 0
        assert len(data["errors"]) > 0
        
        print(f"SUCCESS: Validation returned {len(data['errors'])} errors for missing fields")


# ==================== PROFILE CREATION WITH VALIDATION TESTS ====================
class TestProfileCreationValidation:
    """Tests for split identity/profile validation with employment-type rules"""
    
    def test_create_profile_rejects_service_book_fields(self, api_client, data_entry_token):
        """Test profile update rejects Service Book fields after identity creation"""
        headers = get_auth_header(data_entry_token)
        create_result = create_employee_two_step(
            api_client,
            base_url=BASE_URL,
            headers=headers,
            payload={
                "full_name": "Test User",
                "gender": "Male",
                "date_of_birth": "1990-01-15",
                "employment_type": "REGULAR",
                "date_of_initial_engagement": "2024-01-15",
                "current_department_id": "FIN",
            },
        )
        assert create_result.identity_response.status_code == 200
        employee_id = create_result.employee_id
        assert employee_id

        response = api_client.put(
            f"{BASE_URL}/api/employee-profiles/{employee_id}",
            json={
                "mobile_primary": "9876543210",
                "pay_scale": "L10",
                "basic_pay": 50000,
            },
            headers=headers,
        )
        assert response.status_code in (400, 422)
        data = response.json()
        
        assert "detail" in data
        
        print("SUCCESS: Profile creation rejects Service Book fields")
    
    def test_create_profile_rejects_invalid_combinations(self, api_client, data_entry_token):
        """Test profile extension update rejects invalid field combinations"""
        headers = get_auth_header(data_entry_token)
        unique_id = str(uuid.uuid4())[:8]

        create_result = create_employee_two_step(
            api_client,
            base_url=BASE_URL,
            headers=headers,
            payload={
                "full_name": f"TEST_{unique_id} User",
                "gender": "Male",
                "date_of_birth": "1990-01-15",
                "employment_type": "CONTRACTUAL",
                "date_of_initial_engagement": "2024-01-15",
                "current_department_id": "FIN",
                "current_designation_id": "L6",
                "current_office_id": "HR-HQ",
            },
        )
        assert create_result.identity_response.status_code == 200

        response = api_client.put(
            f"{BASE_URL}/api/employee-profiles/{create_result.employee_id}",
            json={
                "mobile_primary": "9876543210",
                "email_personal": f"test_{unique_id}@test.com",
                "pension_scheme": "NPS",
            },
            headers=headers,
        )
        assert response.status_code in (400, 422)
        data = response.json()
        
        assert "detail" in data
        
        print("SUCCESS: Profile creation rejects pension_scheme for CONTRACTUAL")
    
    @pytest.mark.parametrize("rejected_field", REJECTED_FIELDS[:5])  # Test first 5 rejected fields
    def test_create_profile_rejects_each_service_book_field(self, api_client, data_entry_token, rejected_field):
        """Test each Service Book field is rejected on the profile endpoint"""
        headers = get_auth_header(data_entry_token)
        create_result = create_employee_two_step(
            api_client,
            base_url=BASE_URL,
            headers=headers,
            payload={
                "full_name": "Test User",
                "gender": "Male",
                "date_of_birth": "1990-01-15",
                "employment_type": "REGULAR",
                "date_of_initial_engagement": "2024-01-15",
                "current_department_id": "FIN",
            },
        )
        assert create_result.identity_response.status_code == 200

        response = api_client.put(
            f"{BASE_URL}/api/employee-profiles/{create_result.employee_id}",
            json={"mobile_primary": "9876543210", rejected_field: "test_value"},
            headers=headers,
        )
        assert response.status_code in (400, 422)
        data = response.json()
        
        # Check the rejected field is mentioned in the error response.
        # Domain-separation errors use "detail.violating_fields" (list of field names).
        # Form-validation errors use "detail.errors" (list of dicts with "field_id").
        # Pydantic model rejection uses "detail" as a list of validation errors with "msg".
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            error_fields = detail.get("violating_fields", [])
            if not error_fields:
                error_fields = [e.get("field_id") for e in detail.get("errors", [])]
        elif isinstance(detail, list):
            # Pydantic validation errors — check if field name appears in any error message
            error_fields = [e.get("field_id") for e in detail if isinstance(e, dict) and e.get("field_id")]
            if not error_fields:
                # Field name may appear in the error message text
                msgs = " ".join(e.get("msg", "") for e in detail if isinstance(e, dict))
                if rejected_field in msgs:
                    error_fields = [rejected_field]
        else:
            error_fields = []
        assert rejected_field in error_fields, (
            f"Field {rejected_field} should be rejected, got status={response.status_code} body={data}"
        )
        
        print(f"SUCCESS: Field '{rejected_field}' is rejected as Service Book field")


# ==================== WIZARD STEPS CONFIGURATION TESTS ====================
class TestWizardStepsConfiguration:
    """Tests for wizard steps configuration"""
    
    def test_wizard_has_five_steps(self, api_client):
        """Test wizard configuration has exactly 5 steps"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-schema")
        data = response.json()
        
        assert len(data["wizard_steps"]) == 5
        
        steps = data["wizard_steps"]
        assert steps[0]["title"] == "Personal Information"
        assert steps[1]["title"] == "Contact & Address"
        assert steps[2]["title"] == "Employment Details"
        assert steps[3]["title"] == "Type-Specific Details"
        assert steps[4]["title"] == "Review & Submit"
        
        print("SUCCESS: Wizard has 5 steps: Personal â†’ Contact â†’ Employment â†’ Details â†’ Review")
    
    def test_step_4_is_dynamic(self, api_client):
        """Test step 4 is marked as dynamic (employment-type-driven)"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-schema")
        data = response.json()
        
        step_4 = data["wizard_steps"][3]
        assert step_4["step"] == 4
        assert step_4.get("dynamic") == True
        
        print("SUCCESS: Step 4 is marked as dynamic")
    
    def test_step_5_is_review(self, api_client):
        """Test step 5 is marked as review step"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-schema")
        data = response.json()
        
        step_5 = data["wizard_steps"][4]
        assert step_5["step"] == 5
        assert step_5.get("is_review") == True
        
        print("SUCCESS: Step 5 is marked as review step")
    
    def test_fields_assigned_to_correct_steps(self, api_client):
        """Test fields are assigned to correct wizard steps"""
        response = api_client.get(f"{BASE_URL}/api/masters/employee-form-fields/REGULAR")
        data = response.json()
        
        step_1_fields = [f for f in data["fields"] if f["step"] == 1]
        step_2_fields = [f for f in data["fields"] if f["step"] == 2]
        step_3_fields = [f for f in data["fields"] if f["step"] == 3]
        step_4_fields = [f for f in data["fields"] if f["step"] == 4]
        
        # Step 1 should have personal fields
        step_1_ids = [f["field_id"] for f in step_1_fields]
        assert "full_name" in step_1_ids
        assert "gender" in step_1_ids
        assert "date_of_birth" in step_1_ids
        
        # Step 2 should have contact fields
        step_2_ids = [f["field_id"] for f in step_2_fields]
        assert "mobile_no" in step_2_ids
        assert "email" in step_2_ids
        assert "permanent_address" in step_2_ids
        
        # Step 3 should have employment fields
        step_3_ids = [f["field_id"] for f in step_3_fields]
        assert "employment_type" in step_3_ids
        assert "department_id" in step_3_ids
        
        # Step 4 should have type-specific fields
        step_4_ids = [f["field_id"] for f in step_4_fields]
        assert "pension_scheme" in step_4_ids  # REGULAR-specific
        assert "appointment_order_no" in step_4_ids
        
        print(f"SUCCESS: Fields correctly distributed - Step1:{len(step_1_fields)}, Step2:{len(step_2_fields)}, Step3:{len(step_3_fields)}, Step4:{len(step_4_fields)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

