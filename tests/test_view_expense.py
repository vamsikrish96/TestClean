import pytest
from app.models import ExpenseStatus


def _submit_expense(client, employee_token, amount=100, description="Test"):
    payload = {"amount": amount, "description": description}
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": employee_token}
    )
    return response.json()


def test_view_own_expense_detail(client, employee_token):
    submitted = _submit_expense(client, employee_token, 150, "Conference")
    expense_id = submitted["id"]

    response = client.get(
        f"/expenses/{expense_id}",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    expense = response.json()
    assert expense["id"] == expense_id
    assert expense["employee_id"] == "emp_001"
    assert expense["amount"] == 150
    assert expense["description"] == "Conference"
    assert expense["status"] == ExpenseStatus.SUBMITTED


def test_view_expense_not_found(client, employee_token):
    response = client.get(
        "/expenses/exp_999999",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 404


def test_view_expense_access_denied_different_employee(client, employee_token, manager_token):
    submitted = _submit_expense(client, employee_token, 100, "Test")
    expense_id = submitted["id"]

    response = client.get(
        f"/expenses/{expense_id}",
        headers={"Authorization": manager_token}
    )
    assert response.status_code == 403


def test_view_expense_without_auth(client):
    response = client.get("/expenses/exp_000001")
    assert response.status_code == 401


def test_view_expense_invalid_token(client):
    response = client.get(
        "/expenses/exp_000001",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401


def test_view_expense_manager_role_forbidden(client, manager_token):
    response = client.get(
        "/expenses/exp_000001",
        headers={"Authorization": manager_token}
    )
    assert response.status_code == 403


def test_view_expense_returns_all_audit_fields(client, employee_token):
    submitted = _submit_expense(client, employee_token)
    expense_id = submitted["id"]

    response = client.get(
        f"/expenses/{expense_id}",
        headers={"Authorization": employee_token}
    )
    expense = response.json()
    assert expense["submitted_date"] is not None
    assert expense["approval_date"] is None
    assert expense["processing_date"] is None
    assert expense["approved_by"] is None
    assert expense["processed_by"] is None
    assert expense["returned_date"] is None
    assert expense["version"] == 1
