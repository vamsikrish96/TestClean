from fastapi import FastAPI
from app.repositories import init_test_data
from app.api import expenses, approvals

app = FastAPI(title="Expense Approval Workflow API", version="1.0.0")

# Include routers
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
app.include_router(approvals.router, prefix="/expenses", tags=["approvals"])


@app.on_event("startup")
def startup_event():
    """Initialize test data on startup."""
    init_test_data()


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Expense Approval Workflow API is running"}
