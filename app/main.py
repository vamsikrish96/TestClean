from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.utils.errors import APIException

app = FastAPI(
    title="Expense Approval Workflow API",
    description="API for managing expense claims with approval workflow",
    version="1.0.0",
)


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
