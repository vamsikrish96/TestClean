def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_auth_check_with_valid_token(client, employee_token):
    response = client.get("/auth-check", headers={"Authorization": employee_token})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "emp_001"
    assert data["role"] == "employee"


def test_auth_check_missing_token(client):
    response = client.get("/auth-check")
    assert response.status_code == 401


def test_auth_check_invalid_token(client):
    response = client.get("/auth-check", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
