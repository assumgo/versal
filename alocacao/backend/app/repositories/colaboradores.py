from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.colaborador import Colaborador
from app.schemas.colaborador import ColaboradorCreate, ColaboradorUpdate


def list_colaboradores(db: Session) -> list[Colaborador]:
    return list(db.scalars(select(Colaborador).order_by(Colaborador.nome.asc())).all())


def get_colaborador(db: Session, colaborador_id: int) -> Colaborador | None:
    return db.get(Colaborador, colaborador_id)


def get_by_cpf(db: Session, cpf: str) -> Colaborador | None:
    return db.scalars(select(Colaborador).where(Colaborador.cpf == cpf)).first()


def get_by_email(db: Session, email: str) -> Colaborador | None:
    return db.scalars(select(Colaborador).where(Colaborador.email_pessoal == email.lower())).first()


def create_colaborador(db: Session, payload: ColaboradorCreate) -> Colaborador:
    colaborador = Colaborador(
        nome=payload.nome,
        email_pessoal=str(payload.email_pessoal).lower(),
        cpf=payload.cpf,
        data_nascimento=payload.data_nascimento,
        celular=payload.celular,
        ativo=payload.ativo,
    )
    db.add(colaborador)
    db.commit()
    db.refresh(colaborador)
    return colaborador


def update_colaborador(db: Session, colaborador: Colaborador, payload: ColaboradorUpdate) -> Colaborador:
    data = payload.model_dump(exclude_unset=True)
    if 'email_pessoal' in data and data['email_pessoal'] is not None:
        data['email_pessoal'] = str(data['email_pessoal']).lower()
    for key, value in data.items():
        setattr(colaborador, key, value)
    db.add(colaborador)
    db.commit()
    db.refresh(colaborador)
    return colaborador


def delete_colaborador(db: Session, colaborador: Colaborador) -> None:
    db.delete(colaborador)
    db.commit()
