import pytest
from app.models import Expense, ExpenseStatus


def _submit_expense(client, employee_token, amount=100, description="Test"):
    payload = {"amount": amount, "description": description}
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": employee_token}
    )
    return response.json()


def test_list_own_expenses_returns_empty_list_when_none_submitted(client, employee_token):
    response = client.get(
        "/expenses",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_own_expenses_returns_submitted_expenses(client, employee_token):
    _submit_expense(client, employee_token)
    _submit_expense(client, employee_token, 200, "Second")

    response = client.get(
        "/expenses",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) == 2
    assert expenses[0]["amount"] == 100
    assert expenses[1]["amount"] == 200


def test_list_own_expenses_filters_by_employee(client, employee_token, manager_token):
    _submit_expense(client, employee_token)

    response = client.get(
        "/expenses",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_own_expenses_respects_limit_parameter(client, employee_token):
    for i in range(5):
        _submit_expense(client, employee_token, 100 + i, f"Expense {i}")

    response = client.get(
        "/expenses?limit=2",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_own_expenses_respects_offset_parameter(client, employee_token):
    for i in range(5):
        _submit_expense(client, employee_token, 100 + i, f"Expense {i}")

    response = client.get(
        "/expenses?offset=3",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) == 2
    assert expenses[0]["amount"] == 103


def test_list_own_expenses_limit_offset_combined(client, employee_token):
    for i in range(10):
        _submit_expense(client, employee_token, 100 + i, f"Expense {i}")

    response = client.get(
        "/expenses?limit=3&offset=2",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) == 3
    assert expenses[0]["amount"] == 102


def test_list_own_expenses_limit_default_50(client, employee_token):
    for i in range(100):
        _submit_expense(client, employee_token, 100 + i, f"Expense {i}")

    response = client.get(
        "/expenses",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 200
    assert len(response.json()) == 50


def test_list_own_expenses_limit_max_1000(client, employee_token):
    response = client.get(
        "/expenses?limit=1001",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 400


def test_list_own_expenses_limit_min_1(client, employee_token):
    response = client.get(
        "/expenses?limit=0",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 400


def test_list_own_expenses_offset_negative_rejected(client, employee_token):
    response = client.get(
        "/expenses?offset=-1",
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 400


def test_list_own_expenses_without_auth(client):
    response = client.get("/expenses")
    assert response.status_code == 401


def test_list_own_expenses_invalid_token(client):
    response = client.get(
        "/expenses",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401


def test_list_own_expenses_manager_role_forbidden(client, manager_token):
    response = client.get(
        "/expenses",
        headers={"Authorization": manager_token}
    )
    assert response.status_code == 403


def test_list_own_expenses_returns_all_fields(client, employee_token):
    _submit_expense(client, employee_token, 150, "Conference")

    response = client.get(
        "/expenses",
        headers={"Authorization": employee_token}
    )
    expense = response.json()[0]
    assert expense["id"] is not None
    assert expense["employee_id"] == "emp_001"
    assert expense["amount"] == 150
    assert expense["description"] == "Conference"
    assert expense["status"] == ExpenseStatus.SUBMITTED
    assert expense["submitted_date"] is not None
