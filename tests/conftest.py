import base64
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import ExpenseStore


@pytest.fixture
def client():
    return TestClient(app)


def create_token(user_id: str, role: str) -> str:
    payload = {"user_id": user_id, "role": role}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"Bearer {encoded}"


@pytest.fixture
def employee_token():
    return create_token("emp_001", "employee")


@pytest.fixture
def manager_token():
    return create_token("mgr_001", "manager")


@pytest.fixture
def finance_token():
    return create_token("fin_001", "finance")


@pytest.fixture
def admin_token():
    return create_token("adm_001", "admin")
