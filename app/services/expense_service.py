from datetime import datetime
from app.models.expense import ExpenseCreate, Expense, create_expense
from app.database.store import get_store
from app.utils.errors import NotFound, BadRequest, Conflict


class ExpenseService:
    def __init__(self):
        self.store = get_store()

    def submit_expense(
        self,
        employee_id: str,
        amount: float,
        category: str,
        description: str,
        date_submitted: datetime,
        receipt_url: str = None,
        project_code: str = None,
        department: str = None,
    ) -> Expense:
        expense = create_expense(
            employee_id=employee_id,
            amount=amount,
            category=category,
            description=description,
            date_submitted=date_submitted,
            receipt_url=receipt_url,
            project_code=project_code,
            department=department,
        )
        return self.store.create_expense(expense)

    def get_expense(self, expense_id: str) -> Expense:
        expense = self.store.get_expense(expense_id)
        if not expense:
            raise NotFound(f"Expense {expense_id} not found")
        return expense

    def get_employee_expenses(self, employee_id: str) -> list[Expense]:
        all_expenses = self.store.list_expenses()
        return [e for e in all_expenses if e.employee_id == employee_id]

    def get_employee_expenses_by_status(self, employee_id: str, status: str) -> list[Expense]:
        all_expenses = self.store.list_expenses()
        return [e for e in all_expenses if e.employee_id == employee_id and e.status == status]
