import base64
import json
import pytest
from fastapi import HTTPException
from app.auth import decode_token, TokenPayload, get_current_user


def create_token(user_id: str, role: str) -> str:
    payload = {"user_id": user_id, "role": role}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"Bearer {encoded}"


def test_decode_token_valid():
    token = create_token("emp_123", "employee")
    payload = decode_token(token)
    assert payload.user_id == "emp_123"
    assert payload.role == "employee"


def test_decode_token_manager():
    token = create_token("mgr_456", "manager")
    payload = decode_token(token)
    assert payload.user_id == "mgr_456"
    assert payload.role == "manager"


def test_decode_token_finance():
    token = create_token("fin_789", "finance")
    payload = decode_token(token)
    assert payload.user_id == "fin_789"
    assert payload.role == "finance"


def test_decode_token_missing_bearer():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("invalid_token")
    assert exc_info.value.status_code == 401


def test_decode_token_empty():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("")
    assert exc_info.value.status_code == 401


def test_decode_token_invalid_base64():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("Bearer !!!invalid_base64!!!")
    assert exc_info.value.status_code == 401


def test_decode_token_invalid_json():
    token = f"Bearer {base64.b64encode(b'not json').decode()}"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_decode_token_missing_user_id():
    payload = {"role": "employee"}
    token = f"Bearer {base64.b64encode(json.dumps(payload).encode()).decode()}"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_decode_token_missing_role():
    payload = {"user_id": "emp_123"}
    token = f"Bearer {base64.b64encode(json.dumps(payload).encode()).decode()}"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_get_current_user_valid(client):
    token = create_token("emp_123", "employee")
    response = client.get("/auth-check", headers={"Authorization": token})
    assert response.status_code == 200
    assert response.json()["user_id"] == "emp_123"
    assert response.json()["role"] == "employee"


def test_get_current_user_missing_header(client):
    response = client.get("/auth-check")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    response = client.get("/auth-check", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_token_payload_creation():
    payload = TokenPayload("emp_123", "employee")
    assert payload.user_id == "emp_123"
    assert payload.role == "employee"


def test_employee_only_endpoint_authorized(client):
    token = create_token("emp_123", "employee")
    response = client.get("/employee-only", headers={"Authorization": token})
    assert response.status_code == 200
    assert "employee access" in response.json()["message"]


def test_employee_only_endpoint_manager_denied(client):
    token = create_token("mgr_456", "manager")
    response = client.get("/employee-only", headers={"Authorization": token})
    assert response.status_code == 403


def test_employee_only_endpoint_finance_denied(client):
    token = create_token("fin_789", "finance")
    response = client.get("/employee-only", headers={"Authorization": token})
    assert response.status_code == 403


def test_manager_only_endpoint_authorized(client):
    token = create_token("mgr_456", "manager")
    response = client.get("/manager-only", headers={"Authorization": token})
    assert response.status_code == 200
    assert "manager access" in response.json()["message"]


def test_manager_only_endpoint_employee_denied(client):
    token = create_token("emp_123", "employee")
    response = client.get("/manager-only", headers={"Authorization": token})
    assert response.status_code == 403


def test_manager_only_endpoint_finance_denied(client):
    token = create_token("fin_789", "finance")
    response = client.get("/manager-only", headers={"Authorization": token})
    assert response.status_code == 403


def test_finance_only_endpoint_authorized(client):
    token = create_token("fin_789", "finance")
    response = client.get("/finance-only", headers={"Authorization": token})
    assert response.status_code == 200
    assert "finance access" in response.json()["message"]


def test_finance_only_endpoint_employee_denied(client):
    token = create_token("emp_123", "employee")
    response = client.get("/finance-only", headers={"Authorization": token})
    assert response.status_code == 403


def test_finance_only_endpoint_manager_denied(client):
    token = create_token("mgr_456", "manager")
    response = client.get("/finance-only", headers={"Authorization": token})
    assert response.status_code == 403


def test_role_protected_endpoint_missing_auth(client):
    response = client.get("/manager-only")
    assert response.status_code == 401
