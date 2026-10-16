from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Pydantic's input/context can contain plaintext passwords, even with SecretStr.
    errors = [{key: error[key] for key in ('type', 'loc', 'msg')} for error in exc.errors()]
    return JSONResponse(status_code=422, content={'detail': errors},
                        headers={'Cache-Control': 'no-store'})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
