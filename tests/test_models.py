import pytest
from pydantic import ValidationError
from app.models import Expense, ExpenseStatus, ExpenseSubmit, ExpenseReject


def test_expense_creation():
    expense = Expense(
        employee_id="emp_123",
        amount=100.0,
        description="Test expense"
    )
    assert expense.status == ExpenseStatus.SUBMITTED
    assert expense.amount == 100.0
    assert expense.description == "Test expense"


def test_expense_submit_valid():
    submit = ExpenseSubmit(amount=150.50, description="Conference ticket")
    assert submit.amount == 150.50
    assert submit.description == "Conference ticket"


def test_expense_submit_negative_amount():
    with pytest.raises(ValidationError):
        ExpenseSubmit(amount=-50, description="Invalid")


def test_expense_submit_zero_amount():
    with pytest.raises(ValidationError):
        ExpenseSubmit(amount=0, description="Invalid")


def test_expense_submit_exceeds_max():
    with pytest.raises(ValidationError):
        ExpenseSubmit(amount=150000, description="Too much")


def test_expense_submit_empty_description():
    with pytest.raises(ValidationError):
        ExpenseSubmit(amount=100, description="")


def test_expense_submit_description_too_long():
    with pytest.raises(ValidationError):
        ExpenseSubmit(amount=100, description="x" * 501)


def test_expense_reject_requires_notes():
    with pytest.raises(ValidationError):
        ExpenseReject(manager_notes=None)


def test_expense_reject_notes_too_long():
    with pytest.raises(ValidationError):
        ExpenseReject(manager_notes="x" * 501)
