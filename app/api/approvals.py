from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.auth import get_current_user, require_role
from app.models import UserRole, ExpenseStatus
from app.schemas import (
    ExpenseSchema,
    ExpenseListSchema,
    CurrentUserSchema,
    RejectionSchema,
    ExpenseHistorySchema,
)
from app.services import approval_service
from app.repositories import history_repo, user_repo

router = APIRouter()


@router.get("/team", response_model=List[ExpenseListSchema])
def list_team_expenses(
    current_user: CurrentUserSchema = Depends(require_role(UserRole.MANAGER)),
):
    """List expenses from manager's direct reports."""
    manager = user_repo.get_by_id(current_user.user_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    expenses = []
    for report in user_repo.get_reports_for_manager(current_user.user_id):
        expenses.extend(approval_service.expense_repo.list_by_employee(report.id))

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


@router.patch("/{expense_id}/approve", response_model=ExpenseSchema)
def approve_expense(
    expense_id: str,
    current_user: CurrentUserSchema = Depends(get_current_user),
):
    """Approve an expense (manager or finance role)."""
    if current_user.role == UserRole.MANAGER:
        return _approve_as_manager(expense_id, current_user.user_id)
    elif current_user.role == UserRole.FINANCE:
        return _approve_as_finance(expense_id, current_user.user_id)
    else:
        raise HTTPException(status_code=403, detail="Only manager and finance can approve expenses")


@router.patch("/{expense_id}/reject", response_model=ExpenseSchema)
def reject_expense(
    expense_id: str,
    rejection_data: RejectionSchema,
    current_user: CurrentUserSchema = Depends(get_current_user),
):
    """Reject an expense (manager or finance role)."""
    if current_user.role == UserRole.MANAGER:
        return _reject_as_manager(expense_id, current_user.user_id, rejection_data.rejection_reason)
    elif current_user.role == UserRole.FINANCE:
        return _reject_as_finance(expense_id, current_user.user_id, rejection_data.rejection_reason)
    else:
        raise HTTPException(status_code=403, detail="Only manager and finance can reject expenses")


@router.patch("/{expense_id}/process", response_model=ExpenseSchema)
def process_expense(
    expense_id: str,
    current_user: CurrentUserSchema = Depends(require_role(UserRole.FINANCE)),
):
    """Mark an expense as processed (finance only)."""
    try:
        expense = approval_service.process_expense(expense_id, current_user.user_id)
        history = history_repo.get_by_expense_id(expense_id)
        return _expense_to_schema(expense, history)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


def _approve_as_manager(expense_id: str, manager_id: str) -> ExpenseSchema:
    """Manager approval logic."""
    expense = approval_service.expense_repo.get_by_id(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    manager = user_repo.get_by_id(manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    employee = user_repo.get_by_id(expense.employee_id)
    if not employee or employee.manager_id != manager_id:
        raise HTTPException(status_code=403, detail="Can only approve own reports' expenses")

    try:
        expense = approval_service.approve_as_manager(expense_id, manager_id)
        history = history_repo.get_by_expense_id(expense_id)
        return _expense_to_schema(expense, history)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _reject_as_manager(expense_id: str, manager_id: str, rejection_reason: str) -> ExpenseSchema:
    """Manager rejection logic."""
    expense = approval_service.expense_repo.get_by_id(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    manager = user_repo.get_by_id(manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    employee = user_repo.get_by_id(expense.employee_id)
    if not employee or employee.manager_id != manager_id:
        raise HTTPException(status_code=403, detail="Can only reject own reports' expenses")

    try:
        expense = approval_service.reject_as_manager(expense_id, manager_id, rejection_reason)
        history = history_repo.get_by_expense_id(expense_id)
        return _expense_to_schema(expense, history)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _approve_as_finance(expense_id: str, finance_id: str) -> ExpenseSchema:
    """Finance approval logic."""
    try:
        expense = approval_service.approve_as_finance(expense_id, finance_id)
        history = history_repo.get_by_expense_id(expense_id)
        return _expense_to_schema(expense, history)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


def _reject_as_finance(expense_id: str, finance_id: str, rejection_reason: str) -> ExpenseSchema:
    """Finance rejection logic."""
    try:
        expense = approval_service.reject_as_finance(expense_id, finance_id, rejection_reason)
        history = history_repo.get_by_expense_id(expense_id)
        return _expense_to_schema(expense, history)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


def _expense_to_schema(expense, history) -> ExpenseSchema:
    """Convert expense and history to schema."""
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
