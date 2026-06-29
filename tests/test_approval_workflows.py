import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.repositories import expense_repo, history_repo, user_repo
from app.models import UserRole, User
from app.services import expense_service


@pytest.fixture
def setup_approval_env():
    """Setup test environment with users for approval testing."""
    user_repo.create(User(id="emp1", name="Alice", role=UserRole.EMPLOYEE, manager_id="mgr1"))
    user_repo.create(User(id="emp2", name="Bob", role=UserRole.EMPLOYEE, manager_id="mgr2"))
    user_repo.create(User(id="mgr1", name="Manager1", role=UserRole.MANAGER))
    user_repo.create(User(id="mgr2", name="Manager2", role=UserRole.MANAGER))
    user_repo.create(User(id="fin1", name="Finance", role=UserRole.FINANCE))
    yield
    expense_repo.storage.clear()
    history_repo.storage.clear()


class TestManagerApproval:
    def test_manager_approve_pending_expense(self, setup_approval_env):
        """Manager can approve pending expense from their report."""
        client = TestClient(app)

        # emp1 submits expense
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        # mgr1 approves
        response = client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved_by_manager"
        assert data["approved_by"] == "mgr1"
        assert len(data["history"]) > 1

    def test_manager_cannot_approve_other_manager_report(self, setup_approval_env):
        """Manager cannot approve expense from another manager's report."""
        client = TestClient(app)

        # emp2 (reports to mgr2) submits expense
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp2:employee"},
        )
        expense_id = submit_response.json()["id"]

        # mgr1 tries to approve emp2's expense
        response = client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        assert response.status_code == 403

    def test_manager_reject_pending_expense(self, setup_approval_env):
        """Manager can reject pending expense with reason."""
        client = TestClient(app)

        # emp1 submits expense
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        # mgr1 rejects with reason
        response = client.patch(
            f"/expenses/{expense_id}/reject",
            json={"rejection_reason": "Exceeds budget"},
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Exceeds budget"

    def test_manager_cannot_reject_already_approved(self, setup_approval_env):
        """Manager cannot reject already manager-approved expense."""
        client = TestClient(app)

        # emp1 submits and mgr1 approves
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        # mgr1 tries to reject already approved expense
        response = client.patch(
            f"/expenses/{expense_id}/reject",
            json={"rejection_reason": "Mistake"},
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        assert response.status_code == 400


class TestFinanceApproval:
    def test_finance_approve_manager_approved_expense(self, setup_approval_env):
        """Finance can approve manager-approved expense."""
        client = TestClient(app)

        # emp1 submits and mgr1 approves
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        # fin1 approves
        response = client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer fin1:finance"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved_by_finance"
        assert data["approved_by"] == "fin1"

    def test_finance_cannot_approve_pending_expense(self, setup_approval_env):
        """Finance cannot approve pending (not manager-approved) expense."""
        client = TestClient(app)

        # emp1 submits but manager hasn't approved yet
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        # fin1 tries to approve pending expense
        response = client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer fin1:finance"},
        )

        assert response.status_code == 400

    def test_finance_reject_manager_approved_expense(self, setup_approval_env):
        """Finance can reject manager-approved expense."""
        client = TestClient(app)

        # emp1 submits and mgr1 approves
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        # fin1 rejects
        response = client.patch(
            f"/expenses/{expense_id}/reject",
            json={"rejection_reason": "Policy violation"},
            headers={"Authorization": "Bearer fin1:finance"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Policy violation"

    def test_finance_process_approved_expense(self, setup_approval_env):
        """Finance can mark approved_by_finance expense as processed."""
        client = TestClient(app)

        # emp1 submits, mgr1 approves, fin1 approves
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer fin1:finance"},
        )

        # fin1 processes
        response = client.patch(
            f"/expenses/{expense_id}/process",
            headers={"Authorization": "Bearer fin1:finance"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"

    def test_finance_cannot_process_unapproved_expense(self, setup_approval_env):
        """Finance cannot process expense not approved by finance."""
        client = TestClient(app)

        # emp1 submits and mgr1 approves but fin1 doesn't
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 100.0,
                "category": "Travel",
                "description": "Flight",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )

        # fin1 tries to process without approving first
        response = client.patch(
            f"/expenses/{expense_id}/process",
            headers={"Authorization": "Bearer fin1:finance"},
        )

        assert response.status_code == 400


class TestCompleteWorkflow:
    def test_complete_approval_workflow(self, setup_approval_env):
        """Test complete workflow: submit → manager approve → finance approve → process."""
        client = TestClient(app)

        # 1. Employee submits
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 250.0,
                "category": "Equipment",
                "description": "Laptop",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/laptop.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        assert submit_response.status_code == 201
        expense_id = submit_response.json()["id"]
        assert submit_response.json()["status"] == "pending"

        # 2. Manager approves
        approve_response = client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer mgr1:manager"},
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved_by_manager"

        # 3. Finance approves
        finance_approve = client.patch(
            f"/expenses/{expense_id}/approve",
            headers={"Authorization": "Bearer fin1:finance"},
        )
        assert finance_approve.status_code == 200
        assert finance_approve.json()["status"] == "approved_by_finance"

        # 4. Finance processes
        process_response = client.patch(
            f"/expenses/{expense_id}/process",
            headers={"Authorization": "Bearer fin1:finance"},
        )
        assert process_response.status_code == 200
        assert process_response.json()["status"] == "processed"

        # 5. Check audit trail
        history = process_response.json()["history"]
        assert len(history) >= 4  # Submit + mgr approve + fin approve + process
        statuses = [h["status_to"] for h in history]
        assert "pending" in statuses
        assert "approved_by_manager" in statuses
        assert "approved_by_finance" in statuses
        assert "processed" in statuses

    def test_rejection_workflow(self, setup_approval_env):
        """Test workflow with rejection: submit → manager reject → employee sees reason."""
        client = TestClient(app)

        # 1. Employee submits
        submit_response = client.post(
            "/expenses",
            json={
                "amount": 500.0,
                "category": "Travel",
                "description": "Conference",
                "expense_date": str(date.today()),
                "receipt_url": "https://example.com/conference.pdf",
            },
            headers={"Authorization": "Bearer emp1:employee"},
        )
        expense_id = submit_response.json()["id"]

        # 2. Manager rejects with reason
        reject_response = client.patch(
            f"/expenses/{expense_id}/reject",
            json={"rejection_reason": "Exceeds quarterly limit"},
            headers={"Authorization": "Bearer mgr1:manager"},
        )
        assert reject_response.status_code == 200
        data = reject_response.json()
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Exceeds quarterly limit"

        # 3. Employee retrieves expense and sees rejection reason
        detail_response = client.get(
            f"/expenses/{expense_id}",
            headers={"Authorization": "Bearer emp1:employee"},
        )
        assert detail_response.status_code == 200
        employee_view = detail_response.json()
        assert employee_view["status"] == "rejected"
        assert employee_view["rejection_reason"] == "Exceeds quarterly limit"

        # 4. Check audit trail shows rejection
        history = employee_view["history"]
        rejection_entries = [h for h in history if h["status_to"] == "rejected"]
        assert len(rejection_entries) > 0
        assert rejection_entries[0]["comment"] == "Exceeds quarterly limit"
