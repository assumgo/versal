from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()
_dummy_hash = _hasher.hash('not-a-real-account-password')


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return _hasher.verify(encoded, password)
    except (InvalidHashError, VerificationError, TypeError):
        return False


def verify_unknown_account(password: str) -> None:
    verify_password(password, _dummy_hash)


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode({
        'sub': str(user_id),
        'iat': now,
        'exp': now + timedelta(minutes=settings.access_token_expire_minutes),
        'type': 'access',
        'jti': str(uuid4()),
    }, settings.jwt_secret_key, algorithm='HS256')


def decode_access_token(raw: str) -> int:
    claims = jwt.decode(
        raw,
        get_settings().jwt_secret_key,
        algorithms=['HS256'],
        options={'require': ['sub', 'iat', 'exp', 'type']},
    )
    if claims['type'] != 'access':
        raise jwt.InvalidTokenError('Invalid token type')
    try:
        user_id = int(claims['sub'])
    except (TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError('Invalid subject') from exc
    if user_id <= 0:
        raise jwt.InvalidTokenError('Invalid subject')
    return user_id
