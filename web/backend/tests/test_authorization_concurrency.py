"""Two independent administrator changes must preserve one active administrator."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, delete, event, select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.user import Role, User
from app.services.users import inactivate_user


def test_concurrent_administrator_removal_preserves_one_active_administrator():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to disposable, migrated PostgreSQL')
    engine = create_engine(url, connect_args={
        'options': '-cstatement_timeout=15000 -clock_timeout=10000',
    })
    user_ids = []
    role_id = None
    leader_ready, waiter_ready, release = Event(), Event(), Event()
    pids = {}

    def before(connection, cursor, statement, parameters, context, executemany):
        if 'FROM roles' not in statement or not statement.lstrip().startswith('SELECT'):
            return
        pid = connection.connection.driver_connection.info.backend_pid
        if 'leader' not in pids:
            pids['leader'] = pid
        elif pid != pids['leader'] and 'waiter' not in pids:
            pids['waiter'] = pid
            waiter_ready.set()

    def after(connection, cursor, statement, parameters, context, executemany):
        if 'FROM roles' not in statement or not statement.lstrip().startswith('SELECT'):
            return
        pid = connection.connection.driver_connection.info.backend_pid
        if pid == pids.get('leader') and not leader_ready.is_set():
            leader_ready.set()
            assert release.wait(10), 'Timed out releasing the first administrator change'

    def remove(user_id):
        with Session(engine) as db:
            actor = db.get(User, user_id)
            try:
                inactivate_user(db, user_id, actor, None)
            except HTTPException as exc:
                return exc.status_code
            return 204

    try:
        with Session(engine) as db:
            role = Role(name='Administrador')
            db.add(role)
            db.flush()
            role_id = role.id
            encoded = hash_password('concurrent-administration-test')
            users = [User(email=f'{uuid4().hex}@authorization.test', role=role,
                          password_hash=encoded, is_active=True) for _ in range(2)]
            db.add_all(users)
            db.flush()
            user_ids = [user.id for user in users]
            db.commit()
        event.listen(engine, 'before_cursor_execute', before)
        event.listen(engine, 'after_cursor_execute', after)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            try:
                futures.append(executor.submit(remove, user_ids[0]))
                assert leader_ready.wait(5), 'First change never acquired administrator guard'
                futures.append(executor.submit(remove, user_ids[1]))
                assert waiter_ready.wait(5), 'Second change never reached administrator guard'
                blocked = False
                with engine.connect() as observer:
                    deadline = monotonic() + 5
                    while monotonic() < deadline:
                        blocked = observer.scalar(text(
                            'SELECT :leader = ANY(pg_blocking_pids(:waiter))'
                        ), pids)
                        if blocked:
                            break
                        sleep(0.01)
                assert blocked, 'Administrator changes did not serialize in PostgreSQL'
            finally:
                release.set()
                results = [future.result(timeout=15) for future in futures]
        assert results == [204, 409]
        with Session(engine) as db:
            assert db.scalars(select(User.id).where(
                User.id.in_(user_ids), User.is_active.is_(True))).all() == [user_ids[1]]
            actions = db.scalars(select(AuditLog.action).where(AuditLog.actor_id.in_(user_ids))).all()
            assert actions == ['user.inactivate']
    finally:
        release.set()
        if event.contains(engine, 'before_cursor_execute', before):
            event.remove(engine, 'before_cursor_execute', before)
            event.remove(engine, 'after_cursor_execute', after)
        try:
            with engine.begin() as connection:
                connection.execute(delete(AuditLog).where(AuditLog.actor_id.in_(user_ids)))
                connection.execute(delete(User).where(User.id.in_(user_ids)))
                if role_id is not None:
                    connection.execute(delete(Role).where(Role.id == role_id))
        finally:
            engine.dispose()
