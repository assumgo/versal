"""Read a stable legacy SQLite copy without opening the original with SQLite."""
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory


class MigrationError(Exception):
    """A sanitized, actionable migration failure."""


# Explicit allowlist: no identifiers from the source become SQL identifiers.
TABLE_COLUMNS = {
    'companies': ('id', 'codigo_siagri', 'razao', 'fantasia', 'cnpj', 'status'),
    'employees': ('id', 'company_id', 'nome', 'cpf', 'matricula', 'cargo', 'centro_custo', 'codigo_correntista', 'status'),
    'rubrics': ('id', 'company_id', 'codigo', 'descricao', 'tipo', 'conta_debito', 'conta_credito', 'historico_id', 'historico', 'status', 'debito_gera_cc', 'debito_gera_cor', 'credito_gera_cc', 'credito_gera_cor'),
    'chart_accounts': ('id', 'company_id', 'conta', 'descricao', 'utiliza_cc', 'tipo_correntista', 'gera_cor'),
    'finance_params': ('id', 'company_id', 'tipo', 'documento_id', 'parceiro_cpf_cnpj', 'codigo_parceiro_siagri', 'conta_contrapartida', 'centro_custo', 'vencimento_dia', 'historico', 'ativo'),
    'imports': ('id', 'company_id', 'competencia', 'arquivo', 'data_hora', 'status'),
    'payroll_lines': ('id', 'import_id', 'company_id', 'cpf', 'nome', 'cargo', 'codigo_verba', 'verba', 'referencia', 'valor', 'tipo', 'liquido'),
}
SMALL_INTEGERS = {'debito_gera_cc', 'debito_gera_cor', 'credito_gera_cc', 'credito_gera_cor',
                  'utiliza_cc', 'gera_cor', 'vencimento_dia', 'ativo'}
MONEY = {'valor', 'liquido'}
BIGINT_MIN, BIGINT_MAX = -(2 ** 63), 2 ** 63 - 1


def column_kind(column: str) -> str:
    if column in {'id', 'company_id', 'import_id'} | SMALL_INTEGERS:
        return 'INTEGER'
    return 'NUMERIC' if column in MONEY else 'TEXT'


