"""Parsers must work independently and leave supplied documents untouched."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import pandas

from app.parsers import parse_excel, parse_pdf

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND / 'tests' / 'fixtures' / 'parser_equivalence'


@pytest.mark.parametrize('reader', [parse_excel, parse_pdf])
def test_parsers_accept_only_existing_local_files(monkeypatch, reader):
    def forbidden_remote_reader(*args, **kwargs):
        pytest.fail('remote input reached the Excel fallback')

    monkeypatch.setattr(pandas, 'read_excel', forbidden_remote_reader)
    with pytest.raises(FileNotFoundError):
        reader('https://example.invalid/monthly-statement.xlsx')


def test_parsers_run_without_desktop_qt_or_database(tmp_path):
    script = '''
import importlib.abc
from decimal import Decimal
from pathlib import Path
import sys

class BlockApplicationImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == name or fullname.startswith(name + '.')
               for name in ('PySide6', 'app.core', 'sqlalchemy', 'app.models', 'sqlite3')):
            raise AssertionError('Parser loaded forbidden dependency: ' + fullname)

sys.meta_path.insert(0, BlockApplicationImports())
sys.path.insert(0, sys.argv[1])
from app.parsers import parse_pdf, parse_excel
root = Path(sys.argv[1]) / 'tests/fixtures/parser_equivalence'
for reader, case, suffix in ((parse_pdf, 'extrato_pdf', 'pdf'),
                              (parse_excel, 'extrato_xlsx', 'xlsx')):
    result = reader(root / case / ('input.' + suffix))
    assert result['competencia'] == '09/2026'
    assert len(result['colaboradores']) == 2
    assert isinstance(result['colaboradores'][0]['liquido'], Decimal)
    assert isinstance(result['colaboradores'][0]['rubricas'][0]['valor'], Decimal)
print('isolated parsing OK')
'''
    result = subprocess.run(
        [sys.executable, '-I', '-c', script, str(BACKEND)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'isolated parsing OK' in result.stdout


@pytest.mark.parametrize('case,suffix', [
    ('extrato_pdf', 'pdf'), ('extrato_xls', 'xls'), ('extrato_xlsx', 'xlsx'),
])
def test_parsers_do_not_modify_input_files(tmp_path, case, suffix):
    path = tmp_path / f'input.{suffix}'
    shutil.copyfile(ROOT / case / f'input.{suffix}', path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    reader = parse_pdf if suffix == 'pdf' else parse_excel
    reader(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [path.name]
