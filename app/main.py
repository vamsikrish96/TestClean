from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Query
from app.database import ExpenseStore
from app.auth import get_current_user, require_role, TokenPayload
from app.models import Expense, ExpenseStatus, ExpenseSubmit
from typing import List

app = FastAPI(title="Expense Approval Workflow API", version="1.0.0")

store = ExpenseStore()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/auth-check")
async def auth_check(token: TokenPayload = Depends(get_current_user)):
    return {"user_id": token.user_id, "role": token.role}


@app.get("/employee-only")
async def employee_only(token: TokenPayload = Depends(require_role("employee"))):
    return {"message": f"Hello {token.user_id}, you have employee access"}


@app.get("/manager-only")
async def manager_only(token: TokenPayload = Depends(require_role("manager"))):
    return {"message": f"Hello {token.user_id}, you have manager access"}


@app.get("/finance-only")
async def finance_only(token: TokenPayload = Depends(require_role("finance"))):
    return {"message": f"Hello {token.user_id}, you have finance access"}


@app.post("/expenses", response_model=Expense)
async def submit_expense(
    submit_data: ExpenseSubmit,
    token: TokenPayload = Depends(require_role("employee"))
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
async def list_expenses(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role("employee"))
):
    all_expenses = store.list_by_employee(token.user_id)
    return all_expenses[offset:offset + limit]


@app.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(
    expense_id: str,
    token: TokenPayload = Depends(require_role("employee"))
):
    expense = store.get(expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    if expense.employee_id != token.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return expense
