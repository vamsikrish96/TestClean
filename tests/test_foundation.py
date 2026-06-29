import pytest
from datetime import date
from app.models import (
    Expense,
    ExpenseHistory,
    User,
    UserRole,
    ExpenseStatus,
    ExpenseCategory,
)
from app.repositories import ExpenseRepository, ExpenseHistoryRepository, UserRepository
from app.auth import parse_mocked_token, get_current_user
from app.services import ExpenseService, ApprovalService
from app.schemas import CurrentUserSchema
from fastapi import HTTPException


class TestUserModel:
    def test_user_creation(self):
        user = User(id="emp1", name="John", role=UserRole.EMPLOYEE, manager_id="mgr1")
        assert user.id == "emp1"
        assert user.name == "John"
        assert user.role == UserRole.EMPLOYEE
        assert user.manager_id == "mgr1"


class TestExpenseModel:
    def test_expense_creation(self):
        expense = Expense(
            id="exp1",
            employee_id="emp1",
            amount=100.0,
            category=ExpenseCategory.TRAVEL,
            description="Flight to NYC",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )
        assert expense.id == "exp1"
        assert expense.status == ExpenseStatus.PENDING
        assert expense.amount == 100.0


class TestExpenseRepository:
    def test_create_and_get_expense(self):
        repo = ExpenseRepository()
        expense = Expense(
            id="exp1",
            employee_id="emp1",
            amount=50.0,
            category=ExpenseCategory.MEALS,
            description="Lunch",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )
        repo.create(expense)
        retrieved = repo.get_by_id("exp1")
        assert retrieved is not None
        assert retrieved.id == "exp1"

    def test_list_by_employee(self):
        repo = ExpenseRepository()
        exp1 = Expense(
            id="exp1",
            employee_id="emp1",
            amount=50.0,
            category=ExpenseCategory.MEALS,
            description="Lunch",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )
        exp2 = Expense(
            id="exp2",
            employee_id="emp2",
            amount=100.0,
            category=ExpenseCategory.TRAVEL,
            description="Flight",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )
        repo.create(exp1)
        repo.create(exp2)
        emp1_expenses = repo.list_by_employee("emp1")
        assert len(emp1_expenses) == 1
        assert emp1_expenses[0].id == "exp1"

    def test_update_expense(self):
        repo = ExpenseRepository()
        expense = Expense(
            id="exp1",
            employee_id="emp1",
            amount=50.0,
            category=ExpenseCategory.MEALS,
            description="Lunch",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )
        repo.create(expense)
        expense.status = ExpenseStatus.APPROVED_BY_MANAGER
        repo.update(expense)
        updated = repo.get_by_id("exp1")
        assert updated.status == ExpenseStatus.APPROVED_BY_MANAGER


class TestExpenseHistoryRepository:
    def test_create_and_get_history(self):
        repo = ExpenseHistoryRepository()
        from datetime import datetime

        history = ExpenseHistory(
            id="hist1",
            expense_id="exp1",
            status_from=ExpenseStatus.PENDING,
            status_to=ExpenseStatus.PENDING,
            changed_by="emp1",
            changed_at=datetime.utcnow(),
            comment="Submitted",
        )
        repo.create(history)
        histories = repo.get_by_expense_id("exp1")
        assert len(histories) == 1
        assert histories[0].id == "hist1"


class TestUserRepository:
    def test_create_and_get_user(self):
        repo = UserRepository()
        user = User(id="emp1", name="John", role=UserRole.EMPLOYEE, manager_id="mgr1")
        repo.create(user)
        retrieved = repo.get_by_id("emp1")
        assert retrieved is not None
        assert retrieved.name == "John"

    def test_get_reports_for_manager(self):
        repo = UserRepository()
        mgr = User(id="mgr1", name="Manager", role=UserRole.MANAGER)
        emp1 = User(id="emp1", name="Employee1", role=UserRole.EMPLOYEE, manager_id="mgr1")
        emp2 = User(id="emp2", name="Employee2", role=UserRole.EMPLOYEE, manager_id="mgr1")
        repo.create(mgr)
        repo.create(emp1)
        repo.create(emp2)
        reports = repo.get_reports_for_manager("mgr1")
        assert len(reports) == 2


class TestMockedTokenParsing:
    def test_valid_token_parsing(self):
        token = "emp1:employee"
        user = parse_mocked_token(token)
        assert user.user_id == "emp1"
        assert user.role == UserRole.EMPLOYEE

    def test_manager_token_parsing(self):
        token = "mgr1:manager"
        user = parse_mocked_token(token)
        assert user.user_id == "mgr1"
        assert user.role == UserRole.MANAGER

    def test_finance_token_parsing(self):
        token = "fin1:finance"
        user = parse_mocked_token(token)
        assert user.user_id == "fin1"
        assert user.role == UserRole.FINANCE

    def test_invalid_token_parsing(self):
        with pytest.raises(HTTPException) as exc_info:
            parse_mocked_token("invalid_format")
        assert exc_info.value.status_code == 401


class TestExpenseService:
    def test_submit_expense(self):
        service = ExpenseService()
        expense = service.submit_expense(
            employee_id="emp1",
            amount=100.0,
            category=ExpenseCategory.TRAVEL,
            description="Flight",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )
        assert expense.id is not None
        assert expense.status == ExpenseStatus.PENDING
        assert expense.employee_id == "emp1"

    def test_get_expense_with_history(self):
        service = ExpenseService()
        expense = service.submit_expense(
            employee_id="emp1",
            amount=100.0,
            category=ExpenseCategory.TRAVEL,
            description="Flight",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )
        result = service.get_expense_with_history(expense.id)
        assert result is not None
        assert result["expense"].id == expense.id
        assert len(result["history"]) > 0


class TestApprovalService:
    def test_approve_as_manager(self):
        service = ApprovalService()
        expense_service = ExpenseService()

        expense = expense_service.submit_expense(
            employee_id="emp1",
            amount=100.0,
            category=ExpenseCategory.TRAVEL,
            description="Flight",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )

        approved = service.approve_as_manager(expense.id, "mgr1")
        assert approved.status == ExpenseStatus.APPROVED_BY_MANAGER
        assert approved.approved_by == "mgr1"

    def test_reject_as_manager(self):
        service = ApprovalService()
        expense_service = ExpenseService()

        expense = expense_service.submit_expense(
            employee_id="emp1",
            amount=100.0,
            category=ExpenseCategory.TRAVEL,
            description="Flight",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )

        rejected = service.reject_as_manager(expense.id, "mgr1", "Exceeds budget")
        assert rejected.status == ExpenseStatus.REJECTED
        assert rejected.rejection_reason == "Exceeds budget"

    def test_cannot_approve_non_pending_expense(self):
        service = ApprovalService()
        expense_service = ExpenseService()

        expense = expense_service.submit_expense(
            employee_id="emp1",
            amount=100.0,
            category=ExpenseCategory.TRAVEL,
            description="Flight",
            expense_date="2026-06-15",
            receipt_url="https://example.com/receipt.pdf",
        )

        service.approve_as_manager(expense.id, "mgr1")
        with pytest.raises(ValueError):
            service.approve_as_manager(expense.id, "mgr1")
