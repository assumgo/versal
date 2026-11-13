from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fornecedor import Fornecedor
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate


def list_fornecedores(db: Session) -> list[Fornecedor]:
    return list(db.scalars(select(Fornecedor).order_by(Fornecedor.razao_social.asc())).all())


def get_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor | None:
    return db.get(Fornecedor, fornecedor_id)


def get_by_documento(db: Session, documento: str) -> Fornecedor | None:
    return db.scalars(select(Fornecedor).where(Fornecedor.documento == documento)).first()


def create_fornecedor(db: Session, payload: FornecedorCreate) -> Fornecedor:
    fornecedor = Fornecedor(
        razao_social=payload.razao_social,
        nome_fantasia=payload.nome_fantasia,
        documento=payload.documento,
        ativo=payload.ativo,
    )
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def update_fornecedor(db: Session, fornecedor: Fornecedor, payload: FornecedorUpdate) -> Fornecedor:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(fornecedor, key, value)
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def delete_fornecedor(db: Session, fornecedor: Fornecedor) -> None:
    db.delete(fornecedor)
    db.commit()
