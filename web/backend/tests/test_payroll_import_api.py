import asyncio
import hashlib
from copy import deepcopy
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, func, select, update
from sqlalchemy.orm import Session

from app.api.routes import payroll_imports as route
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models import AuditLog, Company, PayrollImport, PayrollLine, Role, User, UserCompany
from test_authorization import COMPANIES, accounts, admin_db, client, headers as auth_headers
from test_payroll_preview_summary import statement


def endpoint(accounts):
    return f'{COMPANIES}/{accounts[1][0].id}/payroll-imports'


def upload(data=b'%PDF-synthetic payroll statement'):
    return {'file': ('input.pdf', data, 'application/pdf')}


def ready_statement():
    return deepcopy(statement())


@pytest.mark.asyncio
async def test_confirm_persists_snapshot_and_history_excludes_sensitive_data(
    client, accounts, admin_db, monkeypatch,
):
    company = accounts[1][0]
    company.cnpj = '00000000000000'
    admin_db.commit()
    parsed = ready_statement()
    async def parse(path, extension):
        return deepcopy(parsed)
    monkeypatch.setattr(route.preview_runner, 'run', parse)
    body = b'%PDF-synthetic payroll statement'
    digest = hashlib.sha256(body).hexdigest()

    async with client:
        response = await client.post(
            endpoint(accounts), headers=auth_headers(accounts),
            data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body),
        )
        assert response.status_code == 201, response.text
        result = response.json()
        assert result['company_id'] == company.id
        assert result['competence'] == '09/2026'
        assert result['filename'] == 'input.pdf'
        assert result['size_bytes'] == len(body)
        assert result['sha256'] == digest
        assert result['employees'] == 2
        assert result['rubrics'] == 3
        assert result['totals_by_type'] == {'P': '20.00', 'D': '-1.25', 'E': '0'}
        assert result['net_total'] == '18.75'

        history = await client.get(endpoint(accounts), headers=auth_headers(accounts))
        assert history.status_code == 200, history.text
        page = history.json()
        assert page['total'] == 1 and page['offset'] == 0 and page['limit'] == 50
        assert page['items'][0]['import_id'] == result['import_id']
        assert page['items'][0]['competence'] == '09/2026'
        assert 'cpf' not in history.text.lower()
        assert 'Ana' not in history.text and 'João' not in history.text
        assert '18.75' not in history.text and '20.00' not in history.text

    saved = admin_db.get(PayrollImport, result['import_id'])
    assert saved.stored_file_id is None
    assert saved.created_by_id == accounts[0]['Administrador'].id
    lines = admin_db.scalars(select(PayrollLine).where(PayrollLine.import_id == saved.id)).all()
    assert len(lines) == 3
    events = admin_db.scalars(select(AuditLog).where(AuditLog.entity_id == saved.id)).all()
    assert len(events) == 1
    assert 'Ana' not in str(events[0].details) and '00000000000' not in str(events[0].details)


@pytest.mark.asyncio
async def test_confirm_rejects_hash_context_duplicate_and_multipart_errors(
    client, accounts, admin_db, monkeypatch,
):
    company = accounts[1][0]
    company.cnpj = '00000000000000'
    admin_db.commit()
    parsed = ready_statement()
    async def parse(path, extension):
        return deepcopy(parsed)
    monkeypatch.setattr(route.preview_runner, 'run', parse)
    body = b'%PDF-synthetic payroll statement'
    digest = hashlib.sha256(body).hexdigest()
    path, auth = endpoint(accounts), auth_headers(accounts)

    async with client:
        bad_hash = await client.post(path, headers=auth,
            data={'competence': '09/2026', 'preview_sha256': '0' * 64}, files=upload(body))
        assert bad_hash.status_code == 409
        wrong_competence = await client.post(path, headers=auth,
            data={'competence': '10/2026', 'preview_sha256': digest}, files=upload(body))
        assert wrong_competence.status_code == 409
        parsed['empresa']['cnpj'] = '11111111111111'
        wrong_company = await client.post(path, headers=auth,
            data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body))
        assert wrong_company.status_code == 409
        parsed['empresa']['cnpj'] = '00000000000000'
        parsed['colaboradores'] = []
        blocked = await client.post(path, headers=auth,
            data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body))
        assert blocked.status_code == 409
        parsed['colaboradores'] = ready_statement()['colaboradores']
        malformed = await client.post(path, headers=auth,
            data={'competence': '09/2026', 'preview_sha256': digest, 'extra': 'no'}, files=upload(body))
        assert malformed.status_code == 422
        assert (await client.post(path, headers=auth, data={
            'competence': '09/2026', 'preview_sha256': digest,
        }, files=upload(body),)).status_code == 201
        duplicate = await client.post(path, headers=auth,
            data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body))
        assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_import_roles_company_scope_and_inactive_company(
    client, accounts, admin_db, monkeypatch,
):
    companies = accounts[1]
    companies[0].cnpj = companies[1].cnpj = '00000000000000'
    admin_db.commit()
    parsed = ready_statement()
    async def parse(path, extension):
        return deepcopy(parsed)
    monkeypatch.setattr(route.preview_runner, 'run', parse)
    path = endpoint(accounts)
    body = b'%PDF-synthetic payroll statement'
    digest = hashlib.sha256(body).hexdigest()

    async with client:
        assert (await client.get(path, headers=auth_headers(accounts, 'Consulta'))).status_code == 200
        assert (await client.post(path, headers=auth_headers(accounts, 'Consulta'),
            data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body))).status_code == 403
        assert (await client.get(f'{COMPANIES}/{companies[1].id}/payroll-imports',
            headers=auth_headers(accounts))).status_code == 403
        companies[0].status = 'Inativa'
        admin_db.commit()
        assert (await client.post(path, headers=auth_headers(accounts),
            data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body))).status_code == 409


