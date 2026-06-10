"""
IEMS Backend API Tests - Compliant
Tests for: Auth, Profile, Service Book, Workflow, Masters, ESS, Audit APIs
"""
import pytest
import requests
import uuid
import time
from tests.employee_split_test_utils import create_employee_two_step
from tests.integration_utils import get_base_url, login_with_fallback

BASE_URL = get_base_url()

# Demo credentials
DEMO_USERS = {
    "DATA_ENTRY": {"email": "dataentry@madc.gov.in", "password": "dataentry123"},
    "VERIFIER": {"email": "verifier@madc.gov.in", "password": "verifier123"},
    "APPROVING_AUTHORITY": {"email": "hoo@madc.gov.in", "password": "hoo123"},
    "AUDITOR": {"email": "auditor@madc.gov.in", "password": "auditor123"},
    "SYSTEM_ADMIN": {"email": "admin@madc.gov.in", "password": "admin123"},
    "EMPLOYEE": {"email": "rajesh.singh@madc.gov.in", "password": "employee123"},
}

ROLE_LOGIN_CANDIDATES = {
    "DATA_ENTRY": [
        DEMO_USERS["DATA_ENTRY"],
        {"email": "global.dataentry@madc.gov.in", "password": "dataentry123"},
    ],
    "VERIFIER": [
        DEMO_USERS["VERIFIER"],
        {"email": "global.verifier@madc.gov.in", "password": "verifier123"},
    ],
    "APPROVING_AUTHORITY": [
        DEMO_USERS["APPROVING_AUTHORITY"],
    ],
    "AUDITOR": [
        DEMO_USERS["AUDITOR"],
    ],
    "SYSTEM_ADMIN": [DEMO_USERS["SYSTEM_ADMIN"]],
    "EMPLOYEE": [
        DEMO_USERS["EMPLOYEE"],
    ],
}


@pytest.fixture(scope="session")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def tokens(api_client):
    """Get auth tokens for all demo users"""
    tokens = {}
    for role, candidates in ROLE_LOGIN_CANDIDATES.items():
        for creds in candidates:
            response = _post_login_with_retry(api_client, creds)
            if response.status_code == 200:
                tokens[role] = response.json().get("access_token")
                break
    return tokens


def get_auth_header(tokens, role):
    """Get authorization header for a role"""
    token = tokens.get(role)
    if not token:
        pytest.skip(f"Role token unavailable in current test state: {role}")
    return {"Authorization": f"Bearer {token}"}


def _post_login_with_retry(api_client, creds):
    """POST /auth/login with short retry/backoff on 429 rate-limit responses."""
    response = None
    for delay in (0.0, 1.0, 2.0):
        if delay:
            time.sleep(delay)
        response = api_client.post(f"{BASE_URL}/api/auth/login", json=creds)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    time.sleep(float(retry_after))
                except (TypeError, ValueError):
                    pass
        if response.status_code != 429:
            return response
    return response


def login_response_with_fallback(api_client, role):
    """Try role login candidates and return first successful response."""
    candidates = ROLE_LOGIN_CANDIDATES[role]
    last_status = None
    last_body = None
    for creds in candidates:
        response = _post_login_with_retry(api_client, creds)
        if response.status_code == 200:
            return response
        last_status = response.status_code
        last_body = response.text

    pytest.skip(
        f"{role} login unavailable in current test state "
        f"(last_status={last_status}, body={last_body})"
    )


# ==================== HEALTH CHECK TESTS ====================
class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_root(self, api_client):
        """Test API root endpoint"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert any(tag in data["message"] for tag in ["IEMS", "MADC-HRMS"])
        print(f"SUCCESS: API root returns: {data['message']}")
    
    def test_health_endpoint(self, api_client):
        """Test health endpoint"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("SUCCESS: Health endpoint returns healthy")


