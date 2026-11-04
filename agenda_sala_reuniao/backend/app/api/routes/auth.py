from typing import Annotated

from fastapi import APIRouter, Request, Response

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, Database, unauthorized
from app.schemas.auth import AccessTokenResponse, LoginRequest, UserResponse
from app.services.auth import AuthenticationError, TokenPair, authenticate, revoke_refresh, rotate_refresh

router = APIRouter(prefix='/api/v1/auth', tags=['auth'])
COOKIE_NAME = 'refresh_token'
COOKIE_PATH = '/api/v1/auth'


def require_refresh(request: Request) -> str:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw or len(raw) > 256:
        raise unauthorized()
    return raw


def _respond(response: Response, pair: TokenPair) -> AccessTokenResponse:
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME, pair.refresh_token, httponly=True,
        secure=settings.environment == 'production', samesite='lax',
        path=COOKIE_PATH, max_age=settings.refresh_token_expire_days * 86400,
    )
    response.headers['Cache-Control'] = 'no-store'
    return AccessTokenResponse(access_token=pair.access_token)


@router.post('/login', response_model=AccessTokenResponse)
def login(payload: LoginRequest, response: Response, db: Database) -> AccessTokenResponse:
    try:
        pair = authenticate(db, payload.email, payload.password.get_secret_value())
    except AuthenticationError:
        raise unauthorized() from None
    return _respond(response, pair)


@router.post('/refresh', response_model=AccessTokenResponse)
def refresh(request: Request, response: Response, db: Database) -> AccessTokenResponse:
    try:
        pair = rotate_refresh(db, require_refresh(request))
    except AuthenticationError:
        raise unauthorized() from None
    return _respond(response, pair)


@router.post('/logout', status_code=204)
def logout(request: Request, db: Database) -> Response:
    raw = request.cookies.get(COOKIE_NAME)
    if raw and len(raw) <= 256:
        revoke_refresh(db, raw)
    response = Response(status_code=204, headers={'Cache-Control': 'no-store'})
    response.delete_cookie(
        COOKIE_NAME, path=COOKIE_PATH, httponly=True,
        secure=get_settings().environment == 'production', samesite='lax',
    )
    return response


@router.get('/me', response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)
