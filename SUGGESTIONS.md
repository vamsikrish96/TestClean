# Clean Code Review — Slice 1: Foundation

Reviewed against [Clean Code principles](/clean-code). Only meaningful violations are listed; style-only observations are excluded.

---

## Suggestion 1: Extract Duplicated Guard Pattern in ApprovalService

**Location:** `app/services.py:91-95`, `117-121`, `144-148`, `170-174`, `197-201`

**Clean Code Principle:** DRY (Don't Repeat Yourself) — every approval and rejection method opens with an identical fetch-and-validate block that changes only the expected status value.

**Suggested Fix:**

```python
def _get_expense_in_status(self, expense_id: str, expected_status: ExpenseStatus) -> Expense:
    expense = self.expense_repo.get_by_id(expense_id)
    if not expense:
        raise ValueError("Expense not found")
    if expense.status != expected_status:
        raise ValueError(f"Cannot transition expense from {expense.status} status")
    return expense
```

Then each method reduces to:
```python
def approve_as_manager(self, expense_id: str, manager_id: str) -> Expense:
    expense = self._get_expense_in_status(expense_id, ExpenseStatus.PENDING)
    ...
```

**Rationale:** The guard pattern is copy-pasted verbatim five times. A change to the error message or logic (e.g., adding logging) must be applied in five places. Extracting it to a private helper gives it one reason to change.

---

## Suggestion 2: Use Constructor Injection Instead of Module-Level Singletons

**Location:** `app/repositories.py:87-89`, `app/services.py:11-13`, `86-87`, `222-223`

**Clean Code Principle:** F.I.R.S.T. Tests — **Independent**: tests must not share state. Dependency injection enables fresh instances per test.

**Current problem:**
```python
# repositories.py
expense_repo = ExpenseRepository()   # module-level singleton
history_repo = ExpenseHistoryRepository()

# services.py
class ExpenseService:
    def __init__(self):
        self.expense_repo = expense_repo  # grabs the singleton
```

`TestExpenseService` and `TestApprovalService` both silently share the same `expense_repo` instance. Expenses submitted in one test are visible to subsequent tests — a hidden ordering dependency.

**Suggested Fix:**

```python
class ExpenseService:
    def __init__(
        self,
        expense_repo: ExpenseRepository,
        history_repo: ExpenseHistoryRepository,
    ):
        self.expense_repo = expense_repo
        self.history_repo = history_repo
```

Tests then instantiate their own clean repos:
```python
def test_submit_expense():
    service = ExpenseService(ExpenseRepository(), ExpenseHistoryRepository())
    ...
```

Wire the shared instances in a FastAPI dependency function rather than at import time.

**Rationale:** Module-level mutable singletons are global state. They are the primary reason tests are order-dependent and hard to isolate.

---

## Suggestion 3: `Expense.expense_date` Type Mismatch with Schema

**Location:** `app/models.py:47`, `app/schemas.py:21`, `app/schemas.py:38`

**Clean Code Principle:** Meaningful Names / Type Hints — a field typed as `str` but treated as `date` in schemas misleads readers and bypasses type-checker safety.

**Current state:**
```python
# models.py
expense_date: str   # <-- str

# schemas.py
expense_date: date  # <-- date object (validated, not future)
```

The validator in `ExpenseCreateSchema` enforces `date` semantics, but the domain model accepts any string — including `"not-a-date"`. The mismatch means services receive a `date` object from Pydantic but store it as a `str` in the model (or silently coerce it).

**Suggested Fix:**
```python
# models.py
from datetime import date

@dataclass
class Expense:
    ...
    expense_date: date   # matches the schema type
```

**Rationale:** Type consistency between schema and domain model ensures the validator's guarantees flow through the entire system rather than stopping at the API boundary.

---

## Suggestion 4: `get_expense_with_history` Returns `Optional[dict]` with Magic String Keys

**Location:** `app/services.py:73-79`

**Clean Code Principle:** Meaningful Names / Data Structures — raw `dict` with string keys is an untyped contract; callers must know the key names `"expense"` and `"history"` without compiler or IDE help.

**Current state:**
```python
def get_expense_with_history(self, expense_id: str) -> Optional[dict]:
    ...
    return {"expense": expense, "history": history}
```

**Suggested Fix:** Define a small dataclass:
```python
@dataclass
class ExpenseWithHistory:
    expense: Expense
    history: List[ExpenseHistory]
```

Then:
```python
def get_expense_with_history(self, expense_id: str) -> Optional[ExpenseWithHistory]:
    expense = self.expense_repo.get_by_id(expense_id)
    if not expense:
        return None
    history = self.history_repo.get_by_expense_id(expense_id)
    return ExpenseWithHistory(expense=expense, history=history)
```

**Rationale:** Typed return values make the contract explicit, enable autocomplete, and eliminate the magic string keys `"expense"` and `"history"` that callers currently depend on.

---

## Suggestion 5: Two `datetime.utcnow()` Calls Per Transaction Create Timestamp Drift

**Location:** `app/services.py:99+109`, `124+135`, `152+163`, `178+189`, `204+213`

**Clean Code Principle:** Functions Do One Thing — the timestamp used to record `expense.updated_at` and `history.changed_at` should be the same instant. Currently two separate calls can return different microseconds.

**Example (approve_as_manager):**
```python
expense.updated_at = datetime.utcnow()   # call 1 (line 99)
...
history = ExpenseHistory(
    ...
    changed_at=datetime.utcnow(),        # call 2 (line 109) — potentially different
)
```

**Suggested Fix:** Capture once at method entry:
```python
def approve_as_manager(self, expense_id: str, manager_id: str) -> Expense:
    now = datetime.utcnow()
    expense = self._get_expense_in_status(expense_id, ExpenseStatus.PENDING)
    expense.status = ExpenseStatus.APPROVED_BY_MANAGER
    expense.approved_by = manager_id
    expense.updated_at = now
    self.expense_repo.update(expense)
    self.history_repo.create(ExpenseHistory(..., changed_at=now))
    return expense
```

**Rationale:** The history entry is supposed to record when the expense changed. If `changed_at != expense.updated_at`, audit queries will produce confusing results.

---

## Suggestion 6: `init_test_data()` Must Not Run at Production Startup

**Location:** `app/main.py:12-15`, `app/repositories.py:92-99`

**Clean Code Principle:** Single Responsibility Principle — the application's startup event is responsible for wiring the app, not seeding fictional test users.

**Current state:**
```python
@app.on_event("startup")
def startup_event():
    init_test_data()  # runs "Alice Employee", "Bob Employee", etc. in production
```

**Suggested Fix:** Remove the `startup_event` entirely (or make it a no-op). Move `init_test_data()` to a `conftest.py` fixture that runs only during tests, or to an explicit `seed.py` CLI script for local development.

```python
# tests/conftest.py
import pytest
from app.repositories import UserRepository, init_test_users

@pytest.fixture
def seeded_user_repo():
    repo = UserRepository()
    init_test_users(repo)
    return repo
```

**Rationale:** Every production deployment currently starts with hardcoded test users. Any code path that loads user data from the repository will return `emp1`, `emp2`, `mgr1`, `fin1` in production — unintended behavior that is also untestable because the startup hook runs implicitly.

---

## Suggestion 7: Remove Dead `ApprovalSchema`

**Location:** `app/schemas.py:58-60`

**Clean Code Principle:** Zero Noise — dead code left in place signals ambiguity about whether it is intentional or forgotten.

**Current state:**
```python
class ApprovalSchema(BaseModel):
    action: str          # no validation, no consumer
    timestamp: datetime  # never populated anywhere
```

This schema has no endpoint, no serialization call, and no tests. `action: str` is too vague to be useful as-is.

**Suggested Fix:** Delete the class. If an approval-action response schema is needed in a later slice, define it there with the correct fields.

**Rationale:** Unused code adds cognitive load — readers spend time wondering whether it is intentional scaffolding, a mistake, or a hint about future behaviour.

---

## Suggestion 8: Make Repository Internal Storage Private

**Location:** `app/repositories.py:11`, `49`, `66`

**Clean Code Principle:** Objects Hide Internal State — a public `storage` attribute invites callers to bypass the repository's query interface and manipulate the dict directly.

**Current state:**
```python
class ExpenseRepository:
    def __init__(self):
        self.storage: Dict[str, Expense] = {}  # public
```

**Suggested Fix:**
```python
class ExpenseRepository:
    def __init__(self):
        self._storage: Dict[str, Expense] = {}

    def create(self, expense: Expense) -> Expense:
        self._storage[expense.id] = expense
        return expense
    # ... etc.
```

**Rationale:** Callers should interact only through `create`, `get_by_id`, `update`, and `list_*` methods. Exposing `storage` publicly means any code (including tests) can insert or mutate records without going through the defined interface, defeating the repository abstraction.

---

## Suggestion 9: Extract Expense Test Fixture to Eliminate Repetition

**Location:** `tests/test_foundation.py:46-55`, `62-79`, `87-97`, `109-116`, `172-179`, `187-194`, `206-213`, `240-247`

**Clean Code Principle:** DRY — the same `Expense(...)` construction (7 required keyword arguments) is copy-pasted across at least eight test methods.

**Suggested Fix:** Add a factory function (or pytest fixture) at the top of the test file:

```python
def make_expense(
    id: str = "exp1",
    employee_id: str = "emp1",
    amount: float = 100.0,
    category: ExpenseCategory = ExpenseCategory.TRAVEL,
    description: str = "Flight to NYC",
    expense_date: str = "2026-06-15",
    receipt_url: str = "https://example.com/receipt.pdf",
) -> Expense:
    return Expense(
        id=id,
        employee_id=employee_id,
        amount=amount,
        category=category,
        description=description,
        expense_date=expense_date,
        receipt_url=receipt_url,
    )
```

Tests then read as:
```python
expense = make_expense(id="exp2", employee_id="emp2")
```

**Rationale:** If `Expense.__init__` gains or renames a required field, every test currently needs a manual update. A factory centralises the construction in one place and makes the *variation* between test cases immediately visible.

---

## Suggestion 10: Initial History Entry Records a Meaningless No-Op Transition

**Location:** `app/services.py:44-53`

**Clean Code Principle:** Meaningful Names — `status_from=PENDING, status_to=PENDING` records "nothing changed," which misleads audit consumers.

**Current state:**
```python
history = ExpenseHistory(
    ...
    status_from=ExpenseStatus.PENDING,
    status_to=ExpenseStatus.PENDING,   # same as from — no transition
    comment="Expense submitted",
)
```

**Suggested Fix:** Allow `status_from` to be `Optional[ExpenseStatus]` (representing "did not exist before"), or add a `SUBMITTED` comment-only entry pattern:

```python
# Option A — nullable status_from to signal creation
# models.py
status_from: Optional[ExpenseStatus]

# services.py
history = ExpenseHistory(
    status_from=None,
    status_to=ExpenseStatus.PENDING,
    comment="Expense submitted",
    ...
)
```

**Rationale:** An audit trail where `from == to` looks like a data error to anyone querying the history. The initial submission is a creation event, not a status transition, and the history entry should reflect that.
