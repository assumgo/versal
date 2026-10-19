import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
import sqlite3
import threading
import uuid

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import NullPool

from app.migration.source import MigrationError
from app.migration.transfer import migrate
from app.models import Base


@pytest.fixture
def source(tmp_path):
    path = tmp_path / 'legacy.db'
    with sqlite3.connect(path) as db:
        db.executescript(Path(__file__).with_name('fixtures').joinpath('legacy_schema.sql').read_text())
        db.executescript("""
            INSERT INTO companies(id, razao) VALUES (41, ' Empresa sintética ');
            INSERT INTO employees(id, company_id, nome, matricula) VALUES(51,41,NULL,'0001'),(52,41,NULL,'0001');
            INSERT INTO rubrics(id,company_id,codigo,debito_gera_cc) VALUES(81,41,'001',NULL);
            INSERT INTO chart_accounts(id,company_id,conta) VALUES(91,41,'0001');
            INSERT INTO finance_params(id,company_id,documento_id) VALUES(101,41,'007');
            INSERT INTO imports(id,company_id,competencia) VALUES(61,41,'10/2026');
            INSERT INTO payroll_lines(id,company_id,import_id,valor,liquido) VALUES(71,41,61,0.1,-2.3456),(72,NULL,NULL,NULL,NULL);
        """)
    return path


@pytest.fixture
def target():
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Requires disposable TEST_DATABASE_URL')
    schema = 'migration_test_' + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as db:
        db.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={'options': f'-csearch_path={schema}'}, poolclass=NullPool)
    try:
        with engine.begin() as db:
            # Synthetic, isolated copy of the migrated table definitions.
            Base.metadata.create_all(db)
            db.execute(text('CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY)'))
            db.execute(text("INSERT INTO alembic_version VALUES ('0002')"))
            db.execute(text("INSERT INTO roles (id,name) VALUES(1,'Administrador')"))
            db.execute(text("INSERT INTO users(id,email,password_hash,role_id,is_active) VALUES(1,'admin@example.test','test',1,true)"))
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as db:
            db.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_dry_run_does_not_write_rows_or_identity(source, target):
    report = migrate(source, target)
    assert report['committed'] is False
    assert report['counts']['payroll_lines'] == 2
    with target.begin() as db:
        assert db.scalar(text('SELECT count(*) FROM companies')) == 0
        assert db.scalar(text('INSERT INTO companies DEFAULT VALUES RETURNING id')) == 1


def test_apply_preserves_every_field_and_continues_ids(source, target):
    report = migrate(source, target, apply=True)
    assert report['committed'] is True
    with target.begin() as db, sqlite3.connect(source) as old:
        old.row_factory = sqlite3.Row
        for name in ('companies', 'employees', 'rubrics', 'chart_accounts', 'finance_params', 'imports', 'payroll_lines'):
            for row in old.execute(f'SELECT * FROM {name}'):
                copied = db.execute(text(f'SELECT * FROM {name} WHERE id=:id'), {'id': row['id']}).mappings().one()
                for column in row.keys():
                    expected = Decimal(str(row[column])) if column in {'valor', 'liquido'} and row[column] is not None else row[column]
                    assert copied[column] == expected, (name, column)
        assert db.scalar(text('INSERT INTO companies DEFAULT VALUES RETURNING id')) == 42
        assert db.scalar(text('INSERT INTO employees DEFAULT VALUES RETURNING id')) == 53
        assert db.scalar(text('SELECT count(*) FROM users')) == 1
        assert db.scalar(text('SELECT count(*) FROM user_companies')) == 0
    with pytest.raises(MigrationError):
        migrate(source, target, apply=True)


