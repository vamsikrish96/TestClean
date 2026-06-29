from enum import Enum


class ExpenseStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    MANAGER_PENDING = "MANAGER_PENDING"
    FINANCE_PENDING = "FINANCE_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ExpenseCategory(str, Enum):
    TRAVEL = "Travel"
    MEALS = "Meals"
    EQUIPMENT = "Equipment"
    OTHER = "Other"


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    FINANCE = "finance"


VALID_CATEGORIES = [c.value for c in ExpenseCategory]
VALID_ROLES = [r.value for r in UserRole]
