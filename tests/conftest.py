import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories import expense_repo, history_repo, user_repo
from app.models import User, UserRole


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def clear_repos():
    """Clear all repositories before and after each test."""
    expense_repo.storage.clear()
    history_repo.storage.clear()
    user_repo.storage.clear()
    yield
    expense_repo.storage.clear()
    history_repo.storage.clear()
    user_repo.storage.clear()


@pytest.fixture
def setup_users(clear_repos):
    """Create test users for testing."""
    user_repo.create(User(id="emp1", name="Alice Employee", role=UserRole.EMPLOYEE, manager_id="mgr1"))
    user_repo.create(User(id="emp2", name="Bob Employee", role=UserRole.EMPLOYEE, manager_id="mgr1"))
    user_repo.create(User(id="mgr1", name="Charlie Manager", role=UserRole.MANAGER))
    user_repo.create(User(id="fin1", name="Diana Finance", role=UserRole.FINANCE))
    return {
        "emp1": "emp1:employee",
        "emp2": "emp2:employee",
        "mgr1": "mgr1:manager",
        "fin1": "fin1:finance",
    }