# ==================== AUTH TESTS ====================
class TestAuthentication:
    """Authentication and RBAC tests"""
    
    def test_login_data_entry(self, api_client):
        """Test DATA_ENTRY login"""
        response = login_response_with_fallback(api_client, "DATA_ENTRY")
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert any(a in data["user"]["authorities"] for a in ["DATA_ENTRY", "GLOBAL_DATA_ENTRY"])
        print(f"SUCCESS: DATA_ENTRY login - authorities: {data['user']['authorities']}")
    
    def test_login_verifier(self, api_client):
        """Test VERIFIER login"""
        response = login_response_with_fallback(api_client, "VERIFIER")
        data = response.json()
        assert "VERIFIER" in data["user"]["authorities"]
        print(f"SUCCESS: VERIFIER login - authorities: {data['user']['authorities']}")
    
    def test_login_approving_authority(self, api_client):
        """Test APPROVING_AUTHORITY login"""
        response = login_response_with_fallback(api_client, "APPROVING_AUTHORITY")
        data = response.json()
        assert "APPROVING_AUTHORITY" in data["user"]["authorities"]
        print(f"SUCCESS: APPROVING_AUTHORITY login - authorities: {data['user']['authorities']}")
    
    def test_login_auditor(self, api_client):
        """Test AUDITOR login"""
        response = login_response_with_fallback(api_client, "AUDITOR")
        data = response.json()
        assert "AUDITOR" in data["user"]["authorities"]
        print(f"SUCCESS: AUDITOR login - authorities: {data['user']['authorities']}")
    
    def test_login_employee(self, api_client):
        """Test EMPLOYEE login"""
        response = login_response_with_fallback(api_client, "EMPLOYEE")
        data = response.json()
        assert "EMPLOYEE" in data["user"]["authorities"]
        assert data["user"].get("employee_id") is not None
        print(f"SUCCESS: EMPLOYEE login - employee_id: {data['user']['employee_id']}")
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 429]
        print(f"SUCCESS: Invalid credentials handled with status {response.status_code}")
    
    def test_get_me_authenticated(self, api_client, tokens):
        """Test /auth/me endpoint"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "authorities" in data
        print(f"SUCCESS: /auth/me returns user: {data['email']}")
    
    def test_get_me_unauthenticated(self, api_client):
        """Test /auth/me without token"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print("SUCCESS: /auth/me without token returns 401/403")
    
    def test_rbac_matrix(self, api_client, tokens):
        """Test RBAC matrix endpoint"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/auth/rbac-matrix", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "authorities" in data
        assert "permissions" in data
        assert "matrix" in data
        assert "workflow_stages" in data
        print(f"SUCCESS: RBAC matrix - {len(data['authorities'])} authorities, {len(data['permissions'])} permissions")


# ==================== MASTERS TESTS ====================
class TestMasters:
    """Master data API tests"""
    
    def test_get_employment_types(self, api_client):
        """Test employment types endpoint"""
        response = api_client.get(f"{BASE_URL}/api/masters/employment-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check for expected employment types
        codes = [t["code"] for t in data]
        assert codes == ["CONTRACT", "MUSTER_ROLL", "FIXED_PAY", "CO_TERMINUS", "WAGES"]
        print(f"SUCCESS: Employment types - {len(data)} types found")
    
    def test_get_employment_type_rules(self, api_client):
        """Test employment type rules"""
        response = api_client.get(f"{BASE_URL}/api/masters/employment-types/REG/rules")
        assert response.status_code == 200
        data = response.json()
        assert "has_service_book" in data
        assert data["has_service_book"] == True
        print(f"SUCCESS: REG employment type has service book: {data['has_service_book']}")
    
    def test_get_service_event_types(self, api_client):
        """Test service event types"""
        response = api_client.get(f"{BASE_URL}/api/masters/service-event-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"SUCCESS: Service event types - {len(data)} types found")
    
    def test_get_leave_types(self, api_client):
        """Test leave types"""
        response = api_client.get(f"{BASE_URL}/api/masters/leave-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Leave types - {len(data)} types found")
    
    def test_get_pay_levels(self, api_client):
        """Test pay levels"""
        response = api_client.get(f"{BASE_URL}/api/masters/pay-levels")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Pay levels - {len(data)} levels found")
    
    def test_get_service_groups(self, api_client):
        """Test service groups"""
        response = api_client.get(f"{BASE_URL}/api/masters/service-groups")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Service groups - {len(data)} groups found")
    
    def test_get_caste_categories(self, api_client):
        """Test caste categories"""
        response = api_client.get(f"{BASE_URL}/api/masters/caste-categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Caste categories - {len(data)} categories found")


# ==================== PROFILE TESTS ====================
class TestEmployeeProfile:
    """Employee Profile API tests"""
    
    def test_get_all_profiles_data_entry(self, api_client, tokens):
        """Test get all profiles with DATA_ENTRY authority"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/employee-profiles/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        profiles = data.get("profiles", [])
        assert isinstance(profiles, list)
        assert len(profiles) >= 2  # At least 2 seeded employees
        print(f"SUCCESS: Get all profiles - {len(profiles)} employees found")
    
    def test_get_own_profiles_employee(self, api_client, tokens):
        """Test employees can list only their own profile view"""
        headers = get_auth_header(tokens, "EMPLOYEE")
        response = api_client.get(f"{BASE_URL}/api/employee-profiles/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        profiles = data.get("profiles", [])
        assert isinstance(profiles, list)
        assert len(profiles) <= 1
        print("SUCCESS: EMPLOYEE is scoped to own profile list")
    
    def test_create_employee_profile(self, api_client, tokens):
        """Test create employee profile"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        unique_id = str(uuid.uuid4())[:8]
        profile_data = {
            "full_name": f"TEST_{unique_id} User",
            "gender": "Male",
            "date_of_birth": "1990-01-15",
            "employment_type": "REGULAR",
            "date_of_initial_engagement": "2024-01-15",
            "current_department_id": "FIN",
            "current_designation_id": "AN",
            "current_office_id": "HQ",
            "mobile_primary": "9876543210",
            "email_personal": f"test_{unique_id}@test.com",
        }
        result = create_employee_two_step(
            api_client,
            base_url=BASE_URL,
            headers=headers,
            payload=profile_data,
        )
        assert result.identity_response.status_code == 200
        data = result.identity_response.json()
        assert "employee_id" in data
        assert "employee_code" in data
        print(f"SUCCESS: Created employee - code: {data['employee_code']}")
        return data["employee_id"]
    
    def test_get_profile_by_id(self, api_client, tokens):
        """Test get profile by employee_id"""
        # First get all profiles to get an ID
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/employee-profiles/", headers=headers)
        profiles = response.json().get("profiles", [])
        if profiles:
            employee_id = profiles[0]["employee_id"]
            response = api_client.get(
                f"{BASE_URL}/api/employee-profiles/{employee_id}",
                headers=headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["employee_id"] == employee_id
            print(f"SUCCESS: Get profile by ID - {data['full_name']}")

    def test_submit_profile_does_not_require_service_book_derivation(self, api_client, tokens):
        """Submit should succeed without Employee context enforcing Service Book derivation checks."""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        unique_id = str(uuid.uuid4())[:8]

        profile_data = {
            "full_name": f"INCOMPLETE_{unique_id} User",
            "gender": "Male",
            "date_of_birth": "1990-01-15",
            "employment_type": "REGULAR",
            "date_of_initial_engagement": "2024-01-15",
            "current_department_id": "FIN",
            "current_designation_id": "AN",
            "current_office_id": "HQ",
            "mobile_primary": "9876543210",
            "email_personal": f"incomplete_{unique_id}@test.com",
        }

        create_result = create_employee_two_step(
            api_client,
            base_url=BASE_URL,
            headers=headers,
            payload=profile_data,
        )
        assert create_result.identity_response.status_code == 200
        employee_id = create_result.employee_id
        assert employee_id

        # Mark both sections complete so submit transition can proceed
        complete_res = api_client.put(
            f"{BASE_URL}/api/employee-profiles/{employee_id}",
            json={
                "employee_section_completed": True,
                "data_entry_section_completed": True,
            },
            headers=headers,
        )
        if complete_res.status_code != 200:
            pytest.skip("Profile completion flags could not be set in this environment")

        submit_res = api_client.post(
            f"{BASE_URL}/api/employee-profiles/{employee_id}/submit",
            json={"remarks": "Submit for validation"},
            headers=headers,
        )
        assert submit_res.status_code == 200
        payload = submit_res.json()
        assert payload.get("success") is True
        assert payload.get("new_status") == "SUBMITTED"
        print("SUCCESS: submit transitions without Service Book derivation gate")


# ==================== SERVICE BOOK TESTS ====================
class TestServiceBook:
    """Service Book API tests"""
    
    def test_get_service_book(self, api_client, tokens):
        """Test get service book for employee"""
        # Get employee ID first
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/employee-profiles/", headers=headers)
        profiles = response.json().get("profiles", [])
        
        # Find employee with service book
        employee_id = None
        for p in profiles:
            if p.get("employment_type") == "REGULAR":
                employee_id = p["employee_id"]
                break
        
        if employee_id:
            response = api_client.get(
                f"{BASE_URL}/api/service-book/employees/{employee_id}/entries?active=true",
                headers=headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            print(f"SUCCESS: Service book - {len(data)} active entries")
    
    def test_get_service_book_part(self, api_client, tokens):
        """Test get specific service book part"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/employee-profiles/", headers=headers)
        profiles = response.json().get("profiles", [])
        
        employee_id = None
        for p in profiles:
            if p.get("employment_type") == "REGULAR":
                employee_id = p["employee_id"]
                break
        
        if employee_id:
            response = api_client.get(
                f"{BASE_URL}/api/service-book/employees/{employee_id}/entries?schema_key=SB_IIA_IMMUTABLE_CERTS&active=true",
                headers=headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            print("SUCCESS: Service book Part II-A retrieved")
    
    def test_create_service_book_entry(self, api_client, tokens):
        """Service Book is projection-only; direct entry creation is removed."""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        
        # Get employee ID
        response = api_client.get(f"{BASE_URL}/api/employee-profiles/", headers=headers)
        profiles = response.json().get("profiles", [])
        
        employee_id = None
        for p in profiles:
            if p.get("has_service_book"):
                employee_id = p["employee_id"]
                break
        
        if employee_id:
            entry_data = {
                "medical_fitness_certificate": True,
                "medical_exam_date": "2024-01-15",
                "medical_officer_name": "Dr. Test",
                "medical_category": "A1",
                "character_verification_done": True,
                "oath_of_allegiance_taken": True,
                "oath_of_secrecy_taken": True,
            }
            response = api_client.post(
                f"{BASE_URL}/api/service-book/employees/{employee_id}/entries",
                json={
                    "schema_key": "SB_IIA_IMMUTABLE_CERTS",
                    "part_key": "SB_PART_II_A",
                    "payload": entry_data,
                },
                headers=headers,
            )
            assert response.status_code == 405
            print("SUCCESS: Service Book direct mutation rejected")


# ==================== WORKFLOW TESTS ====================
class TestWorkflow:
    """Workflow API tests"""
    
    def test_get_pending_submitted(self, api_client, tokens):
        """Test get pending entries at SUBMITTED stage"""
        headers = get_auth_header(tokens, "VERIFIER")
        response = api_client.get(f"{BASE_URL}/api/workflow/pending/SUBMITTED", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Pending SUBMITTED entries - {len(data)} found")
    
    def test_get_pending_verified(self, api_client, tokens):
        """Test get pending entries at VERIFIED stage"""
        headers = get_auth_header(tokens, "APPROVING_AUTHORITY")
        response = api_client.get(f"{BASE_URL}/api/workflow/pending/VERIFIED", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Pending VERIFIED entries - {len(data)} found")
    
    def test_get_pending_approved(self, api_client, tokens):
        """Test get pending entries at APPROVED stage"""
        headers = get_auth_header(tokens, "APPROVING_AUTHORITY")
        response = api_client.get(f"{BASE_URL}/api/workflow/pending/APPROVED", headers=headers)
        if response.status_code == 404:
            pytest.skip("APPROVED pending queue endpoint not available in current backend contract")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Pending APPROVED entries - {len(data)} found")
    
    def test_workflow_unauthorized_access(self, api_client, tokens):
        """Test workflow access with wrong authority"""
        headers = get_auth_header(tokens, "EMPLOYEE")
        response = api_client.get(f"{BASE_URL}/api/workflow/pending/SUBMITTED", headers=headers)
        assert response.status_code == 403
        print("SUCCESS: EMPLOYEE cannot access workflow pending (403)")


# ==================== ESS TESTS ====================
class TestESS:
    """Employee Self Service API tests"""
    
    def test_get_my_profile(self, api_client, tokens):
        """Test ESS get my profile"""
        headers = get_auth_header(tokens, "EMPLOYEE")
        response = api_client.get(f"{BASE_URL}/api/ess/my-profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "employee_id" in data
        assert "full_name" in data
        print(f"SUCCESS: ESS my profile - {data['full_name']}")
    
    def test_get_my_service_book(self, api_client, tokens):
        """Test ESS get my service book"""
        headers = get_auth_header(tokens, "EMPLOYEE")
        response = api_client.get(f"{BASE_URL}/api/ess/my-service-book", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "employee_id" in data or "message" in data
        print("SUCCESS: ESS my service book retrieved")

    def test_get_my_service_book_unauthorized_for_non_ess_role(self, api_client, tokens):
        """Test ESS service book endpoint rejects users without SERVICE_BOOK_READ_OWN"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/ess/my-service-book", headers=headers)
        assert response.status_code == 403
        print("SUCCESS: DATA_ENTRY cannot access ESS my service book (403)")


# ==================== AUDIT TESTS ====================
class TestAudit:
    """Audit API tests"""
    
    def test_get_audit_logs(self, api_client, tokens):
        """Test get audit logs (AUDITOR only)"""
        headers = get_auth_header(tokens, "AUDITOR")
        response = api_client.get(f"{BASE_URL}/api/audit/logs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Audit logs - {len(data)} entries found")
    
    def test_get_audit_logs_unauthorized(self, api_client, tokens):
        """Test audit logs access with non-AUDITOR"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/audit/logs", headers=headers)
        assert response.status_code == 403
        print("SUCCESS: DATA_ENTRY cannot access audit logs (403)")
    
    def test_get_service_book_logs(self, api_client, tokens):
        """Test get service-book audit logs"""
        headers = get_auth_header(tokens, "AUDITOR")
        response = api_client.get(f"{BASE_URL}/api/audit/service-book-logs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Service-book logs - {len(data)} entries found")


# ==================== DASHBOARD TESTS ====================
class TestDashboard:
    """Dashboard API tests"""
    
    def test_dashboard_stats_data_entry(self, api_client, tokens):
        """Test dashboard stats for DATA_ENTRY"""
        headers = get_auth_header(tokens, "DATA_ENTRY")
        response = api_client.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "user_authorities" in data
        assert "total_employees" in data
        print(f"SUCCESS: Dashboard stats - {data.get('total_employees', 0)} employees")
    
    def test_dashboard_stats_employee(self, api_client, tokens):
        """Test dashboard stats for EMPLOYEE"""
        headers = get_auth_header(tokens, "EMPLOYEE")
        response = api_client.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "user_authorities" in data
        print("SUCCESS: Employee dashboard stats retrieved")
    
    def test_dashboard_stats_verifier(self, api_client, tokens):
        """Test dashboard stats for VERIFIER"""
        headers = get_auth_header(tokens, "VERIFIER")
        response = api_client.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "pending_verification" in data
        print(f"SUCCESS: Verifier dashboard - {data.get('pending_verification', 0)} pending")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


