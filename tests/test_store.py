import pytest
from datetime import datetime
from app.database.store import ExpenseStore
from app.models.expense import create_expense


class TestExpenseStore:
    def test_create_expense(self, store: ExpenseStore):
        expense = create_expense(
            employee_id="emp1",
            amount=100.0,
            category="Travel",
            description="Flight",
            date_submitted=datetime.utcnow(),
        )
        created = store.create_expense(expense)
        assert created.expense_id == expense.expense_id
        assert created.employee_id == "emp1"

    def test_get_expense(self, store: ExpenseStore):
        expense = create_expense(
            employee_id="emp1",
            amount=100.0,
            category="Travel",
            description="Flight",
            date_submitted=datetime.utcnow(),
        )
        store.create_expense(expense)
        retrieved = store.get_expense(expense.expense_id)
        assert retrieved is not None
        assert retrieved.expense_id == expense.expense_id

    def test_get_nonexistent_expense(self, store: ExpenseStore):
        result = store.get_expense("nonexistent")
        assert result is None

    def test_list_expenses_empty(self, store: ExpenseStore):
        expenses = store.list_expenses()
        assert expenses == []

    def test_list_expenses_multiple(self, store: ExpenseStore):
        exp1 = create_expense(
            employee_id="emp1",
            amount=100.0,
            category="Travel",
            description="Flight",
            date_submitted=datetime.utcnow(),
        )
        exp2 = create_expense(
            employee_id="emp2",
            amount=50.0,
            category="Meals",
            description="Lunch",
            date_submitted=datetime.utcnow(),
        )
        store.create_expense(exp1)
        store.create_expense(exp2)
        expenses = store.list_expenses()
        assert len(expenses) == 2
        assert any(e.expense_id == exp1.expense_id for e in expenses)
        assert any(e.expense_id == exp2.expense_id for e in expenses)

    def test_update_expense(self, store: ExpenseStore):
        expense = create_expense(
            employee_id="emp1",
            amount=100.0,
            category="Travel",
            description="Flight",
            date_submitted=datetime.utcnow(),
        )
        store.create_expense(expense)
        expense.status = "APPROVED"
        expense.manager_id = "mgr1"
        updated = store.update_expense(expense)
        retrieved = store.get_expense(expense.expense_id)
        assert retrieved.status == "APPROVED"
        assert retrieved.manager_id == "mgr1"

    def test_manager_mapping(self, store: ExpenseStore):
        store.set_manager_for_employee("emp1", "mgr1")
        store.set_manager_for_employee("emp2", "mgr1")
        store.set_manager_for_employee("emp3", "mgr2")

        assert store.get_manager_for_employee("emp1") == "mgr1"
        assert store.get_manager_for_employee("emp2") == "mgr1"
        assert store.get_manager_for_employee("emp3") == "mgr2"
        assert store.get_manager_for_employee("emp4") is None

    def test_get_employees_for_manager(self, store: ExpenseStore):
        store.set_manager_for_employee("emp1", "mgr1")
        store.set_manager_for_employee("emp2", "mgr1")
        store.set_manager_for_employee("emp3", "mgr2")

        mgr1_employees = store.get_employees_for_manager("mgr1")
        assert len(mgr1_employees) == 2
        assert "emp1" in mgr1_employees
        assert "emp2" in mgr1_employees

        mgr2_employees = store.get_employees_for_manager("mgr2")
        assert len(mgr2_employees) == 1
        assert "emp3" in mgr2_employees
