"""Migrações leves para SQLite (recria tabelas incompatíveis)."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.session import Base


def ensure_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    needs_equipamentos_rebuild = False
    if 'equipamentos' in tables:
        columns = {column['name'] for column in inspector.get_columns('equipamentos')}
        # Schema antigo tinha descricao/categoria_id; o novo usa produto_id.
        if 'produto_id' not in columns or 'descricao' in columns or 'categoria_id' in columns:
            needs_equipamentos_rebuild = True

    if needs_equipamentos_rebuild:
        with engine.begin() as conn:
            if 'alocacoes' in tables:
                conn.execute(text('DELETE FROM alocacoes'))
            conn.execute(text('DROP TABLE IF EXISTS equipamentos'))

    Base.metadata.create_all(bind=engine)
