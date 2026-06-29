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

---

# Clean Code Review — Slice 2 (Employee Submit Expense: POST /expenses)

Review date: 2026-06-29

Reviewed files: `app/main.py`, `tests/test_submit_expense.py`, `tests/conftest.py`

---

## Suggestion 10: `client` Fixture Resets `app.store`, Not the Module-Level `store` the Endpoint Uses

**Location:** `tests/conftest.py:11` / `app/main.py:10, 35`

**Clean Code Principle:** F.I.R.S.T. — **Independent** — no test should depend on the state left by another

**The Problem:**

```python
# conftest.py:11 — sets an attribute on the FastAPI app object
app.store = ExpenseStore()

# main.py:10 — module-level variable, created once at import time
store = ExpenseStore()

# main.py:35 — endpoint calls the module-level variable; app.store is never read
created = store.create(expense)
```

Setting `app.store` is a no-op: the endpoint closure captures the module-level `store`, not
the attribute on `app`. Every test in the suite accumulates state in the same store instance.

**Suggested Fix:** Use FastAPI's dependency-override mechanism so the fixture controls what
the endpoint actually receives:

```python
# app/main.py
store = ExpenseStore()

def get_store() -> ExpenseStore:
    return store

@app.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def submit_expense(
    submit_data: ExpenseSubmit,
    token: TokenPayload = Depends(require_role("employee")),
    expense_store: ExpenseStore = Depends(get_store),
):
    expense = Expense(
        employee_id=token.user_id,
        amount=submit_data.amount,
        description=submit_data.description,
        status=ExpenseStatus.SUBMITTED,
        submitted_date=datetime.now(timezone.utc),
    )
    return expense_store.create(expense)
```

```python
# tests/conftest.py
from app.main import app, get_store

@pytest.fixture
def client():
    fresh_store = ExpenseStore()
    app.dependency_overrides[get_store] = lambda: fresh_store
    yield TestClient(app)
    app.dependency_overrides.clear()
```

**Rationale:** Without this, tests are order-dependent. Whichever test runs first gets ID
`exp_000001`; subsequent tests get higher counters. Adding a new test at the top of the
file silently breaks assertions in all tests below it.

---

## Suggestion 11: Magic String `"exp_000001"` Encodes Hidden Ordering Assumption

**Location:** `tests/test_submit_expense.py:18`

**Clean Code Principle:** No Magic Values — unexplained literals encode hidden assumptions and couple tests to implementation details

**The Problem:**

```python
assert data["id"] == "exp_000001"
```

This encodes two facts that belong to the implementation, not the behavioral contract:
1. The store counter starts at 1.
2. The ID is zero-padded to 6 digits.

If the store is not reset (see Suggestion 10), this assertion breaks on any test that creates
an expense before it.

**Suggested Fix:** Assert the structural contract — that an ID was assigned — not the
exact value:

```python
assert data["id"] is not None
assert data["id"].startswith("exp_")
```

If the zero-padding format is a public contract worth testing, do so in a dedicated store
unit test, not in the HTTP endpoint test.

**Rationale:** Assertions against internal counter values couple the test to the store's
private counter. They will fail on any refactor of ID generation even when the API contract
is unchanged.

---

## Suggestion 12: `test_submit_valid_expense` Tests Multiple Concepts in One Function

**Location:** `tests/test_submit_expense.py:4-19`

**Clean Code Principle:** Single Concept Per Test — one test, one reason to fail

**The Problem:**

`test_submit_valid_expense` makes six assertions covering distinct behavioral outcomes:

```python
assert data["employee_id"] == "emp_001"          # token claim is mapped to expense
assert data["amount"] == 150.50                   # input fields are echoed
assert data["description"] == "Conference ticket" # input fields are echoed
assert data["status"] == ExpenseStatus.SUBMITTED  # initial status is set correctly
assert data["id"] == "exp_000001"                 # ID is assigned (+ magic value)
assert data["submitted_date"] is not None         # timestamp is stamped
```

A failure message says "AssertionError" but does not identify which behavioral contract
broke.

**Suggested Fix:** Break into focused tests named after what they verify:

