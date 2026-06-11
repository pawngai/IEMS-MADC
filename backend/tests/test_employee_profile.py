# Test Cases for Employee Profile API
# =====================================
# Tests the refactored employee profile contracts and permissions

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pydantic import ValidationError

from contexts.employee_master.profile.contracts.schemas import (
    EmployeeCompositeProfileView,
    ContactDetails,
    IdentityDocuments,
    EmploymentType,
    EmployeeStatus,
    WorkflowStatus,
    Gender,
    ESS_EDITABLE_FIELDS,
    IMMUTABLE_AFTER_VERIFICATION,
    PROFILE_EXTENSION_EDITABLE_FIELDS,
)
from contexts.employee_master.identity.schemas.field_policies import DATA_ENTRY_EDITABLE_FIELDS
from contexts.employee_master.identity.schemas.commands import (
    EmployeeIdentityCreate,
    EmployeeIdentityUpdate,
)


# ==================== MODEL VALIDATION TESTS ====================

class TestEmployeeProfileModel:
    """Test the composed employee profile view model"""
    
    def test_create_minimal_profile(self):
        """Create profile with minimum required fields"""
        contact = ContactDetails(mobile_primary="9876543210")
        profile = EmployeeCompositeProfileView(
            full_name="Test Employee",
            gender=Gender.MALE,
            date_of_birth="1990-01-15",
            employment_type=EmploymentType.REGULAR,
            date_of_initial_engagement="2020-04-01",
            current_department_id="FIN",
            contact=contact,
        )
        
        assert profile.employee_id is not None
        assert profile.full_name == "Test Employee"
        assert profile.workflow_status == WorkflowStatus.DRAFT
        assert profile.employee_status == EmployeeStatus.ACTIVE
    
    def test_profile_generates_uuid(self):
        """Profile should auto-generate UUIDs"""
        contact = ContactDetails(mobile_primary="9876543210")
        profile = EmployeeCompositeProfileView(
            full_name="Test",
            gender=Gender.FEMALE,
            date_of_birth="1990-01-15",
            employment_type=EmploymentType.CONTRACTUAL,
            date_of_initial_engagement="2020-04-01",
            current_department_id="FIN",
            contact=contact,
        )
        
        assert len(profile.id) == 36  # UUID format
        assert len(profile.employee_id) == 36
    
    def test_invalid_date_format_rejected(self):
        """Invalid date format should raise validation error"""
        contact = ContactDetails(mobile_primary="9876543210")
        with pytest.raises(ValueError):
            EmployeeCompositeProfileView(
                full_name="Test",
                gender=Gender.MALE,
                date_of_birth="15-01-1990",  # Wrong format
                employment_type=EmploymentType.REGULAR,
                date_of_initial_engagement="2020-04-01",
                current_department_id="FIN",
                contact=contact,
            )
    
    def test_all_employment_types_valid(self):
        """All employment types should be valid"""
        types = [
            EmploymentType.REGULAR,
            EmploymentType.CONTRACTUAL,
            EmploymentType.DAILY_WAGE,
            EmploymentType.DEPUTATION,
            EmploymentType.REEMPLOYED,
            EmploymentType.OUTSOURCED,
        ]
        
        for emp_type in types:
            contact = ContactDetails(mobile_primary="9876543210")
            profile = EmployeeCompositeProfileView(
                full_name="Test",
                gender=Gender.MALE,
                date_of_birth="1990-01-15",
                employment_type=emp_type,
                date_of_initial_engagement="2020-04-01",
                current_department_id="FIN",
                contact=contact,
            )
            assert profile.employment_type == emp_type


# ==================== CONTACT DETAILS TESTS ====================

class TestContactDetails:
    """Test contact details validation"""
    
    def test_valid_mobile_number(self):
        """Valid Indian mobile should pass"""
        contact = ContactDetails(mobile_primary="9876543210")
        assert contact.mobile_primary == "9876543210"
    
    def test_invalid_mobile_rejected(self):
        """Invalid mobile should be rejected"""
        with pytest.raises(ValueError):
            ContactDetails(mobile_primary="1234567890")  # Doesn't start with 6-9
    
    def test_valid_pincode(self):
        """Valid 6-digit pincode should pass"""
        contact = ContactDetails(
            mobile_primary="9876543210",
            pincode="110001"
        )
        assert contact.pincode == "110001"
    
    def test_invalid_pincode_rejected(self):
        """Invalid pincode should be rejected"""
        with pytest.raises(ValueError):
            ContactDetails(
                mobile_primary="9876543210",
                pincode="1100"  # Only 4 digits
            )


