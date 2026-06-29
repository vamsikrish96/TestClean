from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import uuid4

from app.config import ExpenseCategory, ExpenseStatus, VALID_CATEGORIES


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: str
    date_submitted: datetime
    receipt_url: Optional[str] = None
    project_code: Optional[str] = None
    department: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
        return v

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v


class ExpenseApproval(BaseModel):
    reason: Optional[str] = None


class Expense(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    expense_id: str
    employee_id: str
    amount: float
    category: str
    description: str
    date_submitted: datetime
    receipt_url: Optional[str] = None
    project_code: Optional[str] = None
    department: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    manager_id: Optional[str] = None
    manager_approval_reason: Optional[str] = None
    finance_id: Optional[str] = None
    finance_approval_reason: Optional[str] = None


def create_expense(
    employee_id: str,
    amount: float,
    category: str,
    description: str,
    date_submitted: datetime,
    receipt_url: Optional[str] = None,
    project_code: Optional[str] = None,
    department: Optional[str] = None,
) -> Expense:
    now = datetime.utcnow()
    return Expense(
        expense_id=str(uuid4()),
        employee_id=employee_id,
        amount=amount,
        category=category,
        description=description,
        date_submitted=date_submitted,
        receipt_url=receipt_url,
        project_code=project_code,
        department=department,
        status=ExpenseStatus.SUBMITTED,
        created_at=now,
        updated_at=now,
    )
