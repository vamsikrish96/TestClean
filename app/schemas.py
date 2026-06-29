from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import Optional, List
from app.models import ExpenseStatus, ExpenseCategory, UserRole


class ExpenseHistorySchema(BaseModel):
    id: str
    expense_id: str
    status_from: ExpenseStatus
    status_to: ExpenseStatus
    changed_by: str
    changed_at: datetime
    comment: Optional[str] = None


class ExpenseCreateSchema(BaseModel):
    amount: float = Field(..., gt=0, le=100000, description="Amount between 0 and $100,000")
    category: ExpenseCategory
    description: str = Field(..., min_length=1)
    expense_date: date
    receipt_url: str = Field(..., min_length=1)

    @field_validator("expense_date")
    @classmethod
    def validate_expense_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Expense date cannot be in the future")
        return v


class ExpenseSchema(BaseModel):
    id: str
    employee_id: str
    amount: float
    category: ExpenseCategory
    description: str
    expense_date: date
    receipt_url: str
    status: ExpenseStatus
    created_at: datetime
    updated_at: datetime
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    history: List[ExpenseHistorySchema] = []


class ExpenseListSchema(BaseModel):
    id: str
    employee_id: str
    amount: float
    category: ExpenseCategory
    status: ExpenseStatus
    created_at: datetime
    updated_at: datetime


class ApprovalSchema(BaseModel):
    action: str
    timestamp: datetime


class RejectionSchema(BaseModel):
    rejection_reason: str = Field(..., min_length=1)


class UserSchema(BaseModel):
    id: str
    name: str
    role: UserRole
    manager_id: Optional[str] = None


class CurrentUserSchema(BaseModel):
    user_id: str
    role: UserRole
