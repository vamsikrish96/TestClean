from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ExpenseStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"


class Expense(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "exp_000001",
                "employee_id": "emp_123",
                "amount": 150.50,
                "description": "Conference ticket",
                "status": "SUBMITTED",
                "submitted_date": "2026-06-29T10:30:00Z",
                "approval_date": None,
                "processing_date": None,
                "manager_notes": None,
                "finance_notes": None,
                "approved_by": None,
                "processed_by": None,
                "returned_date": None,
            }
        }
    )

    id: Optional[str] = None
    employee_id: str
    amount: float
    description: str
    status: ExpenseStatus = ExpenseStatus.SUBMITTED
    submitted_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    processing_date: Optional[datetime] = None
    manager_notes: Optional[str] = None
    finance_notes: Optional[str] = None
    approved_by: Optional[str] = None
    processed_by: Optional[str] = None
    returned_date: Optional[datetime] = None
    version: int = 1


class ExpenseSubmit(BaseModel):
    amount: float = Field(..., gt=0, le=100000, description="Must be positive and ≤ $100,000")
    description: str = Field(..., min_length=1, max_length=500)


class ExpenseApprove(BaseModel):
    manager_notes: Optional[str] = Field(None, max_length=500)


class ExpenseReject(BaseModel):
    manager_notes: str = Field(..., min_length=1, max_length=500)


class ExpenseProcess(BaseModel):
    finance_notes: Optional[str] = Field(None, max_length=500)


class ExpenseReturn(BaseModel):
    finance_notes: Optional[str] = Field(None, max_length=500)
