import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories import expense_repo, history_repo, user_repo, init_test_data
from app.models import User, UserRole


@pytest.fixture(autouse=True)
def clear_repos_fixture():
    """Clear all repositories before and after each test."""
    expense_repo.storage.clear()
    history_repo.storage.clear()
    user_repo.storage.clear()
    yield
    expense_repo.storage.clear()
    history_repo.storage.clear()
    user_repo.storage.clear()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def setup_users():
    """Create test users for testing."""
    init_test_data()
    return {
        "emp1": "emp1:employee",
        "emp2": "emp2:employee",
        "mgr1": "mgr1:manager",
        "fin1": "fin1:finance",
    }
