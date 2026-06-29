import pytest
from datetime import datetime
from app.models import Expense, ExpenseStatus
from app.database import ExpenseStore


def test_store_create_expense():
    store = ExpenseStore()
    expense = Expense(
        employee_id="emp_123",
        amount=100.0,
        description="Test",
        submitted_date=datetime.now()
    )
    created = store.create(expense)
    assert created.id == "exp_000001"
    assert created.employee_id == "emp_123"
    assert store.exists(created.id)


def test_store_create_generates_unique_ids():
    store = ExpenseStore()
    exp1 = Expense(employee_id="emp_1", amount=100, description="Test 1", submitted_date=datetime.now())
    exp2 = Expense(employee_id="emp_2", amount=200, description="Test 2", submitted_date=datetime.now())

    created1 = store.create(exp1)
    created2 = store.create(exp2)

    assert created1.id != created2.id
    assert created1.id == "exp_000001"
    assert created2.id == "exp_000002"


def test_store_get_expense():
    store = ExpenseStore()
    expense = Expense(employee_id="emp_123", amount=100, description="Test", submitted_date=datetime.now())
    created = store.create(expense)

    retrieved = store.get(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id


def test_store_get_nonexistent():
    store = ExpenseStore()
    assert store.get("nonexistent") is None


def test_store_list_all():
    store = ExpenseStore()
    exp1 = Expense(employee_id="emp_1", amount=100, description="Test 1", submitted_date=datetime.now())
    exp2 = Expense(employee_id="emp_2", amount=200, description="Test 2", submitted_date=datetime.now())

    store.create(exp1)
    store.create(exp2)

    all_expenses = store.list_all()
    assert len(all_expenses) == 2


def test_store_list_by_employee():
    store = ExpenseStore()
    exp1 = Expense(employee_id="emp_1", amount=100, description="Test 1", submitted_date=datetime.now())
    exp2 = Expense(employee_id="emp_1", amount=200, description="Test 2", submitted_date=datetime.now())
    exp3 = Expense(employee_id="emp_2", amount=300, description="Test 3", submitted_date=datetime.now())

    store.create(exp1)
    store.create(exp2)
    store.create(exp3)

    emp1_expenses = store.list_by_employee("emp_1")
    assert len(emp1_expenses) == 2

    emp2_expenses = store.list_by_employee("emp_2")
    assert len(emp2_expenses) == 1


def test_store_list_by_status():
    store = ExpenseStore()
    exp1 = Expense(employee_id="emp_1", amount=100, description="Test 1", status=ExpenseStatus.SUBMITTED, submitted_date=datetime.now())
    exp2 = Expense(employee_id="emp_2", amount=200, description="Test 2", status=ExpenseStatus.APPROVED, submitted_date=datetime.now())
    exp3 = Expense(employee_id="emp_3", amount=300, description="Test 3", status=ExpenseStatus.SUBMITTED, submitted_date=datetime.now())

    store.create(exp1)
    store.create(exp2)
    store.create(exp3)

    submitted = store.list_by_status(ExpenseStatus.SUBMITTED)
    assert len(submitted) == 2

    approved = store.list_by_status(ExpenseStatus.APPROVED)
    assert len(approved) == 1


def test_store_update_expense():
    store = ExpenseStore()
    expense = Expense(employee_id="emp_123", amount=100, description="Test", submitted_date=datetime.now())
    created = store.create(expense)

    created.amount = 150
    updated = store.update(created.id, created)
    assert updated.amount == 150


def test_store_update_nonexistent():
    store = ExpenseStore()
    expense = Expense(employee_id="emp_123", amount=100, description="Test", submitted_date=datetime.now())
    result = store.update("nonexistent", expense)
    assert result is None
