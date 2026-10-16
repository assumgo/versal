"""Atomic transfer into an empty, migrated PostgreSQL schema."""
from decimal import Decimal
from itertools import islice, zip_longest
from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, func, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.migration.source import MigrationError, TABLE_COLUMNS, iter_rows, snapshot, summarize, validate_source
from app.models import Base

VERSION = '1'


class CommitUnknown(MigrationError):
    """A connection failure prevented confirmation of the commit outcome."""


def _preflight(connection) -> str:
    inspector = inspect(connection)
    schema = connection.scalar(text('SELECT current_schema()'))
    if not schema:
        raise MigrationError('Nenhum esquema PostgreSQL selecionado')
    directory = Path(__file__).resolve().parents[2] / 'alembic'
    config = Config()
    config.set_main_option('script_location', str(directory))
    heads = set(ScriptDirectory.from_config(config).get_heads())
    if set(MigrationContext.configure(connection).get_current_heads()) != heads:
        raise MigrationError('Aplique alembic upgrade head no destino antes da migração')
    if not set(Base.metadata.tables) <= set(inspector.get_table_names(schema=schema)):
        raise MigrationError('Esquema PostgreSQL incompleto')
    for name in TABLE_COLUMNS:
        expected = Base.metadata.tables[name]
        columns = {c['name']: c for c in inspector.get_columns(name, schema=schema)}
        if set(columns) != set(expected.c.keys()):
            raise MigrationError(f'Colunas PostgreSQL incompatíveis em {name}')
        for column in expected.c:
            actual = columns[column.name]
            if (str(actual['type'].compile(dialect=connection.dialect)) != str(column.type.compile(dialect=connection.dialect))
                    or actual['nullable'] != column.nullable):
                raise MigrationError(f'Tipo PostgreSQL incompatível em {name}, coluna {column.name}')
        identity = columns['id'].get('identity')
        if not identity or identity.get('always') or identity.get('increment') != 1 or identity.get('cycle'):
            raise MigrationError(f'Identidade PostgreSQL incompatível em {name}')
        if inspector.get_pk_constraint(name, schema=schema)['constrained_columns'] != ['id']:
            raise MigrationError(f'Chave primária incompatível em {name}')
        actual_fks = {
            (tuple(fk['constrained_columns']), fk['referred_table'], tuple(fk['referred_columns']),
             fk.get('options', {}).get('ondelete'), fk.get('referred_schema') or schema)
            for fk in inspector.get_foreign_keys(name, schema=schema)
        }
        expected_fks = {
            (tuple(c.name for c in fk.columns), fk.referred_table.name,
             tuple(e.column.name for e in fk.elements), fk.ondelete, schema)
            for fk in expected.foreign_key_constraints
        }
        if actual_fks != expected_fks:
            raise MigrationError(f'Vínculos PostgreSQL incompatíveis em {name}')
        expected_unique = {('company_id', 'id')} if name == 'imports' else set()
        actual_unique = {tuple(u['column_names']) for u in inspector.get_unique_constraints(name, schema=schema)}
        if actual_unique != expected_unique:
            raise MigrationError(f'Restrições PostgreSQL incompatíveis em {name}')
    return schema


def _empty(connection) -> None:
    for name in TABLE_COLUMNS:
        if connection.scalar(select(Base.metadata.tables[name].c.id).limit(1)) is not None:
            raise MigrationError(f'Destino ocupado em {name}; migração exige tabelas operacionais vazias')


def _verify(connection, source_db, expected: dict) -> None:
    counts = {}
    for name, columns in TABLE_COLUMNS.items():
        table = Base.metadata.tables[name]
        query = select(*(table.c[c] for c in columns)).order_by(table.c.id)
        counts[name] = 0
        with connection.execute(query.execution_options(stream_results=True, yield_per=1000)) as result:
            for old, new in zip_longest(iter_rows(source_db, name), result.mappings()):
                if old is None or new is None:
                    raise MigrationError(f'Contagem divergente em {name}')
                for column in columns:
                    if old[column] != new[column]:
                        raise MigrationError(f'Conferência divergente em {name}, ID {old["id"]}, coluna {column}')
                counts[name] += 1
    lines = Base.metadata.tables['payroll_lines']
    imports = Base.metadata.tables['imports']
    query = select(lines.c.company_id, imports.c.competencia, func.sum(lines.c.valor), func.sum(lines.c.liquido)).select_from(
        lines.outerjoin(imports, lines.c.import_id == imports.c.id)).group_by(lines.c.company_id, imports.c.competencia)
    totals = {(r[0], r[1]): [r[2] or Decimal(0), r[3] or Decimal(0)] for r in connection.execute(query)}
    actual = summarize(counts, totals, expected['extra_tables'])
    def comparable(report):
        return {(r['company_id'], r['competencia']): (Decimal(r['valor']), Decimal(r['liquido'])) for r in report['totals']}
    if counts != expected['counts'] or comparable(actual) != comparable(expected):
        raise MigrationError('Contagens ou totais divergentes na conferência')


def migrate(source: Path, engine: Engine, *, apply: bool = False) -> dict:
    if engine.dialect.name != 'postgresql':
        raise MigrationError('O destino deve ser PostgreSQL')
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            # Finish temporary cleanup before committing: even a cleanup failure rolls back.
            with snapshot(source) as source_db:
                summary = validate_source(source_db)
                if not apply:
                    connection.execute(text('SET TRANSACTION READ ONLY'))
                schema = _preflight(connection)
                quote = connection.dialect.identifier_preparer.quote
                if apply:
                    tables = ', '.join(f'{quote(schema)}.{quote(name)}' for name in TABLE_COLUMNS)
                    connection.execute(text(f'LOCK TABLE {tables} IN SHARE ROW EXCLUSIVE MODE'))
                    _preflight(connection)
                _empty(connection)
                if apply:
                    for name in TABLE_COLUMNS:
                        rows = iter_rows(source_db, name)
                        while batch := list(islice(rows, 1000)):
                            connection.execute(Base.metadata.tables[name].insert(), batch)
                    _verify(connection, source_db, summary)
                    for name in TABLE_COLUMNS:
                        maximum = connection.scalar(select(func.max(Base.metadata.tables[name].c.id)))
                        next_id = max((maximum or 0) + 1, 1)
                        connection.execute(text(f'ALTER TABLE {quote(schema)}.{quote(name)} ALTER COLUMN id RESTART WITH {next_id}'))
            try:
                transaction.commit()
            except BaseException:
                raise CommitUnknown('Resultado do commit indeterminado; confira o destino antes de repetir') from None
        except BaseException:
            if transaction.is_active:
                try:
                    transaction.rollback()
                except SQLAlchemyError:
                    pass  # Preserve the original error, especially an uncertain commit.
            raise
    return {'version': VERSION, 'mode': 'apply' if apply else 'simulate',
            'committed': apply, 'status': 'ok', **summary}
