import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy import select

from test_authorization import admin_db, accounts, client, headers, COMPANIES
from app.models import Base

ROOT = Path(__file__).parent / 'fixtures/parser_equivalence'


def endpoint(accounts, private=False):
    return f'{COMPANIES}/{accounts[1][int(private)].id}/payroll-import-preview'


def upload(suffix='xlsx', case=None):
    path = ROOT / (case or f'extrato_{suffix}') / f'input.{suffix}'
    return {'file': (f'input.{suffix}', path.read_bytes(), 'application/octet-stream')}


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Administrador', 'Contador', 'Operador', 'Consulta'])
async def test_preview_roles_scope_and_inactive(client, accounts, admin_db, role):
    accounts[1][0].cnpj = '00000000000000'
    admin_db.commit()
    async with client:
        response = await client.post(endpoint(accounts), headers=headers(accounts, role), data={'competence': '09/2026'}, files=upload())
        assert response.status_code == (403 if role == 'Consulta' else 200), response.text
        assert (await client.post(endpoint(accounts, True), headers=headers(accounts, role), data={'competence': '09/2026'}, files=upload())).status_code == 403
        assert (await client.post(endpoint(accounts), data={'competence': '09/2026'}, files=upload())).status_code == 401
        accounts[1][0].status = 'Inativa'
        admin_db.commit()
        assert (await client.post(endpoint(accounts), headers=headers(accounts, role), data={'competence': '09/2026'}, files=upload())).status_code == (403 if role == 'Consulta' else 409)


@pytest.mark.asyncio
@pytest.mark.parametrize('suffix', ['pdf', 'xls', 'xlsx'])
async def test_preview_matches_corpus_without_any_database_writes(client, accounts, admin_db, suffix, monkeypatch, tmp_path):
    from app.api.routes import payroll_preview as route
    monkeypatch.setattr(route, 'TemporaryDirectory', lambda: TemporaryDirectory(dir=tmp_path))
    accounts[1][0].cnpj = '00.000.000/0000-00'
    admin_db.commit()
    def snapshot():
        return {t.name: [tuple(row) for row in admin_db.execute(select(t)).all()] for t in Base.metadata.sorted_tables}
    before = snapshot()
    async with client:
        response = await client.post(endpoint(accounts), headers=headers(accounts), data={'competence': '09/2026'}, files=upload(suffix))
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['status'] == 'ready'
    assert result['summary'] == {'employees': 2, 'rubrics': 4, 'totals_by_type': {'P': '5000.00', 'D': '500.00', 'E': '0'}, 'net_total': '4500.00'}
    assert response.headers['cache-control'] == 'no-store'
    assert snapshot() == before
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
async def test_preview_divergence_empty_errors_and_strict_multipart(client, accounts, admin_db):
    async with client:
        path, auth = endpoint(accounts), headers(accounts)
        result = await client.post(path, headers=auth, data={'competence': '08/2026'}, files=upload())
        assert result.status_code == 200 and result.json()['status'] == 'blocked'
        assert {'company_cnpj_missing', 'competence_mismatch'} <= {i['code'] for i in result.json()['issues']}
        empty = await client.post(path, headers=auth, data={'competence': '09/2026'}, files=upload('pdf', 'extrato_pdf_empty'))
        assert empty.status_code == 200 and empty.json()['status'] == 'blocked'
        for data in ({}, {'competence': '13/2026'}, {'competence': '09/2026', 'extra': 'no'}):
            assert (await client.post(path, headers=auth, data=data, files=upload())).status_code == 422
        for files, expected in [({'file': ('empty.pdf', b'')}, 400), ({'file': ('bad.exe', b'bad')}, 415),
                                ({'file': ('bad.pdf', b'%PDF-broken')}, 400),
                                ({'file': ('large.pdf', b'%PDF-' + b'x' * (10 * 1024 * 1024))}, 413)]:
            response = await client.post(path, headers=auth, data={'competence': '09/2026'}, files=files)
            assert response.status_code == expected, response.text
        assert (await client.post(path, headers=auth, data={'competence': '09/2026'})).status_code == 422
        files = [('file', ('one.pdf', b'%PDF-')), ('file', ('two.pdf', b'%PDF-'))]
        assert (await client.post(path, headers=auth, data={'competence': '09/2026'}, files=files)).status_code == 422
        parts = [('competence', (None, '09/2026')), ('competence', (None, '08/2026')), ('file', ('one.pdf', b'%PDF-'))]
        assert (await client.post(path, headers=auth, files=parts)).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('status', [413, 503, 504])
async def test_runner_errors_cleanup(client, accounts, monkeypatch, tmp_path, status):
    from app.api.routes import payroll_preview as route
    from app.services.payroll_preview_files import PreviewInputError
    async def fail(path, extension):
        assert path.is_file()
        raise PreviewInputError(status, 'Falha pública')
    monkeypatch.setattr(route.preview_runner, 'run', fail)
    monkeypatch.setattr(route, 'TemporaryDirectory', lambda: TemporaryDirectory(dir=tmp_path))
    async with client:
        result = await client.post(endpoint(accounts), headers=headers(accounts), data={'competence': '09/2026'}, files=upload())
    assert result.status_code == status
    assert not list(tmp_path.iterdir())


@pytest.mark.asyncio
@pytest.mark.parametrize('declared', [None, '1'])
async def test_stream_byte_limit_ignores_content_length(client, accounts, declared):
    async def body():
        for _ in range(12):
            yield b'x' * (1024 * 1024)
    auth = headers(accounts) | {'Content-Type': 'multipart/form-data; boundary=test'}
    if declared:
        auth['Content-Length'] = declared
    async with client:
        result = await client.post(endpoint(accounts), headers=auth, content=body())
    assert result.status_code == 413


