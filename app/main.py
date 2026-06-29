from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from app.database import ExpenseStore
from app.auth import get_current_user, require_role, TokenPayload
from app.models import Expense, ExpenseStatus, ExpenseSubmit

app = FastAPI(title="Expense Approval Workflow API", version="1.0.0")

_default_store = ExpenseStore()


def get_store() -> ExpenseStore:
    return _default_store


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/auth-check")
async def auth_check(token: TokenPayload = Depends(get_current_user)):
    return {"user_id": token.user_id, "role": token.role}


@app.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def submit_expense(
    submit_data: ExpenseSubmit,
    token: TokenPayload = Depends(require_role("employee")),
    store: ExpenseStore = Depends(get_store)
):
    expense = Expense(
        employee_id=token.user_id,
        amount=submit_data.amount,
        description=submit_data.description,
        status=ExpenseStatus.SUBMITTED,
        submitted_date=datetime.now(timezone.utc)
    )
    created = store.create(expense)
    return created
