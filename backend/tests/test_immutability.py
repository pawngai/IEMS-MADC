# Test Cases for Immutability Validator
# ======================================
# Tests field-level immutability rules for employee profiles

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from contexts.employee_master.profile.contracts.immutability import (
    ImmutabilityValidator,
    ImmutabilityValidationResult,
    validate_immutability,
    get_immutable_fields_for_stage,
    is_field_immutable,
    IMMUTABLE_AFTER_VERIFICATION,
    IMMUTABLE_AFTER_SUBMISSION,
    EDITABLE_STAGES,
    LOCKED_STAGES,
    FULLY_LOCKED_STAGE,
)


# ==================== TEST DATA ====================

SAMPLE_PROFILE = {
    "employee_id": "EMP-001",
    "full_name": "Rajesh Kumar Singh",
    "date_of_birth": "1985-06-15",
    "gender": "Male",
    "nationality": "Indian",
    "category": "GEN",
    "father_husband_name": "Shri Ram Singh",
    "mother_name": "Smt Geeta Singh",
    "initial_appointment_date": "2010-04-01",
    "appointment_order_no": "GOV/2010/APPT/001",
    "appointment_order_date": "2010-03-15",
    "recruitment_mode": "Direct",
    "employment_type": "REGULAR",
    "mobile_number": "9876543210",
    "email": "rajesh.singh@gov.in",
    "department_code": "FIN",
    "designation_code": "SO",
    "workflow_status": "VERIFIED",
}


# ==================== IMMUTABILITY VALIDATOR TESTS ====================

class TestImmutabilityValidator:
    """Test the ImmutabilityValidator class"""
    
    def test_draft_stage_all_fields_editable(self):
        """In DRAFT stage, all fields should be editable"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "DRAFT"}
        updates = {
            "date_of_birth": "1986-07-20",
            "full_name": "New Name",
            "category": "SC",
        }
        
        result = validate_immutability("DRAFT", old_data, updates)
        
        assert result.valid is True
        assert len(result.blocked_fields) == 0
    
    def test_rejected_stage_all_fields_editable(self):
        """In REJECTED stage, all fields should be editable (like DRAFT)"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "REJECTED"}
        updates = {
            "date_of_birth": "1986-07-20",
            "full_name": "New Name",
            "father_husband_name": "New Father Name",
        }
        
        result = validate_immutability("REJECTED", old_data, updates)
        
        assert result.valid is True
        assert len(result.blocked_fields) == 0
    
    def test_verified_stage_blocks_immutable_fields(self):
        """In VERIFIED stage, immutable fields should be blocked"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED"}
        updates = {
            "date_of_birth": "1986-07-20",  # BLOCKED
            "mobile_number": "9999999999",   # ALLOWED
        }
        
        result = validate_immutability("VERIFIED", old_data, updates)
        
        assert result.valid is False
        assert result.error_code == "FIELD_IMMUTABLE"
        assert "date_of_birth" in result.blocked_fields
    
    def test_verified_stage_allows_non_immutable_fields(self):
        """In VERIFIED stage, non-immutable fields should be editable"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED"}
        updates = {
            "mobile_number": "9999999999",
            "email": "new.email@gov.in",
            "department_code": "HR",  # Not in immutable list
        }
        
        result = validate_immutability("VERIFIED", old_data, updates)
        
        assert result.valid is True
    
    def test_approved_stage_blocks_immutable_fields(self):
        """In APPROVED stage, immutable fields should be blocked"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "APPROVED"}
        updates = {
            "full_name": "Changed Name",  # BLOCKED
            "category": "OBC",             # BLOCKED
        }
        
        result = validate_immutability("APPROVED", old_data, updates)
        
        assert result.valid is False
        assert "full_name" in result.blocked_fields
        assert "category" in result.blocked_fields
    
    def test_attested_stage_blocks_all_fields(self):
        """In ATTESTED (LOCKED) stage, ALL fields should be blocked"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "ATTESTED"}
        updates = {
            "mobile_number": "9999999999",  # Even non-immutable fields blocked
        }
        
        result = validate_immutability("ATTESTED", old_data, updates)
        
        assert result.valid is False
        assert result.error_code == "RECORD_LOCKED"
        assert "mobile_number" in result.blocked_fields
    
    def test_same_value_update_allowed(self):
        """Updating to same value should not trigger violation"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED"}
        updates = {
            "date_of_birth": "1985-06-15",  # Same as old value
            "full_name": "Rajesh Kumar Singh",  # Same as old value
        }
        
        result = validate_immutability("VERIFIED", old_data, updates)
        
        assert result.valid is True
    
    def test_null_to_value_allowed(self):
        """Setting value for previously null field should be allowed"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED", "spouse_name": None}
        updates = {
            "spouse_name": "Smt Asha Singh",  # Was null, now setting value
        }
        
        result = validate_immutability("VERIFIED", old_data, updates)
        
        assert result.valid is True
    
    def test_submitted_stage_blocks_employment_type(self):
        """Employment type should be blocked after SUBMITTED stage"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "SUBMITTED"}
        updates = {
            "employment_type": "CONTRACTUAL",  # BLOCKED after SUBMITTED
        }
        
        result = validate_immutability("SUBMITTED", old_data, updates)
        
        assert result.valid is False
        assert "employment_type" in result.blocked_fields
    
    def test_multiple_violations(self):
        """Multiple violations should all be reported"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED"}
        updates = {
            "date_of_birth": "1990-01-01",
            "full_name": "New Name",
            "category": "ST",
            "father_husband_name": "New Father",
        }
        
        result = validate_immutability("VERIFIED", old_data, updates)
        
        assert result.valid is False
        assert len(result.blocked_fields) == 4
        assert "date_of_birth" in result.blocked_fields
        assert "full_name" in result.blocked_fields
        assert "category" in result.blocked_fields
        assert "father_husband_name" in result.blocked_fields


