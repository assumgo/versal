import re

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoUpdate

CODIGO_PREFIX = 'PRD-'
CODIGO_PATTERN = re.compile(r'^PRD-(\d+)$')


def list_produtos(db: Session) -> list[Produto]:
    return list(
        db.scalars(
            select(Produto).options(joinedload(Produto.categoria)).order_by(Produto.codigo.asc())
        ).unique().all()
    )


def get_produto(db: Session, produto_id: int) -> Produto | None:
    return db.scalars(
        select(Produto).options(joinedload(Produto.categoria)).where(Produto.id == produto_id)
    ).unique().first()


def get_by_codigo(db: Session, codigo: str) -> Produto | None:
    return db.scalars(select(Produto).where(Produto.codigo == codigo.strip())).first()


def generate_codigo(db: Session) -> str:
    """Gera próximo código único no formato PRD-000001."""
    codes = db.scalars(select(Produto.codigo)).all()
    max_n = 0
    for code in codes:
        match = CODIGO_PATTERN.match(code or '')
        if match:
            max_n = max(max_n, int(match.group(1)))
    next_n = max_n + 1
    while True:
        candidate = f'{CODIGO_PREFIX}{next_n:06d}'
        if not get_by_codigo(db, candidate):
            return candidate
        next_n += 1


def create_produto(db: Session, payload: ProdutoCreate) -> Produto:
    produto = Produto(
        codigo=generate_codigo(db),
        descricao=payload.descricao,
        marca=payload.marca,
        modelo=payload.modelo,
        categoria_id=payload.categoria_id,
    )
    db.add(produto)
    db.commit()
    return get_produto(db, produto.id)  # type: ignore[return-value]


def update_produto(db: Session, produto: Produto, payload: ProdutoUpdate) -> Produto:
    data = payload.model_dump(exclude_unset=True)
    # Código é imutável após a criação.
    data.pop('codigo', None)
    for key, value in data.items():
        setattr(produto, key, value)
    db.add(produto)
    db.commit()
    return get_produto(db, produto.id)  # type: ignore[return-value]


def delete_produto(db: Session, produto: Produto) -> None:
    db.delete(produto)
    db.commit()


def count_equipamentos(db: Session, produto_id: int) -> int:
    from app.models.equipamento import Equipamento

    return len(list(db.scalars(select(Equipamento.id).where(Equipamento.produto_id == produto_id)).all()))
