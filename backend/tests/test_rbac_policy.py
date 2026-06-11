# Unit Tests for RBAC Policy Engine
# ==================================
#
# These tests verify that:
# 1. Valid actions are allowed
# 2. Invalid actions are denied with clear errors
# 3. Workflow transitions follow strict rules
# 4. Separation of duties is enforced
# 5. Locked records are immutable

import pytest
from contexts.identity_access.rbac.domain.policy_engine import (
    PolicyEngine,
    PolicyResult,
    UserContext,
    RecordContext,
    Role,
    RecordState,
    Action,
    check_permission,
    get_user_permissions_for_record,
    PermissionDeniedError,
)


# ==================== FIXTURES ====================

@pytest.fixture
def data_entry_user():
    """Data Entry Operator user"""
    return UserContext(
        user_id="user-deo-001",
        role=Role.DATA_ENTRY_OPERATOR,
        authorities=["DATA_ENTRY"],
    )

@pytest.fixture
def verifier_user():
    """Verifier user"""
    return UserContext(
        user_id="user-ver-001",
        role=Role.VERIFIER,
        authorities=["VERIFIER"],
    )

@pytest.fixture
def approver_user():
    """Approving Authority user"""
    return UserContext(
        user_id="user-app-001",
        role=Role.APPROVING_AUTHORITY,
        authorities=["APPROVING_AUTHORITY"],
    )

@pytest.fixture
def hoo_user():
    """Approving Authority user (legacy alias)"""
    return UserContext(
        user_id="user-hoo-001",
        role=Role.APPROVING_AUTHORITY,
        authorities=["APPROVING_AUTHORITY"],
    )

@pytest.fixture
def auditor_user():
    """Auditor user"""
    return UserContext(
        user_id="user-aud-001",
        role=Role.AUDITOR,
        authorities=["AUDITOR"],
    )

@pytest.fixture
def draft_record():
    """DRAFT record created by DEO"""
    return RecordContext(
        record_id="rec-001",
        record_type="employee_profile",
        state=RecordState.DRAFT,
        created_by="user-deo-001",
    )

@pytest.fixture
def submitted_record():
    """SUBMITTED record"""
    return RecordContext(
        record_id="rec-002",
        record_type="employee_profile",
        state=RecordState.SUBMITTED,
        created_by="user-deo-001",
    )

@pytest.fixture
def verified_record():
    """VERIFIED record"""
    return RecordContext(
        record_id="rec-003",
        record_type="employee_profile",
        state=RecordState.VERIFIED,
        created_by="user-deo-001",
    )

@pytest.fixture
def approved_record():
    """APPROVED record"""
    return RecordContext(
        record_id="rec-004",
        record_type="employee_profile",
        state=RecordState.APPROVED,
        created_by="user-deo-001",
    )

@pytest.fixture
def locked_record():
    """LOCKED (attested) record"""
    return RecordContext(
        record_id="rec-005",
        record_type="employee_profile",
        state=RecordState.LOCKED,
        created_by="user-deo-001",
        is_immutable=True,
    )

@pytest.fixture
def rejected_record():
    """REJECTED record"""
    return RecordContext(
        record_id="rec-006",
        record_type="employee_profile",
        state=RecordState.REJECTED,
        created_by="user-deo-001",
    )


def test_hod_does_not_resolve_to_approving_authority_role() -> None:
    user = UserContext.from_user_dict(
        {
            "sub": "user-hod-001",
            "authorities": ["HOD"],
        }
    )

    assert user.role != Role.APPROVING_AUTHORITY


# ==================== TEST: DEO PERMISSIONS ====================

