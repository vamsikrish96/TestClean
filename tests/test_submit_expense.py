import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.store import get_store

client = TestClient(app)
store = get_store()


@pytest.fixture(autouse=True)
def clear_store():
    store._expenses.clear()
    store._employee_manager_map.clear()
    yield


class TestSubmitExpense:
    def test_submit_valid_expense(self):
        payload = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight to NYC",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp123", "X-User-Role": "employee"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == "emp123"
        assert data["amount"] == 100.0
        assert data["category"] == "Travel"
        assert data["description"] == "Flight to NYC"
        assert data["status"] == "SUBMITTED"
        assert data["expense_id"] is not None

    def test_submit_with_optional_fields(self):
        payload = {
            "amount": 150.0,
            "category": "Meals",
            "description": "Team lunch",
            "date_submitted": datetime.utcnow().isoformat(),
            "receipt_url": "https://example.com/receipt.pdf",
            "project_code": "PRJ001",
            "department": "Engineering",
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp456", "X-User-Role": "employee"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["receipt_url"] == "https://example.com/receipt.pdf"
        assert data["project_code"] == "PRJ001"
        assert data["department"] == "Engineering"

    def test_submit_invalid_amount_negative(self):
        payload = {
            "amount": -100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp123", "X-User-Role": "employee"},
        )
        assert response.status_code == 422

    def test_submit_invalid_amount_zero(self):
        payload = {
            "amount": 0.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp123", "X-User-Role": "employee"},
        )
        assert response.status_code == 422

    def test_submit_invalid_category(self):
        payload = {
            "amount": 100.0,
            "category": "InvalidCategory",
            "description": "Expense",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp123", "X-User-Role": "employee"},
        )
        assert response.status_code == 422

    def test_submit_empty_description(self):
        payload = {
            "amount": 100.0,
            "category": "Travel",
            "description": "",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp123", "X-User-Role": "employee"},
        )
        assert response.status_code == 422

    def test_submit_missing_auth_headers(self):
        payload = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post("/expenses/", json=payload)
        assert response.status_code == 401

    def test_submit_missing_user_id_header(self):
        payload = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-Role": "employee"},
        )
        assert response.status_code == 401

    def test_submit_invalid_role(self):
        payload = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "mgr123", "X-User-Role": "manager"},
        )
        assert response.status_code == 403

    def test_submit_finance_role(self):
        payload = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "fin123", "X-User-Role": "finance"},
        )
        assert response.status_code == 403

    def test_submit_expense_generates_unique_ids(self):
        payload = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow().isoformat(),
        }
        response1 = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp123", "X-User-Role": "employee"},
        )
        response2 = client.post(
            "/expenses/",
            json=payload,
            headers={"X-User-ID": "emp456", "X-User-Role": "employee"},
        )
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert data1["expense_id"] != data2["expense_id"]
