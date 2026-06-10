"""Documents domain — signature request workflow rules.

A signature request asks a sequence of signers, in order, to sign a specific
document. Each signer either ``signs`` (which records their signature ref +
timestamp and advances the queue to the next signer) or ``declines`` (which
closes the request as DECLINED).

Status transitions:
    PENDING -> COMPLETED  (every signer signed in order)
    PENDING -> DECLINED   (any signer declined)
    PENDING -> CANCELLED  (issuer cancelled before completion)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SIGNATURE_STATUS_PENDING = "PENDING"
SIGNATURE_STATUS_COMPLETED = "COMPLETED"
SIGNATURE_STATUS_DECLINED = "DECLINED"
SIGNATURE_STATUS_CANCELLED = "CANCELLED"
SIGNATURE_TERMINAL_STATES = frozenset({
    SIGNATURE_STATUS_COMPLETED,
    SIGNATURE_STATUS_DECLINED,
    SIGNATURE_STATUS_CANCELLED,
})


@dataclass(slots=True)
class Signer:
    employee_id: str
    role: str
    signed_at: str | None = None
    signature_filename: str | None = None
    declined_at: str | None = None
    decline_reason: str | None = None

    @property
    def is_done(self) -> bool:
        return bool(self.signed_at or self.declined_at)


@dataclass(slots=True)
class SignatureRequest:
    request_id: str
    document_id: str
    filename: str
    status: str
    issuer_user_id: str | None = None
    issuer_employee_id: str | None = None
    created_at: str = ""
    deadline_at: str | None = None
    signers: list[Signer] = field(default_factory=list)
    completed_at: str | None = None

    def current_signer_index(self) -> int | None:
        for idx, signer in enumerate(self.signers):
            if not signer.is_done:
                return idx
        return None

    def is_pending(self) -> bool:
        return self.status == SIGNATURE_STATUS_PENDING


def validate_signers(signers: list[dict[str, Any]]) -> list[Signer]:
    if not signers:
        raise ValueError("At least one signer is required")
    seen_employee_ids: set[str] = set()
    out: list[Signer] = []
    for raw in signers:
        if not isinstance(raw, dict):
            raise ValueError("Each signer must be an object")
        employee_id = str(raw.get("employee_id") or "").strip()
        role = str(raw.get("role") or "").strip() or "signer"
        if not employee_id:
            raise ValueError("Each signer must include employee_id")
        if employee_id in seen_employee_ids:
            raise ValueError(f"Duplicate signer: {employee_id}")
        seen_employee_ids.add(employee_id)
        out.append(Signer(employee_id=employee_id, role=role))
    return out


def assert_can_sign(request: SignatureRequest, *, signer_employee_id: str) -> int:
    if not request.is_pending():
        raise ValueError(f"Signature request is {request.status}; no further signers may act")
    idx = request.current_signer_index()
    if idx is None:
        raise ValueError("No outstanding signer")
    current = request.signers[idx]
    if current.employee_id != signer_employee_id:
        raise ValueError("It is not your turn to sign this document")
    return idx