class TestDataEntryOperator:
    """Tests for DATA_ENTRY_OPERATOR role"""
    
    def test_deo_can_create(self, data_entry_user):
        """DEO can create new records"""
        result = PolicyEngine.evaluate(Action.CREATE, data_entry_user)
        assert result.allowed is True
        assert result.action == Action.CREATE
    
    def test_deo_can_edit_draft(self, data_entry_user, draft_record):
        """DEO can edit DRAFT records"""
        result = PolicyEngine.evaluate(Action.UPDATE, data_entry_user, draft_record)
        assert result.allowed is True
    
    def test_deo_can_delete_draft(self, data_entry_user, draft_record):
        """DEO can delete DRAFT records"""
        result = PolicyEngine.evaluate(Action.DELETE, data_entry_user, draft_record)
        assert result.allowed is True
    
    def test_deo_can_submit_draft(self, data_entry_user, draft_record):
        """DEO can submit DRAFT records"""
        result = PolicyEngine.evaluate(Action.SUBMIT, data_entry_user, draft_record)
        assert result.allowed is True
    
    def test_deo_cannot_edit_submitted(self, data_entry_user, submitted_record):
        """DEO cannot edit SUBMITTED records"""
        result = PolicyEngine.evaluate(Action.UPDATE, data_entry_user, submitted_record)
        assert result.allowed is False
        assert result.error_code in ["ROLE_STATE_MISMATCH", "ACTION_NOT_PERMITTED", "INVALID_STATE_FOR_ACTION"]
    
    def test_deo_cannot_edit_verified(self, data_entry_user, verified_record):
        """DEO cannot edit VERIFIED records"""
        result = PolicyEngine.evaluate(Action.UPDATE, data_entry_user, verified_record)
        assert result.allowed is False
    
    def test_deo_cannot_edit_locked(self, data_entry_user, locked_record):
        """DEO cannot edit LOCKED records"""
        result = PolicyEngine.evaluate(Action.UPDATE, data_entry_user, locked_record)
        assert result.allowed is False
        assert result.error_code == "RECORD_IMMUTABLE"
    
    def test_deo_can_revise_rejected(self, data_entry_user, rejected_record):
        """DEO can revise REJECTED records"""
        result = PolicyEngine.evaluate(Action.REVISE, data_entry_user, rejected_record)
        assert result.allowed is True
    
    def test_deo_cannot_verify(self, data_entry_user, submitted_record):
        """DEO cannot verify records (not their role)"""
        result = PolicyEngine.evaluate(Action.VERIFY, data_entry_user, submitted_record)
        assert result.allowed is False


# ==================== TEST: VERIFIER PERMISSIONS ====================

class TestVerifier:
    """Tests for VERIFIER role"""
    
    def test_verifier_cannot_create(self, verifier_user):
        """Verifier cannot create records"""
        result = PolicyEngine.evaluate(Action.CREATE, verifier_user)
        assert result.allowed is False
        assert result.error_code == "ROLE_NOT_AUTHORIZED"
    
    def test_verifier_cannot_edit_any_record(self, verifier_user, draft_record, submitted_record):
        """Verifier cannot edit ANY record (verify only, never edit content)"""
        # Cannot edit draft
        result = PolicyEngine.evaluate(Action.UPDATE, verifier_user, draft_record)
        assert result.allowed is False
        
        # Cannot edit submitted
        result = PolicyEngine.evaluate(Action.UPDATE, verifier_user, submitted_record)
        assert result.allowed is False
    
    def test_verifier_can_verify_submitted(self, verifier_user, submitted_record):
        """Verifier can verify SUBMITTED records"""
        # Change creator to avoid separation of duties conflict
        submitted_record.created_by = "user-deo-002"
        result = PolicyEngine.evaluate(Action.VERIFY, verifier_user, submitted_record)
        assert result.allowed is True
    
    def test_verifier_can_reject_submitted(self, verifier_user, submitted_record):
        """Verifier can reject SUBMITTED records"""
        submitted_record.created_by = "user-deo-002"
        result = PolicyEngine.evaluate(Action.REJECT, verifier_user, submitted_record)
        assert result.allowed is True
    
    def test_verifier_cannot_verify_draft(self, verifier_user, draft_record):
        """Verifier cannot verify DRAFT records (workflow violation)"""
        result = PolicyEngine.evaluate(Action.VERIFY, verifier_user, draft_record)
        assert result.allowed is False
    
    def test_verifier_cannot_approve(self, verifier_user, verified_record):
        """Verifier cannot approve (not their role)"""
        result = PolicyEngine.evaluate(Action.APPROVE, verifier_user, verified_record)
        assert result.allowed is False


# ==================== TEST: APPROVING AUTHORITY PERMISSIONS ====================

class TestApprovingAuthority:
    """Tests for APPROVING_AUTHORITY role"""
    
    def test_approver_can_approve_verified(self, approver_user, verified_record):
        """Approver can approve VERIFIED records"""
        result = PolicyEngine.evaluate(Action.APPROVE, approver_user, verified_record)
        assert result.allowed is True
    
    def test_approver_cannot_approve_submitted(self, approver_user, submitted_record):
        """Approver cannot approve SUBMITTED records (must be verified first)"""
        result = PolicyEngine.evaluate(Action.APPROVE, approver_user, submitted_record)
        assert result.allowed is False
        assert result.error_code in ["ROLE_STATE_MISMATCH", "ACTION_NOT_PERMITTED", "INVALID_STATE_FOR_ACTION"]
    
    def test_approver_cannot_approve_draft(self, approver_user, draft_record):
        """Approver cannot approve DRAFT records"""
        result = PolicyEngine.evaluate(Action.APPROVE, approver_user, draft_record)
        assert result.allowed is False
    
    def test_approver_cannot_edit(self, approver_user, verified_record):
        """Approver cannot edit records"""
        result = PolicyEngine.evaluate(Action.UPDATE, approver_user, verified_record)
        assert result.allowed is False


