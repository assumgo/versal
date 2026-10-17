"""Frozen corpus must preserve independently checked totals and artifact hashes."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent / 'fixtures' / 'parser_equivalence'
CASES = [
    ('extrato_pdf', 2, 4, '5000', '500', '4500'),
    ('extrato_xls', 2, 4, '5000', '500', '4500'),
    ('extrato_xlsx', 2, 4, '5000', '500', '4500'),
    ('extrato_xlsx_edge', 2, 6, '5000', '479', '4500'),
    ('extrato_pdf_accent', 2, 2, '0', '500', '4500'),
    ('extrato_pdf_empty', 0, 0, '0', '0', '0'),
    ('extrato_xlsx_empty', 0, 0, '0', '0', '0'),
]


@pytest.mark.parametrize('case,employees,lines,provents,discounts,net', CASES)
def test_frozen_parser_corpus_integrity_and_totals(case, employees, lines, provents, discounts, net):
    folder = ROOT / case
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    for artifact in ('input', 'expected'):
        description = manifest[artifact]
        assert hashlib.sha256((folder / description['file']).read_bytes()).hexdigest() == description['sha256']
    output = json.loads((folder / manifest['expected']['file']).read_text(encoding='utf-8'))
    people = output['colaboradores']
    rubrics = [r for person in people for r in person['rubricas']]
    assert len(people) == employees
    assert len(rubrics) == lines
    assert sum((Decimal(r['valor']) for r in rubrics if r['tipo'] == 'P'), Decimal('0')) == Decimal(provents)
    assert sum((Decimal(r['valor']) for r in rubrics if r['tipo'] == 'D'), Decimal('0')) == Decimal(discounts)
    assert sum((Decimal(p['liquido']) for p in people), Decimal('0')) == Decimal(net)


def test_excel_variants_agree_and_pdf_discrepancy_stays_explicit():
    xls = json.loads((ROOT / 'extrato_xls' / 'expected.json').read_text(encoding='utf-8'))
    xlsx = json.loads((ROOT / 'extrato_xlsx' / 'expected.json').read_text(encoding='utf-8'))
    pdf = json.loads((ROOT / 'extrato_pdf' / 'expected.json').read_text(encoding='utf-8'))
    assert xls == xlsx
    # Characterize the original parser's CC/rubric ambiguity; do not normalize it away.
    assert xlsx['colaboradores'][0]['rubricas'][0]['codigo'] == '001'
    assert pdf['colaboradores'][0]['rubricas'][0]['codigo'] == '0001'
    assert pdf['colaboradores'][0]['rubricas'][0]['descricao'] == '001 SALARIO BASE'
