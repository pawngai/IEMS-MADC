from __future__ import annotations

import pytest

from contexts.leave.services.leave_service import (
    applyLeaveRequest,
    approveLeave,
    updateLeaveBalance,
)
from contexts.pay.services.pay_service import applyPayChange, computePayRecord
from contexts.pay.contracts.dto import AllowanceChangeCreateDTO, PayRevisionCreateDTO
from contexts.documents.application.commands import validate_document_metadata


class _LeaveServiceStub:
    async def apply_leave(self, payload, *, current_user):
        return {"kind": "apply", "employee_id": payload.employee_id, "user": current_user.get("sub")}

    async def sanction_leave(self, leave_id, action, *, current_user):
        return {"kind": "approve", "leave_id": leave_id, "remarks": action.remarks}

    async def get_leave_balances(self, employee_id, *, current_user):
        return {"employee_id": employee_id, "available": 12}


class _PayServiceStub:
    async def get_pay_snapshot(self, employee_id, *, current_user):
        return {"employee_id": employee_id, "basic_pay": 50000}

    async def revise_pay(self, payload, *, current_user):
        return {"kind": "revision", "employee_id": payload.employee_id}

    async def change_allowance(self, payload, *, current_user):
        return {"kind": "allowance", "employee_id": payload.employee_id}


class _LeavePayload:
    employee_id = "EMP-1"


class _LeaveAction:
    remarks = "ok"


@pytest.mark.asyncio
async def test_leave_service_functions_delegate() -> None:
    service = _LeaveServiceStub()
    current_user = {"sub": "u1"}

    applied = await applyLeaveRequest(service=service, payload=_LeavePayload(), current_user=current_user)
    approved = await approveLeave(
        service=service,
        leave_id="LEAVE-1",
        action=_LeaveAction(),
        current_user=current_user,
    )
    balances = await updateLeaveBalance(service=service, employee_id="EMP-1", current_user=current_user)

    assert applied["kind"] == "apply"
    assert approved["kind"] == "approve"
    assert balances["available"] == 12


@pytest.mark.asyncio
async def test_pay_service_functions_delegate() -> None:
    service = _PayServiceStub()
    current_user = {"sub": "u1"}

    snapshot = await computePayRecord(service=service, employee_id="EMP-1", current_user=current_user)
    revision = await applyPayChange(
        service=service,
        payload=PayRevisionCreateDTO(
            employee_id="EMP-1",
            effective_date="2026-03-10",
            basic_pay=51000,
        ),
        current_user=current_user,
    )
    allowance = await applyPayChange(
        service=service,
        payload=AllowanceChangeCreateDTO(
            employee_id="EMP-1",
            effective_date="2026-03-10",
            allowance_code="DA",
            amount=500,
        ),
        current_user=current_user,
    )

    assert snapshot["basic_pay"] == 50000
    assert revision["kind"] == "revision"
    assert allowance["kind"] == "allowance"


def test_document_metadata_validation_blocks_service_history_truth() -> None:
    with pytest.raises(ValueError) as exc:
        validate_document_metadata({"entity_type": "LEAVE", "service_history": "truth"})

    assert "service-history truth" in str(exc.value)

    normalized = validate_document_metadata({"entity_type": "leave", "entity_id": "L-1"})
    assert normalized["entity_type"] == "LEAVE"
    assert normalized["entity_id"] == "L-1"


def test_document_metadata_validation_normalizes_optional_classification_fields() -> None:
    normalized = validate_document_metadata(
        {
            "entity_type": "service-book",
            "entity_id": "EMP-1",
            "document_type": "certificate",
            "source_context": "Service Book.Upload",
        }
    )

    assert normalized["entity_type"] == "SERVICE_BOOK"
    assert normalized["document_type"] == "CERTIFICATE"
    assert normalized["source_context"] == "service_book.upload"


def test_document_metadata_validation_requires_supported_entity_type() -> None:
    with pytest.raises(ValueError) as exc:
        validate_document_metadata({"entity_type": "payroll", "entity_id": "PAY-1"})

    assert "entity_type" in str(exc.value)


def test_document_metadata_validation_requires_supported_document_type() -> None:
    with pytest.raises(ValueError) as exc:
        validate_document_metadata({"document_type": "memo"})

    assert "document_type" in str(exc.value)


def test_document_metadata_validation_requires_valid_source_context_format() -> None:
    with pytest.raises(ValueError) as exc:
        validate_document_metadata({"source_context": "service/book"})

    assert "source_context" in str(exc.value)


def test_document_metadata_validation_requires_both_entity_link_fields() -> None:
    with pytest.raises(ValueError) as exc:
        validate_document_metadata({"entity_id": "L-1"})

    assert str(exc.value) == "entity_type is required when entity_id is provided"


def test_document_metadata_validation_requires_entity_id_for_entity_type() -> None:
    with pytest.raises(ValueError) as exc:
        validate_document_metadata({"entity_type": "LEAVE"})

    assert str(exc.value) == "entity_id is required when entity_type is provided"
