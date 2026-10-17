"""Real PDF corpus comparisons plus controlled reader failures."""
from contextlib import contextmanager
from decimal import Decimal
import json
from pathlib import Path
from types import SimpleNamespace

import pymupdf
import pdfplumber
import pytest

from app.parsers import parse_pdf

ROOT = Path(__file__).parent / 'fixtures' / 'parser_equivalence'


def decimal_text(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(type(value).__name__)


@pytest.mark.parametrize('case', ['extrato_pdf', 'extrato_pdf_accent', 'extrato_pdf_empty'])
def test_pdf_matches_frozen_reference(case):
    result = parse_pdf(ROOT / case / 'input.pdf')
    assert json.loads(json.dumps(result, default=decimal_text)) == json.loads(
        (ROOT / case / 'expected.json').read_text()
    )
    for person in result['colaboradores']:
        assert isinstance(person['liquido'], Decimal)
        assert all(isinstance(r['valor'], Decimal) for r in person['rubricas'])


def fail_primary(*args, **kwargs):
    raise OSError('primary reader failed')


def test_pdf_fallback_reads_when_primary_fails(monkeypatch):
    monkeypatch.setattr(pdfplumber, 'open', fail_primary)
    result = parse_pdf(ROOT / 'extrato_pdf' / 'input.pdf')
    assert json.loads(json.dumps(result, default=decimal_text)) == json.loads(
        (ROOT / 'extrato_pdf' / 'expected.json').read_text()
    )
    assert result['competencia'] == '09/2026'
    assert result['empresa']['codigo_siagri'] == '901'
    assert [p['nome'] for p in result['colaboradores']] == ['ANA SINTÉTICA', 'JOÃO FICTÍCIO']
    assert [p['liquido'] for p in result['colaboradores']] == [Decimal('2700.00'), Decimal('1800.00')]


def test_empty_pdf_text_does_not_trigger_fallback(monkeypatch):
    @contextmanager
    def empty_document(path):
        yield SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda **kw: '')])

    def forbidden_fallback(*args, **kwargs):
        pytest.fail('empty text must not trigger fallback')

    monkeypatch.setattr(pdfplumber, 'open', empty_document)
    monkeypatch.setattr(pymupdf, 'open', forbidden_fallback)
    assert parse_pdf(ROOT / 'extrato_pdf_empty' / 'input.pdf')['colaboradores'] == []


def test_pdf_propagates_failure_when_both_readers_fail(monkeypatch):
    def fail_fallback(*args, **kwargs):
        raise ValueError('fallback reader failed')

    monkeypatch.setattr(pdfplumber, 'open', fail_primary)
    monkeypatch.setattr(pymupdf, 'open', fail_fallback)
    with pytest.raises(ValueError, match='fallback reader failed'):
        parse_pdf(ROOT / 'extrato_pdf' / 'input.pdf')
