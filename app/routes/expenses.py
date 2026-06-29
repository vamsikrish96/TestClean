from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator

from app.auth.middleware import extract_auth_headers, AuthContext
from app.config import UserRole, VALID_CATEGORIES
from app.models.expense import Expense, ExpenseCreate
from app.services.expense_service import ExpenseService
from app.utils.errors import Unauthorized, BadRequest, Forbidden

router = APIRouter(prefix="/expenses", tags=["expenses"])
service = ExpenseService()


class CreateExpenseRequest(BaseModel):
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


@router.post("/", response_model=Expense)
async def submit_expense(request: Request, payload: CreateExpenseRequest) -> Expense:
    auth = await extract_auth_headers(request)
    if not auth:
        raise Unauthorized("Missing or invalid authentication headers")

    if auth.role != UserRole.EMPLOYEE.value:
        raise Forbidden("Only employees can submit expenses")

    expense = service.submit_expense(
        employee_id=auth.user_id,
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
        date_submitted=payload.date_submitted,
        receipt_url=payload.receipt_url,
        project_code=payload.project_code,
        department=payload.department,
    )

    return expense
