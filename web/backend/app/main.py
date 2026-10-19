from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.companies import router as companies_router
from app.api.routes.users import router as users_router
from app.api.routes.employees import router as employees_router
from app.api.routes.chart_accounts import router as chart_accounts_router
from app.api.routes.rubrics import router as rubrics_router
from app.api.routes.finance_params import router as finance_params_router
from app.api.routes.accounting_review import router as accounting_review_router
from app.api.routes.payroll_preview import router as payroll_preview_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origins.split(',') if origin.strip()],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    allow_headers=['Authorization', 'Content-Type'],
)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(companies_router)
app.include_router(employees_router)
app.include_router(chart_accounts_router)
app.include_router(rubrics_router)
app.include_router(finance_params_router)
app.include_router(accounting_review_router)
app.include_router(payroll_preview_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Pydantic's input/context can contain plaintext passwords, even with SecretStr.
    errors = [{key: error[key] for key in ('type', 'loc', 'msg')} for error in exc.errors()]
    return JSONResponse(status_code=422, content={'detail': errors},
                        headers={'Cache-Control': 'no-store'})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