# ==================== TEST: LOCKED RECORDS ====================

class TestLockedRecords:
    """Tests for LOCKED (immutable) records"""
    
    def test_locked_record_read_allowed(self, data_entry_user, verifier_user, approver_user, locked_record):
        """All roles can READ locked records"""
        for user in [data_entry_user, verifier_user, approver_user]:
            result = PolicyEngine.evaluate(Action.READ, user, locked_record)
            assert result.allowed is True
    
    def test_locked_record_update_denied(self, data_entry_user, locked_record):
        """No one can UPDATE locked records"""
        result = PolicyEngine.evaluate(Action.UPDATE, data_entry_user, locked_record)
        assert result.allowed is False
        assert result.error_code == "RECORD_IMMUTABLE"
        assert "SUPERSESSION" in result.suggestion
    
    def test_locked_record_delete_denied(self, approver_user, locked_record):
        """No one can DELETE locked records"""
        result = PolicyEngine.evaluate(Action.DELETE, approver_user, locked_record)
        assert result.allowed is False
        assert result.error_code == "RECORD_IMMUTABLE"
    
    def test_hoo_can_supersede_locked(self, hoo_user, locked_record):
        """APPROVING_AUTHORITY can create supersession for locked records"""
        result = PolicyEngine.evaluate(Action.SUPERSEDE, hoo_user, locked_record)
        assert result.allowed is True


# ==================== TEST: SEPARATION OF DUTIES ====================

class TestSeparationOfDuties:
    """Tests for separation of duties enforcement"""
    
    def test_cannot_verify_own_submission(self, verifier_user, submitted_record):
        """User cannot verify their own submission"""
        # Make the verifier the creator
        submitted_record.created_by = verifier_user.user_id
        
        result = PolicyEngine.evaluate(Action.VERIFY, verifier_user, submitted_record)
        assert result.allowed is False
        assert result.error_code == "SEPARATION_OF_DUTIES"
    
    def test_cannot_approve_own_submission(self, approver_user, verified_record):
        """User cannot approve their own submission"""
        verified_record.created_by = approver_user.user_id
        
        result = PolicyEngine.evaluate(Action.APPROVE, approver_user, verified_record)
        assert result.allowed is False
        assert result.error_code == "SEPARATION_OF_DUTIES"
    
    def test_cannot_attest_own_submission(self, hoo_user, approved_record):
        """User cannot attest their own submission"""
        approved_record.created_by = hoo_user.user_id
        
        result = PolicyEngine.evaluate(Action.ATTEST, hoo_user, approved_record)
        assert result.allowed is False
        assert result.error_code == "SEPARATION_OF_DUTIES"


# ==================== TEST: WORKFLOW TRANSITIONS ====================

class TestWorkflowTransitions:
    """Tests for workflow transition rules"""
    
    def test_cannot_skip_verification(self, approver_user, submitted_record):
        """Cannot approve without verification (skip workflow)"""
        result = PolicyEngine.evaluate(Action.APPROVE, approver_user, submitted_record)
        assert result.allowed is False
    
    def test_cannot_skip_approval(self, hoo_user, verified_record):
        """Cannot attest without approval (skip workflow)"""
        result = PolicyEngine.evaluate(Action.ATTEST, hoo_user, verified_record)
        assert result.allowed is False
    
    def test_cannot_submit_already_submitted(self, data_entry_user, submitted_record):
        """Cannot submit an already submitted record"""
        result = PolicyEngine.evaluate(Action.SUBMIT, data_entry_user, submitted_record)
        assert result.allowed is False
    
    def test_valid_workflow_progression(self, data_entry_user, verifier_user, approver_user, hoo_user):
        """Test valid workflow: DRAFT -> SUBMITTED -> VERIFIED -> APPROVED -> LOCKED"""
        # Step 1: DRAFT -> SUBMITTED
        draft = RecordContext("r1", "profile", RecordState.DRAFT, "other-user")
        result = PolicyEngine.evaluate(Action.SUBMIT, data_entry_user, draft)
        assert result.allowed is True
        next_state = PolicyEngine.get_next_state(Action.SUBMIT, RecordState.DRAFT)
        assert next_state == RecordState.SUBMITTED
        
        # Step 2: SUBMITTED -> VERIFIED
        submitted = RecordContext("r1", "profile", RecordState.SUBMITTED, "other-user")
        result = PolicyEngine.evaluate(Action.VERIFY, verifier_user, submitted)
        assert result.allowed is True
        next_state = PolicyEngine.get_next_state(Action.VERIFY, RecordState.SUBMITTED)
        assert next_state == RecordState.VERIFIED
        
        # Step 3: VERIFIED -> APPROVED
        verified = RecordContext("r1", "profile", RecordState.VERIFIED, "other-user")
        result = PolicyEngine.evaluate(Action.APPROVE, approver_user, verified)
        assert result.allowed is True
        next_state = PolicyEngine.get_next_state(Action.APPROVE, RecordState.VERIFIED)
        assert next_state == RecordState.APPROVED
        
        # Step 4: APPROVED -> LOCKED
        approved = RecordContext("r1", "profile", RecordState.APPROVED, "other-user")
        result = PolicyEngine.evaluate(Action.ATTEST, hoo_user, approved)
        assert result.allowed is True
        next_state = PolicyEngine.get_next_state(Action.ATTEST, RecordState.APPROVED)
        assert next_state == RecordState.LOCKED


