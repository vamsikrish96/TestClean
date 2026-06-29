# Clean Code Review — Slice 1 (Foundation: Models, Auth, Storage)

Review date: 2026-06-29

---

## Suggestion 1: Remove Magic Number for Bearer Prefix Offset

**Location:** `app/auth.py:20`
**Clean Code Principle:** Meaningful Names / Avoid Noise — magic numbers hide intent and are fragile
**Suggested Fix:**
```python
# Before
token = authorization[7:]

# After — option A: use removeprefix (Python 3.9+)
token = authorization.removeprefix("Bearer ")

# After — option B: named constant
BEARER_PREFIX = "Bearer "
token = authorization[len(BEARER_PREFIX):]
```
**Rationale:** `7` is a silent assumption that `"Bearer "` is exactly 7 characters. If the prefix ever changes or a reader doesn't know the convention, the number is opaque. `removeprefix` makes the intent explicit and eliminates the literal entirely.

---

## Suggestion 2: Drop Unused Exception Variable

**Location:** `app/auth.py:30`
**Clean Code Principle:** Avoid Noise — unused variables are dead code
**Suggested Fix:**
```python
# Before
except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:

# After
except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
```
**Rationale:** `e` is bound but never referenced. It adds noise that makes readers look for where `e` is used — and finding it nowhere wastes their attention.

---

## Suggestion 3: Eliminate Redundant Null Guard in `get_current_user`

**Location:** `app/auth.py:37-43`
**Clean Code Principle:** Functions Do One Thing / No Duplication — the guard in `get_current_user` is already covered by `decode_token`
**Suggested Fix:**
```python
# Before
def get_current_user(authorization: Optional[str] = Header(None)) -> TokenPayload:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    return decode_token(authorization)

# After — delegate fully; decode_token already handles None/empty
def get_current_user(authorization: Optional[str] = Header(None)) -> TokenPayload:
    return decode_token(authorization or "")
```
**Rationale:** `decode_token` line 14 already guards `if not authorization`. Having two places that raise 401 for missing auth means two places to keep in sync. The outer guard is pure duplication.

---

## Suggestion 4: Make Internal Store State Private

**Location:** `app/database.py:7`
**Clean Code Principle:** Law of Demeter / Objects Hide Data — expose behavior, not internal structure
**Suggested Fix:**
```python
# Before
self.expenses: dict[str, Expense] = {}

# After
self._expenses: dict[str, Expense] = {}
```
Update all internal references to use `self._expenses`. No external callers should access the raw dict directly; they should go through `get()`, `list_all()`, etc.

**Rationale:** A public `expenses` dict invites callers to bypass the store's methods and manipulate state directly, breaking encapsulation. Prefixing with `_` signals the contract clearly.

---

## Suggestion 5: Remove Redundant `list_by_approved` Method

**Location:** `app/database.py:30-31`
**Clean Code Principle:** Avoid Noise / DRY — the method is a thin wrapper around existing behaviour
**Suggested Fix:**
```python
# Remove entirely:
def list_by_approved(self) -> List[Expense]:
    return [exp for exp in self.expenses.values() if exp.status == ExpenseStatus.APPROVED]

# Callers use instead:
store.list_by_status(ExpenseStatus.APPROVED)
```
**Rationale:** `list_by_approved()` is exactly `list_by_status(ExpenseStatus.APPROVED)`. Having a dedicated method for every possible status value would produce unbounded noise. The generic `list_by_status` already covers this case. Remove the specialisation.

---

## Suggestion 6: Raise Exception Instead of Returning `None` from `update`

**Location:** `app/database.py:33-38`
**Clean Code Principle:** Never Return Null — callers should not need to null-check every write operation
**Suggested Fix:**
```python
# Before
def update(self, expense_id: str, expense: Expense) -> Optional[Expense]:
    if expense_id in self.expenses:
        expense.version += 1
        self.expenses[expense_id] = expense
        return expense
    return None

# After
def update(self, expense_id: str, expense: Expense) -> Expense:
    if expense_id not in self._expenses:
        raise KeyError(f"Expense '{expense_id}' not found")
    expense.version += 1
    self._expenses[expense_id] = expense
    return expense
```
**Rationale:** Returning `None` from a write operation forces every caller to guard against `None`. A `KeyError` (or a domain-specific `ExpenseNotFoundError`) makes the failure explicit and lets callers handle a true error condition, not a silent absence.

---

## Suggestion 7: Stop Mutating the Caller's Input Object in `update`

**Location:** `app/database.py:35`
**Clean Code Principle:** Command Query Separation / Predictable Functions — mutating input arguments is a hidden side effect
**Suggested Fix:**
```python
# Before — mutates the caller's object in place
expense.version += 1

# After — work on a copy
updated = expense.model_copy(update={"version": expense.version + 1})
self._expenses[expense_id] = updated
return updated
```
**Rationale:** After calling `store.update(id, my_expense)`, the caller's `my_expense` object has had its `version` silently incremented. That is a hidden side effect that breaks the predictability of the function. Working on a copy keeps the caller's object unchanged.

---

## Suggestion 8: Remove Dead and Broken `store` Fixture from `conftest.py`

**Location:** `tests/conftest.py:15-17`
**Clean Code Principle:** Avoid Noise / Zero Dead Code — unused fixtures that are also incorrect are double noise
**Suggested Fix:**
```python
# Remove entirely — no test file references this fixture,
# and it assigns to app.store (a FastAPI attribute) rather than
# the module-level `store` used by route handlers in main.py.
@pytest.fixture
def store():
    app.store = ExpenseStore()
    return app.store
```
**Rationale:** The fixture is never imported or used by any test. Additionally, it sets `app.store` (an attribute on the FastAPI object) while `main.py` uses a module-level `store` variable — so even if a test did use it, it would not reset the store the routes actually read from. Dead code that is also misleading is the worst kind.

---

## Suggestion 9: Assert Specific Exception Type in Auth Tests

**Location:** `tests/test_auth.py:21, 25, 32, 36, 40, 42`
**Clean Code Principle:** Single Concept Per Test / Self-Validating — a test that accepts any `Exception` does not validate the specific failure contract
**Suggested Fix:**
```python
# Before — too broad
with pytest.raises(Exception):
    decode_token(encoded)

# After — verify the exact HTTP error contract
from fastapi import HTTPException

with pytest.raises(HTTPException) as exc_info:
    decode_token(encoded)
assert exc_info.value.status_code == 401
```
**Rationale:** `pytest.raises(Exception)` passes even if `decode_token` raises a `TypeError`, `AttributeError`, or any other unrelated error. The tests should validate the specific contract: an `HTTPException` with a 401 status code. Otherwise they give false confidence that error handling is correct when it might simply be crashing.
