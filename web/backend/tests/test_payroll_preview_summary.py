from copy import deepcopy
from decimal import Decimal

import pytest

from app.services.payroll_preview import build_preview, summarize


def statement():
    return {'competencia': '09/2026', 'empresa': {'codigo_siagri': '901', 'razao': 'Sintética',
            'cnpj': '00.000.000/0000-00'}, 'tipo_importacao': 'Extrato', 'colaboradores': [
        {'matricula': '001', 'nome': 'Ana', 'cpf': '', 'situacao': '', 'cargo': '',
         'centro_custo': '001', 'liquido': Decimal('10.00'), 'rubricas': [
             {'codigo': '001', 'descricao': 'Salário', 'referencia': '', 'tipo': 'P', 'valor': Decimal('10.00')},
             {'codigo': '001', 'descricao': 'Salário', 'referencia': '', 'tipo': 'P', 'valor': Decimal('10.00')}]},
        {'matricula': '002', 'nome': 'João', 'cpf': '', 'situacao': '', 'cargo': '',
         'centro_custo': '', 'liquido': Decimal('8.75'), 'rubricas': [
             {'codigo': '002', 'descricao': 'Ajuste', 'referencia': '', 'tipo': 'D', 'valor': Decimal('-1.25')}]}]}


def preview(data, **changes):
    options = dict(company_id=1, company_cnpj='00000000000000', competence='09/2026',
                   filename='input.xlsx', size_bytes=50, sha256='a' * 64, extension='.xlsx')
    return build_preview(data, **(options | changes))


def test_summary_counts_each_net_once_and_preserves_multiplicity():
    data = statement()
    before = deepcopy(data)
    result = summarize(data)
    assert result.employees == 2 and result.rubrics == 3
    assert result.totals_by_type == {'P': '20.00', 'D': '-1.25', 'E': '0'}
    assert result.net_total == '18.75'
    response = preview(data)
    assert response.statement.colaboradores[0].rubricas[0].valor == '10.00'
    assert len(response.statement.colaboradores[0].rubricas) == 2
    assert data == before


def test_summary_preserves_large_fractional_decimals():
    data = statement()
    values = [Decimal('123456789012345678901234567890.123456789'), Decimal('0.000000001')]
    for person, value in zip(data['colaboradores'], values):
        person['liquido'] = value
        person['rubricas'] = [dict(person['rubricas'][0], valor=value, tipo='P')]
    result = summarize(data)
    assert result.net_total == '123456789012345678901234567890.123456790'
    assert result.totals_by_type['P'] == result.net_total


@pytest.mark.parametrize('field,value,code', [
    ('cnpj', '', 'company_cnpj_missing'), ('cnpj', '11111111111111', 'company_cnpj_mismatch'),
    ('competencia', '', 'competence_missing'), ('competencia', '13/2026', 'competence_invalid'),
    ('competencia', '08/2026', 'competence_mismatch'),
])
def test_preview_context_issues(field, value, code):
    data = statement()
    if field == 'cnpj':
        data['empresa']['cnpj'] = value
    else:
        data[field] = value
    result = preview(data)
    assert result.status == 'blocked'
    assert code in [issue.code for issue in result.issues if issue.severity == 'blocking']


@pytest.mark.parametrize('cnpj', [None, '', '123'])
def test_incomplete_registered_cnpj_blocks(cnpj):
    assert preview(statement(), company_cnpj=cnpj).status == 'blocked'


def test_empty_result_is_blocked_and_warnings_are_format_specific():
    for extension, code in [('.pdf', 'pdf_known_limitations'), ('.xlsx', 'excel_known_limitations')]:
        result = preview(statement(), extension=extension)
        assert result.status == 'ready'
        assert {issue.code for issue in result.issues} == {'homologation_pending', code}
    data = statement()
    data['colaboradores'] = []
    result = preview(data)
    assert result.status == 'blocked'
    assert {'no_employees', 'no_rubrics'} <= {issue.code for issue in result.issues}
