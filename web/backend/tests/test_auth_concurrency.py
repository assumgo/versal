"""Exercise overlapping HTTP requests using independent PostgreSQL sessions."""
import asyncio
import os
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, event, select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.audit import AuditLog
from app.models.user import RefreshToken, Role, User
from app.services.auth import authenticate

AUTH = '/api/v1/auth'


@pytest.fixture
def concurrent_session():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to disposable, migrated PostgreSQL')
    engine = create_engine(url, connect_args={
        'options': '-cstatement_timeout=15000 -clock_timeout=10000',
    })
    user_id = role_id = None
    previous = app.dependency_overrides.copy()
    try:
        # Commit setup so other connections can see it. Cleanup is scoped to this user.
        with Session(engine) as db:
            suffix = uuid4().hex
            role = Role(name=f'test-{suffix}')
            user = User(email=f'{suffix}@example.test', role=role,
                        password_hash=hash_password('concurrency-test-password'), is_active=True)
            db.add(user)
            db.flush()
            user_id, role_id = user.id, role.id
            db.commit()
            pair = authenticate(db, user.email, 'concurrency-test-password')

        def override_db():
            # Never share a Session or connection between requests.
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        yield engine, user_id, pair.refresh_token
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        try:
            with engine.begin() as connection:
                if user_id is not None:
                    connection.execute(delete(AuditLog).where(AuditLog.actor_id == user_id))
                    connection.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
                    connection.execute(delete(User).where(User.id == user_id))
                if role_id is not None:
                    connection.execute(delete(Role).where(Role.id == role_id))
        finally:
            engine.dispose()


class Overlap:
    """Pause the first user's SELECT while the second request reaches PostgreSQL.

    Only scheduling is controlled; SQL execution and locking remain real. Match
    the SELECT even without FOR UPDATE so removing the lock makes the test fail.
    """

    def __init__(self, engine):
        self.engine = engine
        self.leader_ready = Event()
        self.waiter_ready = Event()
        self.release = Event()
        self.leader_pid = None
        self.waiter_pid = None

    def before(self, connection, cursor, statement, parameters, context, executemany):
        if 'FROM users' not in statement or not statement.lstrip().startswith('SELECT'):
            return
        pid = connection.connection.driver_connection.info.backend_pid
        if self.leader_pid is None:
            self.leader_pid = pid
        elif pid != self.leader_pid and self.waiter_pid is None:
            self.waiter_pid = pid
            self.waiter_ready.set()

    def after(self, connection, cursor, statement, parameters, context, executemany):
        if 'FROM users' not in statement or not statement.lstrip().startswith('SELECT'):
            return
        pid = connection.connection.driver_connection.info.backend_pid
        if pid == self.leader_pid and not self.leader_ready.is_set():
            self.leader_ready.set()
            if not self.release.wait(10):
                raise AssertionError('Timed out waiting to release the first request')

    def observe_blocking(self):
        deadline = monotonic() + 5
        with self.engine.connect() as observer:
            while monotonic() < deadline:
                blocked = observer.scalar(text(
                    'SELECT :leader = ANY(pg_blocking_pids(:waiter))'
                ), {'leader': self.leader_pid, 'waiter': self.waiter_pid})
                if blocked:
                    return True
                sleep(0.01)
        return False


@pytest.mark.asyncio
@pytest.mark.parametrize('first,second,expected,count', [
    ('refresh', 'refresh', (200, 401), 2),
    ('refresh', 'logout', (200, 204), 2),
    ('logout', 'refresh', (204, 401), 1),
])
async def test_session_requests_serialize_and_leave_no_live_refresh(
    concurrent_session, first, second, expected, count,
):
    engine, user_id, raw = concurrent_session
    overlap = Overlap(engine)
    event.listen(engine, 'before_cursor_execute', overlap.before)
    event.listen(engine, 'after_cursor_execute', overlap.after)
    tasks = []

    async def request(action):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='https://test') as client:
            return await client.post(f'{AUTH}/{action}', headers={
                'Cookie': f'refresh_token={raw}',
            })

    try:
        tasks.append(asyncio.create_task(request(first)))
        assert await asyncio.to_thread(overlap.leader_ready.wait, 5), 'First request never reached DB'
        tasks.append(asyncio.create_task(request(second)))
        assert await asyncio.to_thread(overlap.waiter_ready.wait, 5), 'Second request never reached DB'
        assert overlap.leader_pid != overlap.waiter_pid
        assert await asyncio.to_thread(overlap.observe_blocking), (
            'Second request did not block on the first request in PostgreSQL'
        )
        overlap.release.set()
        responses = await asyncio.wait_for(asyncio.gather(*tasks), timeout=15)
        assert tuple(response.status_code for response in responses) == expected
    finally:
        overlap.release.set()
        # Drain requests before removing instrumentation or cleaning committed fixtures.
        await asyncio.gather(*tasks, return_exceptions=True)
        event.remove(engine, 'before_cursor_execute', overlap.before)
        event.remove(engine, 'after_cursor_execute', overlap.after)

    # Read from a fresh connection: successful commits, not in-memory objects.
    with Session(engine) as db:
        tokens = db.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id)).all()
        assert len(tokens) == count
        assert len({token.family_id for token in tokens}) == 1
        assert all(token.revoked_at is not None for token in tokens)
        actions = db.scalars(select(AuditLog.action).where(AuditLog.actor_id == user_id)).all()
        assert actions.count('auth.refresh') == (1 if first == 'refresh' else 0)
        assert actions.count('auth.logout') == (1 if 'logout' in (first, second) else 0)
        assert actions.count('auth.refresh_reuse') == (1 if second == 'refresh' else 0)

    for response in responses:
        for cookie in response.cookies.jar:
            if cookie.value and cookie.value != raw:
                async with AsyncClient(transport=ASGITransport(app=app), base_url='https://test') as client:
                    rejected = await client.post(f'{AUTH}/refresh', headers={
                        'Cookie': f'{cookie.name}={cookie.value}',
                    })
                assert rejected.status_code == 401
