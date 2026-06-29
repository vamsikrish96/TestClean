import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models.expense import ExpenseCreate, create_expense


class TestExpenseCreate:
    def test_valid_expense_creation(self):
        data = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight to NYC",
            "date_submitted": datetime.utcnow(),
        }
        expense = ExpenseCreate(**data)
        assert expense.amount == 100.0
        assert expense.category == "Travel"
        assert expense.description == "Flight to NYC"

    def test_invalid_amount_negative(self):
        data = {
            "amount": -100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow(),
        }
        with pytest.raises(ValidationError) as exc_info:
            ExpenseCreate(**data)
        assert "Amount must be greater than 0" in str(exc_info.value)

    def test_invalid_amount_zero(self):
        data = {
            "amount": 0.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow(),
        }
        with pytest.raises(ValidationError):
            ExpenseCreate(**data)

    def test_invalid_category(self):
        data = {
            "amount": 100.0,
            "category": "InvalidCategory",
            "description": "Flight",
            "date_submitted": datetime.utcnow(),
        }
        with pytest.raises(ValidationError) as exc_info:
            ExpenseCreate(**data)
        assert "Category must be one of" in str(exc_info.value)

    def test_valid_categories(self):
        categories = ["Travel", "Meals", "Equipment", "Other"]
        for cat in categories:
            data = {
                "amount": 100.0,
                "category": cat,
                "description": "Test",
                "date_submitted": datetime.utcnow(),
            }
            expense = ExpenseCreate(**data)
            assert expense.category == cat

    def test_empty_description(self):
        data = {
            "amount": 100.0,
            "category": "Travel",
            "description": "",
            "date_submitted": datetime.utcnow(),
        }
        with pytest.raises(ValidationError):
            ExpenseCreate(**data)

    def test_whitespace_description(self):
        data = {
            "amount": 100.0,
            "category": "Travel",
            "description": "   ",
            "date_submitted": datetime.utcnow(),
        }
        with pytest.raises(ValidationError):
            ExpenseCreate(**data)

    def test_optional_fields(self):
        data = {
            "amount": 100.0,
            "category": "Travel",
            "description": "Flight",
            "date_submitted": datetime.utcnow(),
            "receipt_url": "https://example.com/receipt.pdf",
            "project_code": "PRJ001",
            "department": "Engineering",
        }
        expense = ExpenseCreate(**data)
        assert expense.receipt_url == "https://example.com/receipt.pdf"
        assert expense.project_code == "PRJ001"
        assert expense.department == "Engineering"


class TestCreateExpenseFactory:
    def test_create_expense_populates_fields(self):
        now = datetime.utcnow()
        expense = create_expense(
            employee_id="emp123",
            amount=150.0,
            category="Meals",
            description="Team lunch",
            date_submitted=now,
        )
        assert expense.expense_id is not None
        assert expense.employee_id == "emp123"
        assert expense.amount == 150.0
        assert expense.category == "Meals"
        assert expense.description == "Team lunch"
        assert expense.status == "SUBMITTED"
        assert expense.created_at is not None
        assert expense.updated_at is not None

    def test_create_expense_generates_unique_ids(self):
        now = datetime.utcnow()
        expense1 = create_expense(
            employee_id="emp1",
            amount=100.0,
            category="Travel",
            description="Trip",
            date_submitted=now,
        )
        expense2 = create_expense(
            employee_id="emp2",
            amount=100.0,
            category="Travel",
            description="Trip",
            date_submitted=now,
        )
        assert expense1.expense_id != expense2.expense_id
