from datetime import datetime
from uuid import uuid4
from typing import Optional, List
from app.models import Expense, ExpenseHistory, ExpenseStatus, ExpenseCategory
from app.repositories import expense_repo, history_repo


class ExpenseService:
    """Business logic for expense management."""

    def __init__(self):
        self.expense_repo = expense_repo
        self.history_repo = history_repo

    def submit_expense(
        self,
        employee_id: str,
        amount: float,
        category: ExpenseCategory,
        description: str,
        expense_date: str,
        receipt_url: str,
    ) -> Expense:
        """Create a new expense claim."""
        expense_id = str(uuid4())
        now = datetime.utcnow()

        expense = Expense(
            id=expense_id,
            employee_id=employee_id,
            amount=amount,
            category=category,
            description=description,
            expense_date=expense_date,
            receipt_url=receipt_url,
            status=ExpenseStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        self.expense_repo.create(expense)

        # Record initial history entry
        history = ExpenseHistory(
            id=str(uuid4()),
            expense_id=expense_id,
            status_from=ExpenseStatus.PENDING,
            status_to=ExpenseStatus.PENDING,
            changed_by=employee_id,
            changed_at=now,
            comment="Expense submitted",
        )
        self.history_repo.create(history)

        return expense

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        """Retrieve an expense by ID."""
        return self.expense_repo.get_by_id(expense_id)

    def list_employee_expenses(self, employee_id: str, status: Optional[ExpenseStatus] = None) -> List[Expense]:
        """List expenses for an employee, optionally filtered by status."""
        if status:
            return self.expense_repo.list_by_employee_and_status(employee_id, status)
        return self.expense_repo.list_by_employee(employee_id)

    def list_all_expenses(self, status: Optional[ExpenseStatus] = None) -> List[Expense]:
        """List all expenses, optionally filtered by status."""
        if status:
            return self.expense_repo.list_by_status(status)
        return self.expense_repo.list_all()

    def get_expense_with_history(self, expense_id: str) -> Optional[dict]:
        """Get expense with full audit trail."""
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            return None
        history = self.history_repo.get_by_expense_id(expense_id)
        return {"expense": expense, "history": history}


class ApprovalService:
    """Business logic for expense approvals and rejections."""

    def __init__(self):
        self.expense_repo = expense_repo
        self.history_repo = history_repo

    def approve_as_manager(self, expense_id: str, manager_id: str) -> Expense:
        """Manager approves a pending expense."""
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        if expense.status != ExpenseStatus.PENDING:
            raise ValueError(f"Cannot approve expense in {expense.status} status")

        expense.status = ExpenseStatus.APPROVED_BY_MANAGER
        expense.approved_by = manager_id
        expense.updated_at = datetime.utcnow()

        self.expense_repo.update(expense)

        history = ExpenseHistory(
            id=str(uuid4()),
            expense_id=expense_id,
            status_from=ExpenseStatus.PENDING,
            status_to=ExpenseStatus.APPROVED_BY_MANAGER,
            changed_by=manager_id,
            changed_at=datetime.utcnow(),
        )
        self.history_repo.create(history)

        return expense

    def reject_as_manager(self, expense_id: str, manager_id: str, rejection_reason: str) -> Expense:
        """Manager rejects a pending expense."""
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        if expense.status != ExpenseStatus.PENDING:
            raise ValueError(f"Cannot reject expense in {expense.status} status")

        expense.status = ExpenseStatus.REJECTED
        expense.rejection_reason = rejection_reason
        expense.updated_at = datetime.utcnow()

        self.expense_repo.update(expense)

        history = ExpenseHistory(
            id=str(uuid4()),
            expense_id=expense_id,
            status_from=ExpenseStatus.PENDING,
            status_to=ExpenseStatus.REJECTED,
            changed_by=manager_id,
            changed_at=datetime.utcnow(),
            comment=rejection_reason,
        )
        self.history_repo.create(history)

        return expense

    def approve_as_finance(self, expense_id: str, finance_id: str) -> Expense:
        """Finance approves a manager-approved expense."""
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        if expense.status != ExpenseStatus.APPROVED_BY_MANAGER:
            raise ValueError(f"Cannot approve expense in {expense.status} status")

        expense.status = ExpenseStatus.APPROVED_BY_FINANCE
        expense.approved_by = finance_id
        expense.updated_at = datetime.utcnow()

        self.expense_repo.update(expense)

        history = ExpenseHistory(
            id=str(uuid4()),
            expense_id=expense_id,
            status_from=ExpenseStatus.APPROVED_BY_MANAGER,
            status_to=ExpenseStatus.APPROVED_BY_FINANCE,
            changed_by=finance_id,
            changed_at=datetime.utcnow(),
        )
        self.history_repo.create(history)

        return expense

    def reject_as_finance(self, expense_id: str, finance_id: str, rejection_reason: str) -> Expense:
        """Finance rejects a manager-approved expense."""
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        if expense.status != ExpenseStatus.APPROVED_BY_MANAGER:
            raise ValueError(f"Cannot reject expense in {expense.status} status")

        expense.status = ExpenseStatus.REJECTED
        expense.rejection_reason = rejection_reason
        expense.updated_at = datetime.utcnow()

        self.expense_repo.update(expense)

        history = ExpenseHistory(
            id=str(uuid4()),
            expense_id=expense_id,
            status_from=ExpenseStatus.APPROVED_BY_MANAGER,
            status_to=ExpenseStatus.REJECTED,
            changed_by=finance_id,
            changed_at=datetime.utcnow(),
            comment=rejection_reason,
        )
        self.history_repo.create(history)

        return expense

    def process_expense(self, expense_id: str, finance_id: str) -> Expense:
        """Finance marks an approved expense as processed."""
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise ValueError("Expense not found")
        if expense.status != ExpenseStatus.APPROVED_BY_FINANCE:
            raise ValueError(f"Cannot process expense in {expense.status} status")

        expense.status = ExpenseStatus.PROCESSED
        expense.updated_at = datetime.utcnow()

        self.expense_repo.update(expense)

        history = ExpenseHistory(
            id=str(uuid4()),
            expense_id=expense_id,
            status_from=ExpenseStatus.APPROVED_BY_FINANCE,
            status_to=ExpenseStatus.PROCESSED,
            changed_by=finance_id,
            changed_at=datetime.utcnow(),
        )
        self.history_repo.create(history)

        return expense


# Global service instances
expense_service = ExpenseService()
approval_service = ApprovalService()
