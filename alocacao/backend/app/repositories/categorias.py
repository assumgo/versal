from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


def list_categorias(db: Session, *, apenas_ativos: bool | None = None) -> list[Categoria]:
    query = select(Categoria).order_by(Categoria.nome.asc())
    if apenas_ativos is True:
        query = query.where(Categoria.ativo.is_(True))
    elif apenas_ativos is False:
        query = query.where(Categoria.ativo.is_(False))
    return list(db.scalars(query).all())


def get_categoria(db: Session, categoria_id: int) -> Categoria | None:
    return db.get(Categoria, categoria_id)


def get_by_nome(db: Session, nome: str) -> Categoria | None:
    return db.scalars(select(Categoria).where(Categoria.nome == nome.strip())).first()


def create_categoria(db: Session, payload: CategoriaCreate) -> Categoria:
    categoria = Categoria(
        nome=payload.nome.strip(),
        descricao=payload.descricao.strip() if payload.descricao else None,
        ativo=payload.ativo,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def update_categoria(db: Session, categoria: Categoria, payload: CategoriaUpdate) -> Categoria:
    data = payload.model_dump(exclude_unset=True)
    if 'nome' in data and data['nome'] is not None:
        data['nome'] = data['nome'].strip()
    if 'descricao' in data and isinstance(data['descricao'], str):
        data['descricao'] = data['descricao'].strip() or None
    for key, value in data.items():
        setattr(categoria, key, value)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def delete_categoria(db: Session, categoria: Categoria) -> None:
    db.delete(categoria)
    db.commit()
