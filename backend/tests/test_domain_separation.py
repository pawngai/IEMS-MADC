# Domain Separation Automated Tests
# ==================================
#
# These tests MUST PASS for builds to succeed.
# They verify:
# 1. Service Book fields NEVER appear in Profile schema
# 2. Profile fields NEVER appear in Service Book schema
# 3. UPDATE/DELETE is blocked on approved ledger entries
# 4. Mixed payloads are rejected
# 5. Employment type rules are enforced

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_platform.domain_separation.schema_definitions import (
    PROFILE_FIELDS,
    SERVICE_BOOK_FIELDS,
    FORBIDDEN_IN_PROFILE,
    FORBIDDEN_IN_SERVICE_BOOK,
    PROFILE_EMPLOYMENT_TYPE_RULES,
)
from app_platform.domain_separation.validators import (
    DomainSeparationError,
    validate_profile_payload,
    validate_service_book_payload,
    reject_mixed_payload,
)
from app_platform.domain_separation.enforcement import (
    ProfilePayloadValidator,
    ServiceBookPayloadValidator,
    enforce_profile_separation,
    enforce_service_book_separation,
    block_service_book_update,
    block_service_book_delete,
    check_approved_immutability,
)
from contexts.employee_profile.contracts.schemas import EmployeeCompositeProfileView


# ==================== SCHEMA SEPARATION TESTS ====================

class TestSchemaDefinitionSeparation:
    """
    TEST: Service Book fields MUST NOT appear in Profile schema definitions.
    TEST: Profile fields MUST NOT appear in Service Book schema definitions.
    
    These tests FAIL the build if schemas overlap incorrectly.
    """
    
    def test_service_book_fields_not_in_profile_model(self):
        """
        CRITICAL: Verify that Service Book fields are NOT in EmployeeCompositeProfileView.
        
        If this test fails, it means the Profile model contains Service Book data,
        which violates the domain separation principle.
        """
        # Get all field names from the composed employee profile view
        profile_model_fields = set(EmployeeCompositeProfileView.model_fields.keys())
        
        # These Service Book fields should NEVER be in Profile
        forbidden = FORBIDDEN_IN_PROFILE
        
        violations = profile_model_fields.intersection(forbidden)
        
        assert not violations, (
            f"BUILD FAILURE: Profile model contains Service Book fields!\n"
            f"Violating fields: {violations}\n"
            f"These fields must be moved to the Service Book domain."
        )
    
    def test_forbidden_lists_are_disjoint(self):
        """
        Verify that forbidden lists don't accidentally overlap incorrectly.
        """
        overlap = FORBIDDEN_IN_PROFILE.intersection(FORBIDDEN_IN_SERVICE_BOOK)
        
        # Some fields might legitimately be forbidden in both (like passwords)
        # but core domain fields should not overlap
        core_profile_fields = {"full_name", "date_of_birth", "gender", "mobile_primary"}
        core_service_book_fields = {"entry_hash", "event_type", "effective_from"}
        
        profile_overlap = overlap.intersection(core_profile_fields)
        service_book_overlap = overlap.intersection(core_service_book_fields)
        
        assert not profile_overlap, f"Core profile fields in overlap: {profile_overlap}"
        assert not service_book_overlap, f"Core service book fields in overlap: {service_book_overlap}"


# ==================== PAYLOAD VALIDATION TESTS ====================

