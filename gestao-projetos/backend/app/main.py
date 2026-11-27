from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings
from app.core.database import get_engine
from app.services.seed import ensure_ready


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with Session(get_engine()) as session:
        ensure_ready(session)
        session.commit()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.frontend_origins.split(',') if origin.strip()],
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        allow_headers=['Authorization', 'Content-Type'],
    )
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(projects_router)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{key: error[key] for key in ('type', 'loc', 'msg')} for error in exc.errors()]
        return JSONResponse(status_code=422, content={'detail': errors}, headers={'Cache-Control': 'no-store'})

    @app.get('/health', tags=['health'])
    def health() -> dict[str, str]:
        return {'status': 'ok'}

    return app


app = create_app()