# ==================== IDENTITY DOCUMENTS TESTS ====================

class TestIdentityDocuments:
    """Test identity document validation"""
    
    def test_valid_aadhaar(self):
        """Valid 12-digit Aadhaar should pass"""
        docs = IdentityDocuments(aadhaar_number="123456789012")
        assert docs.aadhaar_number == "123456789012"
    
    def test_invalid_aadhaar_rejected(self):
        """Invalid Aadhaar should be rejected"""
        with pytest.raises(ValueError):
            IdentityDocuments(aadhaar_number="12345")  # Too short
    
    def test_valid_pan(self):
        """Valid PAN format should pass"""
        docs = IdentityDocuments(pan_number="ABCDE1234F")
        assert docs.pan_number == "ABCDE1234F"
    
    def test_pan_uppercase_conversion(self):
        """PAN should be converted to uppercase"""
        docs = IdentityDocuments(pan_number="abcde1234f")
        assert docs.pan_number == "ABCDE1234F"
    
    def test_invalid_pan_rejected(self):
        """Invalid PAN format should be rejected"""
        with pytest.raises(ValueError):
            IdentityDocuments(pan_number="ABC123")  # Wrong format


# ==================== WORKFLOW STATUS TESTS ====================

class TestWorkflowStatus:
    """Test workflow status transitions"""
    
    def test_default_status_is_draft(self):
        """New profile should have DRAFT status"""
        contact = ContactDetails(mobile_primary="9876543210")
        profile = EmployeeCompositeProfileView(
            full_name="Test",
            gender=Gender.MALE,
            date_of_birth="1990-01-15",
            employment_type=EmploymentType.REGULAR,
            date_of_initial_engagement="2020-04-01",
            current_department_id="FIN",
            contact=contact,
        )
        assert profile.workflow_status == WorkflowStatus.DRAFT
    
    def test_all_workflow_statuses_exist(self):
        """All required workflow statuses should exist"""
        statuses = [
            WorkflowStatus.DRAFT,
            WorkflowStatus.SUBMITTED,
            WorkflowStatus.VERIFIED,
            WorkflowStatus.APPROVED,
            WorkflowStatus.LOCKED,
            WorkflowStatus.REJECTED,
        ]
        assert len(statuses) == 6


# ==================== FIELD PERMISSIONS TESTS ====================

class TestFieldPermissions:
    """Test field permission constants"""
    
    def test_data_entry_fields_include_identity(self):
        """Data Entry should be able to edit identity fields"""
        assert "full_name" in DATA_ENTRY_EDITABLE_FIELDS
        assert "gender" in DATA_ENTRY_EDITABLE_FIELDS
        assert "date_of_birth" in DATA_ENTRY_EDITABLE_FIELDS
        assert "aadhaar_number" not in DATA_ENTRY_EDITABLE_FIELDS
    
    def test_profile_extension_fields_include_contact(self):
        """Profile extension editing should own contact fields."""
        assert "mobile_primary" in PROFILE_EXTENSION_EDITABLE_FIELDS
        assert "email_personal" in PROFILE_EXTENSION_EDITABLE_FIELDS
        assert "address_line1" in PROFILE_EXTENSION_EDITABLE_FIELDS
        assert "mobile_primary" not in DATA_ENTRY_EDITABLE_FIELDS
    
    def test_ess_fields_include_allowed_personal_and_contact(self):
        """ESS should include approved personal/contact fields"""
        assert "gender" in ESS_EDITABLE_FIELDS
        assert "mobile_alternate" in ESS_EDITABLE_FIELDS
        assert "email_personal" in ESS_EDITABLE_FIELDS
        
        # Should NOT include identity fields
        assert "full_name" not in ESS_EDITABLE_FIELDS
        assert "date_of_birth" not in ESS_EDITABLE_FIELDS
    
    def test_immutable_fields_include_identity(self):
        """Identity fields should be immutable after verification"""
        assert "full_name" in IMMUTABLE_AFTER_VERIFICATION
        assert "gender" in IMMUTABLE_AFTER_VERIFICATION
        assert "date_of_birth" in IMMUTABLE_AFTER_VERIFICATION
        assert "father_name" in IMMUTABLE_AFTER_VERIFICATION
    
    def test_immutable_fields_include_documents(self):
        """Document fields should be immutable after verification"""
        assert "aadhaar_number" in IMMUTABLE_AFTER_VERIFICATION
        assert "pan_number" in IMMUTABLE_AFTER_VERIFICATION


