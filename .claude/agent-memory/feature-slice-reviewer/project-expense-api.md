---
name: project-expense-api
description: Expense Approval Workflow API — FastAPI project at C:\workspace\WithPlanCleanCode, reviewed through Slice 4
metadata:
  type: project
---

Python FastAPI project for an Expense Approval Workflow. Root at `C:\workspace\WithPlanCleanCode`.

Tech stack: FastAPI, Pydantic v2 (BaseModel), pytest, Python threading (RLock intended but not yet in the store as of Slice 1).

Architecture layers observed (Slice 1): models (Pydantic BaseModel) → database (ExpenseStore in-memory dict) → auth (base64 mock token parsing) → main (FastAPI routes). No separate service layer or exception hierarchy in this version.

**Why:** Learning/demo project built slice-by-slice, with a clean-code review gate before proceeding. Mock Entra ID auth (base64 JSON tokens) is intentional.

**How to apply:** Suggest improvements that fit within this layered architecture. Focus on clean code principles (naming, SRP, null handling, test quality), not production security of the mock auth scheme.

Key patterns observed:
- `ExpenseStore` uses a module-level singleton in `main.py`; no DI container
- `Expense` Pydantic model holds a `version` field that is mutated by the store (coupling concern)
- No custom exception hierarchy — HTTPException raised directly in auth functions
- `conftest.py` `store` fixture is broken/unused — `test_database.py` defines its own local fixture
- `list_by_approved()` in database.py is a redundant specialisation of `list_by_status()`
- Thread safety (RLock) was planned but not implemented in Slice 1