@pytest.mark.asyncio
async def test_history_paginates_metadata_only(client, accounts, admin_db, monkeypatch):
    accounts[1][0].cnpj = '00000000000000'
    admin_db.commit()
    competences = iter(('09/2026', '10/2026'))

    async def parse(path, extension):
        parsed = ready_statement()
        parsed['competencia'] = next(competences)
        return parsed

    monkeypatch.setattr(route.preview_runner, 'run', parse)
    body = b'%PDF-synthetic payroll statement'
    digest = hashlib.sha256(body).hexdigest()
    path = endpoint(accounts)
    async with client:
        created = []
        for competence in ('09/2026', '10/2026'):
            result = await client.post(path, headers=auth_headers(accounts),
                data={'competence': competence, 'preview_sha256': digest}, files=upload(body))
            assert result.status_code == 201, result.text
            created.append(result.json())
        first = await client.get(path, headers=auth_headers(accounts), params={'offset': 0, 'limit': 1})
        second = await client.get(path, headers=auth_headers(accounts), params={'offset': 1, 'limit': 1})
        assert first.status_code == second.status_code == 200
        assert first.json()['total'] == 2
        assert first.json()['limit'] == second.json()['limit'] == 1
        assert first.json()['items'][0]['import_id'] == created[1]['import_id']
        assert second.json()['items'][0]['import_id'] == created[0]['import_id']
        assert first.json()['items'][0]['competence'] == '10/2026'
        assert set(first.json()['items'][0]) == {
            'import_id', 'company_id', 'competence', 'filename', 'status', 'imported_at',
            'size_bytes', 'sha256', 'employees', 'rubrics',
        }
        assert all(value not in first.text.lower() for value in ('cpf', 'ana', 'joão', '20.00'))


@pytest.mark.asyncio
async def test_history_sanitizes_legacy_local_file_path(client, accounts, admin_db):
    company = accounts[1][0]
    legacy = PayrollImport(
        company_id=company.id, competencia='08/2026',
        arquivo=r'C:\\Users\\Gabriel\\Folha\\folha-antiga.pdf', status='Concluida',
    )
    admin_db.add(legacy)
    admin_db.commit()

    async with client:
        response = await client.get(endpoint(accounts), headers=auth_headers(accounts))

    assert response.status_code == 200, response.text
    assert response.json()['items'][0]['filename'] == 'folha-antiga.pdf'
    assert 'C:\\Users' not in response.text


