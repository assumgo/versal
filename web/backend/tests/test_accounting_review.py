"""Hand-checked synthetic examples from desktop refresh_param_contabil rules."""
from decimal import Decimal

import pytest
from sqlalchemy import event, select

from test_authorization import admin_db, accounts, client, headers, COMPANIES
from app.models import AuditLog, ChartAccount, Employee, PayrollImport, PayrollLine, Rubric


def endpoint(accounts, resource='accounting-review', private=False):
    return f'{COMPANIES}/{accounts[1][int(private)].id}/{resource}'


def imported(db, company, *, competence='09/2026', source='Extrato', **values):
    imp = PayrollImport(company_id=company, competencia=competence, status=source, arquivo='synthetic.txt')
    db.add(imp)
    db.flush()
    line = PayrollLine(company_id=company, import_id=imp.id, nome='Ana Sintética', cpf='001.234', codigo_verba='01', verba='Salário', valor=Decimal('123.45'), **values)
    db.add(line)
    db.flush()
    return imp, line


@pytest.mark.asyncio
async def test_review_combines_sources_without_mutation(client, accounts, admin_db):
    company = accounts[1][0].id
    for source in ('Extrato', 'Encargos', 'Provisão Férias', 'Provisão 13'):
        imported(admin_db, company, source=source)
    imported(admin_db, company, competence='08/2026')
    imported(admin_db, accounts[1][1].id)
    emp = Employee(company_id=company, nome='Nome cadastrado', cpf='001.234', centro_custo='0001', codigo_correntista='outro', status='Inativo')
    rb = Rubric(company_id=company, codigo='01', conta_debito='00123', conta_credito='00456', historico_id='182', historico='Texto legado', status='Inativa', debito_gera_cc=0, debito_gera_cor=0, credito_gera_cc=1, credito_gera_cor=1)
    plan = ChartAccount(company_id=company, conta='00123', utiliza_cc=1, gera_cor=1)
    admin_db.add_all([emp, rb, plan]); admin_db.commit()
    before = {model: [(r.id, r.updated_at) for r in admin_db.scalars(select(model))] for model in (PayrollImport, PayrollLine, Employee, Rubric, ChartAccount)}
    async with client:
        result = await client.get(endpoint(accounts), headers=headers(accounts), params={'competence': '09/2026'})
        assert result.status_code == 200, result.text
        page = result.json()
        assert page['total'] == 4 and page['limit'] == 50
        assert {r['fonte'] for r in page['items']} == {'Extrato', 'Encargos', 'Provisão Férias', 'Provisão 13'}
        row = page['items'][0]
        assert {key: row[key] for key in ('cpf', 'nome', 'valor', 'conta_debito', 'debito_gera_cc', 'debito_gera_cor', 'conta_credito', 'credito_gera_cc', 'credito_gera_cor', 'historico_id', 'historico', 'centro_custo', 'correntista')} == {
            'cpf': '001.234', 'nome': 'Ana Sintética', 'valor': '123.45', 'conta_debito': '00123', 'debito_gera_cc': True, 'debito_gera_cor': True,
            'conta_credito': '00456', 'credito_gera_cc': True, 'credito_gera_cor': True, 'historico_id': '000000182', 'historico': 'Texto legado', 'centro_custo': '0001', 'correntista': '001234'}
    admin_db.expire_all()
    assert before == {model: [(r.id, r.updated_at) for r in admin_db.scalars(select(model))] for model in before}
    assert admin_db.scalar(select(AuditLog.id)) is None


