from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date
from typing import Optional, List
from app.auth import get_current_user, require_role
from app.models import UserRole, ExpenseStatus
from app.schemas import (
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseListSchema,
    CurrentUserSchema,
    ExpenseHistorySchema,
)
from app.services import expense_service
from app.repositories import history_repo

router = APIRouter()


@router.post("", response_model=ExpenseSchema, status_code=201)
def submit_expense(
    expense_data: ExpenseCreateSchema,
    current_user: CurrentUserSchema = Depends(require_role(UserRole.EMPLOYEE)),
):
    """Submit a new expense claim (employee only)."""
    try:
        expense = expense_service.submit_expense(
            employee_id=current_user.user_id,
            amount=expense_data.amount,
            category=expense_data.category,
            description=expense_data.description,
            expense_date=expense_data.expense_date.isoformat(),
            receipt_url=expense_data.receipt_url,
        )

        history = history_repo.get_by_expense_id(expense.id)
        return ExpenseSchema(
            id=expense.id,
            employee_id=expense.employee_id,
            amount=expense.amount,
            category=expense.category,
            description=expense.description,
            expense_date=expense.expense_date,
            receipt_url=expense.receipt_url,
            status=expense.status,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
            approved_by=expense.approved_by,
            rejection_reason=expense.rejection_reason,
            history=[
                ExpenseHistorySchema(
                    id=h.id,
                    expense_id=h.expense_id,
                    status_from=h.status_from,
                    status_to=h.status_to,
                    changed_by=h.changed_by,
                    changed_at=h.changed_at,
                    comment=h.comment,
                )
                for h in history
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ExpenseListSchema])
def list_expenses(
    status: Optional[ExpenseStatus] = Query(None),
    current_user: CurrentUserSchema = Depends(require_role(UserRole.EMPLOYEE)),
):
    """List employee's own expenses with optional status filter."""
    expenses = expense_service.list_employee_expenses(current_user.user_id, status)
    return [
        ExpenseListSchema(
            id=e.id,
            employee_id=e.employee_id,
            amount=e.amount,
            category=e.category,
            status=e.status,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in expenses
    ]


@router.get("/{expense_id}", response_model=ExpenseSchema)
def get_expense(
    expense_id: str,
    current_user: CurrentUserSchema = Depends(require_role(UserRole.EMPLOYEE)),
):
    """Get expense detail with full audit trail."""
    expense = expense_service.get_expense(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense.employee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Cannot view other employees' expenses")

    history = history_repo.get_by_expense_id(expense_id)
    return ExpenseSchema(
        id=expense.id,
        employee_id=expense.employee_id,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        expense_date=expense.expense_date,
        receipt_url=expense.receipt_url,
        status=expense.status,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
        approved_by=expense.approved_by,
        rejection_reason=expense.rejection_reason,
        history=[
            ExpenseHistorySchema(
                id=h.id,
                expense_id=h.expense_id,
                status_from=h.status_from,
                status_to=h.status_to,
                changed_by=h.changed_by,
                changed_at=h.changed_at,
                comment=h.comment,
            )
            for h in history
        ],
    )
