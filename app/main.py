from fastapi import FastAPI, Depends
from app.database import ExpenseStore
from app.auth import get_current_user, TokenPayload

app = FastAPI(title="Expense Approval Workflow API", version="1.0.0")

store = ExpenseStore()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/auth-check")
async def auth_check(token: TokenPayload = Depends(get_current_user)):
    return {"user_id": token.user_id, "role": token.role}