@pytest.mark.asyncio
async def test_review_matches_desktop_cc_cor_compatibility_and_history(client, accounts, admin_db):
    company = accounts[1][0].id
    imp, base = imported(admin_db, company)
    admin_db.delete(base)
    # plan cc, plan cor, rubric cc, rubric cor, account, linked, want CC, want COR
    cases = [(0,0,0,0,'00123',True,False,False), (1,0,0,1,'00124',True,True,True),
             (0,1,1,0,'00125',True,True,True), (0,0,0,0,'4211020001',True,False,True),
             (0,0,0,0,'4211010001',True,False,True), (0,0,0,0,'4211020001',False,False,False),
             (2,2,-1,-1,'00128',True,True,True)]
    admin_db.add(Employee(company_id=company, cpf='linked', nome='Funcionária', centro_custo='001'))
    for index, (pcc, pcor, rcc, rcor, account, linked, *_expected) in enumerate(cases):
        code = str(index)
        admin_db.add_all([Rubric(company_id=company, codigo=code, conta_debito=account, debito_gera_cc=rcc, debito_gera_cor=rcor, historico_id='sem número'),
                         ChartAccount(company_id=company, conta=account, utiliza_cc=pcc, gera_cor=pcor),
                         PayrollLine(company_id=company, import_id=imp.id, nome=code, cpf='linked' if linked else 'absent', codigo_verba=code)])
    # Plan COR alone is ignored when rubric is absent.
    admin_db.add(PayrollLine(company_id=company, import_id=imp.id, nome='Z', codigo_verba='missing'))
    admin_db.commit()
    async with client:
        result = await client.get(endpoint(accounts), headers=headers(accounts), params={'competence': '09/2026'})
        assert result.status_code == 200, result.text
        rows = result.json()['items']
        for row, case in zip(rows, cases):
            assert (row['debito_gera_cc'], row['debito_gera_cor']) == case[-2:]
            assert row['historico_id'] == ''
        assert rows[-1]['debito_gera_cor'] is False and rows[-1]['historico_id'] == ''


@pytest.mark.asyncio
async def test_review_employee_matching_and_duplicate_precedence(client, accounts, admin_db):
    company = accounts[1][0].id
    imp, base = imported(admin_db, company)
    admin_db.add_all([Employee(company_id=company, cpf='001.234', nome='Outro', centro_custo='PRIMEIRO'),
                     Employee(company_id=company, cpf='001.234', nome='Outro', centro_custo='SEGUNDO'),
                     Employee(company_id=company, cpf='999', nome='Ana Sintética', centro_custo='NOME'),
                     Employee(company_id=company, cpf='888', nome='ana sintética', centro_custo='NOME2'),
                     Employee(company_id=accounts[1][1].id, cpf='001.234', nome='Outro', centro_custo='PRIVADO'),
                     Rubric(company_id=company, codigo='01', conta_debito='00.123', historico='primeiro'),
                     Rubric(company_id=company, codigo='01', conta_debito='99999', historico='segundo'),
                     ChartAccount(company_id=company, conta='00123', utiliza_cc=0, gera_cor=0),
                     ChartAccount(company_id=company, conta='00123', utiliza_cc=1, gera_cor=1)])
    admin_db.flush()
    rb = admin_db.scalar(select(Rubric).where(Rubric.company_id == company).order_by(Rubric.id))
    rb.debito_gera_cc = 0; rb.debito_gera_cor = 0
    admin_db.add_all([PayrollLine(company_id=company, import_id=imp.id, cpf='', nome='ANA SINTÉTICA', codigo_verba='01'),
                     PayrollLine(company_id=company, import_id=imp.id, cpf='unmatched', nome='Ana Sintética', codigo_verba='01')])
    admin_db.commit()
    async with client:
        result = await client.get(endpoint(accounts), headers=headers(accounts), params={'competence': '09/2026'})
        assert result.status_code == 200, result.text
        rows = result.json()['items']
        assert len(rows) == 3
        by_cpf = {row['cpf']: row for row in rows}
        assert by_cpf['001.234']['centro_custo'] == 'PRIMEIRO'
        assert by_cpf['']['centro_custo'] == 'NOME'
        assert by_cpf['unmatched']['centro_custo'] == ''
        assert all(row['historico'] == 'primeiro' and row['debito_gera_cc'] is False and row['debito_gera_cor'] is False for row in rows)


