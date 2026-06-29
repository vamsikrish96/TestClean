---
name: project-expense-api
description: Expense Approval Workflow API — FastAPI project under expense_api/, first 3 slices reviewed
metadata:
  type: project
---

Python FastAPI project for an Expense Approval Workflow. Root at `C:\workspace\WithPlanCleanCode\expense_api\`.

Tech stack: FastAPI 0.104.1, Pydantic v2 (2.5.0), pytest 7.4.3, Python dataclasses for domain models, threading.RLock for in-memory store.

Architecture layers observed: models (dataclasses) → schemas (Pydantic) → store (in-memory, thread-safe) → services (pure functions) → routers (FastAPI). No database; uses a module-level singleton MemoryStore.

**Why:** This is a learning/demo project built slice-by-slice with a clean-code review gate before proceeding to the next slices.

**How to apply:** Suggest improvements that fit within this layered architecture. The mock Entra ID auth is intentional and known to be non-production. Focus real security feedback on things that would survive into a real implementation (exception breadth, missing validation, data type correctness).

Key patterns:
- Exception hierarchy in `app/exceptions.py` — custom AppException subclasses per HTTP status
- Store methods acquire `RLock` (reentrant) per operation; some methods call other locked methods (get_user inside update_user)
- Services receive `store` as explicit parameter (dependency injection pattern) except `get_current_user` which calls `get_store()` directly
- Pydantic schemas have NOT set `from_attributes=True`, which will break `model_validate(dataclass_instance)` in v2
