from typing import List
from app.models import Expense, ExpenseStatus


class ExpenseStore:
    def __init__(self):
        self._expenses: dict[str, Expense] = {}
        self._id_counter = 1

    def create(self, expense: Expense) -> Expense:
        expense_id = f"exp_{self._id_counter:06d}"
        self._id_counter += 1
        expense.id = expense_id
        expense.version = 1
        self._expenses[expense_id] = expense
        return expense

    def get(self, expense_id: str) -> Expense:
        if expense_id not in self._expenses:
            raise KeyError(f"Expense {expense_id} not found")
        return self._expenses[expense_id]

    def list_all(self) -> List[Expense]:
        return list(self._expenses.values())

    def list_by_employee(self, employee_id: str) -> List[Expense]:
        return [exp for exp in self._expenses.values() if exp.employee_id == employee_id]

    def list_by_status(self, status: ExpenseStatus) -> List[Expense]:
        return [exp for exp in self._expenses.values() if exp.status == status]

    def update(self, expense_id: str, expense: Expense) -> Expense:
        if expense_id not in self._expenses:
            raise KeyError(f"Expense {expense_id} not found")
        updated = expense.model_copy(update={"version": expense.version + 1})
        self._expenses[expense_id] = updated
        return updated

    def exists(self, expense_id: str) -> bool:
        return expense_id in self._expenses