@pytest.mark.asyncio
async def test_review_preserves_decimal_nulls_and_line_multiplicity(client, accounts, admin_db):
    company = accounts[1][0].id
    imp, line = imported(admin_db, company)
    line.valor = Decimal('12345678901234567890.123456789')
    rb = Rubric(company_id=company, codigo='01', conta_debito='00123')
    plan = ChartAccount(company_id=company, conta='00123')
    admin_db.add_all([rb, plan]); admin_db.flush()
    rb.historico_id = None; rb.historico = None
    rb.debito_gera_cc = None; rb.debito_gera_cor = None
    plan.utiliza_cc = None; plan.gera_cor = None
    for _ in range(100):
        admin_db.add(PayrollLine(company_id=company, import_id=imp.id, cpf=None, nome=None, codigo_verba='01', valor=None))
    admin_db.commit()
    statements = []
    connection = admin_db.connection()
    def record(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith('SELECT'):
            statements.append(statement)
    event.listen(connection, 'before_cursor_execute', record)
    try:
        async with client:
            result = await client.get(endpoint(accounts), headers=headers(accounts), params={'competence': '09/2026', 'limit': 100})
            assert result.status_code == 200, result.text
            page = result.json()
            assert page['total'] == 101 and len(page['items']) == 100
            assert all(row['valor'] is None for row in page['items'])
            assert all(row['debito_gera_cc'] is False and row['debito_gera_cor'] is False and row['historico_id'] == '' and row['historico'] is None for row in page['items'])
            assert len(statements) <= 10  # auth + count/page + batched lookups, not one query per row
            result = await client.get(endpoint(accounts), headers=headers(accounts), params={'competence': '09/2026', 'offset': 100})
            assert result.json()['items'][0]['valor'] == '12345678901234567890.123456789'
    finally:
        event.remove(connection, 'before_cursor_execute', record)
    admin_db.refresh(plan)
    assert plan.utiliza_cc is None and plan.gera_cor is None


@pytest.mark.asyncio
@pytest.mark.parametrize('role', ['Administrador', 'Contador', 'Operador', 'Consulta'])
async def test_review_scope_competences_pagination_and_invalid_input(client, accounts, admin_db, role):
    company = accounts[1][0].id
    for competence in ('09/2026', '09/2026', '12/2025', '01/2026', '', None, 'legado'):
        imported(admin_db, company, competence=competence)
    imported(admin_db, accounts[1][1].id, competence='10/2026')
    admin_db.commit()
    auth = headers(accounts, role)
    async with client:
        response = await client.get(endpoint(accounts, 'competences'), headers=auth)
        assert response.status_code == 200, response.text
        assert response.json() == ['09/2026', '01/2026', '12/2025', 'legado']
        assert (await client.get(endpoint(accounts, 'competences', True), headers=auth)).status_code == 403
        assert (await client.get(endpoint(accounts, private=True), headers=auth, params={'competence': '09/2026'})).status_code == 403
        page = (await client.get(endpoint(accounts), headers=auth, params={'competence': '09/2026', 'offset': 1, 'limit': 1})).json()
        assert page['total'] == 2 and len(page['items']) == 1 and page['offset'] == 1
        assert (await client.get(endpoint(accounts), headers=auth, params={'competence': '10/2026'})).json()['items'] == []
        for query in ({}, {'competence': '00/2026'}, {'competence': '13/2026'}, {'competence': '2026-09'}, {'competence': '9/2026'}, {'competence': '09/2026', 'limit': 101}, {'competence': '09/2026', 'offset': -1}):
            assert (await client.get(endpoint(accounts), headers=auth, params=query)).status_code == 422
        accounts[1][0].status = 'Inativa'; admin_db.commit()
        assert (await client.get(endpoint(accounts), headers=auth, params={'competence': '09/2026'})).status_code == 200


@pytest.mark.asyncio
async def test_review_never_matches_null_names_to_null_employee_names(client, accounts, admin_db):
    company = accounts[1][0].id
    imp, line = imported(admin_db, company)
    admin_db.add_all([Employee(company_id=company, cpf='001.234', nome=None, centro_custo='CPF ONLY'),
                     PayrollLine(company_id=company, import_id=imp.id, cpf='', nome=None, codigo_verba='01')])
    admin_db.commit()
    async with client:
        result = await client.get(endpoint(accounts), headers=headers(accounts), params={'competence': '09/2026'})
        assert result.status_code == 200
        rows = result.json()['items']
        assert rows[0]['nome'] is None and rows[0]['centro_custo'] == ''
        assert rows[1]['centro_custo'] == 'CPF ONLY'