@pytest.mark.asyncio
async def test_two_concurrent_confirmations_create_only_one_import(monkeypatch):
    import os
    from app.core.security import hash_password

    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('requires disposable PostgreSQL')
    engine = create_engine(url)
    with Session(engine) as db:
        role = db.scalar(select(Role).where(Role.name == 'Operador'))
        owns_role = role is None
        if role is None:
            role = Role(name='Operador')
            db.add(role)
            db.flush()
        role_id = role.id
        company = Company(razao='Concurrent import', cnpj='00000000000000', status='Ativa')
        actor = User(email=f'{uuid4().hex}@import.test', password_hash=hash_password('synthetic-password'), role=role)
        db.add_all([company, actor])
        db.flush()
        company_id, actor_id = company.id, actor.id
        db.add(UserCompany(user_id=actor_id, company_id=company_id))
        db.commit()

    async def fresh_db():
        with Session(engine) as db:
            yield db
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = fresh_db
    both_parsing = asyncio.Event()
    calls = 0
    parsed = ready_statement()

    async def parse(path, extension):
        nonlocal calls
        calls += 1
        if calls == 2:
            both_parsing.set()
        await both_parsing.wait()
        return deepcopy(parsed)

    monkeypatch.setattr(route.preview_runner, 'run', parse)
    body = b'%PDF-synthetic payroll statement'
    digest = hashlib.sha256(body).hexdigest()
    token_headers = {'Authorization': f'Bearer {create_access_token(actor_id)}'}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='https://test') as concurrent_client:
            async def confirm():
                return await concurrent_client.post(
                    f'{COMPANIES}/{company_id}/payroll-imports', headers=token_headers,
                    data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body),
                )
            responses = await asyncio.wait_for(asyncio.gather(confirm(), confirm()), timeout=10)
        assert sorted(response.status_code for response in responses) == [201, 409]
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(PayrollImport)
                             .where(PayrollImport.company_id == company_id)) == 1
            assert db.scalar(select(func.count()).select_from(PayrollLine)
                             .where(PayrollLine.company_id == company_id)) == 3
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        with engine.begin() as db:
            db.execute(delete(AuditLog).where(AuditLog.company_id == company_id))
            db.execute(delete(PayrollLine).where(PayrollLine.company_id == company_id))
            db.execute(delete(PayrollImport).where(PayrollImport.company_id == company_id))
            db.execute(delete(UserCompany).where(UserCompany.user_id == actor_id))
            db.execute(delete(User).where(User.id == actor_id))
            db.execute(delete(Company).where(Company.id == company_id))
            if owns_role:
                db.execute(delete(Role).where(Role.id == role_id))
        engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(('change', 'expected'), [
    ('membership', 403), ('role', 403), ('user', 401), ('company', 409),
])
async def test_confirm_revalidates_actor_membership_and_company_after_parsing(monkeypatch, change, expected):
    import os
    from app.core.security import hash_password

    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('requires disposable PostgreSQL')
    engine = create_engine(url)
    with Session(engine) as db:
        role = db.scalar(select(Role).where(Role.name == 'Operador'))
        owns_role = role is None
        if role is None:
            role = Role(name='Operador')
            db.add(role)
            db.flush()
        role_id = role.id
        company = Company(razao='Revalidated import', cnpj='00000000000000', status='Ativa')
        actor = User(email=f'{uuid4().hex}@revalidate.test', password_hash=hash_password('synthetic-password'), role=role)
        db.add_all([company, actor])
        db.flush()
        company_id, actor_id = company.id, actor.id
        db.add(UserCompany(user_id=actor_id, company_id=company_id))
        db.commit()

    replacement_role_id = None
    def fresh_db():
        with Session(engine) as db:
            yield db
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = fresh_db

    async def parse_and_revoke(path, extension):
        nonlocal replacement_role_id
        with Session(engine) as independent:
            if change == 'membership':
                independent.execute(delete(UserCompany).where(UserCompany.user_id == actor_id))
            elif change == 'user':
                independent.execute(update(User).where(User.id == actor_id).values(is_active=False))
            elif change == 'company':
                independent.execute(update(Company).where(Company.id == company_id).values(status='Inativa'))
            else:
                replacement = Role(name=f'invalid-{uuid4().hex[:30]}')
                independent.add(replacement)
                independent.flush()
                replacement_role_id = replacement.id
                independent.execute(update(User).where(User.id == actor_id).values(role_id=replacement.id))
            independent.commit()
        return ready_statement()

    monkeypatch.setattr(route.preview_runner, 'run', parse_and_revoke)
    body = b'%PDF-synthetic payroll statement'
    digest = hashlib.sha256(body).hexdigest()
    token_headers = {'Authorization': f'Bearer {create_access_token(actor_id)}'}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='https://test') as request_client:
            response = await request_client.post(
                f'{COMPANIES}/{company_id}/payroll-imports', headers=token_headers,
                data={'competence': '09/2026', 'preview_sha256': digest}, files=upload(body),
            )
        assert response.status_code == expected, response.text
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(PayrollImport)
                             .where(PayrollImport.company_id == company_id)) == 0
            assert db.scalar(select(func.count()).select_from(PayrollLine)
                             .where(PayrollLine.company_id == company_id)) == 0
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        with engine.begin() as db:
            db.execute(delete(AuditLog).where(AuditLog.company_id == company_id))
            db.execute(delete(PayrollLine).where(PayrollLine.company_id == company_id))
            db.execute(delete(PayrollImport).where(PayrollImport.company_id == company_id))
            db.execute(delete(UserCompany).where(UserCompany.user_id == actor_id))
            db.execute(delete(User).where(User.id == actor_id))
            db.execute(delete(Company).where(Company.id == company_id))
            if replacement_role_id is not None:
                db.execute(delete(Role).where(Role.id == replacement_role_id))
            if owns_role:
                db.execute(delete(Role).where(Role.id == role_id))
        engine.dispose()