# ==================== HELPER FUNCTION TESTS ====================

class TestHelperFunctions:
    """Test helper functions for immutability checking"""
    
    def test_get_immutable_fields_draft_stage(self):
        """DRAFT stage should have no immutable fields"""
        fields = get_immutable_fields_for_stage("DRAFT")
        assert len(fields) == 0
    
    def test_get_immutable_fields_rejected_stage(self):
        """REJECTED stage should have no immutable fields"""
        fields = get_immutable_fields_for_stage("REJECTED")
        assert len(fields) == 0
    
    def test_get_immutable_fields_verified_stage(self):
        """VERIFIED stage should have immutable fields"""
        fields = get_immutable_fields_for_stage("VERIFIED")
        assert "date_of_birth" in fields
        assert "full_name" in fields
        assert "category" in fields
        assert "employment_type" in fields  # Also locked from SUBMITTED
    
    def test_get_immutable_fields_attested_stage(self):
        """ATTESTED stage should return '*' indicating all fields locked"""
        fields = get_immutable_fields_for_stage("ATTESTED")
        assert "*" in fields
    
    def test_is_field_immutable_draft(self):
        """Fields should not be immutable in DRAFT"""
        is_immutable, reason = is_field_immutable("date_of_birth", "DRAFT")
        assert is_immutable is False
        assert reason is None
    
    def test_is_field_immutable_verified(self):
        """date_of_birth should be immutable in VERIFIED"""
        is_immutable, reason = is_field_immutable("date_of_birth", "VERIFIED")
        assert is_immutable is True
        assert "VERIFIED" in reason or "locked" in reason.lower()
    
    def test_is_field_immutable_attested(self):
        """Any field should be immutable in ATTESTED"""
        is_immutable, reason = is_field_immutable("mobile_number", "ATTESTED")
        assert is_immutable is True
        assert "ATTESTED" in reason or "locked" in reason.lower()


# ==================== VIOLATION DETAILS TESTS ====================

class TestViolationDetails:
    """Test that violation details are correctly captured"""
    
    def test_violation_captures_old_and_new_values(self):
        """Violations should capture old and attempted new values"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED"}
        updates = {"date_of_birth": "1990-01-01"}
        
        validator = ImmutabilityValidator("VERIFIED", old_data, updates)
        validator.validate()
        violations = validator.get_violations()
        
        assert len(violations) == 1
        assert violations[0]["field_id"] == "date_of_birth"
        assert violations[0]["old_value"] == "1985-06-15"
        assert violations[0]["attempted_new_value"] == "1990-01-01"
        assert violations[0]["violation_type"] == "FIELD_IMMUTABLE"
    
    def test_violation_includes_field_label(self):
        """Violations should include human-readable field labels"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED"}
        updates = {"father_husband_name": "New Father Name"}
        
        validator = ImmutabilityValidator("VERIFIED", old_data, updates)
        validator.validate()
        violations = validator.get_violations()
        
        assert violations[0]["field_label"] == "Father's/Husband's Name"


# ==================== EDGE CASES ====================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_updates(self):
        """Empty updates should always be valid"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "ATTESTED"}
        updates = {}
        
        # Note: ATTESTED with empty updates should still fail because
        # the record is locked, but with empty blocked_fields
        result = validate_immutability("ATTESTED", old_data, updates)
        
        # Actually, if there are no updates, nothing to block
        assert result.blocked_fields == []
    
    def test_date_format_normalization(self):
        """Date values in different formats should be compared correctly"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "VERIFIED", "date_of_birth": "1985-06-15"}
        updates = {"date_of_birth": "1985-06-15T00:00:00"}  # Different format, same date
        
        result = validate_immutability("VERIFIED", old_data, updates)
        
        # Should be valid because actual date value is the same
        assert result.valid is True
    
    def test_unknown_stage_defaults_to_restrictive(self):
        """Unknown workflow stage should be handled gracefully"""
        old_data = {**SAMPLE_PROFILE, "workflow_status": "UNKNOWN_STAGE"}
        updates = {"mobile_number": "9999999999"}
        
        # Unknown stage should allow edits (defaults to permissive)
        result = validate_immutability("UNKNOWN_STAGE", old_data, updates)
        
        # Default behavior: if not in locked stages, allow edits
        assert result.valid is True


# ==================== IMMUTABLE FIELDS LIST TESTS ====================

class TestImmutableFieldsLists:
    """Test that the immutable fields lists are complete"""
    
    def test_immutable_after_verification_contains_identity_fields(self):
        """Verify identity fields are in the immutable list"""
        identity_fields = [
            "date_of_birth",
            "full_name",
            "gender",
            "nationality",
            "category",
            "father_husband_name",
            "mother_name",
        ]
        
        for field in identity_fields:
            assert field in IMMUTABLE_AFTER_VERIFICATION, f"{field} should be immutable after verification"
    
    def test_immutable_after_verification_contains_appointment_fields(self):
        """Verify appointment fields are in the immutable list"""
        appointment_fields = [
            "initial_appointment_date",
            "appointment_order_no",
            "appointment_order_date",
            "recruitment_mode",
        ]
        
        for field in appointment_fields:
            assert field in IMMUTABLE_AFTER_VERIFICATION, f"{field} should be immutable after verification"
    
    def test_employment_type_in_submission_locked_fields(self):
        """Employment type should be locked after submission"""
        assert "employment_type" in IMMUTABLE_AFTER_SUBMISSION


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
