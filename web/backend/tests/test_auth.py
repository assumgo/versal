"""Authentication contracts, using disposable PostgreSQL for session lifecycle tests."""
import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from argon2 import PasswordHasher
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.user import RefreshToken, Role, User

PASSWORD = 'test-only-password-123!'
AUTH = '/api/v1/auth'


def test_password_hash_uses_argon2_and_random_salt():
    from app.core.security import hash_password

    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first != second
    assert first.startswith('$argon2id$')
    assert PasswordHasher().verify(first, PASSWORD)


@pytest.mark.parametrize('password,encoded,expected', [
    (PASSWORD, 'valid', True), ('wrong', 'valid', False),
    (PASSWORD, 'invalid-hash', False),
])
def test_password_verification(password, encoded, expected):
    from app.core.security import verify_password

    if encoded == 'valid':
        encoded = PasswordHasher().hash(PASSWORD)
    assert verify_password(password, encoded) is expected


@pytest.fixture
def auth_db():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to disposable, migrated PostgreSQL')
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                with Session(bind=connection, join_transaction_mode='create_savepoint') as session:
                    yield session
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


@pytest.fixture
def account(auth_db):
    user = User(email='auth@example.test', password_hash=PasswordHasher().hash(PASSWORD),
                role=Role(name='Operador'), is_active=True)
    auth_db.add(user)
    auth_db.flush()
    return user


@pytest.fixture
def auth_client(auth_db, account):
    def override_db():
        yield auth_db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        yield AsyncClient(transport=ASGITransport(app=app), base_url='https://test')
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


async def login(client):
    response = await client.post(f'{AUTH}/login', json={
        'email': 'auth@example.test', 'password': PASSWORD,
    })
    assert response.status_code == 200, response.text
    return response


def refresh_cookie(response):
    # Discover the cookie name rather than prescribing it.
    cookies = list(response.cookies.jar)
    assert len(cookies) == 1
    return cookies[0]


def token_row(db, raw):
    db.expire_all()
    row = db.scalar(select(RefreshToken).where(
        RefreshToken.token_hash == hashlib.sha256(raw.encode()).hexdigest()))
    assert row is not None, 'Refresh token must be stored as a SHA-256 hash'
    return row


@pytest.mark.asyncio
async def test_login_issues_signed_short_lived_access_token(auth_client, account):
    async with auth_client as client:
        response = await login(client)
    body = response.json()
    assert body['token_type'].lower() == 'bearer'
    claims = jwt.decode(body['access_token'], get_settings().jwt_secret_key,
                        algorithms=['HS256'], options={'require': ['sub', 'exp', 'iat']})
    assert claims['sub'] == str(account.id)
    assert 0 < claims['exp'] - claims['iat'] <= 15 * 60
    assert 'refresh_token' not in body
    assert PASSWORD not in response.text
    assert account.password_hash not in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize('environment', ['development', 'production'])
async def test_login_sets_protected_cookie_and_persists_hash(
    auth_client, auth_db, account, monkeypatch, environment,
):
    monkeypatch.setattr(get_settings(), 'environment', environment)
    async with auth_client as client:
        response = await login(client)
    cookie = refresh_cookie(response)
    header = response.headers['set-cookie'].lower()
    assert 'httponly' in header
    assert 'samesite=lax' in header
    if get_settings().environment == 'production':
        assert cookie.secure
    row = token_row(auth_db, cookie.value)
    assert row.user_id == account.id
    assert row.token_hash != cookie.value
    assert row.revoked_at is None
    assert row.expires_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
@pytest.mark.parametrize('email,password', [
    ('auth@example.test', 'incorrect'), ('unknown@example.test', PASSWORD),
])
async def test_login_rejects_invalid_credentials(auth_client, auth_db, email, password):
    async with auth_client as client:
        response = await client.post(f'{AUTH}/login', json={'email': email, 'password': password})
    assert response.status_code == 401
    assert not response.cookies
    assert auth_db.scalars(select(RefreshToken)).all() == []


@pytest.mark.asyncio
async def test_login_rejects_inactive_account(auth_client, auth_db, account):
    account.is_active = False
    auth_db.flush()
    async with auth_client as client:
        response = await client.post(f'{AUTH}/login', json={
            'email': account.email, 'password': PASSWORD,
        })
    assert response.status_code == 401
    assert auth_db.scalars(select(RefreshToken)).all() == []


@pytest.mark.asyncio
async def test_me_returns_identity_without_secrets(auth_client, account):
    async with auth_client as client:
        signed_in = await login(client)
        response = await client.get(f'{AUTH}/me', headers={
            'Authorization': f"Bearer {signed_in.json()['access_token']}",
        })
    assert response.status_code == 200
    assert response.json()['id'] == account.id
    assert response.json()['email'] == account.email
    assert 'password_hash' not in response.json()
    assert 'refresh_tokens' not in response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize('token', [None, 'malformed', 'expired', 'forged'])
