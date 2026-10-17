"""Characterize desktop parsing decisions independently of file readers."""
from datetime import date
from decimal import Decimal

import pytest

from app.parsers.common import br_to_decimal, parse_company_from_text
from app.parsers.extrato import parse_extrato_rows, parse_extrato_text


@pytest.mark.parametrize('value,expected', [
    (None, '0'), ('', '0'), ('sem valor', '0'),
    ('R$ -1.234,56', '-1234.56'), ('1234.56', '1234.56'),
    ('12', '12.00'), (42, '42.00'), (12.5, '12.50'),
    (Decimal('1.2345'), '1.2345'), ('total 10,00 saldo 20,00', '20.00'),
])
def test_money_conversion_preserves_desktop_decimal_rules(value, expected):
    result = br_to_decimal(value)
    assert isinstance(result, Decimal)
    assert str(result) == expected


def test_company_identity_comes_from_content():
    assert parse_company_from_text(
        '901 - EMPRESA SINTÉTICA LTDA\nCNPJ: 00.000.000/0000-00'
    ) == {'codigo_siagri': '901', 'razao': 'EMPRESA SINTÉTICA LTDA',
          'cnpj': '00.000.000/0000-00'}


def test_rows_preserve_duplicate_and_zero_behavior():
    rows = [
        ['Competência:', date(2026, 9, 1)],
        ['Empr.:', '0001', 'ANA SINTÉTICA', 'CPF:', '000.000.000-00'],
        ['CC:', '0001'],
        ['001', 'SALARIO BASE', '30,00', '3000,00', 'P'],
        ['001', 'SALARIO BASE', '30,00', '3000,00', 'P'],
        ['001', 'SALARIO BASE', '30,00', '-20,00', 'P'],
        ['002', 'ZERO', '0,00', '0,00', 'D'],
        ['Líquido:', '2980,00'],
    ]
    result = parse_extrato_rows(rows)
    assert result['competencia'] == '09/2026'
    person, = result['colaboradores']
    assert person['matricula'] == '0001'
    assert person['centro_custo'] == '0001'
    assert person['liquido'] == Decimal('2980.00')
    assert person['rubricas'] == [
        {'codigo': '001', 'descricao': 'SALARIO BASE', 'referencia': '30,00',
         'valor': Decimal('3000.00'), 'tipo': 'P'},
        {'codigo': '001', 'descricao': 'SALARIO BASE', 'referencia': '30,00',
         'valor': Decimal('-20.00'), 'tipo': 'P'},
    ]


def test_text_preserves_known_accent_and_cc_discrepancies():
    header = ('09/2026\nEmpr.: 0001 ANA SINTÉTICA Situação: Ativo '
              'CPF: 000.000.000-00\nCargo: 1 ANALISTA C.B.O\n')
    plain = parse_extrato_text(header + 'CC: 0001 001 SALARIO BASE 30,00 3000,00 P\n')
    accented = parse_extrato_text(header + 'CC: 0001 001 SALÁRIO BASE 30,00 3000,00 P\n')
    assert plain['colaboradores'][0]['rubricas'] == [
        {'codigo': '0001', 'descricao': '001 SALARIO BASE', 'referencia': '30,00',
         'valor': Decimal('3000.00'), 'tipo': 'P'},
    ]
    assert accented['colaboradores'][0]['rubricas'] == []


def test_empty_text_and_rows_keep_desktop_shape():
    expected = {'competencia': '', 'colaboradores': [], 'tipo_importacao': 'Extrato',
                'empresa': {'codigo_siagri': '', 'razao': '', 'cnpj': ''}}
    assert parse_extrato_text('') == expected
    assert parse_extrato_rows([]) == expected
