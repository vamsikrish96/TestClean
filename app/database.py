from typing import List, Optional
from app.models import Expense, ExpenseStatus


class ExpenseStore:
    def __init__(self):
        self.expenses: dict[str, Expense] = {}
        self._id_counter = 1

    def create(self, expense: Expense) -> Expense:
        expense_id = f"exp_{self._id_counter:06d}"
        self._id_counter += 1
        expense.id = expense_id
        self.expenses[expense_id] = expense
        return expense

    def get(self, expense_id: str) -> Optional[Expense]:
        return self.expenses.get(expense_id)

    def list_all(self) -> List[Expense]:
        return list(self.expenses.values())

    def list_by_employee(self, employee_id: str) -> List[Expense]:
        return [exp for exp in self.expenses.values() if exp.employee_id == employee_id]

    def list_by_status(self, status: ExpenseStatus) -> List[Expense]:
        return [exp for exp in self.expenses.values() if exp.status == status]

    def update(self, expense_id: str, expense: Expense) -> Optional[Expense]:
        if expense_id in self.expenses:
            self.expenses[expense_id] = expense
            return expense
        return None

    def exists(self, expense_id: str) -> bool:
        return expense_id in self.expenses