# ==================== PROFILE CREATE MODEL TESTS ====================

class TestEmployeeIdentityCreate:
    """Test the create request model"""
    
    def test_create_model_requires_mandatory_fields(self):
        """Create model should enforce required fields"""
        # This should work with the current core identity fields only
        create_data = EmployeeIdentityCreate(
            full_name="Test Employee",
            gender=Gender.MALE,
            date_of_birth="1990-01-15",
        )
        assert create_data.full_name == "Test Employee"
    
    def test_create_model_optional_fields(self):
        """Optional fields should have defaults"""
        create_data = EmployeeIdentityCreate(
            full_name="Test Employee",
            gender=Gender.FEMALE,
            date_of_birth="1990-01-15",
        )
        assert "login_email" not in create_data.model_dump()
        assert create_data.current_designation_id is None

    def test_create_model_rejects_non_identity_fields(self):
        """Identity create should reject non-identity fields."""
        with pytest.raises(ValidationError) as exc:
            EmployeeIdentityCreate(
                full_name="Test Employee",
                gender=Gender.FEMALE,
                date_of_birth="1990-01-15",
                employment_type=EmploymentType.CONTRACTUAL,
                date_of_initial_engagement="2020-04-01",
                current_department_id="FIN",
                father_name="Parent Name",
            )

        message = str(exc.value)
        assert "Employee identity create accepts only core identity fields" in message
        assert "Move non-identity fields to their owning context" in message
        assert "father_name" in message

    def test_update_model_rejects_non_identity_fields(self):
        """Identity update should reject non-identity fields."""
        with pytest.raises(ValidationError) as exc:
            EmployeeIdentityUpdate(
                current_department_id="FIN",
                father_name="Parent Name",
            )

        message = str(exc.value)
        assert "Employee identity update accepts only core identity fields" in message
        assert "Move non-identity fields to their owning context" in message
        assert "father_name" in message


# ==================== EXCLUDED FIELDS TESTS ====================

class TestExcludedFields:
    """Test that Service Book fields are excluded"""
    
    def test_no_pay_fields(self):
        """Profile should not have pay-related fields"""
        profile_fields = EmployeeCompositeProfileView.model_fields.keys()
        
        assert "basic_pay" not in profile_fields
        assert "pay_level" not in profile_fields
        assert "pay_scale" not in profile_fields
        assert "grade_pay" not in profile_fields
        assert "increment_date" not in profile_fields

    def test_no_service_history_fields(self):
        """Profile should not duplicate service-history fields owned by ServiceEvents."""
        profile_fields = EmployeeCompositeProfileView.model_fields.keys()

        assert "service" not in profile_fields
        assert "pension_scheme" not in profile_fields
        assert "group" not in profile_fields
        assert "mode_of_recruitment" not in profile_fields
        assert "appointment_order_no" not in profile_fields
        assert "appointment_order_date" not in profile_fields
        assert "cadre" not in profile_fields
        assert "grade" not in profile_fields
        assert "probation_period_months" not in profile_fields
    
    def test_no_leave_fields(self):
        """Profile should not have leave-related fields"""
        profile_fields = EmployeeCompositeProfileView.model_fields.keys()
        
        assert "leave_balance" not in profile_fields
        assert "earned_leave" not in profile_fields
        assert "half_pay_leave" not in profile_fields
    
    def test_no_promotion_history(self):
        """Profile should not have promotion history"""
        profile_fields = EmployeeCompositeProfileView.model_fields.keys()
        
        assert "promotion_date" not in profile_fields
        assert "promotion_history" not in profile_fields
        assert "posting_history" not in profile_fields
    
    def test_no_service_book_events(self):
        """Profile should not have service book event fields"""
        profile_fields = EmployeeCompositeProfileView.model_fields.keys()
        
        assert "service_events" not in profile_fields
        assert "disciplinary_records" not in profile_fields
        assert "training_records" not in profile_fields

    def test_no_part_iib_profile_fields(self):
        """Profile should not retain mutable certificate fields owned by Service Book."""
        profile_fields = EmployeeCompositeProfileView.model_fields.keys()

        assert "pcf_account_number" not in profile_fields
        assert "bank_account_number" not in profile_fields
        assert "family_members" not in profile_fields

    def test_no_part_iii_profile_fields(self):
        """Profile should not retain previous-service fields owned by Service Book."""
        profile_fields = EmployeeCompositeProfileView.model_fields.keys()

        assert "previous_services" not in profile_fields
        assert "foreign_services" not in profile_fields
        assert "part_iii_verified" not in profile_fields


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