@pytest.mark.parametrize('sql', [
    'INSERT INTO companies(id) VALUES(999)',
    "UPDATE alembic_version SET version_num='outdated'",
    'ALTER TABLE employees DROP COLUMN cargo',
    'ALTER TABLE employees ALTER COLUMN id DROP IDENTITY',
    'ALTER TABLE payroll_lines DROP CONSTRAINT fk_payroll_lines_company_id_import_id_imports',
])
def test_preflight_rejects_occupied_or_incompatible_target(source, target, sql):
    with target.begin() as db:
        db.execute(text(sql))
    with pytest.raises(MigrationError):
        migrate(source, target, apply=True)
    with target.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM employees')) == 0


def test_non_postgresql_is_rejected(source):
    with pytest.raises(MigrationError):
        migrate(source, create_engine('sqlite://'), apply=True)


def test_failure_after_identity_restart_rolls_back_everything(source, target):
    def fail(conn, cursor, statement, parameters, context, executemany):
        if 'RESTART WITH' in statement and 'employees' in statement:
            raise RuntimeError('injected failure')
    event.listen(target, 'after_cursor_execute', fail)
    try:
        with pytest.raises(RuntimeError):
            migrate(source, target, apply=True)
    finally:
        event.remove(target, 'after_cursor_execute', fail)
    with target.begin() as db:
        assert db.scalar(text('SELECT count(*) FROM companies')) == 0
        assert db.scalar(text('INSERT INTO companies DEFAULT VALUES RETURNING id')) == 1


def test_full_field_verification_detects_trigger_changes(source, target):
    with target.begin() as db:
        db.execute(text("""CREATE FUNCTION change_name() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN NEW.nome := 'changed'; RETURN NEW; END $$"""))
        db.execute(text('CREATE TRIGGER change_employee BEFORE INSERT ON employees FOR EACH ROW EXECUTE FUNCTION change_name()'))
    with pytest.raises(MigrationError):
        migrate(source, target, apply=True)
    with target.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM companies')) == 0


def test_concurrent_applications_serialize_and_second_refuses(source, target):
    locked = threading.Event()
    release = threading.Event()
    pids = []
    def hold(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('LOCK TABLE') and not locked.is_set():
            pids.append(conn.scalar(text('SELECT pg_backend_pid()')))
            locked.set()
            assert release.wait(10)
    event.listen(target, 'after_cursor_execute', hold)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(migrate, source, target, apply=True)
            assert locked.wait(10)
            second = pool.submit(migrate, source, target, apply=True)
            # Poll PostgreSQL's lock state, not timing alone.
            import time
            blocked = False
            deadline = time.monotonic() + 10
            with target.connect() as observer:
                while time.monotonic() < deadline:
                    blocked = observer.scalar(text('SELECT EXISTS(SELECT 1 FROM pg_locks WHERE granted=false AND pid<>:pid)'), {'pid': pids[0]})
                    if blocked:
                        break
                    time.sleep(0.02)
            release.set()
            assert blocked
            assert first.result(timeout=10)['committed']
            with pytest.raises(MigrationError):
                second.result(timeout=10)
    finally:
        release.set()
        event.remove(target, 'after_cursor_execute', hold)


def test_snapshot_cleanup_failure_happens_before_commit(source, target, monkeypatch):
    from contextlib import contextmanager
    from app.migration.source import snapshot
    @contextmanager
    def broken_cleanup(path):
        with snapshot(path) as db:
            yield db
        raise OSError('temporary cleanup failed')
    monkeypatch.setattr('app.migration.transfer.snapshot', broken_cleanup)
    with pytest.raises(OSError):
        migrate(source, target, apply=True)
    with target.connect() as db:
        assert db.scalar(text('SELECT count(*) FROM companies')) == 0


def test_interrupted_commit_is_reported_as_unknown(source, target):
    from app.migration.transfer import CommitUnknown
    def interrupt(connection):
        raise KeyboardInterrupt()
    event.listen(target, 'commit', interrupt)
    try:
        with pytest.raises(CommitUnknown):
            migrate(source, target, apply=True)
    finally:
        event.remove(target, 'commit', interrupt)
