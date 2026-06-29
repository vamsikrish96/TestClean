from fastapi import FastAPI, Depends
from app.database import ExpenseStore
from app.auth import get_current_user, require_role, TokenPayload

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