```python
def test_submit_expense_maps_employee_id_from_token(client, employee_token):
    data = _submit_valid(client, employee_token)
    assert data["employee_id"] == "emp_001"

def test_submit_expense_sets_status_to_submitted(client, employee_token):
    data = _submit_valid(client, employee_token)
    assert data["status"] == ExpenseStatus.SUBMITTED

def test_submit_expense_stamps_submitted_date(client, employee_token):
    data = _submit_valid(client, employee_token)
    assert data["submitted_date"] is not None

def test_submit_expense_echoes_input_fields(client, employee_token):
    payload = {"amount": 150.50, "description": "Conference ticket"}
    data = client.post("/expenses", json=payload, headers={"Authorization": employee_token}).json()
    assert data["amount"] == 150.50
    assert data["description"] == "Conference ticket"

def _submit_valid(client, token):
    return client.post(
        "/expenses",
        json={"amount": 100, "description": "Test"},
        headers={"Authorization": token},
    ).json()
```

**Rationale:** Each test name now documents the behavioral contract in plain English. A
failing test immediately identifies which contract broke without reading the assertion body.

---

## Suggestion 13: Duplicate Tests Add Noise Without Adding Coverage

**Location:** `tests/test_submit_expense.py:152-162` and `164-173`

**Clean Code Principle:** Eliminate Noise / DRY — redundant tests increase maintenance burden without increasing confidence

**The Problem:**

`test_submit_stores_with_submitted_status` (line 152) and `test_employee_id_from_token`
(line 164) each assert a single fact already asserted by `test_submit_valid_expense`:

- line 152-162 duplicates `test_submit_valid_expense:17` (`status == SUBMITTED`)
- line 164-173 duplicates `test_submit_valid_expense:14` (`employee_id == "emp_001"`)

**Suggested Fix:** Delete both functions. After splitting `test_submit_valid_expense` per
Suggestion 12, these behaviors will each have a dedicated, named test.

**Rationale:** Duplicate assertions mean a behavior change requires updating multiple tests.
They also mislead readers into thinking these are testing something distinct when they are not.

---

## Suggestion 14: POST /expenses Returns 200 Instead of 201 Created

**Location:** `app/main.py:23`

**Clean Code Principle:** Intention-Revealing Code — the response code is part of the API contract and must reflect what actually happened

**The Problem:**

```python
@app.post("/expenses", response_model=Expense)  # defaults to 200 OK
```

RFC 9110 (HTTP Semantics) defines `201 Created` for successful resource creation. Returning
`200 OK` signals that a query was answered, not that a resource was created. Clients using
the status code to distinguish creation from retrieval will misread the response.

**Suggested Fix:**

```python
from fastapi import status

@app.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
```

Update test assertions from `== 200` to `== 201` in `test_submit_expense.py:12` and
`test_submit_max_valid_amount:125` and `test_submit_max_description_length:137`.

**Rationale:** HTTP status codes are the API's vocabulary. Using `200` where `201` is
correct is the equivalent of a function named `get` that also creates a record — the
name contradicts the behavior.

---

## Suggestion 15: Identical Role-Forbidden Tests Should Be Parameterized

**Location:** `tests/test_submit_expense.py:98-115`

**Clean Code Principle:** DRY / Eliminate Noise — copy-pasted test functions diverge silently over time

**The Problem:**

`test_submit_as_manager_forbidden` and `test_submit_as_finance_forbidden` differ only in
the fixture they use. Adding a third non-employee role requires copy-pasting a third function.

**Suggested Fix:**

```python
@pytest.mark.parametrize("token_fixture", ["manager_token", "finance_token"])
def test_submit_expense_forbidden_for_non_employees(request, client, token_fixture):
    token = request.getfixturevalue(token_fixture)
    response = client.post(
        "/expenses",
        json={"amount": 100, "description": "Test"},
        headers={"Authorization": token},
    )
    assert response.status_code == 403
```

**Rationale:** A new role is a one-word addition to the parametrize list. Two identical
functions diverge when one is updated and the other is not, eroding test reliability silently.

---

## Slice 2 Summary

| # | Severity | Location | Principle |
|---|----------|----------|-----------|
| 10 | High | `conftest.py:11` / `main.py:10,35` | F.I.R.S.T. Independent |
| 11 | High | `test_submit_expense.py:18` | No Magic Values |
| 12 | Medium | `test_submit_expense.py:4-19` | Single Concept Per Test |
| 13 | Medium | `test_submit_expense.py:152-173` | Eliminate Noise / DRY |
| 14 | Medium | `main.py:23` | Intention-Revealing Code |
| 15 | Low | `test_submit_expense.py:98-115` | DRY |