@pytest.mark.asyncio
@pytest.mark.parametrize('change,expected', [('membership', 403), ('role', 403), ('user', 401), ('company', 409)])
async def test_revalidates_access_from_independent_connection(monkeypatch, change, expected):
    import os
    from uuid import uuid4
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import create_engine, delete, update
    from sqlalchemy.orm import Session
    from app.core.database import get_db
    from app.core.security import create_access_token, hash_password
    from app.main import app
    from app.models import Company, User, UserCompany, Role
    from app.api.routes import payroll_preview as route
    from test_payroll_preview_summary import statement

    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('requires disposable PostgreSQL')
    engine = create_engine(url)
    with Session(engine) as db:
        role = db.scalar(select(Role).where(Role.name == 'Operador'))
        own_role = role is None
        if role is None:
            role = Role(name='Operador')
            db.add(role)
        company = Company(razao='Synthetic concurrency', cnpj='00000000000000')
        user = User(email=f'{uuid4().hex}@preview.test', password_hash=hash_password('synthetic-preview-password'), role=role, is_active=True)
        db.add_all([company, user])
        db.flush()
        user_id, company_id, role_id = user.id, company.id, role.id
        db.add(UserCompany(user_id=user_id, company_id=company_id))
        db.commit()
    replacement_role_id = None
    def fresh_db():
        with Session(engine) as db:
            yield db
    async def parse_and_revoke(path, extension):
        nonlocal replacement_role_id
        with Session(engine) as independent:
            if change == 'membership':
                independent.execute(delete(UserCompany).where(UserCompany.user_id == user_id))
            elif change == 'user':
                independent.execute(update(User).where(User.id == user_id).values(is_active=False))
            elif change == 'company':
                independent.execute(update(Company).where(Company.id == company_id).values(status='Inativa'))
            else:
                replacement = Role(name=f'pv-{uuid4().hex}')
                independent.add(replacement)
                independent.flush()
                replacement_role_id = replacement.id
                independent.execute(update(User).where(User.id == user_id).values(role_id=replacement.id))
            independent.commit()
        return statement()
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = fresh_db
    monkeypatch.setattr(route.preview_runner, 'run', parse_and_revoke)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='https://test') as independent_client:
            response = await independent_client.post(f'{COMPANIES}/{company_id}/payroll-import-preview',
                headers={'Authorization': f'Bearer {create_access_token(user_id)}'}, data={'competence': '09/2026'}, files=upload())
        assert response.status_code == expected, response.text
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        with engine.begin() as connection:
            connection.execute(delete(UserCompany).where(UserCompany.user_id == user_id))
            connection.execute(delete(User).where(User.id == user_id))
            connection.execute(delete(Company).where(Company.id == company_id))
            if replacement_role_id:
                connection.execute(delete(Role).where(Role.id == replacement_role_id))
            if own_role:
                connection.execute(delete(Role).where(Role.id == role_id))
        engine.dispose()


@pytest.mark.asyncio
async def test_disconnect_cancels_runner_before_cleanup(monkeypatch, tmp_path):
    from app.api.routes import payroll_preview as route
    started = asyncio.Event()
    finished = asyncio.Event()
    async def parse(path, extension):
        started.set()
        try:
            await asyncio.sleep(60)
        finally:
            finished.set()
    class Disconnected:
        async def receive(self):
            await started.wait()
            return {'type': 'http.disconnect'}
    monkeypatch.setattr(route.preview_runner, 'run', parse)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        await route.run_connected(Disconnected(), tmp_path / 'input.pdf', '.pdf')
    assert error.value.status_code == 499
    assert finished.is_set()


@pytest.mark.asyncio
async def test_immediate_parser_error_does_not_hang_disconnect_cleanup(monkeypatch, tmp_path):
    from starlette.requests import Request
    from app.api.routes import payroll_preview as route
    from app.services.payroll_preview_files import PreviewInputError
    async def fail(path, extension):
        raise PreviewInputError(503, 'busy')
    async def receive():
        await asyncio.Event().wait()
    request = Request({'type': 'http', 'headers': []}, receive)
    monkeypatch.setattr(route.preview_runner, 'run', fail)
    with pytest.raises(PreviewInputError):
        await asyncio.wait_for(route.run_connected(request, tmp_path / 'file.pdf', '.pdf'), 0.5)


@pytest.mark.asyncio
async def test_cancelled_multipart_parse_closes_partial_spooled_files(monkeypatch):
    from starlette.datastructures import Headers, UploadFile
    from app.api.routes import payroll_preview as route
    files = []
    async def cancelled_write(self, data):
        files.append(self.file)
        raise asyncio.CancelledError()
    class UploadRequest:
        headers = Headers({'Content-Type': 'multipart/form-data; boundary=test'})
        async def stream(self):
            yield (b'--test\r\nContent-Disposition: form-data; name="file"; filename="input.pdf"\r\n'
                   b'Content-Type: application/pdf\r\n\r\n%PDF-content\r\n--test--\r\n')
    monkeypatch.setattr(UploadFile, 'write', cancelled_write)
    try:
        with pytest.raises(asyncio.CancelledError):
            await route.read_form(UploadRequest())
        assert files and all(file.closed for file in files)
    finally:
        for file in files:
            file.close()