def _fingerprint(path: Path) -> tuple | None:
    try:
        with path.open('rb') as stream:
            stat = path.stat()
            digest = hashlib.file_digest(stream, 'sha256').digest()
            after = path.stat()
        if (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) != (
                after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise MigrationError('Origem em alteração; feche o desktop e tente novamente')
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, digest
    except FileNotFoundError:
        return None


@contextmanager
def snapshot(source: Path) -> Iterator[sqlite3.Connection]:
    """Copy a quiescent DB/WAL/SHM, verify stability, then use SQLite backup."""
    try:
        source = source.expanduser().resolve(strict=True)
        if not source.is_file():
            raise MigrationError('A origem deve ser um arquivo SQLite')
        with TemporaryDirectory(prefix='versal-migration-') as folder:
            paths = [Path(str(source) + suffix) for suffix in ('', '-wal', '-shm', '-journal')]
            if paths[-1].exists():
                raise MigrationError('Journal SQLite presente; feche o desktop e obtenha uma cópia consistente')
            before = [_fingerprint(p) for p in paths]
            copied = Path(folder) / 'source.db'
            for path, fingerprint, suffix in zip(paths, before, ('', '-wal', '-shm')):
                if fingerprint is not None:
                    target = Path(str(copied) + suffix)
                    shutil.copyfile(path, target)
                    target.chmod(0o600)
                    with target.open('rb') as stream:
                        if hashlib.file_digest(stream, 'sha256').digest() != fingerprint[-1]:
                            raise MigrationError('Origem em alteração; feche o desktop e tente novamente')
            if [_fingerprint(p) for p in paths] != before:
                raise MigrationError('Origem em alteração; feche o desktop e tente novamente')
            source_db = sqlite3.connect(copied.as_uri() + '?mode=ro', uri=True)
            frozen_path = Path(folder) / 'snapshot.db'
            frozen = sqlite3.connect(frozen_path)
            frozen_path.chmod(0o600)
            try:
                source_db.backup(frozen)
                frozen.execute('PRAGMA query_only=ON')
                frozen.row_factory = sqlite3.Row
                if [r[0] for r in frozen.execute('PRAGMA quick_check')] != ['ok']:
                    raise MigrationError('Falha na integridade do SQLite')
                yield frozen
            finally:
                frozen.close()
                source_db.close()
    except MigrationError:
        raise
    except (OSError, sqlite3.Error):
        raise MigrationError('Não foi possível ler o SQLite; confira o arquivo e feche o desktop') from None


def iter_rows(db: sqlite3.Connection, table: str) -> Iterator[dict]:
    columns = TABLE_COLUMNS[table]
    expressions = [f'CAST("{c}" AS TEXT) AS "{c}"' if c in MONEY else f'"{c}"' for c in columns]
    for column in columns:
        if column in MONEY and db.execute(
                f'''SELECT 1 FROM "{table}" WHERE typeof("{column}") NOT IN ('integer', 'real', 'null') LIMIT 1''').fetchone():
            raise MigrationError(f'Tipo monetário incompatível em {table}, coluna {column}')
    for column in columns:
        if column in MONEY and db.execute(
                f'''SELECT 1 FROM "{table}" WHERE typeof("{column}")='real'
                    AND CAST(CAST("{column}" AS TEXT) AS REAL)<>"{column}" LIMIT 1''').fetchone():
            raise MigrationError(f'Precisão monetária não preservável por texto em {table}, coluna {column}; carga bloqueada')
    for record in db.execute(f'SELECT {", ".join(expressions)} FROM "{table}" ORDER BY id'):
        row = dict(record)
        if type(row['id']) is not int or not BIGINT_MIN <= row['id'] < BIGINT_MAX:
            raise MigrationError(f'ID inválido em {table}')
        for column, value in row.items():
            if value is None:
                continue
            kind = column_kind(column)
            valid = True
            if kind == 'NUMERIC':
                try:
                    value = Decimal(value)
                    valid = value.is_finite()
                    row[column] = value
                except (InvalidOperation, ValueError, TypeError):
                    valid = False
            elif kind == 'INTEGER':
                minimum, maximum = (-(2 ** 31), 2 ** 31 - 1) if column in SMALL_INTEGERS else (BIGINT_MIN, BIGINT_MAX)
                valid = type(value) is int and minimum <= value <= maximum
                if column == 'id' and value == BIGINT_MAX:
                    valid = False
            else:
                valid = isinstance(value, str) and '\0' not in value
                if valid:
                    try:
                        value.encode('utf-8')
                    except UnicodeError:
                        valid = False
            if not valid:
                raise MigrationError(f'Valor incompatível em {table}, ID {row["id"]}, coluna {column}')
        yield row


def summarize(counts: dict, totals: dict, extra_tables: list[str]) -> dict:
    return {
        'counts': counts,
        'totals': [{'company_id': company, 'competencia': competence,
                    'valor': str(values[0]), 'liquido': str(values[1])}
                   for (company, competence), values in sorted(totals.items(), key=lambda item: (
                       item[0][0] is not None, item[0][0] or 0, item[0][1] is not None, item[0][1] or ''))],
        'extra_tables': extra_tables,
    }


def validate_source(db: sqlite3.Connection) -> dict:
    names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    if not set(TABLE_COLUMNS) <= names:
        raise MigrationError('Tabelas legadas obrigatórias ausentes')
    for table, columns in TABLE_COLUMNS.items():
        schema = db.execute(f'PRAGMA table_xinfo("{table}")').fetchall()
        if {r['name'] for r in schema} != set(columns) or any(
                r['hidden'] != 0 or r['type'].upper() != column_kind(r['name']) or bool(r['pk']) != (r['name'] == 'id') for r in schema):
            raise MigrationError(f'Esquema incompatível em {table}')
        if any(r['origin'] == 'pk' for r in db.execute(f'PRAGMA index_list("{table}")')):
            raise MigrationError(f'Chave primária SQLite incompatível em {table}')
    # Validate every ID and field before any relational diagnostic uses an ID.
    counts = {table: sum(1 for _ in iter_rows(db, table)) for table in TABLE_COLUMNS}
    for table in TABLE_COLUMNS:
        if table != 'companies':
            orphan = db.execute(f'SELECT id FROM "{table}" WHERE company_id IS NOT NULL AND NOT EXISTS '
                                f'(SELECT 1 FROM companies c WHERE c.id="{table}".company_id) LIMIT 1').fetchone()
            if orphan:
                raise MigrationError(f'Empresa inexistente em {table}, ID {orphan[0]}')
    bad_import = db.execute('''SELECT p.id FROM payroll_lines p LEFT JOIN imports i ON i.id=p.import_id
        WHERE p.import_id IS NOT NULL AND (i.id IS NULL OR
        (p.company_id IS NOT NULL AND (i.company_id IS NULL OR p.company_id<>i.company_id))) LIMIT 1''').fetchone()
    if bad_import:
        raise MigrationError(f'Importação inexistente ou empresa divergente em payroll_lines, ID {bad_import[0]}')
    totals = {}
    # SQLite REAL has at most ~309 integer digits; sufficient exact accumulator even for very large corpora.
    with localcontext() as context:
        context.prec = 1000
        for row in iter_rows(db, 'payroll_lines'):
            competence = None
            if row['import_id'] is not None:
                competence = db.execute('SELECT competencia FROM imports WHERE id=?', (row['import_id'],)).fetchone()[0]
            values = totals.setdefault((row['company_id'], competence), [Decimal(0), Decimal(0)])
            for index, column in enumerate(('valor', 'liquido')):
                if row[column] is not None:
                    values[index] += row[column]
    return summarize(counts, totals, sorted(names - set(TABLE_COLUMNS)))
