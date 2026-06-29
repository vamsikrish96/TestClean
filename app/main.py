from fastapi import FastAPI
from app.database import ExpenseStore

app = FastAPI(title="Expense Approval Workflow API", version="1.0.0")

store = ExpenseStore()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
