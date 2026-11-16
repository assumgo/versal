"""Migrações leves para SQLite (recria tabelas incompatíveis)."""

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.produto import Produto
from app.utils.codigos import NUMERIC_CODE

PRODUTO_CODIGO_START = 1


def _add_column_if_missing(engine: Engine, table: str, column: str, ddl: str) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    columns = {item['name'] for item in inspector.get_columns(table)}
    if column in columns:
        return
    with engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {ddl}'))


def ensure_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    needs_equipamentos_rebuild = False
    if 'equipamentos' in tables:
        columns = {column['name'] for column in inspector.get_columns('equipamentos')}
        if (
            'produto_id' not in columns
            or 'codigo' not in columns
            or 'descricao' in columns
            or 'categoria_id' in columns
        ):
            needs_equipamentos_rebuild = True

    needs_alocacoes_rebuild = False
    if 'alocacoes' in tables:
        columns = {column['name'] for column in inspector.get_columns('alocacoes')}
        required = {'codigo', 'tipo', 'destino_tipo', 'quantidade', 'tre_id'}
        if not required.issubset(columns):
            needs_alocacoes_rebuild = True

    with engine.begin() as conn:
        if needs_equipamentos_rebuild or needs_alocacoes_rebuild:
            if 'tre_itens' in tables:
                conn.execute(text('UPDATE tre_itens SET alocacao_id = NULL'))
            if 'alocacoes' in tables:
                conn.execute(text('DROP TABLE IF EXISTS alocacoes'))
            if needs_equipamentos_rebuild:
                conn.execute(text('DROP TABLE IF EXISTS equipamentos'))

    Base.metadata.create_all(bind=engine)

    _add_column_if_missing(engine, 'alocacoes', 'data_previsao', 'data_previsao DATE')
    _add_column_if_missing(engine, 'tre_itens', 'marca', "marca VARCHAR(100) NOT NULL DEFAULT ''")
    _add_column_if_missing(engine, 'tre_itens', 'modelo', "modelo VARCHAR(100) NOT NULL DEFAULT ''")

    with Session(engine) as session:
        produtos = list(session.scalars(select(Produto).order_by(Produto.id.asc())).all())
        if any(not NUMERIC_CODE.match((p.codigo or '').strip()) for p in produtos):
            for index, produto in enumerate(produtos, start=PRODUTO_CODIGO_START):
                produto.codigo = f'{index:06d}'
            session.commit()