async def test_me_rejects_missing_or_invalid_access_token(token):
    if token in ('expired', 'forged'):
        now = datetime.now(timezone.utc)
        token = jwt.encode({'sub': '1', 'type': 'access', 'iat': now - timedelta(hours=1),
                            'exp': now - timedelta(seconds=1) if token == 'expired'
                            else now + timedelta(minutes=5)},
                           get_settings().jwt_secret_key if token == 'expired'
                           else 'different-test-secret-at-least-32-characters', algorithm='HS256')
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url='https://test') as client:
        response = await client.get(f'{AUTH}/me', headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates_cookie_and_revokes_previous_token(auth_client, auth_db):
    async with auth_client as client:
        initial = refresh_cookie(await login(client))
        family = token_row(auth_db, initial.value).family_id
        response = await client.post(f'{AUTH}/refresh')
        assert response.status_code == 200, response.text
        current = refresh_cookie(response)
        assert current.value != initial.value
        assert token_row(auth_db, initial.value).revoked_at is not None
        new = token_row(auth_db, current.value)
        assert new.family_id == family
        assert new.revoked_at is None
        assert 'refresh_token' not in response.json()
        me = await client.get(f'{AUTH}/me', headers={
            'Authorization': f"Bearer {response.json()['access_token']}",
        })
        assert me.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize('state', ['expired', 'revoked'])
async def test_refresh_rejects_expired_or_revoked_token(auth_client, auth_db, state):
    async with auth_client as client:
        cookie = refresh_cookie(await login(client))
        row = token_row(auth_db, cookie.value)
        if state == 'expired':
            row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        else:
            row.revoked_at = datetime.now(timezone.utc)
        auth_db.flush()
        response = await client.post(f'{AUTH}/refresh')
    assert response.status_code == 401
    assert 'access_token' not in response.json()
    assert len(auth_db.scalars(select(RefreshToken)).all()) == 1


@pytest.mark.asyncio
async def test_refresh_rejects_reuse_of_rotated_token(auth_client, auth_db):
    async with auth_client as client:
        original = refresh_cookie(await login(client))
        assert (await client.post(f'{AUTH}/refresh')).status_code == 200
        count = len(auth_db.scalars(select(RefreshToken)).all())
        client.cookies.clear()
        response = await client.post(f'{AUTH}/refresh', headers={
            'Cookie': f'{original.name}={original.value}',
        })
    assert response.status_code == 401
    assert 'access_token' not in response.json()
    assert len(auth_db.scalars(select(RefreshToken)).all()) == count


@pytest.mark.asyncio
async def test_refresh_requires_cookie():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='https://test') as client:
        response = await client.post(f'{AUTH}/refresh')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_and_clears_cookie(auth_client, auth_db):
    async with auth_client as client:
        cookie = refresh_cookie(await login(client))
        response = await client.post(f'{AUTH}/logout')
        assert response.status_code in (200, 204)
        assert token_row(auth_db, cookie.value).revoked_at is not None
        assert 'max-age=0' in response.headers['set-cookie'].lower()
        client.cookies.clear()
        reused = await client.post(f'{AUTH}/refresh', headers={
            'Cookie': f'{cookie.name}={cookie.value}',
        })
        assert reused.status_code == 401


@pytest.mark.asyncio
async def test_reuse_revokes_entire_refresh_family(auth_client, auth_db):
    async with auth_client as client:
        original = refresh_cookie(await login(client))
        rotated = await client.post(f'{AUTH}/refresh')
        assert rotated.status_code == 200
        current = refresh_cookie(rotated)
        client.cookies.clear()
        replay = await client.post(f'{AUTH}/refresh', headers={
            'Cookie': f'{original.name}={original.value}',
        })
        assert replay.status_code == 401
        rejected = await client.post(f'{AUTH}/refresh', headers={
            'Cookie': f'{current.name}={current.value}',
        })
        assert rejected.status_code == 401
    assert all(row.revoked_at is not None for row in auth_db.scalars(select(RefreshToken)))


@pytest.mark.asyncio
async def test_inactive_user_cannot_refresh_or_use_access_token(auth_client, auth_db, account):
    async with auth_client as client:
        response = await login(client)
        account.is_active = False
        auth_db.flush()
        me = await client.get(f'{AUTH}/me', headers={
            'Authorization': f"Bearer {response.json()['access_token']}",
        })
        assert me.status_code == 401
        refresh = await client.post(f'{AUTH}/refresh')
        assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_authentication_events_are_audited_without_secrets(auth_client, auth_db, account):
    from app.models.audit import AuditLog

    async with auth_client as client:
        response = await login(client)
        raw = refresh_cookie(response).value
        assert (await client.post(f'{AUTH}/refresh')).status_code == 200
        assert (await client.post(f'{AUTH}/logout')).status_code == 204
    entries = auth_db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [entry.action for entry in entries] == ['auth.login', 'auth.refresh', 'auth.logout']
    assert all(entry.actor_id == account.id for entry in entries)
    assert all(entry.ip_address == '127.0.0.1' for entry in entries)
    assert PASSWORD not in str([entry.details for entry in entries])
    assert raw not in str([entry.details for entry in entries])


@pytest.mark.asyncio
async def test_invalid_login_payload_does_not_echo_password(auth_client):
    password = 'sensitive-password-' * 100
    async with auth_client as client:
        response = await client.post(f'{AUTH}/login', json={
            'email': 'auth@example.test', 'password': password,
        })
    assert response.status_code == 422
    assert password not in response.text
    assert 'sensitive-password-' not in response.text
