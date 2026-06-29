from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


class ExpenseStatus(str, Enum):
    PENDING = "pending"
    APPROVED_BY_MANAGER = "approved_by_manager"
    APPROVED_BY_FINANCE = "approved_by_finance"
    REJECTED = "rejected"
    PROCESSED = "processed"


class ExpenseCategory(str, Enum):
    TRAVEL = "Travel"
    MEALS = "Meals"
    EQUIPMENT = "Equipment"
    OTHER = "Other"


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    FINANCE = "finance"


@dataclass
class User:
    id: str
    name: str
    role: UserRole
    manager_id: Optional[str] = None

    def __hash__(self):
        return hash(self.id)


@dataclass
class Expense:
    id: str
    employee_id: str
    amount: float
    category: ExpenseCategory
    description: str
    expense_date: str
    receipt_url: str
    status: ExpenseStatus = ExpenseStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None


@dataclass
class ExpenseHistory:
    id: str
    expense_id: str
    status_from: ExpenseStatus
    status_to: ExpenseStatus
    changed_by: str
    changed_at: datetime
    comment: Optional[str] = None
