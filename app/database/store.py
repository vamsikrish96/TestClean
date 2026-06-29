from typing import Dict, List, Optional
from app.models.expense import Expense


class ExpenseStore:
    def __init__(self):
        self._expenses: Dict[str, Expense] = {}
        self._employee_manager_map: Dict[str, str] = {}

    def create_expense(self, expense: Expense) -> Expense:
        self._expenses[expense.expense_id] = expense
        return expense

    def get_expense(self, expense_id: str) -> Optional[Expense]:
        return self._expenses.get(expense_id)

    def list_expenses(self) -> List[Expense]:
        return list(self._expenses.values())

    def update_expense(self, expense: Expense) -> Expense:
        self._expenses[expense.expense_id] = expense
        return expense

    def set_manager_for_employee(self, employee_id: str, manager_id: str) -> None:
        self._employee_manager_map[employee_id] = manager_id

    def get_manager_for_employee(self, employee_id: str) -> Optional[str]:
        return self._employee_manager_map.get(employee_id)

    def get_employees_for_manager(self, manager_id: str) -> List[str]:
        return [emp_id for emp_id, mgr_id in self._employee_manager_map.items() if mgr_id == manager_id]


# Global store instance
_store = ExpenseStore()


def get_store() -> ExpenseStore:
    return _store
