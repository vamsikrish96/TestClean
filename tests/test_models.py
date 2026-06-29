import pytest
from pydantic import ValidationError
from app.models import Expense, ExpenseStatus, ExpenseSubmit, ExpenseApprove, ExpenseReject


class TestExpenseModel:
    def test_expense_creation_with_required_fields(self):
        exp = Expense(employee_id="emp_001", amount=100.0, description="Test")
        assert exp.employee_id == "emp_001"
        assert exp.amount == 100.0
        assert exp.description == "Test"
        assert exp.status == ExpenseStatus.SUBMITTED
        assert exp.version == 1

    def test_expense_status_enum(self):
        assert ExpenseStatus.SUBMITTED == "SUBMITTED"
        assert ExpenseStatus.APPROVED == "APPROVED"
        assert ExpenseStatus.REJECTED == "REJECTED"
        assert ExpenseStatus.PROCESSED == "PROCESSED"


class TestExpenseSubmitValidation:
    def test_valid_submit(self):
        submit = ExpenseSubmit(amount=150.0, description="Conference")
        assert submit.amount == 150.0
        assert submit.description == "Conference"

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            ExpenseSubmit(amount=-50.0, description="Test")

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            ExpenseSubmit(amount=0, description="Test")

    def test_amount_exceeds_max(self):
        with pytest.raises(ValidationError):
            ExpenseSubmit(amount=100001, description="Test")

    def test_empty_description_rejected(self):
        with pytest.raises(ValidationError):
            ExpenseSubmit(amount=100.0, description="")

    def test_description_exceeds_max_length(self):
        long_desc = "a" * 501
        with pytest.raises(ValidationError):
            ExpenseSubmit(amount=100.0, description=long_desc)

    def test_description_max_length_accepted(self):
        max_desc = "a" * 500
        submit = ExpenseSubmit(amount=100.0, description=max_desc)
        assert len(submit.description) == 500


class TestExpenseApproveValidation:
    def test_approve_without_notes(self):
        approve = ExpenseApprove()
        assert approve.manager_notes is None

    def test_approve_with_notes(self):
        approve = ExpenseApprove(manager_notes="Looks good")
        assert approve.manager_notes == "Looks good"

    def test_notes_exceed_max_length(self):
        long_notes = "a" * 501
        with pytest.raises(ValidationError):
            ExpenseApprove(manager_notes=long_notes)


class TestExpenseRejectValidation:
    def test_reject_requires_notes(self):
        with pytest.raises(ValidationError):
            ExpenseReject()

    def test_reject_with_notes(self):
        reject = ExpenseReject(manager_notes="Missing receipt")
        assert reject.manager_notes == "Missing receipt"

    def test_reject_notes_too_short(self):
        with pytest.raises(ValidationError):
            ExpenseReject(manager_notes="")

    def test_reject_notes_exceed_max_length(self):
        long_notes = "a" * 501
        with pytest.raises(ValidationError):
            ExpenseReject(manager_notes=long_notes)
