from sqlalchemy import exists, select
from sqlalchemy.orm import Session, joinedload

from app.models.alocacao import Alocacao
from app.models.equipamento import Equipamento
from app.models.produto import Produto
from app.schemas.equipamento import EquipamentoCreate, EquipamentoUpdate, StatusEquipamento


def _ativo_alocado_exists():
    return exists().where(
        Alocacao.equipamento_id == Equipamento.id,
        Alocacao.ativa.is_(True),
    )


def equipamento_status(db: Session, equipamento_id: int) -> StatusEquipamento:
    ativa = db.scalars(
        select(Alocacao.id).where(
            Alocacao.equipamento_id == equipamento_id,
            Alocacao.ativa.is_(True),
        ).limit(1)
    ).first()
    return 'alocado' if ativa else 'disponivel'


def list_equipamentos(
    db: Session,
    *,
    categoria_id: int | None = None,
    status: StatusEquipamento | None = None,
) -> list[Equipamento]:
    query = (
        select(Equipamento)
        .options(joinedload(Equipamento.produto).joinedload(Produto.categoria))
        .order_by(Equipamento.id.asc())
    )
    if categoria_id is not None:
        query = query.join(Equipamento.produto).where(Produto.categoria_id == categoria_id)
    if status == 'alocado':
        query = query.where(_ativo_alocado_exists())
    elif status == 'disponivel':
        query = query.where(~_ativo_alocado_exists())
    return list(db.scalars(query).unique().all())


def get_equipamento(db: Session, equipamento_id: int) -> Equipamento | None:
    return db.scalars(
        select(Equipamento)
        .options(joinedload(Equipamento.produto).joinedload(Produto.categoria))
        .where(Equipamento.id == equipamento_id)
    ).unique().first()


def get_by_patrimonio(db: Session, numero_patrimonio: str) -> Equipamento | None:
    return db.scalars(
        select(Equipamento).where(Equipamento.numero_patrimonio == numero_patrimonio.strip())
    ).first()


def create_equipamento(db: Session, payload: EquipamentoCreate) -> Equipamento:
    equipamento = Equipamento(
        produto_id=payload.produto_id,
        numero_serie=payload.numero_serie,
        numero_patrimonio=payload.numero_patrimonio,
        mac_address=payload.mac_address,
    )
    db.add(equipamento)
    db.commit()
    return get_equipamento(db, equipamento.id)  # type: ignore[return-value]


def update_equipamento(db: Session, equipamento: Equipamento, payload: EquipamentoUpdate) -> Equipamento:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(equipamento, key, value)
    db.add(equipamento)
    db.commit()
    return get_equipamento(db, equipamento.id)  # type: ignore[return-value]


def delete_equipamento(db: Session, equipamento: Equipamento) -> None:
    inativas = db.scalars(
        select(Alocacao).where(
            Alocacao.equipamento_id == equipamento.id,
            Alocacao.ativa.is_(False),
        )
    ).all()
    for alocacao in inativas:
        db.delete(alocacao)
    db.delete(equipamento)
    db.commit()


def has_alocacao_ativa(db: Session, equipamento_id: int) -> bool:
    return equipamento_status(db, equipamento_id) == 'alocado'
