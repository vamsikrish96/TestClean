from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from app.models import Expense, ExpenseHistory, User, ExpenseStatus, UserRole


class ExpenseRepository:
    """In-memory storage for expenses."""

    def __init__(self):
        self.storage: Dict[str, Expense] = {}

    def create(self, expense: Expense) -> Expense:
        """Create and store a new expense."""
        self.storage[expense.id] = expense
        return expense

    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        """Retrieve expense by ID."""
        return self.storage.get(expense_id)

    def update(self, expense: Expense) -> Expense:
        """Update an existing expense."""
        self.storage[expense.id] = expense
        return expense

    def list_by_employee(self, employee_id: str) -> List[Expense]:
        """List all expenses for an employee."""
        return [e for e in self.storage.values() if e.employee_id == employee_id]

    def list_by_status(self, status: ExpenseStatus) -> List[Expense]:
        """List all expenses with given status."""
        return [e for e in self.storage.values() if e.status == status]

    def list_by_employee_and_status(self, employee_id: str, status: ExpenseStatus) -> List[Expense]:
        """List expenses for employee with given status."""
        return [e for e in self.storage.values() if e.employee_id == employee_id and e.status == status]

    def list_all(self) -> List[Expense]:
        """List all expenses."""
        return list(self.storage.values())


class ExpenseHistoryRepository:
    """In-memory storage for expense history/audit trail."""

    def __init__(self):
        self.storage: Dict[str, List[ExpenseHistory]] = {}

    def create(self, history: ExpenseHistory) -> ExpenseHistory:
        """Add a new history entry."""
        if history.expense_id not in self.storage:
            self.storage[history.expense_id] = []
        self.storage[history.expense_id].append(history)
        return history

    def get_by_expense_id(self, expense_id: str) -> List[ExpenseHistory]:
        """Get all history entries for an expense."""
        return self.storage.get(expense_id, [])


class UserRepository:
    """In-memory storage for users."""

    def __init__(self):
        self.storage: Dict[str, User] = {}

    def create(self, user: User) -> User:
        """Create and store a new user."""
        self.storage[user.id] = user
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by ID."""
        return self.storage.get(user_id)

    def list_all(self) -> List[User]:
        """List all users."""
        return list(self.storage.values())

    def get_reports_for_manager(self, manager_id: str) -> List[User]:
        """Get all users who report to a manager."""
        return [u for u in self.storage.values() if u.manager_id == manager_id]


# Global repository instances
expense_repo = ExpenseRepository()
history_repo = ExpenseHistoryRepository()
user_repo = UserRepository()


def init_test_data():
    """Initialize test data for development/testing."""
    # Create test users
    user_repo.create(User(id="emp1", name="Alice Employee", role=UserRole.EMPLOYEE, manager_id="mgr1"))
    user_repo.create(User(id="emp2", name="Bob Employee", role=UserRole.EMPLOYEE, manager_id="mgr1"))
    user_repo.create(User(id="mgr1", name="Charlie Manager", role=UserRole.MANAGER))
    user_repo.create(User(id="fin1", name="Diana Finance", role=UserRole.FINANCE))
