from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.alocacao import Alocacao
from app.models.local import Local
from app.schemas.local import LocalCreate, LocalUpdate
from app.utils.codigos import next_numeric_codigo

LOCAL_CODIGO_START = 1


def generate_codigo(db: Session) -> str:
    codes = list(db.scalars(select(Local.codigo)).all())
    return next_numeric_codigo(codes, start=LOCAL_CODIGO_START)


def list_locais(db: Session, *, q: str | None = None) -> list[Local]:
    query = select(Local).order_by(Local.codigo.asc())
    if q and q.strip():
        term = f'%{q.strip()}%'
        query = query.where(or_(Local.nome.ilike(term), Local.codigo.ilike(term)))
    return list(db.scalars(query).all())


def get_local(db: Session, local_id: int) -> Local | None:
    return db.get(Local, local_id)


def create_local(db: Session, payload: LocalCreate) -> Local:
    local = Local(codigo=generate_codigo(db), nome=payload.nome, descricao=payload.descricao)
    db.add(local)
    db.commit()
    db.refresh(local)
    return local


def update_local(db: Session, local: Local, payload: LocalUpdate) -> Local:
    data = payload.model_dump(exclude_unset=True)
    data.pop('codigo', None)
    for key, value in data.items():
        setattr(local, key, value)
    db.add(local)
    db.commit()
    db.refresh(local)
    return local


def delete_local(db: Session, local: Local) -> None:
    db.delete(local)
    db.commit()


def count_alocacoes(db: Session, local_id: int) -> int:
    return len(list(db.scalars(select(Alocacao.id).where(Alocacao.local_id == local_id)).all()))
