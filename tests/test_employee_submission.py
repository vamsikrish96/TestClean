import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.repositories import expense_repo, history_repo, user_repo
from app.models import UserRole


@pytest.fixture
def setup_test_env():
    """Setup test environment with users."""
    expense_repo.storage.clear()
    history_repo.storage.clear()
    user_repo.storage.clear()
    yield
    expense_repo.storage.clear()
    history_repo.storage.clear()
    user_repo.storage.clear()


class TestExpenseSubmission:
    def test_submit_expense_success(self, setup_test_env):
        """Test successful expense submission."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight to NYC",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["amount"] == 100.0
        assert data["category"] == "Travel"
        assert data["employee_id"] == "emp1"
        assert len(data["history"]) > 0

    def test_submit_expense_missing_auth_header(self, setup_test_env):
        """Test submission without authorization header."""
        client = TestClient(app)

        response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
        )

        assert response.status_code == 401

    def test_submit_expense_invalid_role(self, setup_test_env):
        """Test submission by non-employee role."""
        client = TestClient(app)
        token = "mgr1:manager"

        response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    def test_submit_expense_amount_too_high(self, setup_test_env):
        """Test submission with amount exceeding $100,000."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": 150000.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_expense_zero_amount(self, setup_test_env):
        """Test submission with zero amount."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": 0.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_expense_negative_amount(self, setup_test_env):
        """Test submission with negative amount."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": -50.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_expense_future_date(self, setup_test_env):
        """Test submission with future expense date."""
        client = TestClient(app)
        token = "emp1:employee"
        future_date = date.today() + timedelta(days=1)

        response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(future_date),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_expense_missing_receipt_url(self, setup_test_env):
        """Test submission without receipt URL."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_expense_empty_description(self, setup_test_env):
        """Test submission with empty description."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_expense_invalid_category(self, setup_test_env):
        """Test submission with invalid category."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "InvalidCategory",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_submit_multiple_expenses(self, setup_test_env):
        """Test submitting multiple expenses."""
        client = TestClient(app)
        token = "emp1:employee"

        exp1 = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt1.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        exp2 = client.post(
            "/expenses",
            json={
                "amount": 50.0,
                "category": "Meals",
                "description": "Lunch",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt2.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert exp1.status_code == 201
        assert exp2.status_code == 201
        assert exp1.json()["id"] != exp2.json()["id"]

    def test_submit_expense_max_amount(self, setup_test_env):
        """Test submission with maximum allowed amount ($100,000)."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.post(
            "/expenses",
            json={
                "amount": 100000.0,
                "category": "Equipment",
                "description": "Server equipment",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        assert response.json()["amount"] == 100000.0


class TestExpenseList:
    def test_list_empty_expenses(self, setup_test_env):
        """Test listing expenses when none exist."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.get(
            "/expenses",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_employee_expenses(self, setup_test_env):
        """Test listing employee's own expenses."""
        client = TestClient(app)
        token = "emp1:employee"

        # Submit expense
        client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # List expenses
        response = client.get(
            "/expenses",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["amount"] == 100.0
        assert data[0]["status"] == "pending"

    def test_list_expenses_by_status(self, setup_test_env):
        """Test listing expenses filtered by status."""
        client = TestClient(app)
        token = "emp1:employee"

        # Submit expense
        client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # List by pending status
        response = client.get(
            "/expenses?status=pending",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

        # List by rejected status
        response = client.get(
            "/expenses?status=rejected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_list_expenses_requires_auth(self, setup_test_env):
        """Test listing expenses without authorization."""
        client = TestClient(app)

        response = client.get("/expenses")

        assert response.status_code == 401


class TestExpenseDetail:
    def test_get_expense_detail(self, setup_test_env):
        """Test getting expense detail with full audit trail."""
        client = TestClient(app)
        token = "emp1:employee"

        # Submit expense
        create_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        expense_id = create_response.json()["id"]

        # Get expense detail
        response = client.get(
            f"/expenses/{expense_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == expense_id
        assert data["status"] == "pending"
        assert len(data["history"]) > 0

    def test_get_expense_not_found(self, setup_test_env):
        """Test getting non-existent expense."""
        client = TestClient(app)
        token = "emp1:employee"

        response = client.get(
            "/expenses/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_cannot_view_other_employee_expense(self, setup_test_env):
        """Test that employee cannot view other employees' expenses."""
        client = TestClient(app)
        token1 = "emp1:employee"
        token2 = "emp2:employee"

        # emp1 submits expense
        create_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token1}"},
        )

        expense_id = create_response.json()["id"]

        # emp2 tries to view emp1's expense
        response = client.get(
            f"/expenses/{expense_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
