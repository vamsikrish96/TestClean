import base64
import json


def create_token(user_id: str, role: str) -> str:
    payload = {"user_id": user_id, "role": role}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"Bearer {encoded}"


def test_list_expenses_empty(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.get("/expenses", headers={"Authorization": token})
    assert response.status_code == 200
    assert response.json() == []


def test_list_expenses_single(client, clean_store):
    token = create_token("emp_123", "employee")

    client.post(
        "/expenses",
        json={"amount": 100, "description": "Test"},
        headers={"Authorization": token}
    )

    response = client.get("/expenses", headers={"Authorization": token})
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) == 1
    assert expenses[0]["amount"] == 100


def test_list_expenses_multiple_own(client, clean_store):
    token = create_token("emp_123", "employee")

    for i in range(3):
        client.post(
            "/expenses",
            json={"amount": 100 + i * 10, "description": f"Expense {i}"},
            headers={"Authorization": token}
        )

    response = client.get("/expenses", headers={"Authorization": token})
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) == 3


def test_list_expenses_filters_by_employee(client, clean_store):
    token1 = create_token("emp_123", "employee")
    token2 = create_token("emp_456", "employee")

    for i in range(2):
        client.post(
            "/expenses",
            json={"amount": 100 + i, "description": f"Emp1-{i}"},
            headers={"Authorization": token1}
        )

    for i in range(3):
        client.post(
            "/expenses",
            json={"amount": 200 + i, "description": f"Emp2-{i}"},
            headers={"Authorization": token2}
        )

    response1 = client.get("/expenses", headers={"Authorization": token1})
    response2 = client.get("/expenses", headers={"Authorization": token2})

    assert len(response1.json()) == 2
    assert len(response2.json()) == 3


def test_list_expenses_with_limit(client, clean_store):
    token = create_token("emp_123", "employee")

    for i in range(10):
        client.post(
            "/expenses",
            json={"amount": 100 + i, "description": f"Expense {i}"},
            headers={"Authorization": token}
        )

    response = client.get("/expenses?limit=3", headers={"Authorization": token})
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_expenses_with_offset(client, clean_store):
    token = create_token("emp_123", "employee")

    for i in range(5):
        client.post(
            "/expenses",
            json={"amount": 100 + i, "description": f"Expense {i}"},
            headers={"Authorization": token}
        )

    response = client.get("/expenses?offset=2&limit=10", headers={"Authorization": token})
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_expenses_default_limit(client, clean_store):
    token = create_token("emp_123", "employee")

    for i in range(100):
        client.post(
            "/expenses",
            json={"amount": 100 + i, "description": f"Expense {i}"},
            headers={"Authorization": token}
        )

    response = client.get("/expenses", headers={"Authorization": token})
    assert response.status_code == 200
    assert len(response.json()) == 50


def test_list_expenses_no_auth(client, clean_store):
    response = client.get("/expenses")
    assert response.status_code == 401


def test_list_expenses_invalid_auth(client, clean_store):
    response = client.get("/expenses", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_list_expenses_manager_denied(client, clean_store):
    token = create_token("mgr_456", "manager")
    response = client.get("/expenses", headers={"Authorization": token})
    assert response.status_code == 403


def test_list_expenses_finance_denied(client, clean_store):
    token = create_token("fin_789", "finance")
    response = client.get("/expenses", headers={"Authorization": token})
    assert response.status_code == 403


def test_get_expense_success(client, clean_store):
    token = create_token("emp_123", "employee")

    submit_response = client.post(
        "/expenses",
        json={"amount": 150, "description": "Test"},
        headers={"Authorization": token}
    )
    expense_id = submit_response.json()["id"]

    response = client.get(f"/expenses/{expense_id}", headers={"Authorization": token})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == expense_id
    assert data["employee_id"] == "emp_123"
    assert data["amount"] == 150


def test_get_expense_not_found(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.get("/expenses/nonexistent", headers={"Authorization": token})
    assert response.status_code == 404


def test_get_expense_forbidden_other_employee(client, clean_store):
    token1 = create_token("emp_123", "employee")
    token2 = create_token("emp_456", "employee")

    submit_response = client.post(
        "/expenses",
        json={"amount": 100, "description": "Emp1 expense"},
        headers={"Authorization": token1}
    )
    expense_id = submit_response.json()["id"]

    response = client.get(f"/expenses/{expense_id}", headers={"Authorization": token2})
    assert response.status_code == 403


def test_get_expense_no_auth(client, clean_store):
    response = client.get("/expenses/exp_001")
    assert response.status_code == 401


def test_get_expense_invalid_auth(client, clean_store):
    response = client.get("/expenses/exp_001", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_get_expense_manager_denied(client, clean_store):
    token = create_token("mgr_456", "manager")
    response = client.get("/expenses/exp_001", headers={"Authorization": token})
    assert response.status_code == 403


def test_get_expense_finance_denied(client, clean_store):
    token = create_token("fin_789", "finance")
    response = client.get("/expenses/exp_001", headers={"Authorization": token})
    assert response.status_code == 403


def test_list_expenses_invalid_limit(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.get("/expenses?limit=0", headers={"Authorization": token})
    assert response.status_code == 422


def test_list_expenses_negative_offset(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.get("/expenses?offset=-1", headers={"Authorization": token})
    assert response.status_code == 422


def test_list_expenses_excessive_limit(client, clean_store):
    token = create_token("emp_123", "employee")
    response = client.get("/expenses?limit=2000", headers={"Authorization": token})
    assert response.status_code == 422
