import pytest
from app.models import ExpenseStatus


def _submit_valid_expense(client, employee_token):
    payload = {"amount": 150.50, "description": "Conference ticket"}
    return client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": employee_token}
    )


def test_submit_expense_returns_created_status(client, employee_token):
    response = _submit_valid_expense(client, employee_token)
    assert response.status_code == 201


def test_submit_expense_maps_employee_id_from_token(client, employee_token):
    response = _submit_valid_expense(client, employee_token)
    assert response.json()["employee_id"] == "emp_001"


def test_submit_expense_echoes_input_fields(client, employee_token):
    response = _submit_valid_expense(client, employee_token)
    data = response.json()
    assert data["amount"] == 150.50
    assert data["description"] == "Conference ticket"


def test_submit_expense_sets_status_to_submitted(client, employee_token):
    response = _submit_valid_expense(client, employee_token)
    assert response.json()["status"] == ExpenseStatus.SUBMITTED


def test_submit_expense_stamps_submitted_date(client, employee_token):
    response = _submit_valid_expense(client, employee_token)
    assert response.json()["submitted_date"] is not None


def test_submit_expense_assigns_expense_id(client, employee_token):
    response = _submit_valid_expense(client, employee_token)
    data = response.json()
    assert data["id"] is not None
    assert data["id"].startswith("exp_")


@pytest.mark.parametrize("payload,expected_status", [
    ({"amount": -50, "description": "Test"}, 422),
    ({"amount": 0, "description": "Test"}, 422),
    ({"amount": 100001, "description": "Test"}, 422),
    ({"amount": 100, "description": ""}, 422),
    ({"amount": 100}, 422),
    ({"description": "Test"}, 422),
])
def test_submit_validation_failures(client, employee_token, payload, expected_status):
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": employee_token}
    )
    assert response.status_code == expected_status


def test_submit_without_auth(client):
    payload = {"amount": 100, "description": "Test"}
    response = client.post("/expenses", json=payload)
    assert response.status_code == 401


def test_submit_with_invalid_token(client):
    payload = {"amount": 100, "description": "Test"}
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401


@pytest.mark.parametrize("token_fixture", ["manager_token", "finance_token"])
def test_submit_as_non_employee_forbidden(client, request, token_fixture):
    token = request.getfixturevalue(token_fixture)
    payload = {"amount": 100, "description": "Test"}
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": token}
    )
    assert response.status_code == 403


def test_submit_max_valid_amount(client, employee_token):
    payload = {"amount": 100000, "description": "Max valid"}
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 201
    assert response.json()["amount"] == 100000


def test_submit_max_description_length(client, employee_token):
    max_desc = "a" * 500
    payload = {"amount": 100, "description": max_desc}
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 201
    assert len(response.json()["description"]) == 500


def test_submit_exceeding_description_length(client, employee_token):
    long_desc = "a" * 501
    payload = {"amount": 100, "description": long_desc}
    response = client.post(
        "/expenses",
        json=payload,
        headers={"Authorization": employee_token}
    )
    assert response.status_code == 422


