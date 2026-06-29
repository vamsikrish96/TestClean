import pytest
from datetime import datetime
from app.database.store import get_store, ExpenseStore
from app.models.expense import create_expense


@pytest.fixture
def store() -> ExpenseStore:
    store_instance = get_store()
    store_instance._expenses.clear()
    store_instance._employee_manager_map.clear()
    return store_instance


@pytest.fixture
def test_expense_data():
    return {
        "amount": 100.0,
        "category": "Travel",
        "description": "Flight to NYC",
        "date_submitted": datetime.utcnow(),
    }


@pytest.fixture
def test_employees():
    return {
        "emp1": "employee1",
        "emp2": "employee2",
        "emp3": "employee3",
    }


@pytest.fixture
def test_managers():
    return {
        "mgr1": "manager1",
        "mgr2": "manager2",
    }


@pytest.fixture
def test_finance():
    return "finance1"


@pytest.fixture
def setup_manager_relationships(store, test_employees, test_managers):
    store.set_manager_for_employee(test_employees["emp1"], test_managers["mgr1"])
    store.set_manager_for_employee(test_employees["emp2"], test_managers["mgr1"])
    store.set_manager_for_employee(test_employees["emp3"], test_managers["mgr2"])
    return store
