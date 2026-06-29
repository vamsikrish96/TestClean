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


@app.get("/expenses", response_model=List[Expense])
async def list_own_expenses(
    limit: int = 50,
    offset: int = 0,
    token: TokenPayload = Depends(require_role("employee")),
    store: ExpenseStore = Depends(get_store)
):
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="offset must be >= 0")

    all_expenses = store.list_by_employee(token.user_id)
    return all_expenses[offset:offset + limit]


@app.get("/expenses/{expense_id}", response_model=Expense)
async def view_expense_detail(
    expense_id: str,
    token: TokenPayload = Depends(require_role("employee")),
    store: ExpenseStore = Depends(get_store)
):
    try:
        expense = store.get(expense_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if expense.employee_id != token.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return expense
