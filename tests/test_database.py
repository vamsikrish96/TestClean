import pytest
from app.models import Expense, ExpenseStatus
from app.database import ExpenseStore


class TestExpenseStore:
    @pytest.fixture
    def store(self):
        return ExpenseStore()

    def test_create_expense(self, store):
        exp = Expense(employee_id="emp_001", amount=100.0, description="Test")
        created = store.create(exp)

        assert created.id == "exp_000001"
        assert created.employee_id == "emp_001"
        assert created.version == 1

    def test_create_increments_id(self, store):
        exp1 = Expense(employee_id="emp_001", amount=100.0, description="Test 1")
        exp2 = Expense(employee_id="emp_002", amount=200.0, description="Test 2")

        created1 = store.create(exp1)
        created2 = store.create(exp2)

        assert created1.id == "exp_000001"
        assert created2.id == "exp_000002"

    def test_get_expense(self, store):
        exp = Expense(employee_id="emp_001", amount=100.0, description="Test")
        created = store.create(exp)
        retrieved = store.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.employee_id == "emp_001"

    def test_get_nonexistent_expense(self, store):
        with pytest.raises(KeyError):
            store.get("exp_999999")

    def test_list_all_expenses(self, store):
        exp1 = Expense(employee_id="emp_001", amount=100.0, description="Test 1")
        exp2 = Expense(employee_id="emp_002", amount=200.0, description="Test 2")

        store.create(exp1)
        store.create(exp2)

        all_expenses = store.list_all()
        assert len(all_expenses) == 2

    def test_list_by_employee(self, store):
        exp1 = Expense(employee_id="emp_001", amount=100.0, description="Test 1")
        exp2 = Expense(employee_id="emp_001", amount=150.0, description="Test 2")
        exp3 = Expense(employee_id="emp_002", amount=200.0, description="Test 3")

        store.create(exp1)
        store.create(exp2)
        store.create(exp3)

        emp1_expenses = store.list_by_employee("emp_001")
        assert len(emp1_expenses) == 2
        assert all(e.employee_id == "emp_001" for e in emp1_expenses)

    def test_list_by_status(self, store):
        exp1 = Expense(employee_id="emp_001", amount=100.0, description="Test 1", status=ExpenseStatus.SUBMITTED)
        exp2 = Expense(employee_id="emp_002", amount=200.0, description="Test 2", status=ExpenseStatus.APPROVED)
        exp3 = Expense(employee_id="emp_003", amount=300.0, description="Test 3", status=ExpenseStatus.APPROVED)

        store.create(exp1)
        store.create(exp2)
        store.create(exp3)

        approved = store.list_by_status(ExpenseStatus.APPROVED)
        assert len(approved) == 2
        assert all(e.status == ExpenseStatus.APPROVED for e in approved)

    def test_update_expense(self, store):
        exp = Expense(employee_id="emp_001", amount=100.0, description="Test")
        created = store.create(exp)

        created.description = "Updated"
        updated = store.update(created.id, created)

        assert updated is not None
        assert updated.description == "Updated"
        assert updated.version == 2

    def test_update_nonexistent_expense(self, store):
        exp = Expense(employee_id="emp_001", amount=100.0, description="Test")
        with pytest.raises(KeyError):
            store.update("exp_999999", exp)

    def test_exists_true(self, store):
        exp = Expense(employee_id="emp_001", amount=100.0, description="Test")
        created = store.create(exp)
        assert store.exists(created.id) is True

    def test_exists_false(self, store):
        assert store.exists("exp_999999") is False