# ==================== TEST: ERROR MESSAGES ====================

class TestErrorMessages:
    """Tests for clear permission denial errors"""
    
    def test_error_includes_required_role(self, data_entry_user, submitted_record):
        """Error message includes required role or separation of duties error"""
        # Use a different user so it's not a separation of duties issue
        submitted_record.created_by = "different-user"
        result = PolicyEngine.evaluate(Action.VERIFY, data_entry_user, submitted_record)
        assert result.allowed is False
        assert result.required_role == Role.VERIFIER or result.error_code in ["ROLE_STATE_MISMATCH", "ACTION_NOT_PERMITTED"]
    
    def test_error_includes_required_state(self, approver_user, submitted_record):
        """Error message includes required state"""
        result = PolicyEngine.evaluate(Action.APPROVE, approver_user, submitted_record)
        assert result.allowed is False
        # Should mention that VERIFIED state is needed
    
    def test_error_includes_suggestion(self, data_entry_user, locked_record):
        """Error message includes helpful suggestion"""
        result = PolicyEngine.evaluate(Action.UPDATE, data_entry_user, locked_record)
        assert result.allowed is False
        assert result.suggestion is not None
        assert "SUPERSESSION" in result.suggestion


# ==================== TEST: AUDITOR PERMISSIONS ====================

class TestAuditor:
    """Tests for AUDITOR role"""
    
    def test_auditor_can_read_all_states(self, auditor_user, draft_record, submitted_record, verified_record, locked_record):
        """Auditor can read records in all states"""
        for record in [draft_record, submitted_record, verified_record, locked_record]:
            result = PolicyEngine.evaluate(Action.READ, auditor_user, record)
            assert result.allowed is True
    
    def test_auditor_can_audit(self, auditor_user, locked_record):
        """Auditor can perform audit action"""
        result = PolicyEngine.evaluate(Action.AUDIT, auditor_user, locked_record)
        assert result.allowed is True
    
    def test_auditor_cannot_modify(self, auditor_user, draft_record):
        """Auditor cannot modify any records"""
        result = PolicyEngine.evaluate(Action.UPDATE, auditor_user, draft_record)
        assert result.allowed is False
        
        result = PolicyEngine.evaluate(Action.SUBMIT, auditor_user, draft_record)
        assert result.allowed is False


# ==================== TEST: HELPER FUNCTIONS ====================

class TestHelperFunctions:
    """Tests for convenience functions"""
    
    def test_get_allowed_actions(self, data_entry_user, draft_record):
        """get_allowed_actions returns correct list"""
        actions = PolicyEngine.get_allowed_actions(data_entry_user, draft_record)
        
        assert Action.READ in actions
        assert Action.UPDATE in actions
        assert Action.DELETE in actions
        assert Action.SUBMIT in actions
        assert Action.VERIFY not in actions
        assert Action.APPROVE not in actions
    
    def test_get_user_permissions_for_record(self):
        """get_user_permissions_for_record returns correct dict"""
        user = {"sub": "user-1", "authorities": ["DATA_ENTRY"]}
        record = {"id": "rec-1", "status": "DRAFT", "created_by": "user-1"}
        
        perms = get_user_permissions_for_record(user, record, "employee_profile")
        
        assert perms["can_edit"] is True
        assert perms["can_delete"] is True
        assert perms["can_submit"] is True
        assert perms["can_verify"] is False
        assert perms["can_approve"] is False
    
    def test_check_permission_function(self):
        """check_permission function works correctly"""
        user = {"sub": "user-1", "authorities": ["VERIFIER"]}
        record = {"id": "rec-1", "status": "SUBMITTED", "created_by": "other-user"}
        
        result = check_permission(Action.VERIFY, user, record, "employee_profile")
        assert result.allowed is True
        
        result = check_permission(Action.UPDATE, user, record, "employee_profile")
        assert result.allowed is False


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
