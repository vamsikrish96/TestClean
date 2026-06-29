import base64
import json
from datetime import datetime
from app.models import ExpenseStatus


def create_token(user_id: str, role: str) -> str:
    payload = {"user_id": user_id, "role": role}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"Bearer {encoded}"


def test_submit_expense_success(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": 150.50, "description": "Conference ticket"},
        headers={"Authorization": token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["employee_id"] == "emp_123"
    assert data["amount"] == 150.50
    assert data["description"] == "Conference ticket"
    assert data["status"] == ExpenseStatus.SUBMITTED.value
    assert data["submitted_date"] is not None


def test_submit_expense_creates_unique_ids(client, clean_store):
    token = create_token("emp_123", "employee")

    response1 = client.post(
        "/expenses",
        json={"amount": 100, "description": "Expense 1"},
        headers={"Authorization": token}
    )

    response2 = client.post(
        "/expenses",
        json={"amount": 200, "description": "Expense 2"},
        headers={"Authorization": token}
    )

    id1 = response1.json()["id"]
    id2 = response2.json()["id"]
    assert id1 != id2


def test_submit_expense_manager_denied(client, clean_store):
    token = create_token("mgr_456", "manager")
    response = client.post(
        "/expenses",
        json={"amount": 150.50, "description": "Expense"},
        headers={"Authorization": token}
    )
    assert response.status_code == 403


def test_submit_expense_finance_denied(client, clean_store):
    token = create_token("fin_789", "finance")
    response = client.post(
        "/expenses",
        json={"amount": 150.50, "description": "Expense"},
        headers={"Authorization": token}
    )
    assert response.status_code == 403


def test_submit_expense_no_auth_header(client, clean_store):
    response = client.post(
        "/expenses",
        json={"amount": 150.50, "description": "Expense"}
    )
    assert response.status_code == 401


def test_submit_expense_invalid_auth_token(client, clean_store):
    response = client.post(
        "/expenses",
        json={"amount": 150.50, "description": "Expense"},
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401


def test_submit_expense_negative_amount(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": -50, "description": "Invalid"},
        headers={"Authorization": token}
    )
    assert response.status_code == 422


def test_submit_expense_zero_amount(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": 0, "description": "Invalid"},
        headers={"Authorization": token}
    )
    assert response.status_code == 422


def test_submit_expense_exceeds_max(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": 150000, "description": "Too much"},
        headers={"Authorization": token}
    )
    assert response.status_code == 422


def test_submit_expense_empty_description(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": 100, "description": ""},
        headers={"Authorization": token}
    )
    assert response.status_code == 422


def test_submit_expense_description_too_long(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": 100, "description": "x" * 501},
        headers={"Authorization": token}
    )
    assert response.status_code == 422


def test_submit_expense_missing_amount(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"description": "Missing amount"},
        headers={"Authorization": token}
    )
    assert response.status_code == 422


def test_submit_expense_missing_description(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": 100},
        headers={"Authorization": token}
    )
    assert response.status_code == 422


def test_submit_expense_multiple_employees(client, clean_store):
    token1 = create_token("emp_123", "employee")
    token2 = create_token("emp_456", "employee")

    response1 = client.post(
        "/expenses",
        json={"amount": 100, "description": "Emp 1 expense"},
        headers={"Authorization": token1}
    )

    response2 = client.post(
        "/expenses",
        json={"amount": 200, "description": "Emp 2 expense"},
        headers={"Authorization": token2}
    )

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["employee_id"] == "emp_123"
    assert response2.json()["employee_id"] == "emp_456"


def test_submit_expense_stored_in_database(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.post(
        "/expenses",
        json={"amount": 150.50, "description": "Test"},
        headers={"Authorization": token}
    )

    expense_id = response.json()["id"]
    stored = clean_store.get(expense_id)
    assert stored is not None
    assert stored.employee_id == "emp_123"
    assert stored.amount == 150.50
