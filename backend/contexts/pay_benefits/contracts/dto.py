from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AllowanceOperation(str, Enum):
    SET = "SET"
    INCREMENT = "INCREMENT"
    DECREMENT = "DECREMENT"


class PayRevisionCreateDTO(BaseModel):
    employee_id: str
    effective_date: str = Field(..., description="YYYY-MM-DD")
    basic_pay: float = Field(..., gt=0)
    pay_level: str | None = None
    remarks: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AllowanceChangeCreateDTO(BaseModel):
    employee_id: str
    effective_date: str = Field(..., description="YYYY-MM-DD")
    allowance_code: str
    amount: float
    operation: AllowanceOperation = AllowanceOperation.SET
    remarks: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PayLedgerEntryResponseDTO(BaseModel):
    entry_id: str
    employee_id: str
    event_code: str
    amount: float
    payload: dict[str, Any]
    created_at: str | None = None
    created_by: str | None = None


class PaySnapshotResponseDTO(BaseModel):
    employee_id: str
    basic_pay: float | None = None
    pay_level: str | None = None
    effective_date: str | None = None
    allowances: dict[str, float] = Field(default_factory=dict)
