"""Real, independent sessions prove company locking, never the application DB."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, event, select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models import AuditLog, ChartAccount, Company, Role, Rubric, User, UserCompany


@pytest.fixture
def catalog_database():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Requires disposable PostgreSQL')
    engine = create_engine(url, connect_args={'options': '-cstatement_timeout=20000 -clock_timeout=15000'})
    created_role = None
    with Session(engine) as db:
        role = db.scalar(select(Role).where(Role.name == 'Administrador'))
        if role is None:
            role = Role(name='Administrador')
            db.add(role)
            db.flush()
            created_role = role.id
        company = Company(razao='Synthetic concurrency company')
        user = User(email=f'{uuid4().hex}@catalog.test', password_hash='unused-test-hash', role_id=role.id, is_active=True)
        db.add_all([company, user])
        db.flush()
        db.add(UserCompany(user_id=user.id, company_id=company.id))
        company_id, user_id = company.id, user.id
        db.commit()
    previous = app.dependency_overrides.copy()
    def dependency():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = dependency
    try:
        yield engine, company_id, {'Authorization': f'Bearer {create_access_token(user_id)}'}
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        with engine.begin() as db:
            for model in (AuditLog, Rubric, ChartAccount, UserCompany):
                db.execute(delete(model).where(model.company_id == company_id))
            db.execute(delete(User).where(User.id == user_id))
            db.execute(delete(Company).where(Company.id == company_id))
            if created_role is not None:
                db.execute(delete(Role).where(Role.id == created_role))
        engine.dispose()


def send(method, path, auth, payload):
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            return await client.request(method, path, headers=auth, json=payload)
    return asyncio.run(request())


class CompanyOverlap:
    def __init__(self, engine):
        self.engine = engine
        self.locked, self.waiting, self.release = Event(), Event(), Event()
        self.leader = self.waiter = None

    def before(self, conn, cursor, statement, parameters, context, executemany):
        if 'FROM companies' not in statement or 'FOR UPDATE' not in statement:
            return
        pid = conn.connection.driver_connection.info.backend_pid
        if self.leader is None:
            self.leader = pid
        elif pid != self.leader:
            self.waiter = pid
            self.waiting.set()

    def after(self, conn, cursor, statement, parameters, context, executemany):
        if 'FROM companies' in statement and 'FOR UPDATE' in statement:
            if conn.connection.driver_connection.info.backend_pid == self.leader and not self.locked.is_set():
                self.locked.set()
                assert self.release.wait(15)

    def blocked(self):
        deadline = monotonic() + 5
        with self.engine.connect() as db:
            while monotonic() < deadline:
                if db.scalar(text('SELECT :leader = ANY(pg_blocking_pids(:waiter))'), {'leader': self.leader, 'waiter': self.waiter}):
                    return True
                sleep(0.02)
        return False


@pytest.mark.parametrize('resource', ['chart-accounts', 'rubrics'])
@pytest.mark.parametrize('leader_action', ['create', 'inactivate'])
def test_catalog_writes_serialize_with_duplicates_and_company_inactivation(catalog_database, resource, leader_action):
    engine, company, auth = catalog_database
    path = f'/api/v1/companies/{company}/{resource}'
    payload = {'conta': '00123', 'descricao': 'Synthetic'} if resource == 'chart-accounts' else {'codigo': 'FGTS', 'descricao': 'Synthetic'}
    overlap = CompanyOverlap(engine)
    event.listen(engine, 'before_cursor_execute', overlap.before)
    event.listen(engine, 'after_cursor_execute', overlap.after)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            if leader_action == 'create':
                leader = pool.submit(send, 'POST', path, auth, payload)
            else:
                leader = pool.submit(send, 'PATCH', f'/api/v1/companies/{company}', auth, {'status': 'Inativa'})
            assert overlap.locked.wait(15)
            waiter = pool.submit(send, 'POST', path, auth, payload)
            try:
                assert overlap.waiting.wait(15)
                assert overlap.blocked()
            finally:
                overlap.release.set()
            assert leader.result(timeout=20).status_code == (201 if leader_action == 'create' else 200)
            assert waiter.result(timeout=20).status_code == 409
        with Session(engine) as db:
            model = ChartAccount if resource == 'chart-accounts' else Rubric
            rows = db.scalars(select(model).where(model.company_id == company)).all()
            assert len(rows) == (1 if leader_action == 'create' else 0)
    finally:
        overlap.release.set()
        event.remove(engine, 'before_cursor_execute', overlap.before)
        event.remove(engine, 'after_cursor_execute', overlap.after)
