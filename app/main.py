from fastapi import FastAPI
from app.api import expenses, approvals

app = FastAPI(title="Expense Approval Workflow API", version="1.0.0")

# Include routers
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
app.include_router(approvals.router, prefix="/expenses", tags=["approvals"])


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Expense Approval Workflow API is running"}