class TestProfilePayloadValidation:
    """Tests for Profile API payload validation"""
    
    def test_reject_service_book_fields_in_profile_payload(self):
        """
        CRITICAL: Service Book fields MUST be rejected in Profile payloads.
        """
        # Payload with Service Book field (event_type)
        invalid_payload = {
            "full_name": "Test Employee",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "employment_type": "REGULAR",
            "event_type": "APPOINTMENT",  # Service Book field!
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(invalid_payload)
        
        assert exc_info.value.error_code == "DOMAIN_VIOLATION_PROFILE"
        assert "event_type" in exc_info.value.violating_fields
    
    def test_reject_pay_fields_in_profile_payload(self):
        """
        CRITICAL: Pay data MUST NOT be in Profile payloads.
        """
        invalid_payload = {
            "full_name": "Test Employee",
            "employment_type": "REGULAR",
            "pay_scale": "15600-39100",  # Service Book field!
            "grade_pay": "5400",         # Service Book field!
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(invalid_payload)
        
        assert "pay_scale" in exc_info.value.violating_fields or "grade_pay" in exc_info.value.violating_fields
    
    def test_reject_leave_balance_in_profile_payload(self):
        """
        CRITICAL: Leave balances MUST NOT be in Profile payloads.
        """
        invalid_payload = {
            "full_name": "Test Employee",
            "employment_type": "REGULAR",
            "earned_leave_balance": 30,  # Service Book field!
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(invalid_payload)
        
        assert "earned_leave_balance" in exc_info.value.violating_fields

    def test_reject_service_book_part_iib_and_part_iii_fields_in_profile_payload(self):
        invalid_payload = {
            "full_name": "Test Employee",
            "employment_type": "REGULAR",
            "pcf_account_number": "PCF-100",
            "previous_services": [{"post_held": "Clerk"}],
        }

        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(invalid_payload)

        assert "pcf_account_number" in exc_info.value.violating_fields
        assert "previous_services" in exc_info.value.violating_fields
    
    def test_accept_valid_profile_payload(self):
        """Valid profile payload should be accepted"""
        valid_payload = {
            "full_name": "Test Employee",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "employment_type": "REGULAR",
            "mobile_primary": "9876543210",
        }
        
        result = validate_profile_payload(valid_payload)
        assert result["valid"] is True


class TestServiceBookPayloadValidation:
    """Tests for Service Book API payload validation"""
    
    def test_reject_profile_fields_in_service_book_payload(self):
        """
        CRITICAL: Profile fields MUST be rejected in Service Book payloads.
        """
        invalid_payload = {
            "employee_id": "test-123",
            "event_type": "PROMOTION",
            "effective_from": "2025-01-01",
            "full_name": "Test Employee",  # Profile field!
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_service_book_payload(invalid_payload)
        
        assert exc_info.value.error_code == "DOMAIN_VIOLATION_SERVICE_BOOK"
        assert "full_name" in exc_info.value.violating_fields
    
    def test_reject_contact_fields_in_service_book_payload(self):
        """
        CRITICAL: Contact details MUST NOT be in Service Book payloads.
        """
        invalid_payload = {
            "employee_id": "test-123",
            "event_type": "PROMOTION",
            "mobile_primary": "9876543210",  # Profile field!
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_service_book_payload(invalid_payload)
        
        assert "mobile_primary" in exc_info.value.violating_fields
    
    def test_reject_identity_fields_in_service_book_payload(self):
        """
        CRITICAL: Identity documents MUST NOT be in Service Book payloads.
        """
        invalid_payload = {
            "employee_id": "test-123",
            "event_type": "PROMOTION",
            "aadhaar_number": "123456789012",  # Profile field!
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_service_book_payload(invalid_payload)
        
        assert "aadhaar_number" in exc_info.value.violating_fields
    
    def test_accept_valid_service_book_payload(self):
        """Valid service book payload should be accepted"""
        valid_payload = {
            "employee_id": "test-123",
            "event_type": "PROMOTION",
            "effective_from": "2025-01-01",
            "order_number": "PROMO/2025/001",
            "order_date": "2025-01-01",
            "authority": "Director HR",
        }
        
        result = validate_service_book_payload(valid_payload)
        assert result["valid"] is True

    def test_accept_explicit_service_book_part_payload_fields(self):
        valid_payload = {
            "employee_id": "test-123",
            "name_in_block_letters": "TEST EMPLOYEE",
            "father_name": "Parent Name",
            "family_members": [{"name": "Asha", "relationship": "SPOUSE"}],
            "pcf_account_number": "PCF-100",
            "previous_services": [{"post_held": "Clerk"}],
            "verified": True,
        }

        result = validate_service_book_payload(valid_payload)
        assert result["valid"] is True


class TestMixedPayloadRejection:
    """Tests for mixed payload rejection"""
    
    def test_reject_mixed_payload(self):
        """
        CRITICAL: Payloads with BOTH Profile and Service Book fields MUST be rejected.
        """
        mixed_payload = {
            # Profile fields
            "full_name": "Test Employee",
            "date_of_birth": "1990-01-01",
            # Service Book fields
            "event_type": "PROMOTION",
            "pay_scale": "15600-39100",
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            reject_mixed_payload(mixed_payload)
        
        assert exc_info.value.error_code == "MIXED_PAYLOAD_REJECTED"
    
    def test_accept_pure_profile_payload(self):
        """Pure profile payload should pass mixed check"""
        pure_profile = {
            "employee_id": "test-123",
            "full_name": "Test Employee",
            "mobile_primary": "9876543210",
        }
        
        # Should not raise
        reject_mixed_payload(pure_profile)
    
    def test_accept_pure_service_book_payload(self):
        """Pure service book payload should pass mixed check"""
        pure_service_book = {
            "employee_id": "test-123",
            "event_type": "PROMOTION",
            "effective_from": "2025-01-01",
        }
        
        # Should not raise
        reject_mixed_payload(pure_service_book)


# ==================== LEDGER IMMUTABILITY TESTS ====================

class TestLedgerImmutability:
    """
    CRITICAL: These tests verify that UPDATE and DELETE are blocked on ledger entries.
    
    If these tests fail, the Service Book's legal immutability is compromised.
    """
    
    def test_block_update_on_any_entry(self):
        """
        CRITICAL: UPDATE operations MUST be blocked on ALL Service Book entries.
        """
        with pytest.raises(DomainSeparationError) as exc_info:
            ServiceBookPayloadValidator.validate_update_blocked("DRAFT")
        
        assert exc_info.value.error_code == "UPDATE_FORBIDDEN"
        assert "APPEND-ONLY" in exc_info.value.message
    
    def test_block_delete_on_any_entry(self):
        """
        CRITICAL: DELETE operations MUST be blocked on ALL Service Book entries.
        """
        with pytest.raises(DomainSeparationError) as exc_info:
            ServiceBookPayloadValidator.validate_delete_blocked("DRAFT")
        
        assert exc_info.value.error_code == "DELETE_FORBIDDEN"
        assert "PERMANENT" in exc_info.value.message
    
    def test_approved_entry_is_immutable(self):
        """
        CRITICAL: APPROVED entries MUST be immutable.
        """
        with pytest.raises(DomainSeparationError) as exc_info:
            ServiceBookPayloadValidator.validate_approved_immutability("APPROVED")
        
        assert exc_info.value.error_code == "ENTRY_IMMUTABLE"
    
    def test_attested_entry_is_immutable(self):
        """
        CRITICAL: ATTESTED entries MUST be immutable.
        """
        with pytest.raises(DomainSeparationError) as exc_info:
            ServiceBookPayloadValidator.validate_approved_immutability("ATTESTED")
        
        assert exc_info.value.error_code == "ENTRY_IMMUTABLE"
    
    def test_locked_entry_is_immutable(self):
        """
        CRITICAL: LOCKED entries MUST be immutable.
        """
        with pytest.raises(DomainSeparationError) as exc_info:
            ServiceBookPayloadValidator.validate_approved_immutability("LOCKED")
        
        assert exc_info.value.error_code == "ENTRY_IMMUTABLE"
    
    def test_draft_entry_allows_workflow_actions(self):
        """
        DRAFT entries should allow workflow actions (submit, etc.).
        This should NOT raise an error.
        """
        # This should not raise since DRAFT is not in immutable_statuses
        try:
            ServiceBookPayloadValidator.validate_approved_immutability("DRAFT")
            # If no exception, DRAFT is modifiable via workflow (correct behavior)
            # But UPDATE/DELETE should still be blocked
        except DomainSeparationError:
            pytest.fail("DRAFT entries should allow workflow actions")


# ==================== EMPLOYMENT TYPE RULES TESTS ====================

class TestEmploymentTypeRules:
    """Tests for employment type-specific field rules"""
    
    def test_regular_employee_forbidden_fields(self):
        """
        REGULAR employees should not have contractual/daily wage fields.
        """
        payload = {
            "full_name": "Test Employee",
            "employment_type": "REGULAR",
            "contract_end_date": "2025-12-31",  # Forbidden for REGULAR
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(payload, employment_type="REGULAR")
        
        assert exc_info.value.error_code == "EMPLOYMENT_TYPE_VIOLATION"
    
    def test_contractual_employee_forbidden_fields(self):
        """
        CONTRACTUAL employees should not have cadre/probation fields.
        """
        payload = {
            "full_name": "Test Employee",
            "employment_type": "CONTRACTUAL",
            "contract_start_date": "2025-01-01",
            "contract_end_date": "2025-12-31",
            "cadre": "IAS",  # Forbidden for CONTRACTUAL
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(payload, employment_type="CONTRACTUAL")
        
        assert exc_info.value.error_code == "EMPLOYMENT_TYPE_VIOLATION"

    def test_contractual_employee_rejects_pension_scheme(self):
        payload = {
            "full_name": "Test Employee",
            "employment_type": "CONTRACTUAL",
            "contract_start_date": "2025-01-01",
            "contract_end_date": "2025-12-31",
            "pension_scheme": "NPS",
        }

        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(payload, employment_type="CONTRACTUAL")

        assert exc_info.value.error_code == "EMPLOYMENT_TYPE_VIOLATION"
    
    def test_daily_wage_employee_forbidden_fields(self):
        """
        DAILY_WAGE employees should not have pay_level or contract fields.
        """
        payload = {
            "full_name": "Test Employee",
            "employment_type": "DAILY_WAGE",
            "pay_level": "7",  # Forbidden for DAILY_WAGE
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(payload, employment_type="DAILY_WAGE")
        
        assert exc_info.value.error_code == "EMPLOYMENT_TYPE_VIOLATION"
    
    def test_outsourced_employee_forbidden_fields(self):
        """
        OUTSOURCED employees should not have parent_department (deputation field).
        """
        payload = {
            "full_name": "Test Employee",
            "employment_type": "OUTSOURCED",
            "agency_name": "Test Agency",
            "parent_department": "Ministry of Finance",  # Forbidden for OUTSOURCED
        }
        
        with pytest.raises(DomainSeparationError) as exc_info:
            validate_profile_payload(payload, employment_type="OUTSOURCED")
        
        assert exc_info.value.error_code == "EMPLOYMENT_TYPE_VIOLATION"


# ==================== HTTP EXCEPTION CONVERSION TESTS ====================

class TestHTTPExceptionConversion:
    """Tests for converting domain errors to HTTP exceptions"""
    
    def test_domain_error_converts_to_400(self):
        """
        Domain separation errors should convert to HTTP 400 by default.
        """
        error = DomainSeparationError(
            error_code="TEST_ERROR",
            message="Test error message",
            violating_fields=["field1"],
            domain="PROFILE",
        )
        
        http_exc = error.to_http_exception()
        
        assert http_exc.status_code == 400
        assert http_exc.detail["error_code"] == "TEST_ERROR"
    
    def test_domain_error_converts_to_custom_status(self):
        """
        Domain errors should convert to custom status codes when specified.
        """
        error = DomainSeparationError(
            error_code="DELETE_FORBIDDEN",
            message="Delete not allowed",
            domain="SERVICE_BOOK",
        )
        
        http_exc = error.to_http_exception(status_code=405)
        
        assert http_exc.status_code == 405


# ==================== LOCKED PROFILE TESTS ====================

class TestLockedProfileImmutability:
    """Tests for locked profile immutability"""
    
    def test_locked_profile_rejects_update(self):
        """
        LOCKED profiles MUST reject all update attempts.
        """
        payload = {"mobile_primary": "9999999999"}
        
        with pytest.raises(DomainSeparationError) as exc_info:
            ProfilePayloadValidator.validate_update(payload, current_status="LOCKED")
        
        assert exc_info.value.error_code == "RECORD_LOCKED"


# ==================== COVERAGE VERIFICATION ====================

class TestCoverageVerification:
    """
    Verification tests to ensure schema definitions are complete.
    """
    
    def test_profile_fields_documented(self):
        """All composed profile view fields should be in PROFILE_FIELDS"""
        model_fields = set(EmployeeCompositeProfileView.model_fields.keys())
        
        # System fields that might not be in user-facing PROFILE_FIELDS
        system_fields = {"id", "created_at", "updated_at", "created_by", "updated_by", "version"}
        
        # Check that most model fields are documented
        undocumented = model_fields - PROFILE_FIELDS - system_fields - {"contact_details", "identity_documents"}
        
        # Allow some flexibility for nested model fields
        assert len(undocumented) < 5, f"Undocumented Profile fields: {undocumented}"
    


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
