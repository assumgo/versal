import hashlib
import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from app.migration.source import MigrationError, iter_rows, snapshot, validate_source


@pytest.fixture
def source(tmp_path):
    path = tmp_path / 'source #?.db'
    with sqlite3.connect(path) as db:
        db.executescript(Path(__file__).with_name('fixtures').joinpath('legacy_schema.sql').read_text())
        db.executescript("""
            INSERT INTO companies (id, razao, cnpj) VALUES (41, ' Empresa sintética ', '11.222.333/0001-81');
            INSERT INTO employees (id, company_id, nome, matricula) VALUES (51, 41, NULL, '0001'), (52, 41, NULL, '0001');
            INSERT INTO imports (id, company_id, competencia) VALUES (61, 41, '10/2026');
            INSERT INTO payroll_lines (id, company_id, import_id, valor, liquido) VALUES (71, 41, 61, 0.1, -2.3456);
        """)
    return path


def test_snapshot_preserves_fields_and_decimal(source):
    with snapshot(source) as db:
        result = validate_source(db)
        assert result['counts']['companies'] == 1
        assert result['counts']['employees'] == 2
        assert list(iter_rows(db, 'companies'))[0]['razao'] == ' Empresa sintética '
        rows = list(iter_rows(db, 'employees'))
        assert [r['nome'] for r in rows] == [None, None]
        assert [r['matricula'] for r in rows] == ['0001', '0001']
        row = list(iter_rows(db, 'payroll_lines'))[0]
        assert row['valor'] == Decimal('0.1')
        assert row['liquido'] == Decimal('-2.3456')
        assert result['totals'] == [{'company_id': 41, 'competencia': '10/2026', 'valor': '0.1', 'liquido': '-2.3456'}]


def test_snapshot_includes_wal_without_touching_original(source):
    db = sqlite3.connect(source)
    try:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute("INSERT INTO companies (id, razao) VALUES (42, 'WAL')")
        db.commit()
        paths = [Path(str(source) + s) for s in ('', '-wal', '-shm')]
        before = [(p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).digest()) for p in paths]
        with snapshot(source) as copied:
            assert validate_source(copied)['counts']['companies'] == 2
        after = [(p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).digest()) for p in paths]
        assert after == before
    finally:
        db.close()


@pytest.mark.parametrize('sql', [
    'ALTER TABLE companies ADD COLUMN surprise TEXT',
    'ALTER TABLE companies DROP COLUMN fantasia',
    'UPDATE employees SET company_id=999',
    'UPDATE payroll_lines SET import_id=999',
    'INSERT INTO companies(id) VALUES (42); UPDATE imports SET company_id=42',
    "UPDATE payroll_lines SET valor='not money'",
    "UPDATE payroll_lines SET liquido='Infinity'",
    "UPDATE employees SET codigo_correntista=x'0102'",
    'INSERT INTO rubrics(id, company_id, debito_gera_cc) VALUES(91,41,2147483648)',
    'INSERT INTO companies (id) VALUES (9223372036854775807)',
])
def test_rejects_incompatible_source(source, sql):
    with sqlite3.connect(source) as db:
        db.executescript(sql)
    with pytest.raises(MigrationError):
        with snapshot(source) as copied:
            validate_source(copied)


def test_rejects_nul_without_echoing_personal_data(source):
    with sqlite3.connect(source) as db:
        db.execute('UPDATE employees SET nome=?', ('private-person\0secret',))
    with pytest.raises(MigrationError) as error:
        with snapshot(source) as copied:
            validate_source(copied)
    assert 'private-person' not in str(error.value)


def test_accepts_nullable_references_and_reports_additional_tables(source):
    with sqlite3.connect(source) as db:
        db.executescript('CREATE TABLE extra (id INTEGER); UPDATE payroll_lines SET company_id=NULL; UPDATE employees SET company_id=NULL')
    with snapshot(source) as copied:
        report = validate_source(copied)
        assert report['extra_tables'] == ['extra']
        assert report['counts']['payroll_lines'] == 1


@pytest.mark.parametrize('content', [None, b'not a sqlite database'])
def test_rejects_missing_or_invalid_file(tmp_path, content):
    path = tmp_path / 'bad.db'
    if content is not None:
        path.write_bytes(content)
    with pytest.raises(MigrationError):
        with snapshot(path) as copied:
            validate_source(copied)


def test_rejects_blob_even_if_it_looks_like_a_number(source):
    with sqlite3.connect(source) as db:
        db.execute("UPDATE payroll_lines SET valor=x'3132'")
    with pytest.raises(MigrationError):
        with snapshot(source) as db:
            validate_source(db)


def test_refuses_rollback_journal_instead_of_loading_uncommitted_pages(source):
    Path(str(source) + '-journal').write_bytes(b'pending rollback')
    with pytest.raises(MigrationError):
        with snapshot(source) as db:
            validate_source(db)


def test_detects_source_changed_during_copy(source, monkeypatch):
    import shutil
    copy = shutil.copyfile
    def change_after_copy(src, dst):
        result = copy(src, dst)
        if Path(src) == source:
            with sqlite3.connect(source) as original:
                original.execute("INSERT INTO companies(id) VALUES(99)")
        return result
    monkeypatch.setattr('app.migration.source.shutil.copyfile', change_after_copy)
    with pytest.raises(MigrationError, match='alteração'):
        with snapshot(source) as db:
            validate_source(db)


def test_refuses_real_value_that_text_cast_would_round(source):
    with sqlite3.connect(source) as db:
        db.execute('UPDATE payroll_lines SET valor=1.2345678901234567')
    with pytest.raises(MigrationError):
        with snapshot(source) as db:
            validate_source(db)


def test_refuses_extra_generated_column(source):
    with sqlite3.connect(source) as db:
        db.execute("ALTER TABLE companies ADD COLUMN unexpected TEXT GENERATED ALWAYS AS (razao || '!') VIRTUAL")
    with pytest.raises(MigrationError):
        with snapshot(source) as db:
            validate_source(db)


@pytest.mark.parametrize('bad_id', [None, 'private-id-secret'])
def test_refuses_non_rowid_primary_key_and_never_echoes_invalid_id(source, bad_id):
    with sqlite3.connect(source) as db:
        db.executescript('''
            DROP TABLE employees;
            CREATE TABLE employees(id INTEGER PRIMARY KEY DESC, company_id INTEGER,
                nome TEXT, cpf TEXT, matricula TEXT, cargo TEXT, centro_custo TEXT,
                codigo_correntista TEXT, status TEXT DEFAULT 'Ativo');
        ''')
        db.execute('INSERT INTO employees(id, company_id) VALUES(?,41)', (bad_id,))
    with pytest.raises(MigrationError) as error:
        with snapshot(source) as db:
            validate_source(db)
    assert 'private-id-secret' not in str(error.value)
